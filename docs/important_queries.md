# SQL query demonstrations

The executable examples are in `db/07_queries.sql` and `db/08_explain_demo.sql`. They use the actual composite-key schema, with PNR as the booking key.

| Example | Concept | Why it matters |
| --- | --- | --- |
| Timetable | Multi-table JOIN through `v_train_route` | Reconstruct ordered stops and derived halt durations |
| Popular runs | CTE, GROUP BY, HAVING, SUM and AVG | Count passengers separately so fares are not multiplied by joins |
| Booking ranking | ROW_NUMBER, DENSE_RANK and running SUM | Compare booking values and cumulative fare per train |
| Station roles | Correlated EXISTS and MAX | Find stations that originate and terminate routes |
| Inventory summary | CTE and conditional aggregates | Report available, held and booked seats per run/class/quota |
| Station relevance | FULLTEXT MATCH/AGAINST | Rank indexed station names and cities |
| Plans | EXPLAIN TREE/JSON and EXPLAIN ANALYZE | Inspect actual index choices and observed execution |

To execute against the configured local database and check every statement:

```powershell
.\.venv\Scripts\python.exe scripts/document_schema.py --check-queries
```

The script uses the read-only application account. SQL files say `USE tatkal_db` when run directly; the script substitutes `MYSQL_DATABASE` from `.env`. EXPLAIN output depends on local data and server configuration; no constant execution time or row count is promised.
