# Data Flow Diagrams (DFD)

## Overview

Data Flow Diagrams (DFD) show how data moves through AuthMed - from users, through processing, into storage, and back out to consumers.

## Level 0: System Context DFD

```mermaid
graph LR
    Users["Users"]
    HealthFacility["Healthcare Facility"]
    Regulators["Regulators"]

    AuthMed["AUTHMED<br/>Medicine Inspection<br/>System"]

    Storage["Data Storage<br/>- Database<br/>- S3 Objects"]
    
    Users -->|Inspections, Decisions| AuthMed
    HealthFacility -->|Batch Data| AuthMed
    AuthMed -->|Reports, Status| Users
    AuthMed -->|Compliance Reports| Regulators
    AuthMed -->|Batch Status| HealthFacility
    AuthMed -.->|Read/Write| Storage
    
    %% Styles removed for neutral diagram presentation
```

## Level 1: Major Processes DFD

```mermaid
graph TD
    Users["Users"]
    HealthFacility["Healthcare Facility"]
    
    subgraph AUTHMED["AUTHMED SYSTEM"]
        Process1["1.0 Inspection<br/>Reception<br/>& Registration"]
        Process2["2.0 Evidence<br/>Capture &<br/>Data Entry"]
        Process3["3.0 Risk<br/>Scoring &<br/>Analysis"]
        Process4["4.0 Human<br/>Review &<br/>Decision"]
        Process5["5.0 Reporting<br/>& Compliance"]
    end
    
    subgraph STORAGE["DATA STORAGE"]
        DB["Database<br/>- Batches<br/>- Users<br/>- Decisions"]
        ObjStore["Object Store<br/>- Photos<br/>- Documents"]
    end
    
    HealthFacility -->|Batch Notification| Process1
    Process1 -->|Batch Data| DB
    
    Users -->|Evidence Upload| Process2
    Process2 -->|Photos| ObjStore
    Process2 -->|Batch Details| DB
    
    DB -->|Batch Data| Process3
    Process3 -->|Risk Score| DB
    
    DB -->|Pending Inspections| Process4
    Users -->|Decisions| Process4
    Process4 -->|Final Decision| DB
    
    DB -->|Historical Data| Process5
    Process5 -->|Reports| Users
    Process5 -->|Compliance Data| HealthFacility
    
    %% Styles removed for neutral diagram presentation
```

## Level 2: Detailed Process Flows

### Process 1: Inspection Reception & Registration

```mermaid
graph TD
    Batch["Batch Received"]
    
    Reg["1.1 Register<br/>Batch"]
    
    Search["1.2 Search<br/>Supplier"]
    
    Assign["1.3 Assign<br/>Inspector"]
    
    Notify["1.4 Notify<br/>Inspector"]
    
    DB[(Database)]
    
    Batch --> Reg
    Reg -->|Batch Details| DB
    
    Reg -->|Supplier ID| Search
    Search -->|Supplier Info| DB
    
    Reg -->|Site Info| Assign
    Assign -->|Inspector ID| DB
    
    Assign -->|Notify Inspector| Notify
    Notify -->|Push Notification| Users["Mobile App"]
    
    style Batch fill:#27ae60,color:#fff
    style Reg fill:#3498db,color:#fff
    style Search fill:#3498db,color:#fff
    style Assign fill:#3498db,color:#fff
    style Notify fill:#3498db,color:#fff
    style DB fill:#95a5a6,color:#fff
    style Users fill:#9b59b6,color:#fff
```

### Process 2: Evidence Capture & Data Entry

```mermaid
graph TD
    Mobile["Mobile App"]
    
    Capture["2.1 Capture<br/>Evidence<br/>Photos/Notes"]
    
    Upload["2.2 Upload<br/>Evidence"]
    
    Extract["2.3 Extract<br/>Batch Data"]
    
    Validate["2.4 Validate<br/>Data"]
    
    Store["2.5 Store<br/>in DB"]
    
    S3["Object Store"]
    DB[(Database)]
    
    Mobile --> Capture
    Capture -->|Photos, Notes| Upload
    Upload -->|Evidence Files| S3
    Upload -->|Metadata| DB
    
    Mobile --> Extract
    Extract -->|Product Info, Conditions| Validate
    Validate -->|Validated Data| Store
    Store -->|Batch Data| DB
    
    style Mobile fill:#9b59b6,color:#fff
    style Capture fill:#e74c3c,color:#fff
    style Upload fill:#e74c3c,color:#fff
    style Extract fill:#e74c3c,color:#fff
    style Validate fill:#e74c3c,color:#fff
    style Store fill:#e74c3c,color:#fff
    style S3 fill:#95a5a6,color:#fff
    style DB fill:#95a5a6,color:#fff
```

