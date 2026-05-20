# API Endpoints Complete Reference

## Overview

This document provides comprehensive reference for all AuthMed API endpoints, including request/response formats, error codes, and usage examples.

## Base URL

```
Development: http://localhost:8000/api/v1/
Staging: https://staging-api.authmed.dev/api/v1/
Production: https://api.authmed.com/api/v1/
```

## Authentication

All endpoints require JWT token in header:

```
Authorization: Bearer {access_token}
```

---

## Authentication Endpoints

### POST /auth/login/
**Description:** Authenticate user and receive tokens  
**Role:** Any  
**Rate Limit:** 5 per minute  

**Request:**
```json
{
  "username": "john.doe@authmed.local",
  "password": "SecurePassword123!"
}
```

**Response (200):**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIs...",
  "expires_in": 86400,
  "user": {
    "id": "u-12345",
    "username": "john.doe@authmed.local",
    "email": "john.doe@authmed.local",
    "first_name": "John",
    "last_name": "Doe",
    "role": "inspector",
    "organization_id": "org-789",
    "site_id": "site-456"
  }
}
```

**Error (401):**
```json
{
  "error": "invalid_credentials",
  "message": "Username or password incorrect"
}
```

### POST /auth/refresh/
**Description:** Refresh access token using refresh token  
**Role:** Any  

**Request:**
```json
{
  "refresh_token": "eyJhbGciOiJIUzI1NiIs..."
}
```

**Response (200):**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "expires_in": 86400
}
```

### POST /auth/logout/
**Description:** Invalidate refresh token  
**Role:** Any  

**Request:**
```json
{
  "refresh_token": "eyJhbGciOiJIUzI1NiIs..."
}
```

**Response (204):**
```
(No content)
```

---

## Batch Endpoints

### POST /batches/
**Description:** Create new batch inspection  
**Role:** Inspector, Admin  
**Rate Limit:** 100 per minute  

**Request:**
```json
{
  "lot_number": "LOT-20260519-001",
  "supplier_id": "sup-789",
  "product_id": "prod-456",
  "quantity_received": 120,
  "received_date": "2026-05-19T08:30:00Z",
  "received_by_id": "u-12345"
}
```

**Response (201):**
```json
{
  "id": "batch-001",
  "lot_number": "LOT-20260519-001",
  "supplier_id": "sup-789",
  "product_id": "prod-456",
  "status": "draft",
  "received_date": "2026-05-19T08:30:00Z",
  "created_at": "2026-05-19T08:35:00Z",
  "created_by_id": "u-12345",
  "organization_id": "org-789",
  "site_id": "site-456"
}
```

**Error (400):**
```json
{
  "error": "validation_error",
  "details": {
    "lot_number": ["Required field"],
    "supplier_id": ["Supplier not found"]
  }
}
```

### GET /batches/
**Description:** List batches with filtering  
**Role:** Any  

**Query Parameters:**
```
status=draft,pending_inspection,under_inspection,accepted,isolated,escalated,archived
supplier_id=sup-789
product_id=prod-456
created_after=2026-05-01T00:00:00Z
created_before=2026-05-31T23:59:59Z
page=1
page_size=20
```

**Response (200):**
```json
{
  "count": 150,
  "next": "https://api.authmed.com/api/v1/batches/?page=2",
  "previous": null,
  "results": [
    {
      "id": "batch-001",
      "lot_number": "LOT-20260519-001",
      "supplier_id": "sup-789",
      "product_id": "prod-456",
      "status": "pending_inspection",
      "received_date": "2026-05-19T08:30:00Z",
      "created_at": "2026-05-19T08:35:00Z"
    }
  ]
}
```

### GET /batches/{id}/
**Description:** Get batch details with full context  
**Role:** Any (org-scoped)  

**Response (200):**
```json
{
  "id": "batch-001",
  "lot_number": "LOT-20260519-001",
  "supplier": {
    "id": "sup-789",
    "name": "Pharma Corp International",
    "reliability_score": 0.92
  },
  "product": {
    "id": "prod-456",
    "name": "Aspirin 500mg",
    "sku": "ASP-500-001"
  },
  "status": "pending_review",
  "quantity_received": 120,
  "received_date": "2026-05-19T08:30:00Z",
  "inspection": {
    "id": "insp-001",
    "status": "evidence_captured",
    "inspector_id": "u-12345",
    "started_at": "2026-05-19T09:00:00Z"
  },
  "risk_result": {
    "score": 35,
    "recommendation": "isolate",
    "factors": {
      "condition_score": 30,
      "anomaly_score": 40,
      "supplier_score": 35,
      "product_score": 20
    }
  },
  "decision": null,
  "evidence_count": 8,
  "created_at": "2026-05-19T08:35:00Z",
  "updated_at": "2026-05-19T09:15:00Z"
}
```

