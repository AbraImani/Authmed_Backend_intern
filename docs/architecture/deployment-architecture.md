# Deployment Architecture

## Overview

This document describes how AuthMed is deployed, scaled, monitored, and maintained across development, staging, and production environments.

## Infrastructure Overview

```mermaid
graph TB
    Users["👥 Users<br/>Mobile + Web"]
    
    subgraph "CDN"
        CDN["📡 CloudFront<br/>Static assets<br/>Images<br/>JS/CSS"]
    end
    
    subgraph "API Layer"
        LB["⚖️ Load Balancer<br/>HTTPS<br/>TLS 1.3"]
        
        API1["🔧 API Server 1<br/>Django 4.2<br/>Port 8000"]
        API2["🔧 API Server 2<br/>Django 4.2<br/>Port 8000"]
        API3["🔧 API Server 3<br/>Django 4.2<br/>Port 8000"]
    end
    
    subgraph "Data Layer"
        MainDB["🗄️ PostgreSQL<br/>Primary<br/>Replication"]
        ReplicaDB["🗄️ PostgreSQL<br/>Replica<br/>Read-only"]
        Cache["⚡ Redis<br/>Cache<br/>Sessions"]
    end
    
    subgraph "Storage"
        S3["💾 AWS S3<br/>Evidence files<br/>Backups"]
    end
    
    subgraph "Services"
        Queue["📬 Celery Queue<br/>Async jobs<br/>Risk scoring"]
        Notifications["🔔 Notification<br/>Email<br/>Push"]
        Search["🔍 Elasticsearch<br/>Full-text search<br/>Logging"]
    end
    
    subgraph "Monitoring"
        Prometheus["📊 Prometheus<br/>Metrics"]
        Grafana["📈 Grafana<br/>Dashboards"]
        ELK["🔍 ELK Stack<br/>Logs<br/>Analysis"]
    end
    
    Users -->|HTTPS| CDN
    Users -->|API Calls| LB
    
    LB -->|Route| API1
    LB -->|Route| API2
    LB -->|Route| API3
    
    API1 -->|Read/Write| MainDB
    API2 -->|Read/Write| MainDB
    API3 -->|Read/Write| MainDB
    
    API1 -->|Cache| Cache
    API2 -->|Cache| Cache
    API3 -->|Cache| Cache
    
    MainDB -->|Replicate| ReplicaDB
    ReplicaDB -->|Read| API1
    ReplicaDB -->|Read| API2
    ReplicaDB -->|Read| API3
    
    API1 -->|Store| S3
    API2 -->|Store| S3
    API3 -->|Store| S3
    
    API1 -->|Queue jobs| Queue
    API2 -->|Queue jobs| Queue
    API3 -->|Queue jobs| Queue
    
    Queue -->|Send| Notifications
    Queue -->|Read/Write| MainDB
    
    API1 -->|Index| Search
    API2 -->|Index| Search
    API3 -->|Index| Search
    
    API1 -->|Metrics| Prometheus
    API2 -->|Metrics| Prometheus
    API3 -->|Metrics| Prometheus
    
    Prometheus -->|Display| Grafana
    Search -->|Display| ELK
    
    style LB fill:#e74c3c,color:#fff
    style API1 fill:#3498db,color:#fff
    style API2 fill:#3498db,color:#fff
    style API3 fill:#3498db,color:#fff
    style MainDB fill:#95a5a6,color:#fff
    style ReplicaDB fill:#95a5a6,color:#fff
    style Cache fill:#f39c12,color:#fff
    style S3 fill:#34495e,color:#fff
    style Queue fill:#9b59b6,color:#fff
    style Prometheus fill:#2980b9,color:#fff
    style Grafana fill:#2980b9,color:#fff
```

## Deployment Environments

### Development
**Purpose:** Local development and testing  
**Infrastructure:**
- Single Django server (local)
- SQLite or PostgreSQL (local)
- No load balancing
- No redundancy

**Deployment:** Manual (run locally)

---

