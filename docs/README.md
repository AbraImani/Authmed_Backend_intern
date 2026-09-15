# AuthMed documentation

Current implementation: [repository setup](../README.md),
[runtime and migration notes](phase1_5/runtime.md),
[cleanup report](phase1_5/report.md). Generate `/api/schema/` for the actual API.

Implementation records (historical snapshots, not current setup instructions):

- [Phase 0 report](phase0/report.md)
- [Phase 1 report](phase1/report.md)
- [Phase 1 identity design](phase1/identity.md)
- [Phase 1 tenant model and role matrix](phase1/tenancy.md)

Phase 1.5 supersedes the older JWT/dependency/dataset setup instructions.
Historical dependency locks are stored alongside those phase reports.

The product/, workflows/, architecture/, data-model/, deployment/ and
sequences/ folders contain product intent and proposed diagrams for later
phases. They are excluded from runtime images and do not assert implemented
endpoints, production deployments or final business guarantees. Phase 2/5/6/8
will reconcile their relevant designs during implementation. No production
configuration or executable code depends on these documents.