### PUT /batches/{id}/
**Description:** Update batch status (admin only)  
**Role:** Admin  

**Request:**
```json
{
  "status": "archived",
  "notes": "Recall notice issued"
}
```

**Response (200):**
```json
{
  "id": "batch-001",
  "status": "archived",
  "updated_at": "2026-05-19T10:00:00Z"
}
```

---

## Inspection Endpoints

### POST /inspections/
**Description:** Create inspection for batch  
**Role:** Inspector, Admin  

**Request:**
```json
{
  "batch_id": "batch-001",
  "inspector_id": "u-12345"
}
```

**Response (201):**
```json
{
  "id": "insp-001",
  "batch_id": "batch-001",
  "inspector_id": "u-12345",
  "status": "draft",
  "created_at": "2026-05-19T08:40:00Z"
}
```

### GET /inspections/
**Description:** List inspections for user  
**Role:** Any  

**Query Parameters:**
```
status=draft,pending,under_inspection,evidence_captured,pending_scoring,pending_review,review_in_progress,completed
assigned_to_id=u-12345
batch_id=batch-001
```

**Response (200):**
```json
{
  "count": 25,
  "results": [
    {
      "id": "insp-001",
      "batch_id": "batch-001",
      "batch_number": "LOT-20260519-001",
      "inspector_id": "u-12345",
      "status": "evidence_captured",
      "created_at": "2026-05-19T08:40:00Z",
      "started_at": "2026-05-19T09:00:00Z"
    }
  ]
}
```

### GET /inspections/{id}/
**Description:** Get inspection full details  
**Role:** Any (org-scoped)  

**Response (200):**
```json
{
  "id": "insp-001",
  "batch_id": "batch-001",
  "inspector_id": "u-12345",
  "status": "evidence_captured",
  "batch_data": {
    "temperature_observed": 22.5,
    "humidity_observed": 45,
    "seal_integrity": "intact",
    "packaging_condition": "good",
    "anomalies": ["slight_discoloration_on_label"]
  },
  "evidence": [
    {
      "id": "ev-001",
      "type": "photo",
      "url": "https://s3.aws.com/authmed-evidence/ev-001.jpg",
      "description": "Package exterior",
      "uploaded_at": "2026-05-19T09:05:00Z"
    }
  ],
  "risk_result": null,
  "created_at": "2026-05-19T08:40:00Z",
  "updated_at": "2026-05-19T09:15:00Z"
}
```

### PUT /inspections/{id}/
**Description:** Update inspection (submit data, mark complete)  
**Role:** Inspector (own) or Admin  

**Request:**
```json
{
  "status": "evidence_captured",
  "batch_data": {
    "temperature_observed": 22.5,
    "humidity_observed": 45,
    "seal_integrity": "intact",
    "anomalies": []
  }
}
```

**Response (200):**
```json
{
  "id": "insp-001",
  "status": "evidence_captured",
  "batch_data": {...},
  "updated_at": "2026-05-19T09:20:00Z"
}
```

---

## Evidence Endpoints

### POST /evidence/
**Description:** Upload evidence file  
**Role:** Inspector  
**Max File Size:** 50MB  

**Request:**
```
Content-Type: multipart/form-data

Fields:
- inspection_id: insp-001
- file: (binary file)
- description: "Package exterior photo"
- type: "photo" or "document"
```

**Response (201):**
```json
{
  "id": "ev-001",
  "inspection_id": "insp-001",
  "type": "photo",
  "url": "https://s3.aws.com/authmed-evidence/ev-001.jpg",
  "size_bytes": 2048576,
  "description": "Package exterior photo",
  "uploaded_at": "2026-05-19T09:05:00Z",
  "uploaded_by_id": "u-12345"
}
```

### GET /evidence/
**Description:** List evidence for inspection  
**Role:** Any (org-scoped)  

**Query Parameters:**
```
inspection_id=insp-001
type=photo,document
```

