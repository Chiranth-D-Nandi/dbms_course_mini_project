> Historical audit of the original checkout. Its findings drove the implementation fixes; see `testing_results.md` and the current README for the finished behavior and verification.

# Project completeness review

Reviewed 6 November 2026 against commit `7453f8f` and the repository's functional requirements. No external assignment rubric was supplied. Application source was not changed during this review.

## Verdict

The project is substantially implemented but is not complete or ready for an end-to-end demonstration. SQL schema, procedures, triggers, views, seed scripts, backend endpoints, frontend screens, and documentation exist. The main gaps are integration, missing customer pages, payment correctness, and reliable verification.

## Blocking findings

1. **Missing customer routes.** The tracked frontend has no pages for `/book/[runId]`, `/pay/[pnr]`, `/bookings/[pnr]`, or `/trains/[id]`. `TrainCard.tsx` and `bookings/page.tsx` link to these paths. Customers cannot complete the documented search → reserve → pay → view/cancel ticket flow. Existing seat-map and countdown components do not supply these missing pages.

2. **Train search contract does not match.** `frontend/src/lib/api.ts` sends `from` and `to`, but `TrainSearchView` requires `source` and `dest`. The frontend expects an array of trains with nested `availability`; the backend returns an envelope containing flat per-class `trains` rows. Fixing parameter names alone will still leave `.filter`/`.map` failures in the search UI. Direct invocation confirmed a 400 MISSING_PARAMETERS response for a request without `source` and `dest`.

3. **Other API paths and response shapes diverge.** The frontend uses `/bookings/mine` instead of `/bookings/my/`, `/bookings/{pnr}/pay` instead of `/payments/confirm/`, `/admin/reports/revenue` instead of `/admin/revenue/`, and `/admin/audit-log` instead of `/admin/audit-logs/`. Occupancy and Tatkal-demand report routes do not exist. The inventory screen calls `/admin/runs/{id}/generate-inventory`, which does not exist; the backend creates runs via POST `/admin/runs/`. FAQ/vector methods expect arrays but the backend returns `{results, ...}`. Profile and seat-map responses also need adapters. Standardize trailing slashes, especially for POST requests, instead of relying on GET redirects.

4. **Anyone can register as an administrator.** `RegisterRequestSerializer` accepts `ADMIN`; the unauthenticated registration endpoint persists the submitted role. A direct serializer check accepted an ADMIN registration payload. This undermines all admin endpoint restrictions. Public registration should create customers; admin provisioning needs a trusted path. The FRS itself permits role selection and should be corrected too.

5. **Payment lacks booking ownership enforcement.** `ConfirmPaymentView` selects `user_id` but never checks it against the authenticated user. A signed-in customer can submit another user's PNR to the payment simulation. Enforce owner/admin authorization before processing or returning payment details.

6. **Idempotency keys are not bound to a booking.** `sp_confirm_payment` returns SUCCESS for any existing key without comparing its PNR/amount/method. The API then returns that key's payment details while claiming the requested PNR is confirmed. A reused key can therefore produce false confirmation and expose another transaction. Concurrent same-key requests are not covered by a robust retry path either. Check the key's request identity under appropriate transaction control and return the original result only for equivalent requests.

7. **Expired payment can leave a seat unavailable for reuse.** The expired-payment branch frees `run_seat` and changes booking status but does not clear passenger `(run_id, seat_id)` references. The unique passenger seat constraint can reject subsequent allocations until the scheduled sweeper clears those references. Payment and sweeper should use one consistent transactional expiration operation. The sweeper itself updates seats, bookings, and passengers in separate statements without an explicit transaction; payment/expiry races require real concurrent tests.

8. **Revenue view multiplies money by inventory size.** `v_admin_revenue` joins bookings and all `run_seat` rows for each run before summing fares/refunds. For example, one confirmed fare of 100 with 80 inventory rows contributes 8,000. DISTINCT booking counts do not fix the sums. Separately, cancellation removes a fare from gross revenue but still subtracts its refund, which can create negative net revenue unrelated to actual receipts. Aggregate payments/refunds and inventory independently before joining.

## Further requirements and implementation gaps

