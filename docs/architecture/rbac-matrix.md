# RBAC Matrix (Role-Based Access Control)

## Overview

This matrix defines which roles have permission to perform which actions across all endpoints and features in AuthMed.

## Role Definitions

| Role | Description | Use Case |
|------|-------------|----------|
| **Inspector** | Field inspection personnel | Conducts batch inspections, captures evidence, enters data |
| **Reviewer** | Quality assurance officer | Reviews inspections, makes approval/isolation/escalation decisions |
| **Manager** | Site/organization manager | Monitors KPI, manages users, views trends, escalates issues |
| **QA Officer** | Quality auditor | Audits compliance, validates decisions, views all audit trails |
| **Admin** | System administrator | Full system access, user management, configuration |
| **API Client** | External service integration | Limited API access for specific integrations (future) |

---

## API Endpoint Access Matrix

### Authentication Endpoints

| Endpoint | Inspector | Reviewer | Manager | QA Officer | Admin | API Client |
|----------|-----------|----------|---------|------------|-------|------------|
| POST /auth/login | Yes | Yes | Yes | Yes | Yes | No |
| POST /auth/refresh | Yes | Yes | Yes | Yes | Yes | No |
| POST /auth/logout | Yes | Yes | Yes | Yes | Yes | No |

---

### Batch Endpoints

| Endpoint | Inspector | Reviewer | Manager | QA Officer | Admin |
|----------|-----------|----------|---------|------------|-------|
| POST /batches/ | Yes (Own org) | No | No | No | Yes |
| GET /batches/ | Yes (Own org) | Yes (Own org) | Yes (Own org) | Yes (All) | Yes (All) |
| GET /batches/{id}/ | Yes (Own org) | Yes (Own org) | Yes (Own org) | Yes (All) | Yes (All) |
| PUT /batches/{id}/ | No | No | No | No | Yes |
| DELETE /batches/{id}/ | No | No | No | No | No |

---

### Inspection Endpoints

| Endpoint | Inspector | Reviewer | Manager | QA Officer | Admin |
|----------|-----------|----------|---------|------------|-------|
| POST /inspections/ | Yes (Assign self) | No | No | No | Yes |
| GET /inspections/ | Yes (Own assigned) | Yes (Own org) | Yes (Own org) | Yes (All) | Yes (All) |
| GET /inspections/{id}/ | Yes (Own assigned) | Yes (Own org) | Yes (Own org) | Yes (All) | Yes (All) |
| PUT /inspections/{id}/ | Yes (Own assigned) | No | No | No | Yes |

---

### Evidence Endpoints

| Endpoint | Inspector | Reviewer | Manager | QA Officer | Admin |
|----------|-----------|----------|---------|------------|-------|
| POST /evidence/ | Yes (Own inspection) | No | No | No | Yes |
| GET /evidence/ | Yes (Own org) | Yes (Own org) | Yes (Own org) | Yes (All) | Yes (All) |
| GET /evidence/{id}/ | Yes (Own org) | Yes (Own org) | Yes (Own org) | Yes (All) | Yes (All) |
| DELETE /evidence/{id}/ | No | No | No | No | Yes |

---

### Risk Scoring Endpoints

| Endpoint | Inspector | Reviewer | Manager | QA Officer | Admin |
|----------|-----------|----------|---------|------------|-------|
| POST /risk/calculate/ | No | No | No | No | Yes |
| GET /risk/results/ | Yes (Own org) | Yes (Own org) | Yes (Own org) | Yes (All) | Yes (All) |

---

### Decision Endpoints

| Endpoint | Inspector | Reviewer | Manager | QA Officer | Admin |
|----------|-----------|----------|---------|------------|-------|
| POST /decisions/ | No | Yes (Own org) | No | Yes (All) | Yes |
| GET /decisions/ | Yes (Own org) | Yes (Own org) | Yes (Own org) | Yes (All) | Yes (All) |
| GET /decisions/{id}/ | Yes (Own org) | Yes (Own org) | Yes (Own org) | Yes (All) | Yes (All) |
| PUT /decisions/{id}/ | No | Yes (Own) | No | No | Yes |

