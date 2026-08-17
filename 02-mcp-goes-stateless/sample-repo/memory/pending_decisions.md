# Pending decisions

Sample data for `protocol_diff.py` to read against — not real project state,
just enough content for `list_pending_decisions` to have something to return.

| Decision | Current setting | Trigger to act | Direction |
|---|---|---|---|
| Database choice | Postgres, single instance | Read replicas needed once traffic grows | Add a replica when p95 query latency crosses 200ms |
| Deploy cadence | Manual, ad-hoc | Team grows past 2 people | Move to CI-gated deploys |
