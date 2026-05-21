# AuthMed Architecture Overview

## Executive Summary

AuthMed is a **Medicine Intake Inspection and Risk-Control System** that digitizes and automates the process of inspecting pharmaceutical batches upon receipt at healthcare facilities.

**Core Value Proposition:**
- Transform manual, untraced medicine receiving into a traceable, risk-scored workflow
- Empower pharmacists, inspectors, and quality officers with data-driven decision-making
- Ensure compliance and maintain complete audit trails
- Scale across multiple healthcare sites and organizations

---

## Product Repositioning

### From: "Medicine Scan App"
A simple barcode scanning application that immediately returned accept/reject results.
- Limited documentation
- No evidence capture
- No risk nuance
- No audit trail
- Single-user experience
- Compliance gaps

### To: "Medicine Intake Inspection & Risk-Control System"
An enterprise workflow platform that manages the complete inspection lifecycle with human oversight.
- Multi-step workflow
- Rich evidence documentation
- Intelligent risk scoring
- Complete audit trails
- Multi-user, multi-site
- Compliance-ready
- Dashboard monitoring

---

## Main Workflow (Simplified)

```
Reception → Inspection → Evidence Capture → Data Extraction → Risk Scoring
    ↓
Operational Decision → Human Review (if needed) → Execution → Audit & Dashboard
```

**Timeline:** ~2-5 minutes per batch (depending on complexity)

---

## Core Business Objects

### Entities

| Entity | Purpose | Key Fields |
|--------|---------|-----------|
| **Organization** | Healthcare structure group | name, address, contact |
| **Site** | Physical location | org_id, name, address |
| **User** | Team member | username, email, role, org_id, site_id |
| **Supplier** | Pharma supplier | name, address, contact, history |
| **ProductReference** | Known products | name, sku, description, org_id |
| **BatchInspection** | **Central entity** | batch_number, status, outcome, inspector_id, site_id |
| **Evidence** | Proof documents | file_path, file_type, notes, inspection_id |
| **RiskResult** | Scored risk | risk_score, reason, flags, inspection_id |
| **ReviewDecision** | Decision made | decision, notes, reviewer_id, inspection_id |
| **AuditLog** | Activity trail | actor_id, action, object_type, timestamp |

### Relationships

```
Organization (1) ──→ (many) Site
Organization (1) ──→ (many) User
Organization (1) ──→ (many) BatchInspection

Site (1) ──→ (many) BatchInspection
Site (1) ──→ (many) User

User (1) ──→ (many) BatchInspection (as inspector)
User (1) ──→ (many) ReviewDecision (as reviewer)

Supplier (1) ──→ (many) BatchInspection
ProductReference (1) ──→ (many) BatchInspection

BatchInspection (1) ──→ (many) Evidence
BatchInspection (1) ──→ (1) RiskResult
BatchInspection (1) ──→ (many) ReviewDecision
BatchInspection (1) ──→ (many) AuditLog
```

---

## System Architecture

### Technology Stack

| Layer | Technology | Purpose |
|-------|-----------|---------|
| **Backend** | Django + Django REST Framework | API, business logic, auth |
| **Database** | PostgreSQL | Persistent data storage |
| **Mobile** | React Native / Flutter (future) | Field inspection app |
| **Web Dashboard** | React / Vue (future) | Monitoring and review UI |
| **Storage** | S3 / Object Storage | Evidence file storage |
| **Cache** | Redis (future) | Performance optimization |
| **Monitoring** | Prometheus + ELK (future) | Observability |

### Architecture Layers

```
┌─────────────────────────────────────────────┐
│           Clients (Mobile + Web)            │
├─────────────────────────────────────────────┤
│         Django REST API Layer               │
├─────────────────────────────────────────────┤
│   Business Logic (Inspection, Risk, etc)    │
├─────────────────────────────────────────────┤
│   Database (PostgreSQL) + Storage (S3)      │
└─────────────────────────────────────────────┘
```

### Key Components

**Backend (Django):**
- JWT Authentication
- Organization & User Management
- Inspection Orchestration
- Risk Scoring Engine
- Decision Logic
- Audit Logging
- Dashboard APIs
- Role-Based Access Control

**Database:**
- Organization, Site, User
- Supplier, ProductReference
- BatchInspection (central)
- Evidence (metadata)
- RiskResult
- ReviewDecision
- AuditLog

**Storage:**
- Evidence files (photos, documents)
- Backups
- Future: ML model artifacts

---

## Batch Inspection Lifecycle

```
Draft → Pending → Under Inspection → Pending Review → Review
    ↓
    └─→ Accepted / Isolated / Escalated → Completed / Archived
```

### State Transitions

| State | Meaning | Next | Who |
|-------|---------|------|-----|
| **Draft** | Created but not started | Pending | Inspector |
| **Pending** | Assigned, waiting to start | Under Inspection | Inspector |
| **Under Inspection** | Evidence being captured | Pending Review | Inspector |
| **Pending Review** | Queue for reviewer | Review | System |
| **Review** | Reviewer validating | Accepted/Isolated/Escalated | Reviewer |
| **Accepted** | OK, ready for stock | Completed | Reviewer |
| **Isolated** | Suspect, quarantine | Completed | Reviewer |
| **Escalated** | Critical, requires direction | Completed | Reviewer |
| **Completed** | Decision executed | Archived | System |
| **Archived** | Final state, historical | - | - |

---

## Operational Decision Outcomes

At the end of an inspection, the system enforces **exactly one** of three decisions:

### ACCEPTED
- Risk score is below threshold
- No anomalies detected
- Physical inspection passed
- **Action:** Batch released to stock