---

### Dashboard Endpoints

| Endpoint | Inspector | Reviewer | Manager | QA Officer | Admin |
|----------|-----------|----------|---------|------------|-------|
| GET /dashboard/kpis/ | No | Yes (Own org) | Yes (Own org) | Yes (All) | Yes (All) |
| GET /dashboard/queue/ | No | Yes (Own org) | Yes (Own org) | Yes (All) | Yes (All) |
| GET /dashboard/trends/ | No | Yes (Own org) | Yes (Own org) | Yes (All) | Yes (All) |

---

### Report Endpoints

| Endpoint | Inspector | Reviewer | Manager | QA Officer | Admin |
|----------|-----------|----------|---------|------------|-------|
| POST /reports/ | No | No | Yes (Own org) | Yes (All) | Yes |
| GET /reports/ | No | No | Yes (Own org) | Yes (All) | Yes |
| GET /reports/{id}/ | No | No | Yes (Own org) | Yes (All) | Yes |
| DELETE /reports/{id}/ | No | No | No | No | Yes |

---

### User Management Endpoints

| Endpoint | Inspector | Reviewer | Manager | QA Officer | Admin |
|----------|-----------|----------|---------|------------|-------|
| GET /users/ | No | No | Yes (Own org) | No | Yes |
| POST /users/ | No | No | No | No | Yes |
| GET /users/{id}/ | No | No | Yes (Own org) | No | Yes |
| PUT /users/{id}/ | No | No | No | No | Yes |
| DELETE /users/{id}/ | No | No | No | No | Yes |

---

### Configuration Endpoints

| Endpoint | Inspector | Reviewer | Manager | QA Officer | Admin |
|----------|-----------|----------|---------|------------|-------|
| GET /config/ | No | No | No | No | Yes |
| PUT /config/ | No | No | No | No | Yes |
| GET /audit-log/ | No | No | No | Yes (All) | Yes |

---

## Data Access Scoping

### Inspector
- Can only view/edit own organization's data
- Can only manage own assigned inspections
- Can only upload evidence for own inspections
- Cannot view decisions or approvals

### Reviewer
- Can view all batches in own organization
- Can view all decisions in own organization
- Can make decisions only on batches assigned to own org
- Cannot manage users or system config

### Manager
- Can view all data in own organization
- Can generate reports for own org
- Can view KPI dashboards for own org
- Cannot make decisions or manage system config
- Can invite users (creates ticket for admin)

### QA Officer
- Can view all data across all organizations
- Can view all audit logs
- Can make decisions on any batch
- Can generate compliance reports
- Cannot manage users or system config

### Admin
- Full system access
- Can create/edit/delete anything
- Can manage users and permissions
- Can configure rules and thresholds
- Can view all audit logs
- Can export any data

### API Client
- Limited to specific authenticated endpoints
- Scoped to specific organization
- Read-only by default
- Specific endpoints whitelisted

---

## Feature-Level Permissions

### Batch Management
| Action | Inspector | Reviewer | Manager | QA | Admin |
|--------|-----------|----------|---------|-----|-------|
| Create batch | Yes | No | No | No | Yes |
| View batch | Yes (Org) | Yes (Org) | Yes (Org) | Yes (All) | Yes |
| Edit batch | No | No | No | No | Yes |
| Delete batch | No | No | No | No | No |

### Inspection Management
| Action | Inspector | Reviewer | Manager | QA | Admin |
|--------|-----------|----------|---------|-----|-------|
| Create inspection | Yes | No | No | No | Yes |
| Assign to self | Yes | No | No | No | Yes |
| Start inspection | Yes (Own) | No | No | No | Yes |
| Upload evidence | Yes (Own) | No | No | No | Yes |
| View inspection | Yes (Org) | Yes (Org) | Yes (Org) | Yes (All) | Yes |
| Complete inspection | Yes (Own) | No | No | No | Yes |

