# Sequence 14g — Offline sync and conflict resolution

**Résumé**
Gestion des inspections créées hors-ligne sur mobile et synchronisation lorsque la connectivité revient, avec résolution de conflits simples.

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