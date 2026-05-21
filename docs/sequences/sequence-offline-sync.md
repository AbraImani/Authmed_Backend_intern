# Sequence — Offline Sync and Conflict Resolution

**Summary**
Handling of inspections created offline on the mobile client and synchronization when connectivity is restored, including simple conflict resolution.

```mermaid
sequenceDiagram
    participant Mobile
    participant API
    participant DB
    Mobile->>Mobile: queue local changes (inspection, photos)
    Mobile-->>API: bulk sync when online
    API->>DB: attempt create/update
    DB-->>API: conflict detected? (version/timestamp)
    alt no conflict
        API->>DB: apply changes
        DB-->>API: ack
        API-->>Mobile: sync success
    else conflict
        API-->>Mobile: respond with conflict payload
        Mobile->>User: prompt merge/resolve
        Mobile-->>API: re-send resolved payload
        API->>DB: apply resolved changes
        API-->>Mobile: sync success
    end
```