### Decision Making
| Action | Inspector | Reviewer | Manager | QA | Admin |
|--------|-----------|----------|---------|-----|-------|
| View risk score | Yes (Own) | Yes (Org) | Yes (Org) | Yes (All) | Yes |
| View pending review queue | No | Yes (Org) | Yes (Org) | Yes (All) | Yes |
| Make decision | No | Yes (Org) | No | Yes (All) | Yes |
| Override risk score | No | Yes (Org) | No | Yes (All) | Yes |
| View decision history | Yes (Org) | Yes (Org) | Yes (Org) | Yes (All) | Yes |

### Reporting & Analytics
| Action | Inspector | Reviewer | Manager | QA | Admin |
|--------|-----------|----------|---------|-----|-------|
| View KPI dashboard | No | Yes (Org) | Yes (Org) | Yes (All) | Yes |
| Generate compliance report | No | No | Yes (Org) | Yes (All) | Yes |
| Generate trend analysis | No | No | Yes (Org) | Yes (All) | Yes |
| Export data | No | No | Yes (Org) | Yes (All) | Yes |
| View audit log | No | No | No | Yes (All) | Yes |

### Administration
| Action | Inspector | Reviewer | Manager | QA | Admin |
|--------|-----------|----------|---------|-----|-------|
| Manage users | No | No | No | No | Yes |
| Configure rules | No | No | No | No | Yes |
| Set thresholds | No | No | No | No | Yes |
| Manage organizations | No | No | No | No | Yes |
| Manage sites | No | No | No | No | Yes |
| System configuration | No | No | No | No | Yes |

---

## Permission Groups

### Inspectors Group
- Create & manage own inspections
- Capture evidence
- Enter batch data
- View own risk scores (read-only)

### Reviewers Group
- All Inspector permissions
- View all org inspections
- View pending review queue
- Make approval/isolation/escalation decisions
- View decision history
- View KPI metrics (own org)

### Managers Group
- All Reviewer permissions
- Cannot make decisions
- Generate reports (org-level)
- Manage org users (request to admin)
- View KPI trends (org-level)

### QA/Compliance Group
- All permission permissions except management
- View all organizations' data
- Make decisions on any batch
- Access complete audit logs
- Generate compliance reports (cross-org)

### Administrators Group
- All permissions
- System management
- User management
- Configuration management
- No restrictions

---

## Permission Inheritance

```
Admin (all permissions)
├── QA Officer (all except management)
├── Manager (org-level only)
├── Reviewer (org-level decisions)
└── Inspector (own assignments)
```

Each role inherits from lower roles in the hierarchy for read operations but has additional write permissions.

---

## Multi-Organization Scoping

### Data Visibility Rules
1. **Inspector:** Own org only
2. **Reviewer:** Own org only
3. **Manager:** Own org only
4. **QA Officer:** All orgs
5. **Admin:** All orgs

### Cross-Organization Actions
- Only Admin can work across organizations
- QA Officer can view all orgs but cannot make changes
- Org-level reports cannot cross organization boundaries
- Audit logs filtered by accessible org

---

## Audit Trail Recording

All role-based actions are recorded:

```json
{
  "timestamp": "2026-05-19T14:45:00Z",
  "actor_id": "u-54321",
  "actor_role": "reviewer",
  "action": "decision_created",
  "resource": "batch-001",
  "decision": "accept",
  "result": "success"
}
```

---

## Permission Checking Implementation

```python
# Pseudo-code for permission checking

@require_permission('POST', '/decisions/', ['reviewer', 'qa_officer', 'admin'])
def create_decision(request):
    # Also check org scoping
    if not user_has_org_access(request.user, batch.organization_id):
        raise PermissionDenied()
    # ... proceed
```

---

## Next Steps

See:
1. [API Endpoints](api-endpoints.md) - Detailed endpoint reference
2. [Security Architecture](security-architecture.md) - Authentication & encryption
3. [Audit Logging](../architecture/audit-logging.md) - Permission audit trail

---

**Key Insight:** Permissions follow role-based access control (RBAC) with org-level scoping. Each role has specific allowed actions and data access patterns, enforced at API level.