**Response (200):**
```json
{
  "count": 8,
  "results": [
    {
      "id": "ev-001",
      "inspection_id": "insp-001",
      "type": "photo",
      "url": "https://s3.aws.com/authmed-evidence/ev-001.jpg",
      "description": "Package exterior photo",
      "uploaded_at": "2026-05-19T09:05:00Z"
    }
  ]
}
```

### DELETE /evidence/{id}/
**Description:** Delete evidence (admin only)  
**Role:** Admin  

**Response (204):**
```
(No content)
```

---

## Risk Scoring Endpoints

### POST /risk/calculate/
**Description:** Trigger risk calculation (usually automatic)  
**Role:** System (automatic) or Admin  

**Request:**
```json
{
  "inspection_id": "insp-001"
}
```

**Response (200):**
```json
{
  "inspection_id": "insp-001",
  "score": 35,
  "recommendation": "isolate",
  "factors": {
    "condition_score": 30,
    "condition_weight": 0.4,
    "anomaly_score": 40,
    "anomaly_weight": 0.3,
    "supplier_score": 35,
    "supplier_weight": 0.2,
    "product_score": 20,
    "product_weight": 0.1
  },
  "anomalies_detected": ["slight_discoloration"],
  "calculated_at": "2026-05-19T09:20:00Z"
}
```

### GET /risk/results/
**Description:** List risk results  
**Role:** Any  

**Query Parameters:**
```
inspection_id=insp-001
score_min=0
score_max=100
recommendation=accept,isolate,escalate
```

**Response (200):**
```json
{
  "count": 150,
  "results": [
    {
      "inspection_id": "insp-001",
      "score": 35,
      "recommendation": "isolate",
      "calculated_at": "2026-05-19T09:20:00Z"
    }
  ]
}
```

---

## Decision Endpoints

### POST /decisions/
**Description:** Make decision on batch inspection  
**Role:** Reviewer, Admin  

**Request:**
```json
{
  "inspection_id": "insp-001",
  "decision": "accept",
  "notes": "All conditions normal, seal intact, no anomalies",
  "override_risk": false
}
```

**Response (201):**
```json
{
  "id": "dec-001",
  "inspection_id": "insp-001",
  "batch_id": "batch-001",
  "decision": "accept",
  "reviewer_id": "u-54321",
  "notes": "All conditions normal, seal intact, no anomalies",
  "override_risk": false,
  "created_at": "2026-05-19T14:45:00Z"
}
```

### GET /decisions/
**Description:** List decisions  
**Role:** Any  

**Query Parameters:**
```
inspection_id=insp-001
batch_id=batch-001
decision=accept,isolate,escalate
reviewer_id=u-54321
created_after=2026-05-01T00:00:00Z
```

**Response (200):**
```json
{
  "count": 45,
  "results": [
    {
      "id": "dec-001",
      "inspection_id": "insp-001",
      "batch_id": "batch-001",
      "decision": "accept",
      "reviewer_id": "u-54321",
      "created_at": "2026-05-19T14:45:00Z"
    }
  ]
}
```

### GET /decisions/{id}/
**Description:** Get decision details with audit trail  
**Role:** Any (org-scoped)  

**Response (200):**
```json
{
  "id": "dec-001",
  "inspection_id": "insp-001",
  "batch_id": "batch-001",
  "decision": "accept",
  "reviewer_id": "u-54321",
  "risk_score": 35,
  "risk_recommendation": "isolate",
  "override_risk": false,
  "notes": "All conditions normal, seal intact, no anomalies",
  "created_at": "2026-05-19T14:45:00Z",
  "audit_log": [
    {
      "event": "decision_created",
      "actor_id": "u-54321",
      "timestamp": "2026-05-19T14:45:00Z"
    }
  ]
}
```

---

## Dashboard Endpoints

### GET /dashboard/kpis/
**Description:** Get KPI metrics  
**Role:** Reviewer, Manager, Admin  

**Query Parameters:**
```
organization_id=org-789
site_id=site-456
date_from=2026-05-01T00:00:00Z
date_to=2026-05-31T23:59:59Z
```

**Response (200):**
```json
{
  "date_range": {
    "from": "2026-05-01T00:00:00Z",
    "to": "2026-05-31T23:59:59Z"
  },
  "total_batches_inspected": 250,
  "total_accepted": 220,
  "total_isolated": 20,
  "total_escalated": 10,
  "acceptance_rate_percent": 88.0,
  "isolation_rate_percent": 8.0,
  "escalation_rate_percent": 4.0,
  "average_risk_score": 28.5,
  "average_inspection_time_minutes": 12,
  "average_review_time_minutes": 45,
  "top_suppliers": [
    {
      "supplier_id": "sup-789",
      "name": "Pharma Corp",
      "batches_inspected": 50,
      "rejection_rate_percent": 8.0
    }
  ],
  "top_products": [
    {
      "product_id": "prod-456",
      "name": "Aspirin 500mg",
      "batches_inspected": 30,
      "rejection_rate_percent": 3.3
    }
  ]
}
```