### Process 3: Risk Scoring & Analysis

```mermaid
graph TD
    Trigger["Batch Data<br/>Submitted"]
    
    Fetch["3.1 Fetch<br/>Batch Data"]
    
    FetchProd["3.2 Fetch<br/>Product Info"]
    
    FetchSupp["3.3 Fetch<br/>Supplier History"]
    
    Calculate["3.4 Calculate<br/>Risk Score"]
    
    Generate["3.5 Generate<br/>Recommendation"]
    
    Store["3.6 Store<br/>Result"]
    
    DB[(Database)]
    RiskEngine["Risk Scoring<br/>Engine"]
    
    Trigger --> Fetch
    Fetch -->|Batch Data| DB
    DB -->|Batch Info| Calculate
    
    FetchProd -->|Product Data| DB
    FetchSupp -->|Supplier History| DB
    
    Calculate -->|Score Calculation| RiskEngine
    RiskEngine -->|Score + Factors| Generate
    Generate -->|Score + Recommendation| Store
    Store -->|Risk Result| DB
    
    style RiskEngine fill:#e67e22,color:#fff
    style Calculate fill:#e67e22,color:#fff
    style Generate fill:#e67e22,color:#fff
    style Fetch fill:#3498db,color:#fff
    style FetchProd fill:#3498db,color:#fff
    style FetchSupp fill:#3498db,color:#fff
    style Store fill:#16a085,color:#fff
    style DB fill:#95a5a6,color:#fff
```

### Process 4: Human Review & Decision

```mermaid
graph TD
    Queue["Add to<br/>Review Queue"]
    
    Assign["4.1 Assign<br/>Reviewer"]
    
    Notify["4.2 Notify<br/>Reviewer"]
    
    Fetch["4.3 Fetch<br/>Batch Details"]
    
    Review["4.4 Review<br/>Evidence"]
    
    Decide["4.5 Decide<br/>Accept/Isolate/Escalate"]
    
    Record["4.6 Record<br/>Decision"]
    
    DB[(Database)]
    Dashboard["Dashboard"]
    
    Queue --> Assign
    Assign -->|Reviewer ID| DB
    Assign -->|Reviewer ID| Notify
    Notify -->|Notification| Dashboard
    
    Dashboard -->|User Action| Fetch
    Fetch -->|Batch Data| DB
    Fetch -->|Evidence| S3["Storage"]
    
    Fetch --> Review
    Review -->|User Decision| Decide
    Decide -->|Final Decision| Record
    Record -->|Decision + Notes| DB
    
    style Assign fill:#9b59b6,color:#fff
    style Notify fill:#9b59b6,color:#fff
    style Fetch fill:#8e44ad,color:#fff
    style Review fill:#8e44ad,color:#fff
    style Decide fill:#8e44ad,color:#fff
    style Record fill:#16a085,color:#fff
    style DB fill:#95a5a6,color:#fff
    style Dashboard fill:#3498db,color:#fff
    style S3 fill:#95a5a6,color:#fff
```

### Process 5: Reporting & Compliance

```mermaid
graph TD
    Request["Report<br/>Request"]
    
    Query["5.1 Query<br/>Data"]
    
    Format["5.2 Format<br/>Report"]
    
    Export["5.3 Export<br/>Report"]
    
    Archive["5.4 Archive<br/>Batch"]
    
    DB[(Database)]
    Reports["Reports<br/>- CSV<br/>- PDF"]
    Archive_Store["Archive<br/>Storage"]
    
    Request -->|User/System| Query
    Query -->|SQL Query| DB
    DB -->|Historical Data| Query
    
    Query -->|Data| Format
    Format -->|Formatted Data| Export
    Export -->|Reports| Reports
    
    Query -->|Completed Batches| Archive
    Archive -->|Immutable| Archive_Store
    
    style Query fill:#16a085,color:#fff
    style Format fill:#16a085,color:#fff
    style Export fill:#16a085,color:#fff
    style Archive fill:#34495e,color:#fff
    style DB fill:#95a5a6,color:#fff
    style Reports fill:#2980b9,color:#fff
    style Archive_Store fill:#95a5a6,color:#fff
```

