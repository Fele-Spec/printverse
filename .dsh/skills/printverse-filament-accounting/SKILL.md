---
name: printverse-filament-accounting
description: Design and verify PrintVerse's dual virtual/physical filament ledger, quotas, first-print-free rule, idempotent reservations, and administrator unlimited mode. Use when implementing balances, metering, entitlements, or billing-adjacent logic without processing real payments.
whenToUse: A task mentions filament grams, virtual spools, quotas, free first print, admin entitlement, refunds, or cost accounting.
metadata:
  version: "0.1.0"
  owner: PrintVerse
  license: MIT
  requires: [database, backend, pydantic]
---

# PrintVerse Filament Accounting

## Non-negotiable boundary

This skill implements accounting only. It does **not** process payments, store card data, or
call a payment provider. Monetary top-ups remain a separate, explicitly authorized project.

## Two ledgers, one unit

- **Virtual ledger** — grams consumed by the digital twin and AI generation quota.
- **Physical ledger** — grams estimated for a real spool, reconciled only after a real print.

Both use integer milligrams (`mg`) internally, never floats. Display grams with three
decimals. A conversion is `grams = mg / 1000`.

## Rules

1. New verified user gets one `first_print_free` entitlement. It covers the first completed
   virtual print only; cancellation before completion releases the reservation and does not
   consume it.
2. A print creates a **reservation** before slicing output is released to the simulator.
   On completion, commit the reservation. On failure/cancel, release it.
3. All mutations are idempotent by `operation_id`; retries must not double-charge.
4. Admin `unlimited_virtual` bypasses balance checks but still writes usage records for
   analytics and abuse detection.
5. Physical and virtual balances are separate. A virtual grant never implies a real spool.
6. Never allow a negative available balance; enforce it in the database transaction, not only
   in UI code.
7. Every ledger entry stores: user, kind (`grant|reserve|commit|release|adjust`), mg,
   operation_id, print_id, actor, reason, created_at, and before/after balance.

## Suggested tables

```sql
users(id, role, first_print_used_at)
wallets(user_id, virtual_mg, physical_mg, version)
ledger(id, user_id, kind, mg, operation_id UNIQUE, print_id, actor, reason, created_at)
print_jobs(id, user_id, status, estimated_g_mg, committed_g_mg, created_at, completed_at)
```

Use `SELECT ... FOR UPDATE` or an equivalent optimistic version check. A unique constraint on
`operation_id` is the last line of defense against duplicate charges.

## Verification tests

- Two identical commit requests → one ledger row, one balance change.
- Reserve 10 g, cancel → available balance restored exactly.
- Complete → entitlement consumed once; second print requires balance.
- Admin has unlimited virtual use, but usage rows still appear.
- Concurrent reserve requests cannot drive available below zero.
- Estimated vs committed grams differ; both are retained.
- A physical reconciliation cannot mutate the virtual wallet.

## Failure handling

| Symptom | Action |
|---|---|
| negative balance | roll back transaction, emit audit event, return 409 |
| duplicate operation | return the original result, do not insert |
| missing price/entitlement | fail closed; do not guess |
| real payment requested | stop; require separate written authorization |

## Outputs

Schema/migration, service code, deterministic unit tests, and a reconciliation report.
