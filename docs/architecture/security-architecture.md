# Security Architecture

## Overview

This document describes the security design principles, mechanisms, and controls implemented in AuthMed to protect data, systems, and users.

## Security Principles

1. **Least Privilege:** Users get minimum permissions needed
2. **Defense in Depth:** Multiple layers of security
3. **Fail Secure:** Errors default to denying access
4. **Separation of Concerns:** Auth, validation, business logic separate
5. **Audit Everything:** All security-relevant actions logged

---

## Authentication

### JWT Token-Based

**Token Structure:**
```json
{
  "sub": "user_id",
  "username": "john.doe@authmed.local",
  "role": "inspector",
  "org_id": "org-789",
  "site_id": "site-456",
  "iat": 1234567890,
  "exp": 1234654290,
  "iss": "authmed-api"
}
```

**Token Lifecycle:**
- **Access Token:**
  - Expiry: 24 hours
  - Used for API calls
  - In Authorization header
  - Cannot be revoked (use blacklist for emergency)

- **Refresh Token:**
  - Expiry: 7 days
  - Secure httpOnly cookie
  - Used to get new access token
  - Can be blacklisted on logout

**Security:**
- Signed with HS256 (HMAC-SHA256)
- Secret key: 256-bit random (stored in Secrets Manager)
- Issued only after successful password authentication
- Validated on every API request

### Password Policy