### Staging
**Purpose:** Pre-production testing, UAT, performance testing  
**Infrastructure:**
- 2 API servers behind load balancer
- PostgreSQL database (with replication)
- Redis cache
- S3 for evidence storage
- Celery for async tasks
- Full monitoring

**Deployment:** Continuous deployment on merge to `staging` branch

---

### Production
**Purpose:** Live service for end-users  
**Infrastructure:**
- 3+ API servers behind load balancer (auto-scaling)
- PostgreSQL database with primary-replica replication
- Redis cache cluster (multi-node)
- S3 for evidence storage (replicated regions)
- Celery workers (auto-scaling)
- Complete monitoring & alerting
- CDN for static assets
- Backup and disaster recovery

**Deployment:** Controlled, tagged releases with rollback capability

---

## Container & Orchestration

### Docker

**Dockerfile (Multi-stage):**
```dockerfile
# Build stage
FROM python:3.11-slim as builder
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Runtime stage
FROM python:3.11-slim
WORKDIR /app
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY . .
RUN python manage.py collectstatic --noinput
CMD ["gunicorn", "authmed.wsgi:application", "--bind", "0.0.0.0:8000"]
```

**Images:**
- `authmed-api:latest` - API server
- `authmed-worker:latest` - Celery worker
- `authmed-nginx:latest` - Reverse proxy

### Kubernetes (Future)

**Deployments:**
- API Deployment (3 replicas, auto-scaling 1-10)
- Worker Deployment (2 replicas, auto-scaling 1-5)
- PostgreSQL StatefulSet
- Redis Sentinel

**Services:**
- api-service (LoadBalancer)
- database-service (ClusterIP)
- cache-service (ClusterIP)

**ConfigMaps:**
- environment variables
- risk scoring rules
- alert thresholds

**Secrets:**
- database password
- JWT secret key
- AWS credentials
- API keys

---

## Database Deployment

### PostgreSQL Configuration

**Primary Database:**
- Version: 14+
- Storage: 100GB initially (auto-scaling)
- Backup: Daily snapshots + WAL archiving
- Replication: Streaming replication to replica

**Replica Database:**
- Read-only copy for analytics
- Used for reporting queries
- Reduces load on primary

**Backups:**
- Daily automated backups (AWS RDS automated backups)
- 30-day retention
- Cross-region replication
- Point-in-time recovery available

**Monitoring:**
- Query performance
- Slow query log
- Replication lag
- Disk space usage

---

## Cache Layer

### Redis

**Primary Cache:**
- Cluster mode: No (single-node for MVP)
- Memory: 2GB initially
- Eviction policy: LRU
- Persistence: RDB snapshots

**Use Cases:**
- Session storage
- KPI metric caching
- Rate limiting counters
- Temporary job state

**Monitoring:**
- Memory usage
- Hit/miss ratio
- Connection count

---

## Object Storage

### AWS S3

**Buckets:**
- `authmed-evidence` (production)
- `authmed-staging` (staging)

**Configuration:**
- Versioning: Enabled
- Encryption: AES-256
- Lifecycle: 90 days -> Glacier
- Replication: Cross-region
- ACLs: Private

**Access:**
- Signed URLs (temporary access)
- IAM role-based (EC2 instances)
- CloudFront distribution

---

## Load Balancing

### AWS Application Load Balancer (ALB)

**Configuration:**
- HTTPS only (redirect HTTP to HTTPS)
- TLS 1.3
- Certificate: AWS Certificate Manager
- Health check: `/api/v1/health/` (every 5 seconds)
- Sticky sessions: Disabled (stateless)

**Routing:**
- `/api/*` → API servers
- `/static/*` → CloudFront
- `/media/*` → S3 signed URLs

---

## Monitoring & Observability

### Prometheus Metrics

**Collected:**
- HTTP request duration
- Request count by endpoint
- Error rates
- Database query latency
- Cache hit/miss ratio
- Worker queue depth
- Memory/CPU usage

**Retention:** 15 days

### Grafana Dashboards

**Dashboards:**
- System health
- API performance
- Database metrics
- Cache performance
- Business metrics (KPI trends)
- Error rates & alerts

### ELK Stack (Logging)

