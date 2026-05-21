# Sequence — Risk Result

**Summary**
Scoring pipeline: triggered after data ingestion or extraction. The Risk Engine computes and stores a `RiskResult`.

```mermaid
sequenceDiagram
    participant API
    participant Ingest
    participant RiskEngine
    participant DB
    API->>Ingest: trigger scoring for inspection
    Ingest->>RiskEngine: send inspection data
    RiskEngine-->>Ingest: risk_score + flags
    Ingest->>DB: write RiskResult
    DB-->>Ingest: ack
    Ingest-->>API: notify scoring complete
    API->>DB: update inspection.status = "pending_review"
    API-->>Web: websocket/event notify reviewer
```
