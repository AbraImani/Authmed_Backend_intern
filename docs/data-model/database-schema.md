# Database Schema (PostgreSQL)

## Overview

Complete PostgreSQL database schema for AuthMed with tables, columns, indexes, and constraints.

## Schema SQL

### Organizations Table

```sql
CREATE TABLE organizations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(100) NOT NULL,
    registration_number VARCHAR(50) UNIQUE,
    country VARCHAR(2) NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT name_not_empty CHECK (LENGTH(name) > 0),
    CONSTRAINT country_length CHECK (LENGTH(country) = 2)
);

CREATE INDEX idx_organizations_is_active ON organizations(is_active);
CREATE INDEX idx_organizations_country ON organizations(country);
```

### Sites Table

```sql
CREATE TABLE sites (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID NOT NULL REFERENCES organizations(id),
    name VARCHAR(100) NOT NULL,
    address VARCHAR(500),
    city VARCHAR(50),
    country VARCHAR(2),
    phone VARCHAR(20),
    manager_id UUID,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT site_name_not_empty CHECK (LENGTH(name) > 0)
);

CREATE INDEX idx_sites_organization_id ON sites(organization_id);
CREATE INDEX idx_sites_manager_id ON sites(manager_id);
CREATE INDEX idx_sites_is_active ON sites(is_active);
```

### Users Table

```sql
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID NOT NULL REFERENCES organizations(id),
    site_id UUID REFERENCES sites(id),
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(254) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    first_name VARCHAR(50),
    last_name VARCHAR(50),
    role VARCHAR(20) NOT NULL DEFAULT 'inspector',
    phone VARCHAR(20),
    is_active BOOLEAN DEFAULT TRUE,
    last_login TIMESTAMP,
    password_expires_at TIMESTAMP,
    mfa_enabled BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT valid_role CHECK (role IN ('inspector', 'reviewer', 'manager', 'qa_officer', 'admin')),
    CONSTRAINT username_length CHECK (LENGTH(username) >= 3),
    CONSTRAINT email_not_empty CHECK (email ~ '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}$')
);

CREATE INDEX idx_users_organization_id ON users(organization_id);
CREATE INDEX idx_users_site_id ON users(site_id);
CREATE INDEX idx_users_role ON users(role);
CREATE INDEX idx_users_is_active ON users(is_active);
CREATE INDEX idx_users_email ON users(email);
```

### Suppliers Table

```sql
CREATE TABLE suppliers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(100) NOT NULL,
    registration_number VARCHAR(50),
    country VARCHAR(2),
    contact_person VARCHAR(100),
    phone VARCHAR(20),
    email VARCHAR(254),
    quality_score NUMERIC(3,2),
    batches_supplied INTEGER DEFAULT 0,
    batches_rejected INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT name_not_empty CHECK (LENGTH(name) > 0),
    CONSTRAINT score_range CHECK (quality_score >= 0 AND quality_score <= 1)
);

CREATE INDEX idx_suppliers_name ON suppliers(name);
CREATE INDEX idx_suppliers_quality_score ON suppliers(quality_score);
```

### Products Table

```sql
CREATE TABLE products (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    sku VARCHAR(50) UNIQUE NOT NULL,
    name VARCHAR(200) NOT NULL,
    description VARCHAR(1000),
    manufacturer VARCHAR(100),
    risk_category VARCHAR(20) DEFAULT 'medium',
    requires_refrigeration BOOLEAN DEFAULT FALSE,
    storage_temp_min NUMERIC(5,1),
    storage_temp_max NUMERIC(5,1),
    shelf_life_days INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT valid_risk_category CHECK (risk_category IN ('low', 'medium', 'high')),
    CONSTRAINT name_not_empty CHECK (LENGTH(name) > 0)
);

CREATE INDEX idx_products_sku ON products(sku);
CREATE INDEX idx_products_risk_category ON products(risk_category);
```

### Batch Inspections Table

