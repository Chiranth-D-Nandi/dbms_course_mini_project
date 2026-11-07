# Demonstration walkthrough

1. Start `scripts/dev.ps1` and open http://localhost:3000.
2. Log in as `chiranth@example.com` / `Customer@123`.
3. Search SBC to MAS for three days from today, choose AC 3 Tier, and inspect a halt schedule.
4. Select Book General, inspect the map, and enter one or two demo passengers (do not use real identity data).
5. Reserve seats. Show the eight-minute countdown and assigned coach/seat numbers.
6. Complete simulated payment. Show the confirmed ticket and print option.
7. Open My Bookings; view the ticket and cancel it. Explain the displayed demo refund.
8. Search Help for `tatkal cancellation refund` and show similarity-ranked policy matches.
9. On the homepage search semantic train descriptions and open a matching timetable.
10. Log out; log in as `admin@tatkal.com` / `Admin@123`. Show real revenue/occupancy values and trigger audit state changes.
11. Open Train Runs, enter a train ID from the catalog and an unseeded future date; create inventory. Run the manual expiry sweep.
12. To demonstrate actual race protection run `scripts/demo_concurrency.ps1`. To show fast-forwarded expiry run `scripts/demo_expiry.ps1`. Both execute isolated database tests.

Explain that MySQL owns the transaction and locks, Django validates/authorizes API requests, and Next.js renders the workflow. Chroma handles discovery only; it never allocates seats.

The project uses simulated payments and simplified refund rules. Do not claim official railway affiliation, real financial settlement, guaranteed latency, or a proof of correctness from a finite stress test.