9. **Manual expiry endpoint has the wrong procedure signature.** `AdminReleaseHoldsView` calls `sp_release_expired_holds(@p_released_count)`, but the SQL procedure takes zero arguments. The manual sweep will fail.

10. **Hold duration conflicts.** README, FRS, screenshots, and testing narrative describe eight minutes. The procedure assigns five minutes to bookings and seats; the help UI describes five minutes. Choose and apply one requirement consistently.

11. **Refund requirement is only partially implemented.** The FRS distinguishes >48, 48–12, 12–4, and <4 hours. SQL has only >48, >=12, and otherwise zero; no separate 12–4 tier exists. Departure calculation ignores the boarding stop's `day_offset`. Clarify the intended project policy and add boundary tests; this review does not certify the documentation's claims about official railway rules.

12. **Deadlock retry is bypassed for stored-procedure deadlocks.** SQL catches error 1213 and returns `DEADLOCK_RETRY`; `BookTicketView` retries only raised exceptions and returns 409 for a non-PENDING output. Handle this output explicitly or propagate a retriable exception.

13. **Refresh tokens cannot be refreshed through the supplied backend.** The frontend posts to `/auth/refresh`, but no refresh route exists. It also does not store a rotated refresh token. Token expiry breaks the promised session continuity.

14. **Validation and schema disagree.** The API accepts `PREMIUM_TATKAL` and `DRIVING_LICENSE`, which the SQL enums do not support. Payment PNR is read outside serializer validation and converted with `int()`. The serializer requires a body idempotency key even when the header is supplied, despite the documented header contract. Align accepted values and validate complete requests before executing SQL.

15. **Environment template does not control the documented settings.** `.env.example` uses `DJANGO_SECRET_KEY`, `DJANGO_DEBUG`, and `DJANGO_ALLOWED_HOSTS`; settings read `SECRET_KEY` and `DEBUG` and hardcode wildcard hosts. CORS and JWT settings in the template are also not applied. Changing the documented secret does not change the signing key actually used. Vector path settings are hardcoded too.

16. **Tests and evidence are insufficient for completion claims.** Backend tests depend on a pre-seeded database and the concurrency test directly uses that database. It asserts at least one successful booking and no duplicate allocations among successes, but does not reject every worker error or prove the report's claim that all 16 succeeded. The Locust script treats every 409 as expected success, masking unrelated booking failures. E2E tests include a missing booking route and text that differs from the current UI. No raw benchmark artifacts or actual screenshot images were found supporting the published latency/results tables; `screenshots.md` contains descriptions/ASCII mockups. Existing results were not independently reproduced in this review.

## Verification performed

- Cloned the remote's current default branch; reviewed commit `7453f8f`.
- Installed frontend dependencies using `npm ci`; typecheck passed.
- Installed core Django/DRF/test dependencies in a local `.venv` for review.
- Direct checks: ADMIN registration payload accepted; payment serializer rejects missing body idempotency key; search without `source`/`dest` returns 400.
- Model pytest collected four tests but stopped on database connection setup in the sandbox. A subsequent permitted read-only connection reached MySQL and was rejected with error 1045 for the repo's configured `app_ro` account. No database initialization/reset, seed, booking, or concurrency mutations were performed.
- Django system check was blocked by absent ChromaDB dependencies in the partial review environment. Full ML dependencies/model were not installed; this is an environment limitation, not evidence that installing requirements fails.
- Production build passed after rerunning outside the sandbox following a file-permission failure. Its generated route table confirms that booking, payment, ticket-detail, and train-detail pages are absent. A successful build does not validate the frontend/backend contracts or live workflows.

## Completion order

1. Align API routes, parameters, and response models; implement missing customer pages.
2. Fix admin provisioning, payment authorization/idempotency, expiration consistency, and revenue math.
3. Reconcile hold/refund rules, enum validation, refresh routing, environment configuration, and deadlock retry.
4. Configure an isolated MySQL test database, install full vector dependencies, ingest the model/data, and verify the entire customer/admin workflow.
5. Run meaningful concurrency/expiry/idempotency/refund tests, collect actual load-test artifacts and screenshots, and update documentation from measured results.

An assignment rubric is still needed to certify academic deliverable completeness (for example normalization, report format, presentation, or required query counts).
