# C4 Container Diagram

**Explication courte**
Vue "container" qui montre les composants principaux du système : mobile, dashboard, API Django DRF, stockage, base de données et services futurs (ML/OCR).

```mermaid
graph TB
    subgraph "CLIENT_LAYER"
        Mobile["📱 Mobile App<br/>Inspection Terrain<br/>- Batch reception<br/>- Evidence capture<br/>- Field inspection<br/>- Offline support"]
        Web["🌐 Web Dashboard<br/>Review & Monitoring<br/>- Inspection tracking<br/>- Risk review<br/>- Decision queue<br/>- KPI dashboard"]
        Admin["⚙️ Admin Portal<br/>Administration<br/>- User mgmt<br/>- Config<br/>- Reports"]
    end
    
    subgraph "API_LAYER"
        API["🔌 Django REST API<br/>Inspection API<br/>- /inspections<br/>- /evidence<br/>- /risk-results<br/>- /decisions<br/>- /audit-logs"]
    end
    
    subgraph "APPLICATION_LAYER"
        Backend["⚙️ Django Application<br/>- Auth & JWT<br/>- Business Logic<br/>- Risk Scoring<br/>- Workflow Orchestration<br/>- Audit Logging"]
    end
    
    subgraph "DATA_LAYER"
        DB["🗄️ PostgreSQL Database<br/>- Organizations<br/>- Sites<br/>- Users<br/>- Inspections<br/>- Evidence<br/>- Risk Results<br/>- Decisions<br/>- Audit Logs"]
        Storage["💾 Evidence Storage<br/>- Photos<br/>- Documents<br/>- File service"]
    end
    
    subgraph "FUTURE_SERVICES"
        MLService["🤖 ML/OCR Service<br/>Future: Advanced<br/>risk scoring,<br/>data extraction"]
    end
    
    Mobile -->|API calls<br/>JSON| API
    Web -->|API calls<br/>JSON| API
    Admin -->|API calls<br/>JSON| API
    
    API -->|exposes| Backend
    Backend -->|queries/writes| DB
    Backend -->|stores/retrieves| Storage
    Backend -.->|future<br/>integration| MLService
    
    style CLIENT_LAYER fill:#ecf0f1,stroke:#34495e
    style API_LAYER fill:#e8f8f5,stroke:#27ae60
    style APPLICATION_LAYER fill:#fef5e7,stroke:#f39c12
    style DATA_LAYER fill:#fadbd8,stroke:#e74c3c
    style FUTURE_SERVICES fill:#f4ecf7,stroke:#9b59b6
```
