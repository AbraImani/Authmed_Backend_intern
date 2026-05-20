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
| POST /auth/login | ✅ | ✅ | ✅ | ✅ | ✅ | ❌ |
| POST /auth/refresh | ✅ | ✅ | ✅ | ✅ | ✅ | ❌ |
| POST /auth/logout | ✅ | ✅ | ✅ | ✅ | ✅ | ❌ |

---

### Batch Endpoints

| Endpoint | Inspector | Reviewer | Manager | QA Officer | Admin |
|----------|-----------|----------|---------|------------|-------|
| POST /batches/ | ✅ Own org | ❌ | ❌ | ❌ | ✅ |
| GET /batches/ | ✅ Own org | ✅ Own org | ✅ Own org | ✅ All | ✅ All |
| GET /batches/{id}/ | ✅ Own org | ✅ Own org | ✅ Own org | ✅ All | ✅ All |
| PUT /batches/{id}/ | ❌ | ❌ | ❌ | ❌ | ✅ |
| DELETE /batches/{id}/ | ❌ | ❌ | ❌ | ❌ | ❌ |

---

### Inspection Endpoints

| Endpoint | Inspector | Reviewer | Manager | QA Officer | Admin |
|----------|-----------|----------|---------|------------|-------|
| POST /inspections/ | ✅ Assign self | ❌ | ❌ | ❌ | ✅ |
| GET /inspections/ | ✅ Own assigned | ✅ Own org | ✅ Own org | ✅ All | ✅ All |
| GET /inspections/{id}/ | ✅ Own assigned | ✅ Own org | ✅ Own org | ✅ All | ✅ All |
| PUT /inspections/{id}/ | ✅ Own assigned | ❌ | ❌ | ❌ | ✅ |

---

### Evidence Endpoints

| Endpoint | Inspector | Reviewer | Manager | QA Officer | Admin |
|----------|-----------|----------|---------|------------|-------|
| POST /evidence/ | ✅ Own inspection | ❌ | ❌ | ❌ | ✅ |
| GET /evidence/ | ✅ Own org | ✅ Own org | ✅ Own org | ✅ All | ✅ All |
| GET /evidence/{id}/ | ✅ Own org | ✅ Own org | ✅ Own org | ✅ All | ✅ All |
| DELETE /evidence/{id}/ | ❌ | ❌ | ❌ | ❌ | ✅ |

---

### Risk Scoring Endpoints

| Endpoint | Inspector | Reviewer | Manager | QA Officer | Admin |
|----------|-----------|----------|---------|------------|-------|
| POST /risk/calculate/ | ❌ | ❌ | ❌ | ❌ | ✅ |
| GET /risk/results/ | ✅ Own org | ✅ Own org | ✅ Own org | ✅ All | ✅ All |

---

### Decision Endpoints

| Endpoint | Inspector | Reviewer | Manager | QA Officer | Admin |
|----------|-----------|----------|---------|------------|-------|
| POST /decisions/ | ❌ | ✅ Own org | ❌ | ✅ All | ✅ |
| GET /decisions/ | ✅ Own org | ✅ Own org | ✅ Own org | ✅ All | ✅ All |
| GET /decisions/{id}/ | ✅ Own org | ✅ Own org | ✅ Own org | ✅ All | ✅ All |
| PUT /decisions/{id}/ | ❌ | ✅ Own | ❌ | ❌ | ✅ |

---

### Dashboard Endpoints

| Endpoint | Inspector | Reviewer | Manager | QA Officer | Admin |
|----------|-----------|----------|---------|------------|-------|
| GET /dashboard/kpis/ | ❌ | ✅ Own org | ✅ Own org | ✅ All | ✅ All |
| GET /dashboard/queue/ | ❌ | ✅ Own org | ✅ Own org | ✅ All | ✅ All |
| GET /dashboard/trends/ | ❌ | ✅ Own org | ✅ Own org | ✅ All | ✅ All |

---

### Report Endpoints

| Endpoint | Inspector | Reviewer | Manager | QA Officer | Admin |
|----------|-----------|----------|---------|------------|-------|
| POST /reports/ | ❌ | ❌ | ✅ Own org | ✅ All | ✅ |
| GET /reports/ | ❌ | ❌ | ✅ Own org | ✅ All | ✅ |
| GET /reports/{id}/ | ❌ | ❌ | ✅ Own org | ✅ All | ✅ |
| DELETE /reports/{id}/ | ❌ | ❌ | ❌ | ❌ | ✅ |