### ISOLATED
- Risk score in medium range
- Minor anomalies detected
- Requires quarantine or separate handling
- **Action:** Batch quarantined for further analysis

### ESCALATED
- Risk score exceeds threshold
- Major anomalies or suspicious signs detected
- Requires immediate escalation to management or quality officers
- **Action:** Escalated to management for investigation

---

## Multi-Site & Multi-User Support

### Organization Hierarchy

```
Organization (e.g., "National Hospital Group")
├── Site A (e.g., "Main Pharmacy")
│   ├── Users (Inspector, Reviewer, Manager)
│   └── Batches Received
├── Site B (e.g., "Emergency Dept")
│   ├── Users (Inspector, Reviewer, Manager)
│   └── Batches Received
└── Site C (e.g., "Warehouse")
    ├── Users (Inspector, Reviewer, Manager)
    └── Batches Received
```

### User Roles & Visibility

- **Inspector** - Can see own site's inspections
- **Reviewer** - Can see all org's inspections (if approval required)
- **Site Manager** - Can see own site's metrics
- **Org Manager** - Can see all org's metrics and trends
- **Quality Officer** - Can see all data for audit
- **Admin** - Can see and manage everything

---

## Audit & Compliance

### Traceability

Every action is logged:
- Who created what
- When actions occurred
- What changed
- Why (notes/comments)

### Compliance Features

- Complete audit trail (immutable)
- Timestamp on all records
- Actor identification (who did what)
- Evidence attachment and versioning
- PDF export for regulatory submission
- Multi-site traceability

### Reporting

- Batch history reports
- Supplier performance trends
- Risk distribution analysis
- Compliance audits
- Executive summaries

---

## MVP vs. Phases Roadmap

### MVP (Foundation - Already in Backend)
- [x] User Authentication (JWT)
- [x] Multi-org/Site support
- [x] Batch Inspection CRUD
- [x] Evidence Capture (file storage)
- [x] Basic Risk Scoring
- [x] Simple Decisions
- [x] Audit Logging
- [x] Database Schema
- [x] REST API Foundation
- [x] Test Suite

### Phase 1 (Review & Monitoring)
- [ ] Review Queue Management
- [ ] Reviewer Workflow
- [ ] Decision Queue
- [ ] Basic Dashboard (KPI, batch status)
- [ ] Email Notifications
- [ ] Approval Chain

### Phase 2 (Optimization & Reporting)
- [ ] Assisted Data Extraction (OCR ready)
- [ ] Advanced Risk Rules
- [ ] PDF Report Generation
- [ ] CSV Export
- [ ] Mobile UX Optimization
- [ ] Offline Support for Mobile
- [ ] Performance Optimization
- [ ] 2FA Security

### Future Phases
- [ ] ML-based Risk Scoring
- [ ] OCR for auto data extraction
- [ ] Supplier Performance Prediction
- [ ] IoT Sensor Integration
- [ ] Advanced Compliance Reporting
- [ ] Blockchain Audit Trail (optional)
- [ ] Multi-language Support
- [ ] API for External Systems

---

## Security & Permissions

### Authentication
- JWT tokens with refresh logic
- Session-based mobile support
- Secure password hashing (bcrypt)

### Authorization
- Role-Based Access Control (RBAC)
- Site-level visibility scoping
- Resource-level permissions
- Feature gates for phases

### Data Protection
- HTTPS/TLS for all communications
- Encrypted sensitive fields (future)
- Audit trail of all access
- Compliance-ready compliance logs

---

## Performance Characteristics

| Metric | Target |
|--------|--------|
| Avg Inspection Duration | 2-5 minutes |
| Average Batch Size | 50-500 units |
| Risk Scoring Latency | < 1 second |
| Dashboard Query | < 500ms |
| Concurrent Users | 100+ |
| Daily Batches (large site) | 50-100 |

---

## Deployment Architecture

### Production Environment

```
Load Balancer (HTTPS)
    ↓
API Servers (Django x3, horizontally scaled)
    ↓
PostgreSQL Primary (with replicas)
Redis Cache (session, tokens)
    ↓
S3 Object Storage (evidence files)
Monitoring (Prometheus + ELK)
    ↓
Backup Strategy (daily snapshots)
```

### Environments

- **Development** - Local, single server
- **Staging** - Pre-production testing
- **Production** - High availability, load-balanced, monitored
- **Backup & DR** - Automated backups, recovery procedures

---

## Integration Points

### Current
- Django ORM ↔ PostgreSQL
- Django REST API ↔ Mobile/Web clients
- File API ↔ Object Storage

### Future
- ML Service ↔ Risk Engine
- OCR Service ↔ Data Extraction
- IoT Sensors ↔ Condition Monitoring
- External Supplier DB ↔ Product Library
- Health Authorities API ↔ Compliance Reporting

---

## Success Metrics

- **Inspection Time** - Reduce from 30min to 5min per batch
- **Decision Quality** - 99%+ decision accuracy with review
- **Compliance** - 100% audit trail coverage
- **User Adoption** - 90%+ team using system within 3 months
- **System Uptime** - 99.5% availability
- **Data Integrity** - 0 audit trail discrepancies

---

## Document Index

For deeper dives, see:
1. [Product Context](product/product-context.md) - Ecosystem view
2. [Domain Model](data-model/domain-model.md) - Entities & relationships
3. [C4 Container](architecture/c4-container.md) - System components
4. [RBAC Matrix](architecture/rbac-matrix.md) - Permissions detail
5. [Deployment Diagram](deployment/deployment-diagram.md) - Ops view

---

**Last Updated:** May 19, 2026  
**Version:** 1.0  
**Audience:** Architects, Developers, Product Managers
