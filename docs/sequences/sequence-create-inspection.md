# Sequence — Create Inspection (Mobile)

**Summary**
Sequence describing reception of a batch from the mobile app through creation of the initial inspection record.

```mermaid
sequenceDiagram
    participant Mobile
    participant API
    participant DB
    participant Storage
    Mobile->>API: POST /api/inspections/ {batch_number, supplier, product, photos}
    API->>Storage: store photos
    Storage-->>API: file urls
    API->>DB: create BatchInspection + metadata (photos urls)
    DB-->>API: created inspection id
    API-->>Mobile: 201 Created + inspection id
    Mobile->>API: PATCH /api/inspections/{id} {status: "under_inspection"}
    API->>DB: update status
    API-->>Mobile: 200 OK
```