```sql
CREATE TABLE batch_inspections (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID NOT NULL REFERENCES organizations(id),
    site_id UUID NOT NULL REFERENCES sites(id),
    lot_number VARCHAR(50) NOT NULL,
    supplier_id UUID NOT NULL REFERENCES suppliers(id),
    product_id UUID NOT NULL REFERENCES products(id),
    quantity_received INTEGER NOT NULL,
    received_date TIMESTAMP NOT NULL,
    received_by_id UUID REFERENCES users(id),
    inspector_id UUID REFERENCES users(id),
    status VARCHAR(50) NOT NULL DEFAULT 'draft',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT valid_status CHECK (status IN (
        'draft', 'pending_inspection', 'under_inspection', 'evidence_captured',
        'pending_scoring', 'scored', 'pending_review', 'review_in_progress',
        'accepted', 'isolated', 'escalated', 'execution_pending', 'archived'
    )),
    CONSTRAINT quantity_positive CHECK (quantity_received > 0),
    CONSTRAINT unique_batch_check UNIQUE (organization_id, site_id, lot_number, supplier_id, received_date)
);

CREATE INDEX idx_batch_inspections_organization_id ON batch_inspections(organization_id);
CREATE INDEX idx_batch_inspections_site_id ON batch_inspections(site_id);
CREATE INDEX idx_batch_inspections_supplier_id ON batch_inspections(supplier_id);
CREATE INDEX idx_batch_inspections_product_id ON batch_inspections(product_id);
CREATE INDEX idx_batch_inspections_status ON batch_inspections(status);
CREATE INDEX idx_batch_inspections_created_at ON batch_inspections(created_at);
CREATE INDEX idx_batch_inspections_inspector_id ON batch_inspections(inspector_id);
```

### Evidence Table

```sql
CREATE TABLE evidence (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    batch_inspection_id UUID NOT NULL REFERENCES batch_inspections(id),
    type VARCHAR(20) NOT NULL,
    description VARCHAR(500),
    file_url VARCHAR(500),
    file_size_bytes INTEGER,
    mime_type VARCHAR(50),
    uploaded_by_id UUID NOT NULL REFERENCES users(id),
    uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    thumbnail_url VARCHAR(500),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT valid_type CHECK (type IN ('photo', 'document', 'note', 'video')),
    CONSTRAINT file_size_positive CHECK (file_size_bytes > 0)
);

CREATE INDEX idx_evidence_batch_inspection_id ON evidence(batch_inspection_id);
CREATE INDEX idx_evidence_uploaded_by_id ON evidence(uploaded_by_id);
CREATE INDEX idx_evidence_created_at ON evidence(created_at);
```

### Risk Results Table

```sql
CREATE TABLE risk_results (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    batch_inspection_id UUID UNIQUE NOT NULL REFERENCES batch_inspections(id),
    risk_score NUMERIC(5,2) NOT NULL,
    recommendation VARCHAR(20) NOT NULL,
    condition_score NUMERIC(5,2),
    condition_weight NUMERIC(3,2),
    anomaly_score NUMERIC(5,2),
    anomaly_weight NUMERIC(3,2),
    supplier_score NUMERIC(5,2),
    supplier_weight NUMERIC(3,2),
    product_score NUMERIC(5,2),
    product_weight NUMERIC(3,2),
    confidence_percent NUMERIC(5,2),
    calculated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT valid_recommendation CHECK (recommendation IN ('accept', 'isolate', 'escalate')),
    CONSTRAINT score_range CHECK (risk_score >= 0 AND risk_score <= 100),
    CONSTRAINT weights_sum CHECK (
        (condition_weight + anomaly_weight + supplier_weight + product_weight) BETWEEN 0.99 AND 1.01
    )
);

CREATE INDEX idx_risk_results_batch_inspection_id ON risk_results(batch_inspection_id);
CREATE INDEX idx_risk_results_risk_score ON risk_results(risk_score);
CREATE INDEX idx_risk_results_recommendation ON risk_results(recommendation);
```

### Anomalies Table

```sql
CREATE TABLE anomalies (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    risk_result_id UUID NOT NULL REFERENCES risk_results(id),
    anomaly_type VARCHAR(50) NOT NULL,
    description VARCHAR(500),
    severity VARCHAR(20) NOT NULL DEFAULT 'medium',
    evidence_link_ids TEXT,
    detected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT valid_anomaly_type CHECK (anomaly_type IN (
        'seal_damage', 'packaging_damage', 'contamination', 'discoloration',
        'temperature_exposure', 'humidity_exposure', 'leakage', 'other'
    )),
    CONSTRAINT valid_severity CHECK (severity IN ('low', 'medium', 'high'))
);

CREATE INDEX idx_anomalies_risk_result_id ON anomalies(risk_result_id);
CREATE INDEX idx_anomalies_anomaly_type ON anomalies(anomaly_type);
```

