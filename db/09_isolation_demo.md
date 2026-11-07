# Transaction isolation and point locking

Django's MySQL connections use READ COMMITTED by default. Reservation correctness comes from explicit exclusive row locks, transaction boundaries and unique active seat allocation, rather than from plain snapshot reads alone. The MySQL server default for a separate CLI session may be REPEATABLE READ.

Run this exercise in two MySQL sessions connected to a disposable/demo database. Both sessions first choose the same available inventory key:

```sql
SET SESSION TRANSACTION ISOLATION LEVEL READ COMMITTED;
SET @run=(SELECT MIN(run_id) FROM train_run WHERE journey_date>CURDATE());
SET @seat=(SELECT MIN(seat_id) FROM run_seat WHERE run_id=@run AND seat_status='AVAILABLE');
```

In Session A:

```sql
START TRANSACTION;
SELECT seat_id FROM run_seat WHERE run_id=@run AND seat_id=@seat FOR UPDATE;
-- Leave this transaction open briefly.
```

In Session B:

```sql
START TRANSACTION;
SELECT seat_id FROM run_seat WHERE run_id=@run AND seat_id=@seat FOR UPDATE SKIP LOCKED;
-- No row: Session A owns the lock. Without SKIP LOCKED this query would wait.
ROLLBACK;
```

Finally run `ROLLBACK` in Session A. This exercise changes no seat state.

The booking procedure discovers candidate IDs without locking coach rows, then attempts exact `(run_id,seat_id)` locking reads. Its lock acquisition does not scan/sort and lock the entire inventory before applying a seat limit. Multi-passenger allocation commits only when every requested seat was secured.

The automated oversubscription test synchronizes 16 workers for eight available seats and verifies eight holds, eight sold-out responses and no duplicate assignments. A finite test validates the observed execution, not every possible future schedule. See the [MySQL locking-read documentation](https://dev.mysql.com/doc/refman/8.0/en/innodb-locking-reads.html).