## Complete Data Flow Summary

```
INBOUND DATA:
├── Batch Registration
│   ├── Batch number
│   ├── Supplier ID
│   ├── Product ID
│   ├── Quantity
│   └── Received date/time
│
├── Field Inspection
│   ├── Photos (S3)
│   ├── Inspector notes
│   ├── Conditions observed
│   ├── Anomalies detected
│   └── Timestamps
│
└── Human Decisions
    ├── Reviewer ID
    ├── Decision (Accept/Isolate/Escalate)
    ├── Comments
    └── Override flags

PROCESSING:
├── Risk Scoring
│   ├── Analyze conditions (40%)
│   ├── Detect anomalies (30%)
│   ├── Supplier history (20%)
│   └── Product risk (10%)
│
├── Decision Logic
│   ├── Auto-approve (score < 20)
│   ├── Queue for review (score 20-60)
│   └── Auto-escalate (score > 60)
│
└── Audit Logging
    ├── All user actions
    ├── All system events
    ├── Timestamps
    └── Change history

STORAGE:
├── Database (PostgreSQL)
│   ├── Batch metadata
│   ├── User actions
│   ├── Decisions
│   ├── Risk scores
│   └── Audit logs
│
└── Object Store (S3)
    ├── Evidence photos
    ├── Documents
    └── Export files

OUTBOUND DATA:
├── Real-time Updates
│   ├── Batch status to mobile
│   ├── Queue updates to dashboard
│   └── KPI metrics
│
├── Reports
│   ├── CSV exports
│   ├── PDF compliance reports
│   └── Historical analytics
│
└── Compliance Data
    ├── Audit trails
    ├── Regulatory reports
    └── Traceability records
```

---

## Data Stores

### Primary Database (PostgreSQL)

**Tables:**
- `users` - User accounts and roles
- `organizations` - Multi-org support
- `sites` - Multiple locations per org
- `batch_inspection` - Main batch records
- `evidence` - Photos and documents metadata
- `risk_result` - Calculated risk scores
- `review_decision` - Final decisions
- `audit_log` - Complete activity trail
- `suppliers` - Supplier information
- `products` - Product reference library

### Object Storage (S3)

**Buckets:**
- `authmed-evidence` - Photos and documents
- `authmed-exports` - Report files
- `authmed-archive` - Long-term archive

---

## Data Flows by Use Case

### Use Case 1: Inspect & Score (Minutes 0-7)
```
Batch Registered → Inspector Assigned → Evidence Captured → 
Data Validated → Risk Calculated → Decision Routed
Data Flow: Batch metadata → Photos → Validation → Score
```

### Use Case 2: Review & Approve (Minutes 7-15)
```
Pending Review → Reviewer Opens → Reviews Evidence → 
Makes Decision → Records Audit → Executes Action
Data Flow: Batch details + Evidence → Decision → Action
```

### Use Case 3: Reporting & Audit (On Demand)
```
Query Date Range → Fetch Batches → Fetch Decisions → 
Generate Report → Export to Format
Data Flow: Historical batches → Aggregated metrics → Report
```

---

## Data Security

### At Rest
- Database: Encrypted PostgreSQL (optional)
- S3: Encrypted objects

### In Transit
- HTTPS/TLS for all API calls
- Signed URLs for S3 access
- JWT tokens for authentication

### Access Control
- Role-based permission filtering
- User can only see own org data
- Admin access limited to authorized users
- Audit log immutable

---

## Next Steps

See:
1. [API Interactions](api-interactions.md) - How components exchange data via APIs
2. [API Endpoints](api-endpoints.md) - Detailed endpoint specifications
3. [Database Schema](../data-model/database-schema.md) - Table structures

---

**Key Insight:** Data flows through AuthMed in a structured pipeline from batch intake through inspection, analysis, decision, execution, and permanent archive - with every step logged and auditable.