### Review Decisions Table

```sql
CREATE TABLE review_decisions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    batch_inspection_id UUID UNIQUE NOT NULL REFERENCES batch_inspections(id),
    risk_result_id UUID REFERENCES risk_results(id),
    reviewer_id UUID NOT NULL REFERENCES users(id),
    decision VARCHAR(20) NOT NULL,
    override_risk_recommendation BOOLEAN DEFAULT FALSE,
    notes VARCHAR(2000),
    evidence_reviewed_ids TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT valid_decision CHECK (decision IN ('accepted', 'isolated', 'escalated'))
);

CREATE INDEX idx_review_decisions_batch_inspection_id ON review_decisions(batch_inspection_id);
CREATE INDEX idx_review_decisions_reviewer_id ON review_decisions(reviewer_id);
CREATE INDEX idx_review_decisions_decision ON review_decisions(decision);
CREATE INDEX idx_review_decisions_created_at ON review_decisions(created_at);
```

### Audit Log Table

```sql
CREATE TABLE audit_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID NOT NULL REFERENCES organizations(id),
    actor_id UUID REFERENCES users(id),
    action VARCHAR(100) NOT NULL,
    resource_type VARCHAR(50) NOT NULL,
    resource_id VARCHAR(100) NOT NULL,
    changes JSONB,
    reason VARCHAR(500),
    ip_address VARCHAR(45),
    user_agent VARCHAR(500),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    
    CONSTRAINT log_immutable UNIQUE (id)
);

CREATE INDEX idx_audit_logs_organization_id ON audit_logs(organization_id);
CREATE INDEX idx_audit_logs_actor_id ON audit_logs(actor_id);
CREATE INDEX idx_audit_logs_resource_type ON audit_logs(resource_type);
CREATE INDEX idx_audit_logs_resource_id ON audit_logs(resource_id);
CREATE INDEX idx_audit_logs_created_at ON audit_logs(created_at);
CREATE INDEX idx_audit_logs_action ON audit_logs(action);

-- Immutability trigger
CREATE OR REPLACE FUNCTION prevent_audit_log_update()
RETURNS TRIGGER AS $$
BEGIN
    RAISE EXCEPTION 'Audit logs are immutable and cannot be updated';
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER audit_log_immutable
    BEFORE UPDATE OR DELETE ON audit_logs
    FOR EACH ROW EXECUTE FUNCTION prevent_audit_log_update();
```

---

## Indexes Summary

**Total Indexes:** 40+

**High-Priority Indexes (used frequently):**
- batch_inspections.status
- batch_inspections.created_at
- batch_inspections.organization_id
- audit_logs.created_at
- risk_results.risk_score
- review_decisions.decision

---

## Database Size Estimate

At scale (1 year of operation, 250 batches/day):

```
Organizations: 10 KB
Sites: 100 KB
Users: 1 MB
Suppliers: 500 KB
Products: 5 MB
Batch Inspections: 100 MB
Evidence (metadata): 50 MB
Risk Results: 30 MB
Review Decisions: 30 MB
Audit Logs: 500 MB
────────────────────
Total (without evidence files): ~720 MB
Evidence Files (S3): 1-2 TB
```

---

## Backup Strategy

**Full backups:** Daily (AWS RDS automated)
**Incremental backups:** Hourly via WAL archiving
**Retention:** 30 days rolling
**Recovery:** Point-in-time recovery available

---

## Migration Management

All schema changes via Alembic migrations:

```bash
# Create migration
alembic revision --autogenerate -m "Add new column"

# Apply migration
alembic upgrade head

# Rollback
alembic downgrade -1
```

---

## Next Steps

See:
1. [Domain Model](domain-model.md) - Entity relationships
2. [Batch Inspection Entity](batch-inspection-entity.md) - Detailed entity spec
3. [API Endpoints](../architecture/api-endpoints.md) - How to query this data

---

**Key Insight:** Schema is normalized (3NF), indexed for performance, immutable for audit logs, and designed for scalability and compliance.
