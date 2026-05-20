# AuthMed Documentation

## Product Overview

**AuthMed** is repositioned as a **Medicine Intake Inspection and Risk-Control Solution** for healthcare structures.

It transforms medicine lot reception from a manual, untraced process into a digitalized workflow with:
- Automated batch inspection workflows
- Evidence capture and documentation
- Intelligent risk scoring
- Nuanced operational decision-making (Accept/Isolate/Escalate)
- Complete audit trails for compliance
- Multi-site, multi-user support
- Real-time monitoring dashboards

## Documentation Purpose

This documentation provides:
1. **Product understanding** - What is AuthMed and why it matters
2. **Architectural clarity** - How the system is structured
3. **Workflow guidance** - How inspections flow through the system
4. **Data modeling** - What objects exist and how they relate
5. **Developer onboarding** - How to implement and extend the system
6. **Deployment readiness** - How to operate AuthMed in production

## Quick Start for Interns

**Recommended Reading Order:**

### Phase 1: Product Understanding (30 min)
1. [Product Transformation Vision](product/product-transformation.md) - Understand the shift from "scan app" to "risk control system"
2. [Product Context](product/product-context.md) - See AuthMed in its ecosystem
3. [End-to-End Product Flow](product/end-to-end-product-flow.md) - Follow a complete batch inspection journey

### Phase 2: Business Understanding (45 min)
4. [Business Capability Map](product/business-capability-map.md) - Core capabilities and features
5. [Business Workflow](workflows/business-workflow.md) - Complete inspection workflow
6. [Use Cases](workflows/use-cases.md) - Actor interactions

### Phase 3: System Architecture (60 min)
7. [Architecture Overview](authmed-architecture-overview.md) - System at a glance
8. [C4 System Context](architecture/c4-system-context.md) - External interactions
9. [C4 Container Diagram](architecture/c4-container.md) - Major components
10. [C4 Component Diagram](architecture/c4-component-backend.md) - Backend internals

### Phase 4: Data & Workflows (45 min)
11. [Domain Model](data-model/domain-model.md) - Business entities and relationships
12. [Entity Relationship Diagram](data-model/erd.md) - Database structure
13. [Batch Inspection State Machine](workflows/batch-inspection-state-machine.md) - Inspection lifecycle

### Phase 5: Integration & Operations (60 min)
14. [API Interactions](architecture/api-interactions.md) - How components communicate
15. [Data Flow](architecture/data-flow.md) - Data movement through the system
16. [RBAC Matrix](architecture/rbac-matrix.md) - Who can do what
17. [Deployment Architecture](deployment/deployment-diagram.md) - Production environment

### Phase 6: Detailed Workflows (60 min)
18. [Activity Diagram](workflows/activity-diagram.md) - Detailed inspection process
19. [Sequence: Login](sequences/sequence-login.md) - JWT authentication
20. [Sequence: Create Inspection](sequences/sequence-create-inspection.md) - Batch creation
21. [Sequence: Add Evidence](sequences/sequence-add-evidence.md) - Proof capture
22. [Sequence: Risk Result](sequences/sequence-risk-result.md) - Scoring process
23. [Sequence: Review Decision](sequences/sequence-review-decision.md) - Human review
24. [Sequence: Dashboard](sequences/sequence-dashboard.md) - Monitoring
25. [Sequence: Audit Log](sequences/sequence-audit-log.md) - Traceability

### Phase 7: Delivery Roadmap (15 min)
26. [MVP / Phase Mapping](product/mvp-phase-mapping.md) - What's built, what's next

---

## Documentation Structure

```
docs/
├── README.md (this file)
├── authmed-architecture-overview.md
├── product/
│   ├── product-transformation.md
│   ├── product-context.md
│   ├── business-capability-map.md
│   ├── mvp-phase-mapping.md
│   └── end-to-end-product-flow.md
├── workflows/
│   ├── use-cases.md
│   ├── business-workflow.md
│   ├── activity-diagram.md
│   └── batch-inspection-state-machine.md
├── data-model/
│   ├── domain-model.md
│   └── erd.md
├── architecture/
│   ├── c4-system-context.md
│   ├── c4-container.md
│   ├── c4-component-backend.md
│   ├── api-interactions.md
│   ├── data-flow.md
│   └── rbac-matrix.md
├── sequences/
│   ├── sequence-login.md
│   ├── sequence-create-inspection.md
│   ├── sequence-add-evidence.md
│   ├── sequence-risk-result.md
│   ├── sequence-review-decision.md
│   ├── sequence-dashboard.md
│   └── sequence-audit-log.md
└── deployment/
    └── deployment-diagram.md
```

---

## Key Concepts

### The Inspection Workflow
1. **Reception** - Batch arrives at healthcare facility
2. **Registration** - Lot is identified and logged
3. **Inspection** - Inspector performs field inspection
4. **Evidence** - Photos, documents, notes are captured
5. **Extraction** - Batch data is extracted/confirmed
6. **Scoring** - Risk is automatically calculated
7. **Decision** - System recommends Accept/Isolate/Escalate
8. **Review** - Reviewer validates decision (if needed)
9. **Execution** - Decision is acted upon
10. **Audit** - Entire flow is traceable and compliant

### Core Business Objects
- **Organization** - Healthcare structure (hospital, pharmacy)
- **Site** - Physical location within organization
- **User** - Team members with specific roles
- **Supplier** - Pharma supplier/distributor
- **ProductReference** - Catalog of known products
- **BatchInspection** - The central entity tracking an inspection
- **Evidence** - Photos, documents, notes
- **RiskResult** - Automated risk score
- **ReviewDecision** - Human-made operational decision
- **AuditLog** - Complete activity trail

### User Roles
- **Inspector** - Conducts field inspections, captures evidence
- **Reviewer** - Reviews and approves inspection decisions
- **Admin** - System administration and configuration
- **Organization Manager** - Site and team oversight
- **Quality Officer** - Quality assurance and compliance auditing

---

## Using These Diagrams

All diagrams are created in **Mermaid** format and are fully compatible with:
- GitHub (renders directly in repositories)
- GitLab
- Notion
- Confluence
- VS Code (with Markdown Preview Enhancement)
- Any Markdown previewer that supports Mermaid

To view locally in VS Code, install the "Markdown Preview Enhanced" extension.

---

## Questions?

Refer to:
1. The [Architecture Overview](authmed-architecture-overview.md) for high-level answers
2. Specific domain files for detailed questions
3. Backend code comments and docstrings for implementation details
4. The project's README.md for setup and running instructions

---

**Last Updated:** May 19, 2026
**Version:** 1.0
**Status:** Complete for MVP + Phase 1 & 2
