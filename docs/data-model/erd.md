# Entity Relationship Diagram (ERD)

## Overview
This diagram represents the relational database structure for the Django/DRF backend. It shows the main tables, key fields and relationships (PK/FK).

```mermaid
erDiagram
    ORGANIZATION ||--o{ SITE : manages
    ORGANIZATION ||--o{ USER : "has"
    ORGANIZATION ||--o{ PRODUCTREFERENCE : "owns"
    ORGANIZATION ||--o{ BATCHINSPECTION : "owns"
    
    SITE ||--o{ USER : "assigns"
    SITE ||--o{ BATCHINSPECTION : "receives"
    
    USER ||--o{ BATCHINSPECTION : "inspects"
    USER ||--o{ REVIEWDECISION : "reviews"
    USER ||--o{ EVIDENCE : "creates"
    USER ||--o{ AUDITLOG : "acts"
    
    SUPPLIER ||--o{ BATCHINSPECTION : "supplies"
    
    PRODUCTREFERENCE ||--o{ BATCHINSPECTION : "contains"
    
    BATCHINSPECTION ||--o{ EVIDENCE : "generates"
    BATCHINSPECTION ||--|| RISKRESULT : "produces"
    BATCHINSPECTION ||--o{ REVIEWDECISION : "receives"
    BATCHINSPECTION ||--o{ AUDITLOG : "triggers"
    
    ORGANIZATION : int id PK
    ORGANIZATION : string name
    ORGANIZATION : string address
    ORGANIZATION : string contact
    ORGANIZATION : timestamp created_at
    
    SITE : int id PK
    SITE : int organization_id FK
    SITE : string name
    SITE : string address
    SITE : timestamp created_at
    
    USER : int id PK
    USER : string username
    USER : string email
    USER : string password_hash
    USER : enum role
    USER : int organization_id FK
    USER : int site_id FK
    USER : boolean is_active
    USER : timestamp created_at
    
    SUPPLIER : int id PK
    SUPPLIER : string name
    SUPPLIER : string address
    SUPPLIER : string contact
    SUPPLIER : json historical_performance
    SUPPLIER : timestamp created_at
    
    PRODUCTREFERENCE : int id PK
    PRODUCTREFERENCE : int organization_id FK
    PRODUCTREFERENCE : string name
    PRODUCTREFERENCE : string sku
    PRODUCTREFERENCE : string description
    PRODUCTREFERENCE : timestamp created_at
    
    BATCHINSPECTION : int id PK
    BATCHINSPECTION : int organization_id FK
    BATCHINSPECTION : int site_id FK
    BATCHINSPECTION : int supplier_id FK
    BATCHINSPECTION : int product_id FK
    BATCHINSPECTION : int inspector_id FK
    BATCHINSPECTION : string batch_number
    BATCHINSPECTION : timestamp received_at
    BATCHINSPECTION : enum status
    BATCHINSPECTION : enum outcome
    BATCHINSPECTION : text notes
    BATCHINSPECTION : timestamp created_at
    
    EVIDENCE : int id PK
    EVIDENCE : int inspection_id FK
    EVIDENCE : string file_path
    EVIDENCE : string file_type
    EVIDENCE : text notes
    EVIDENCE : int created_by_id FK
    EVIDENCE : timestamp created_at
    
    RISKRESULT : int id PK
    RISKRESULT : int inspection_id FK
    RISKRESULT : float risk_score
    RISKRESULT : text reason
    RISKRESULT : json flags
    RISKRESULT : timestamp calculated_at
    
    REVIEWDECISION : int id PK
    REVIEWDECISION : int inspection_id FK
    REVIEWDECISION : int reviewer_id FK
    REVIEWDECISION : enum decision
    REVIEWDECISION : text notes
    REVIEWDECISION : timestamp reviewed_at
    
    AUDITLOG : int id PK
    AUDITLOG : int actor_id FK
    AUDITLOG : string action
    AUDITLOG : string object_type
    AUDITLOG : string object_id
    AUDITLOG : json details
    AUDITLOG : timestamp timestamp
```