**Elasticsearch:**
- Logs from all servers
- Retention: 30 days
- Searchable

**Kibana:**
- Log visualization
- Alert creation
- Debugging support

### CloudWatch (AWS)

**Alarms:**
- CPU > 80%
- Memory > 85%
- API error rate > 1%
- Database connection pool exhausted
- Cache eviction spike
- Replication lag > 1 second

---

## CI/CD Pipeline

### GitHub Actions

**On every commit:**
```yaml
1. Lint (flake8, black)
2. Type check (mypy)
3. Unit tests (pytest)
4. Security scan (bandit)
5. Coverage report (>80% required)
6. Build Docker image
7. Push to registry (if merged)
8. Deploy to staging (if merged to main)
9. Smoke tests
10. Deploy to production (manual trigger)
```

**Manual approval required for production deployment**

---

## Scaling Strategy

### Horizontal Scaling (API Servers)

**Auto-Scaling Rules:**
- CPU > 70% for 5 min → Add 1 instance
- CPU < 30% for 10 min → Remove 1 instance
- Min: 1 instance, Max: 10 instances

**Load:**
- 1 instance: ~50 req/sec
- 3 instances: ~150 req/sec
- 10 instances: ~500 req/sec

### Vertical Scaling (Database)

**Monitoring:**
- Connections approaching limit → Increase instance size
- Disk usage > 80% → Increase volume
- Query latency increasing → Add indexes or upgrade CPU

---

## Disaster Recovery

### RTO/RPO Targets
- **RTO (Recovery Time Objective):** 1 hour
- **RPO (Recovery Point Objective):** 15 minutes

### Backup Strategy
- Daily snapshots (automated)
- Cross-region replication
- Point-in-time recovery (30 days)
- Test restore monthly

### Failover Process
1. Detect primary failure
2. Promote replica to primary
3. Create new replica
4. DNS failover
5. Notify team

---

## Security

### Network Security
- VPC with private subnets for database
- Security groups restrict access
- WAF protects from common attacks
- DDoS protection (AWS Shield)

### Encryption
- TLS 1.3 in transit
- AES-256 at rest (S3)
- Database encryption enabled
- Secrets stored in AWS Secrets Manager

### Access Control
- IAM roles for EC2
- Database credentials rotation
- API key management
- Audit logging

---

## Cost Optimization

### Current Estimate (Production)
- API servers (3 × t3.medium): $120/month
- RDS PostgreSQL (db.t3.medium): $200/month
- Redis (cache.t3.small): $50/month
- S3 (100GB/month): $25/month
- Load balancer: $20/month
- Monitoring/logging: $100/month
- **Total: ~$515/month**

### Scaling Costs
- Per additional API server: ~$40/month
- Per 100GB S3: ~$25/month
- Database upgrade tier: $50-100/month

---

## Rollback Strategy

### Zero-Downtime Deployments

```
1. New version running alongside old
2. Route 10% traffic to new version
3. Monitor for errors (5 minutes)
4. If errors: Rollback (automatic)
5. If success: Route 50% traffic (5 min)
6. If success: Route 100% traffic
7. Drain old version gracefully
```

### Database Migration Strategy
- Backward-compatible migrations only
- Run migrations before code deployment
- Rollback migrations if deployment fails

---

## Maintenance Windows

### Scheduled Maintenance
- Frequency: Monthly (second Sunday 2 AM UTC)
- Duration: 30 minutes max
- Notification: Email 1 week before
- Rollback tested before maintenance

### Unscheduled Maintenance
- Emergency patches within 24 hours
- Security patches within 4 hours
- Communication: Incident page updated

---

## Next Steps

See:
1. [Security Architecture](security-architecture.md) - Authentication, encryption, compliance
2. [Monitoring & Alerting](monitoring-alerting.md) - Detailed monitoring setup
3. [Runbooks](../operations/runbooks.md) - Operational procedures

---

**Key Insight:** AuthMed infrastructure is designed for reliability (99.5% uptime), security (encryption in transit & at rest), scalability (auto-scaling), and observability (comprehensive monitoring) in production environments.