**Requirements:**
- Minimum 12 characters
- Must contain:
  - Uppercase letter (A-Z)
  - Lowercase letter (a-z)
  - Number (0-9)
  - Special character (!@#$%^&*)
- No repeats of previous 5 passwords
- Expire after 90 days

**Enforcement:**
- Client-side validation (UX feedback)
- Server-side validation (security enforcement)
- Rejection of weak passwords

### Multi-Factor Authentication (Future Phase 2)

**Implementation:**
- TOTP (Time-based One-Time Password)
- SMS backup codes
- Hardware security keys (YubiKey)

**Enforcement:**
- Required for admins immediately
- Optional for others (user choice)
- Can be mandated by org policy

---

## Authorization (Access Control)

### Role-Based Access Control (RBAC)

**Roles:**
- Inspector: Field inspection personnel
- Reviewer: QA decision makers
- Manager: Site/org oversight
- QA Officer: Compliance auditors
- Admin: System administrators

**Enforcement:**
- Every API endpoint has @require_permission decorator
- Checked at middleware level
- Organization scoping enforced

### Permission Model

```python
@require_permission(['GET'], '/batches/', ['inspector', 'reviewer', 'manager', 'qa', 'admin'])
def list_batches():
    # User must have one of these roles
    # AND must have org access
    pass
```

### Organization Scoping

**Rule:** Users can only access data in their organization

```sql
SELECT * FROM batches 
WHERE organization_id = request.user.organization_id
```

**Exceptions:**
- Admin can see all orgs
- QA Officer can see all orgs (read-only)

---

## Data Protection

### Encryption in Transit

**HTTPS/TLS:**
- Enforced on all endpoints
- Redirect HTTP to HTTPS
- TLS 1.3 minimum
- Strong cipher suites (AES-256-GCM)
- HSTS header (1 year, includeSubdomains)

**Configuration:**
```python
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_HSTS_SECONDS = 31536000
```

### Encryption at Rest

**Database:**
- PostgreSQL native encryption (pgcrypto)
- Encryption: AES-256
- Key management: AWS KMS
- Automatic encryption of sensitive columns

**S3 Storage:**
- Server-side encryption (SSE-S3)
- Encryption type: AES-256
- Automatic key rotation

**Backups:**
- Encrypted before transmission
- Encrypted in S3 Glacier
- Cross-region replication

### Sensitive Data Handling

**PII (Personally Identifiable Information):**
- User names hashed when possible
- Email addresses encrypted
- Phone numbers encrypted (if collected)
- Passwords never stored (use bcrypt + salt)

**Medical Data:**
- Batch data minimally collected
- Evidence photos encrypted
- No patient data in system (future: medical record linking)

**Configuration:**
```python
SENSITIVE_FIELDS = [
    'password',
    'email',
    'phone_number',
    'personal_notes'
]

# Automatically encrypt/hash these fields
class User(Model):
    email = EncryptedField()
    password = PasswordField()  # bcrypt
```

---

## Input Validation & Sanitization

### Input Validation

**All inputs validated:**
```python
class BatchSerializer(Serializer):
    lot_number = CharField(max_length=50, required=True)
    supplier_id = IntegerField(required=True)
    quantity = IntegerField(min_value=1, max_value=10000)
    received_date = DateTimeField()
    
    def validate_lot_number(self, value):
        if not re.match(r'^LOT-\d{8}-\d{3}$', value):
            raise ValidationError("Invalid lot number format")
        return value
```

**Validation layers:**
1. Type checking
2. Format validation
3. Range/length checks
4. Business logic validation

### Output Sanitization

**HTML escaping:**
```python
# In serializers: auto-escaped in JSON
safe_notes = escape(notes)
```

**URL encoding:**
```python
# S3 signed URLs properly encoded
signed_url = s3.generate_presigned_url(...)
```

### SQL Injection Prevention

**ORM Protection:**
- Use Django ORM (parameterized queries)
- Never raw SQL

```python
# Safe (ORM)
batches = Batch.objects.filter(lot_number=user_input)

# Unsafe (NEVER DO THIS)
# batches = Batch.objects.raw(f"SELECT * FROM batch WHERE lot_number = '{user_input}'")
```

---

## API Security

### Rate Limiting

**Implementation:**
```python
class RateLimitThrottle:
    scope = 'default'
    rate = '100/minute'
```

**Endpoints:**
- Login: 5 attempts/minute per IP
- API (authenticated): 100 requests/minute
- API (anonymous): 10 requests/minute

**Implementation:** Redis-backed counter

### CORS (Cross-Origin Resource Sharing)

**Configuration:**
```python
CORS_ALLOWED_ORIGINS = [
    "https://app.authmed.com",
    "https://dashboard.authmed.com",
]
CORS_ALLOW_CREDENTIALS = True
```

### CSRF (Cross-Site Request Forgery) Protection

**Token-based:**
- CSRF token issued with form/session
- Token validated on state-changing requests (POST, PUT, DELETE)
- SameSite cookie attribute

```python
CSRF_COOKIE_SECURE = True
CSRF_COOKIE_SAMESITE = 'Strict'
```

### Security Headers

```
Strict-Transport-Security: max-age=31536000; includeSubDomains
X-Content-Type-Options: nosniff
X-Frame-Options: DENY
X-XSS-Protection: 1; mode=block
Content-Security-Policy: default-src 'self'; script-src 'self'
```

---

## Logging & Monitoring

### Security Logging

**Logged Events:**
- Failed login attempts (with IP, timestamp)
- Successful logins (user, role, IP)
- Permission denied attempts
- Sensitive data access
- Configuration changes
- User management actions
- Data exports
- Deletion of records

**Format:**
```json
{
  "timestamp": "2026-05-19T14:45:00Z",
  "event": "login_success",
  "user_id": "u-12345",
  "username": "john.doe@authmed.local",
  "ip_address": "192.168.1.1",
  "user_agent": "Mozilla/5.0...",
  "status": "success"
}
```

**Retention:** 90 days

### Intrusion Detection

**Monitoring for:**
- Brute force attacks (>5 failed logins/hour)
- Unusual access patterns (high data export volume)
- Permission escalation attempts
- Unusual times of access
- Geographic anomalies

**Actions:**
- Alert security team
- Lock account (temporarily)
- Request 2FA verification

---

## Vulnerability Management

### Code Security

**Static Analysis:**
- Bandit (Python security linter)
- Runs in CI/CD pipeline
- Fails build on high-severity issues

**Dependency Scanning:**
- Safety checks (known vulnerabilities)
- Weekly automated scans
- Automatic updates for patches

**SAST (Static Application Security Testing):**
- SonarQube integration
- Identifies code weaknesses
- Enforces quality gates

### Dynamic Testing

**DAST (Dynamic Application Security Testing):**
- OWASP ZAP scans (staging)
- Penetration testing (quarterly)
- Load testing with security checks

### Vulnerability Disclosure

**Process:**
1. Security researcher discovers issue
2. Reports via security@authmed.com
3. Team reproduces and assesses severity
4. Fix developed and tested
5. Release coordinated
6. Researcher credited (if desired)

**SLA:**
- Critical: Fix within 24 hours
- High: Fix within 7 days
- Medium: Fix within 30 days

---

## Infrastructure Security

### Network Security

**VPC Architecture:**
```
Internet Gateway
    ↓
Load Balancer (Public)
    ↓
API Servers (Private)
    ↓
Database/Cache (Private, isolated)
```

**Security Groups:**
- Load Balancer: Allow HTTPS (443) from Internet
- API Servers: Allow 8000 only from LB
- Database: Allow 5432 only from API
- Redis: Allow 6379 only from API

### DDoS Protection

**AWS Shield Standard:**
- Automatic, no cost
- Layer 3/4 protection

**AWS WAF:**
- Layer 7 protection
- Rate limiting rules
- SQL injection rules
- XSS protection

### Secrets Management

**AWS Secrets Manager:**
- Database credentials
- API keys
- JWT secret key
- OAuth secrets
- SSL certificates

**Rotation:**
- Automatic every 90 days
- No downtime rotation
- Old secrets remain valid temporarily

---

## Compliance & Standards

### HIPAA (if handling patient data in future)
- Encryption of data in transit and at rest
- Access control with audit logging
- Business associate agreements (BAA)
- Regular security assessments

### GDPR (if serving EU)
- Data privacy by design
- User consent management
- Data retention policies
- Right to be forgotten (data deletion)
- DPA compliance

### ISO 27001 (Information Security Management)
- Information security policies
- Access control procedures
- Incident response plan
- Regular audits and reviews

---

## Incident Response

### Incident Classification

| Severity | Example | Response Time |
|----------|---------|----------------|
| Critical | Data breach, data loss | 1 hour |
| High | Service unavailable, auth bypass | 4 hours |
| Medium | Security flaw, account compromise | 24 hours |
| Low | Minor vulnerability, policy violation | 7 days |

### Response Procedure

1. **Detect:** Monitoring alerts, user reports
2. **Analyze:** Determine scope, severity, root cause
3. **Contain:** Stop ongoing damage (disable accounts, etc.)
4. **Eradicate:** Fix the vulnerability
5. **Recover:** Restore service
6. **Review:** Post-incident review, improvements

### Communication

- Notify affected users within 1 hour (critical)
- Transparency about what happened
- What users should do
- Prevention going forward

---

## Third-Party Security

### Vendor Assessment

**Before integration:**
- Security questionnaire
- Certifications review (SOC 2, ISO 27001)
- Data handling practices
- Incident response procedures

**Ongoing:**
- Annual re-assessment
- Vulnerability scanning
- Audit access logs

### Approved Third Parties

- AWS (cloud infrastructure)
- GitHub (code repository)
- Datadog (monitoring)
- SendGrid (email)

---

## Security Testing Checklist

- ✅ SQL injection tests
- ✅ XSS tests
- ✅ CSRF tests
- ✅ Authentication bypass tests
- ✅ Authorization bypass tests
- ✅ Sensitive data exposure tests
- ✅ Rate limiting tests
- ✅ Input validation tests
- ✅ Encryption verification
- ✅ Audit logging verification

---

## Next Steps

See:
1. [RBAC Matrix](rbac-matrix.md) - Permission details
2. [API Endpoints](api-endpoints.md) - Security by endpoint
3. [Deployment Architecture](deployment-architecture.md) - Infrastructure security

---

**Key Insight:** Security is multi-layered - authentication, authorization, encryption, validation, logging, and monitoring all work together to protect AuthMed data and systems.
