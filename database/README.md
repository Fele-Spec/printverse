# Database

Planned PostgreSQL schema (integer milligrams for all balances):

```sql
users(id, email, role, first_print_used_at, created_at)
wallets(user_id PK, virtual_mg BIGINT, physical_mg BIGINT, version BIGINT)
ledger(id, user_id, kind, mg BIGINT, operation_id TEXT UNIQUE, print_id, actor, reason, created_at)
print_jobs(id, user_id, status, estimated_g_mg BIGINT, committed_g_mg BIGINT, created_at, completed_at)
entitlements(user_id, kind, consumed_at)
```

Rules: one ledger row per `operation_id`, no negative available balance, separate virtual and
physical wallets, admin unlimited virtual still logs usage. No payment tables in this phase.
