# Sequence — Decision Execution and Notification

**Summary**
After a decision is recorded, the system executes operational actions (release to stock, quarantine, or escalation) and sends notifications to stakeholders.

```mermaid
sequenceDiagram
    participant System
    participant DB
    participant API
    participant Notifications
    participant Warehouse
    System->>DB: read ReviewDecision
    DB-->>System: decision payload
    System->>Warehouse: if accepted -> release to stock
    System->>Warehouse: if isolated -> mark quarantined
    System->>Notifications: send email/push to stakeholders
    Notifications-->>System: ack
    System->>DB: update inspection state = completed
    System-->>API: emit event for dashboards
```