---

### User Management Endpoints

| Endpoint | Inspector | Reviewer | Manager | QA Officer | Admin |
|----------|-----------|----------|---------|------------|-------|
| GET /users/ | ❌ | ❌ | ✅ Own org | ❌ | ✅ |
| POST /users/ | ❌ | ❌ | ❌ | ❌ | ✅ |
| GET /users/{id}/ | ❌ | ❌ | ✅ Own org | ❌ | ✅ |
| PUT /users/{id}/ | ❌ | ❌ | ❌ | ❌ | ✅ |
| DELETE /users/{id}/ | ❌ | ❌ | ❌ | ❌ | ✅ |

---

### Configuration Endpoints

| Endpoint | Inspector | Reviewer | Manager | QA Officer | Admin |
|----------|-----------|----------|---------|------------|-------|
| GET /config/ | ❌ | ❌ | ❌ | ❌ | ✅ |
| PUT /config/ | ❌ | ❌ | ❌ | ❌ | ✅ |
| GET /audit-log/ | ❌ | ❌ | ❌ | ✅ All | ✅ |

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
| Create batch | ✅ | ❌ | ❌ | ❌ | ✅ |
| View batch | ✅ Org | ✅ Org | ✅ Org | ✅ All | ✅ |
| Edit batch | ❌ | ❌ | ❌ | ❌ | ✅ |
| Delete batch | ❌ | ❌ | ❌ | ❌ | ❌ |

### Inspection Management
| Action | Inspector | Reviewer | Manager | QA | Admin |
|--------|-----------|----------|---------|-----|-------|
| Create inspection | ✅ | ❌ | ❌ | ❌ | ✅ |
| Assign to self | ✅ | ❌ | ❌ | ❌ | ✅ |
| Start inspection | ✅ Own | ❌ | ❌ | ❌ | ✅ |
| Upload evidence | ✅ Own | ❌ | ❌ | ❌ | ✅ |
| View inspection | ✅ Org | ✅ Org | ✅ Org | ✅ All | ✅ |
| Complete inspection | ✅ Own | ❌ | ❌ | ❌ | ✅ |

### Decision Making
| Action | Inspector | Reviewer | Manager | QA | Admin |
|--------|-----------|----------|---------|-----|-------|
| View risk score | ✅ Own | ✅ Org | ✅ Org | ✅ All | ✅ |
| View pending review queue | ❌ | ✅ Org | ✅ Org | ✅ All | ✅ |
| Make decision | ❌ | ✅ Org | ❌ | ✅ All | ✅ |
| Override risk score | ❌ | ✅ Org | ❌ | ✅ All | ✅ |
| View decision history | ✅ Org | ✅ Org | ✅ Org | ✅ All | ✅ |

### Reporting & Analytics
| Action | Inspector | Reviewer | Manager | QA | Admin |
|--------|-----------|----------|---------|-----|-------|
| View KPI dashboard | ❌ | ✅ Org | ✅ Org | ✅ All | ✅ |
| Generate compliance report | ❌ | ❌ | ✅ Org | ✅ All | ✅ |
| Generate trend analysis | ❌ | ❌ | ✅ Org | ✅ All | ✅ |
| Export data | ❌ | ❌ | ✅ Org | ✅ All | ✅ |
| View audit log | ❌ | ❌ | ❌ | ✅ All | ✅ |

### Administration
| Action | Inspector | Reviewer | Manager | QA | Admin |
|--------|-----------|----------|---------|-----|-------|
| Manage users | ❌ | ❌ | ❌ | ❌ | ✅ |
| Configure rules | ❌ | ❌ | ❌ | ❌ | ✅ |
| Set thresholds | ❌ | ❌ | ❌ | ❌ | ✅ |
| Manage organizations | ❌ | ❌ | ❌ | ❌ | ✅ |
| Manage sites | ❌ | ❌ | ❌ | ❌ | ✅ |
| System configuration | ❌ | ❌ | ❌ | ❌ | ✅ |

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
