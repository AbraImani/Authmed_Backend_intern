# Phase 1 tenancy and authorization

`OrganizationMembership(user, organization, role, is_active, primary_site)`
is the business authority. A database uniqueness constraint permits one row
per user/organization; inactive rows are reactivated rather than duplicated.
The optional primary site must belong to that organization. No site permission
M2M is introduced. Old User.organization, User.site and User.role are preserved
for compatibility/data migration but no longer decide API authorization.

## Active context and /me

`GET /api/me/` requires authentication, not membership. It returns only user
id, firebase_uid, email, names, memberships, active_context and capabilities.
Inactive memberships can be shown as inactive but give no capabilities.
One active membership is selected automatically. With multiple memberships,
`/me` returns them without a selected context until `X-Organization-ID` is
supplied. Tenant APIs reject an absent/ambiguous/unauthorized context with 403.
Each request rechecks membership; the resolved context is cached only within
that request. `?organization=` can narrow an existing context, never select
an unauthorized tenant. No Firebase custom claim grants business authority.

## Role matrix

| Capability | admin | organization_manager | inspector | reviewer | quality_officer |
| --- | --- | --- | --- | --- | --- |
| Read tenant business resources | yes | yes | yes | yes | yes |
| Manage sites, references, suppliers, datasets | yes | yes | no | no | no |
| Inspections, evidence and OCR actions | yes | yes | yes | no | no |
| Existing decision writes | yes | no | no | yes | yes |
| Existing risk writes | yes | no | no | no | yes |
| Read tenant audit logs | yes | yes | no | yes | yes |
| Read tenant user directory | yes | yes | no | no | no |

Role definitions and capability sets live only in `organizations/roles.py`.
Future review/escalation state transitions remain for later phases. Current
risk/decision CRUD receives this minimum role boundary; final versioning,
immutability and workflow guarantees remain Phase 5.

Membership provisioning is through trusted Django Admin in this phase.
The public user directory is read-only and cannot edit identity, roles or
memberships. Organization creation/deletion is internal administration;
tenant administrators can update their organization's profile. A tenant
`admin` is never a platform administrator. Even staff/superusers require a
membership on business APIs; global administration stays in Django Admin.

## Boundaries

`TenantQuerysetMixin` filters lists and object/action lookup. `TenantPermission`
checks active membership, capability and ownership from the actual object.
`TenantSerializerMixin` scopes FK and many-to-many querysets before ID lookup,
scopes browsable-API filter choices through `TenantFilterBackend`,
validates relation consistency and rejects foreign organization input even
when that field is read-only. Inspector/reviewer/creator identity is assigned
server-side. Legacy inconsistent foreign IDs and display values are hidden
in representations; the underlying data is retained for internal repair.

Covered: organizations, sites, suppliers, products, reference images, datasets,
inspections, evidence, OCR tasks/actions, processing runs/actions, risks,
decisions, user directory and audit logs. `/me`, auth and schema/documentation
are identity/infrastructure endpoints rather than tenant collections.

## Data migrations

- Existing users with an explicit organization and known legacy role receive
  the corresponding membership. Inactive users get inactive membership.
  Unknown roles/no organization receive none. Inconsistent old site values
  stay on the legacy user but do not become membership defaults.
- Suppliers receive ownership when exactly one tenant can be inferred from
  products/inspections. Previously shared suppliers are copied per tenant and
  those relations are repointed. Original shared/unreferenced records remain
  unassigned and hidden from tenant APIs. No global writable supplier catalog.
- AuditLog receives a nullable organization field. Historical events are scoped
  only when the referenced object's ownership is recoverable. Unknown/deleted/
  global events remain hidden from tenant APIs. New nested-object events capture
  their organization. This preserves the existing best-effort audit mechanism;
  it is not the final Phase 5 audit architecture.
- Historical migrations are unchanged. Forward migrations are tested both on
  empty databases and populated Phase 0 data. Existing local DB/media have not
  been migrated or modified by these verification runs.

Migration reversals do not attempt to merge copied supplier records or remove
subsequently administered memberships. Back up deployed data before applying
schema migrations; test and review any future rollback separately.