### GET /dashboard/queue/
**Description:** Get review queue  
**Role:** Reviewer, Admin  

**Query Parameters:**
```
status=pending_review
priority=high,medium,low
assigned_to=u-54321
page=1
page_size=20
```

**Response (200):**
```json
{
  "count": 35,
  "results": [
    {
      "id": "insp-001",
      "batch_id": "batch-001",
      "batch_number": "LOT-20260519-001",
      "risk_score": 55,
      "priority": "high",
      "assigned_to": null,
      "created_at": "2026-05-19T09:15:00Z"
    }
  ]
}
```

---

## Report Endpoints

### POST /reports/
**Description:** Generate report  
**Role:** Manager, QA, Admin  

**Request:**
```json
{
  "report_type": "compliance",
  "date_from": "2026-05-01T00:00:00Z",
  "date_to": "2026-05-31T23:59:59Z",
  "organization_id": "org-789",
  "format": "pdf"
}
```

**Response (202):**
```json
{
  "report_id": "rep-001",
  "status": "processing",
  "created_at": "2026-05-19T15:00:00Z"
}
```

### GET /reports/{id}/
**Description:** Download report (or check status)  
**Role:** Any (created by)  

**Response (200):**
```
Content-Type: application/pdf
Content-Disposition: attachment; filename="compliance-report-may-2026.pdf"

(Binary PDF content)
```

---

## User Endpoints

### GET /users/
**Description:** List users (admin only)  
**Role:** Admin  

**Query Parameters:**
```
organization_id=org-789
role=inspector,reviewer,admin
```

**Response (200):**
```json
{
  "count": 15,
  "results": [
    {
      "id": "u-12345",
      "username": "john.doe@authmed.local",
      "email": "john.doe@authmed.local",
      "first_name": "John",
      "last_name": "Doe",
      "role": "inspector",
      "organization_id": "org-789",
      "created_at": "2026-01-15T10:00:00Z"
    }
  ]
}
```

### POST /users/
**Description:** Create user (admin only)  
**Role:** Admin  

**Request:**
```json
{
  "username": "jane.smith@authmed.local",
  "email": "jane.smith@authmed.local",
  "first_name": "Jane",
  "last_name": "Smith",
  "password": "TemporaryPassword123!",
  "role": "reviewer",
  "organization_id": "org-789"
}
```

**Response (201):**
```json
{
  "id": "u-67890",
  "username": "jane.smith@authmed.local",
  "email": "jane.smith@authmed.local",
  "first_name": "Jane",
  "last_name": "Smith",
  "role": "reviewer",
  "organization_id": "org-789",
  "created_at": "2026-05-19T15:05:00Z"
}
```

---

## Health Check

### GET /health/
**Description:** System health check (no auth required)  
**Role:** Any  

**Response (200):**
```json
{
  "status": "healthy",
  "timestamp": "2026-05-19T15:10:00Z",
  "database": "connected",
  "cache": "connected",
  "storage": "connected"
}
```

---

## Rate Limiting

All endpoints subject to rate limiting:

**Headers Returned:**
```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1234567890
```

**When exceeded (429):**
```json
{
  "error": "rate_limit_exceeded",
  "message": "Too many requests. Please retry after 60 seconds",
  "retry_after": 60
}
```

---

## Pagination

All list endpoints support pagination:

**Query Parameters:**
```
page=1 (default)
page_size=20 (default, max 100)
```

**Response includes:**
```json
{
  "count": 1500,
  "next": "https://api.authmed.com/api/v1/batches/?page=2",
  "previous": null,
  "results": [...]
}
```

---

## Next Steps

See:
1. [API Interactions](api-interactions.md) - How components use these endpoints
2. [RBAC Matrix](rbac-matrix.md) - Permission matrix for endpoints
3. [Sequence Diagrams](../sequences/) - Request/response flows

---

**Key Insight:** All endpoints follow RESTful conventions with consistent request/response formats, error handling, and authentication mechanisms.
