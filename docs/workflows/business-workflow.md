# Business Workflow Diagram

## Overview

This diagram illustrates the complete end-to-end business workflow for inspecting and approving/rejecting a medicine batch. It shows all phases from lot arrival through final execution and audit recording.

## Workflow Diagram

```mermaid
flowchart TD
   Start["Batch Received"]

   Register["Register Batch\n- identify lot\n- supplier, product, quantity, date"]

   InspectionCreate["Create Inspection\n- assign inspector\n- site / organization\n- draft status"]

   FieldInspection["Field Inspection\n- physical verification\n- sampling if required"]

   EvidenceCapture["Capture Evidence\n- photos, documents, notes"]

   DataExtraction["Data Extraction / Entry\n- product info, batch details, observations"]

   RiskGeneration["Risk Scoring\n- automatic analysis\n- scoring rules\n- recommendations"]

   OperationalDecision["Operational Decision\n- Accept, Isolate, Escalate"]

   HumanReview{"Human Review required?"}

   ReviewQueue["Review Queue\n- pending inspections\n- reviewer assignment"]

   ReviewDecision["Review & Validation\n- review evidence\n- approve / reject"]

   RecordAudit["Record Audit\n- immutable audit entry\n- actor and timestamp"]

   Execution["Execute Decision\n- release, quarantine, or escalate"]

   Dashboard["Dashboard Visibility\n- batch status, risk level, KPIs"]

   End["Inspection Complete"]

   Start --> Register
   Register --> InspectionCreate
   InspectionCreate --> FieldInspection
   FieldInspection --> EvidenceCapture
   EvidenceCapture --> DataExtraction
   DataExtraction --> RiskGeneration
   RiskGeneration --> OperationalDecision
   OperationalDecision --> HumanReview
   HumanReview -->|Yes (complex)| ReviewQueue
   HumanReview -->|No (clear)| RecordAudit
   ReviewQueue --> ReviewDecision
   ReviewDecision --> RecordAudit
   RecordAudit --> Execution
   Execution --> Dashboard
   Dashboard --> End

```

## Workflow Steps

### Step 1: Reception & Registration (2 min)
**Trigger:** Medicine batch arrives at facility  
**Actor:** Receiving staff  
**Location:** Warehouse/Receiving area  

**Activities:**
1. Batch physically arrives
2. Receiving staff notified (email, system notification)
3. Staff opens AuthMed and creates new batch record:
   - Batch/Lot number
   - Supplier (selected from dropdown)
   - Product reference (selected from dropdown)
   - Quantity received
   - Date/time received
   - Received by (user)
4. Batch saved → Status = "Draft"
5. System automatically assigns available inspector

**Output:** Batch registered, Status = "Draft"  
**Next:** Inspector assigned

---

### Step 2: Inspection Creation & Assignment (1 min)
**Trigger:** Batch registered  
**Actor:** Inspector  
**Location:** Mobile app / Office  

**Activities:**
1. Inspector receives push notification: "New batch for inspection"
2. Inspector opens AuthMed mobile app
3. Sees assigned batch with details
4. Acknowledges receipt (taps "Start Inspection")
5. Status → "Pending"
6. Inspector prepares for field work

**Output:** Status = "Pending", Inspector acknowledged  
**Next:** Field inspection

---

### Step 3: Field Inspection (1-2 min)
**Trigger:** Inspector ready  
**Actor:** Inspector  
**Location:** Warehouse/Receiving area  

**Activities:**
1. Inspector physically locates batch
2. Verifies batch identity against system record
3. Performs visual inspection:
   - Check package condition (seal, label, packaging)
   - Look for damage, contamination signs
   - Observe storage area conditions
   - Check temperature/humidity if available
   - Note any deviations from expected state
4. Opens mobile app, taps "Start field inspection"
5. Status → "Under Inspection"

**Output:** Status = "Under Inspection", Field inspection initiated  
**Next:** Evidence capture

---

### Step 4: Evidence Capture (1-2 min)
**Trigger:** Field inspection underway  
**Actor:** Inspector  
**Location:** Warehouse/Receiving area  

**Activities:**
1. Inspector uses mobile app camera to capture photos:
   - Package exterior (full view)
   - Seals and labels (close-up)
   - Any visible damage or anomalies
   - Batch identity/lot number markings
   - Storage area conditions (if relevant)
2. Inspector types notes into app:
   - Observations about condition
   - Any anomalies or red flags
   - Environmental factors (temperature, humidity)
   - Anything noteworthy
3. Inspector uploads all evidence
4. System timestamps and attributes all evidence to inspector

**Output:** Evidence stored in S3, metadata in database  
**Next:** Data extraction

---

### Step 5: Data Extraction & Entry (1 min)
**Trigger:** Evidence captured  
**Actor:** Inspector  
**Location:** Mobile app  

**Activities:**
1. Inspector confirms/corrects batch information:
   - Product details (name, SKU, expected packaging)
   - Batch details (manufacturing date, expiration date, etc.)
   - Lot size and condition
2. Inspector enters observed conditions:
   - Temperature (if measured)
   - Humidity (if measured)
   - Any storage deviations
3. Inspector notes any anomalies:
   - Packaging damage
   - Seal compromise
   - Discoloration
   - Leakage
   - Contamination signs
4. Inspector submits all data
5. Status → "Evidence Captured"

**Output:** Batch data complete, ready for analysis  
**Next:** Risk scoring

---

### Step 6: Automatic Risk Scoring (2-5 sec)
**Trigger:** All batch data entered  
**Actor:** Risk Engine (automated)  
**Location:** Backend  

**Activities:**
1. Risk Engine retrieves all batch information:
   - Physical observations from evidence
   - Inspector notes
   - Batch metadata
   - Product risk category (from library)
   - Supplier historical data
2. Engine applies scoring rules:
   - Condition factors (packaging, seal, temperature exposure) = 40%
   - Observable anomalies detected = 30%
   - Supplier reliability history = 20%
   - Product risk category = 10%
3. Engine calculates numeric score (0-100):
   - Score < 20: Low risk → Recommend "ACCEPT"
   - Score 20-60: Medium risk → Recommend "ISOLATE"
   - Score > 60: High risk → Recommend "ESCALATE"
4. Engine flags any detected anomalies
5. RiskResult record created and stored

**Output:** Risk score calculated, recommendation generated  
**Next:** Operational decision

---

### Step 7: Operational Decision (2-5 sec)
**Trigger:** Risk score generated  
**Actor:** Decision Engine (automated)  
**Location:** Backend  

**Activities:**
1. Decision Engine evaluates risk score against thresholds
2. Decision Engine determines:
   - **ACCEPT** if score < low threshold (typically 20)
   - **ISOLATE** if score between thresholds (typically 20-60)
   - **ESCALATE** if score > high threshold (typically 60)
3. Stores decision in OperationalDecision record
4. Status → "Pending Review"

**Output:** Initial decision proposed  
**Next:** Human review (conditional)

---

### Step 8a: Human Review - Simple Case (0-2 min)
**Trigger:** Clear decision (low risk or high risk)  
**Condition:** Automated decision is obvious  
**Actor:** Reviewer  
**Location:** Dashboard (expedited path)  

**Activities:**
1. Low-risk batch (score < 20):
   - Reviewer sees batch in "Auto-Approved" queue
   - Can spot-check evidence if desired
   - Can approve with one click
   - Low-risk batches expedited
2. High-risk batch (score > 60):
   - Reviewer sees batch in "Auto-Escalate" queue
   - May briefly confirm high risk is warranted
   - Escalates to management

**Output:** Decision confirmed  
**Next:** Record audit

---

### Step 8b: Human Review - Complex Case (2-5 min)
**Trigger:** Medium-risk decision (20-60 range)  
**Condition:** Reviewer judgment needed  
**Actor:** Reviewer  
**Location:** Dashboard / Review Queue  

**Activities:**
1. Batch appears in reviewer's "Pending Decision" queue
2. Reviewer opens batch record
3. Reviews evidence:
   - Views all photos captured by inspector
   - Reads inspector notes
   - Examines risk score breakdown
   - Sees supplier history
4. Reviewer may:
   - Approve the recommendation
   - Override with different decision
   - Request additional inspection
   - Add notes/comments
5. Reviewer clicks "Submit Decision"
6. Status → "Review Complete"

**Output:** Final decision recorded by human  
**Next:** Record audit

---

### Step 9: Record Audit (1-2 sec)
**Trigger:** Decision made (auto or human)  
**Actor:** Audit Service (automated)  
**Location:** Backend  

**Activities:**
1. System records decision in AuditLog
2. Records who made decision (actor ID)
3. Records when decision was made (timestamp)
4. Records what decision was made
5. Records justification/notes
6. Records all evidence attached
7. System generates immutable audit record
8. Status → "Execution Pending"

**Output:** Complete audit trail created  
**Next:** Execution

---

### Step 10: Execution (5-10 min)
**Trigger:** Decision finalized  
**Actor:** Logistics/Warehouse staff  
**Location:** Physical warehouse  

**Activities:**

**If ACCEPTED:**
1. Batch released from receiving
2. Moved to appropriate storage location
3. Made available for dispensing
4. Status → "Accepted"
5. Stakeholders notified (email)

**If ISOLATED:**
1. Batch moved to quarantine area
2. Marked as "Do Not Dispense"
3. Flagged for further analysis or observation
4. Status → "Isolated"
5. Quality officer notified for follow-up

**If ESCALATED:**
1. Batch immediately held
2. Director/Management notified urgently
3. Investigation initiated
4. Potential rejection, supplier contact, regulatory reporting
5. Status → "Escalated"
6. Follow-up actions documented

**Output:** Decision physically executed  
**Next:** Dashboard update

---

### Step 11: Dashboard Update (1 sec)
**Trigger:** Execution complete  
**Actor:** System (automated)  
**Location:** Backend  

**Activities:**
1. Batch status updated to final state
2. Dashboard metrics recalculated:
   - Total batches processed
   - Acceptance/isolation/escalation rates
   - Average risk scores
   - Supplier trends
3. KPI dashboard refreshes in real-time
4. Managers see updated metrics
5. Notifications sent to relevant stakeholders

**Output:** Full visibility achieved  
**Next:** Completed & archived

---

### Step 12: Permanent Archive & Compliance (Ongoing)
**Trigger:** Inspection complete  
**Actor:** System & Compliance teams  
**Location:** Storage & Portal  

**Activities:**
1. Batch inspection marked as "Completed"
2. Evidence files archived permanently (S3)
3. Metadata archived in database
4. Audit trail immutable and searchable
5. Available for:
   - Regulatory audit requests
   - Compliance reporting
   - Historical analysis
   - Traceability (if recall needed)

**Output:** Complete, traceable, compliance-ready record  
**Status:** "Archived"

---

## Total Timeline

| Phase | Duration | Status |
|-------|----------|--------|
| Reception + Registration | 2 min | Batch In System |
| Field Inspection | 1-2 min | Inspector Working |
| Evidence Capture | 1-2 min | Capturing Proof |
| Data Extraction | 1 min | Entering Details |
| Risk Scoring | < 1 sec | Automated |
| Initial Decision | < 1 sec | Proposed |
| Human Review (if needed) | 0-5 min | Reviewer Working |
| Record Audit | < 1 sec | Logged |
| Execution | 5-10 min | Physical Action |
| **Total** | **~5-15 min** | **Complete** |

---

## Decision Matrix

| Risk Score | Condition | Decision | Review | Execution |
|------------|-----------|----------|--------|-----------|
| 0-20 | Low risk, no anomalies | ACCEPT | Expedited/Optional | Release to stock |
| 20-40 | Medium, minor anomalies | ISOLATE | Required | Quarantine |
| 40-60 | Medium-high, needs validation | ISOLATE/ESCALATE | Required | Quarantine/Review |
| 60-80 | High risk, serious concerns | ESCALATE | Required | Immediate escalation |
| 80-100 | Critical, fail inspection | ESCALATE | Required | Reject/Investigate |

---

## Exception Handling

**Inspector questions about risk?**
- Inspector can add notes/photos before inspection is submitted
- Can request preliminary feedback from system
- Doesn't block workflow

**Reviewer disagrees with score?**
- Reviewer can override automated decision
- Override is recorded in audit trail
- System can learn from override (future ML)

**Batch needs additional testing?**
- Can be isolated pending lab results
- Status remains "Isolated" until resolved
- Can re-inspect batch with new evidence

**Discovery of issues after acceptance?**
- Batch can be recalled
- Audit trail shows who accepted and why
- Can find all related batches from same supplier/batch run
- Future: Track which patients/pharmacies received batch

---

## Workflow Variations

### Express Path (Low Risk < 20)
```
Registration → Inspection → Scoring → Auto-Accept → Done
Duration: ~5-8 minutes
Reviewer: Spot-check only
```

### Standard Path (Medium Risk 20-60)
```
Registration → Inspection → Scoring → Review Queue → Reviewer Decision → Done
Duration: ~10-15 minutes
Reviewer: Full review required
```

### Escalation Path (High Risk > 60)
```
Registration → Inspection → Scoring → Auto-Escalate → Management Action → Done
Duration: ~15-30 minutes
Manager: Investigation + follow-up
```

---

## Next Steps

See:
1. [Activity Diagram](activity-diagram.md) - Detailed step-by-step process
2. [Batch Inspection State Machine](batch-inspection-state-machine.md) - State transitions
3. [Sequence Diagrams](../sequences/) - Technical implementation details

---

**Key Insight:** The workflow is designed to be fast (5-15 min), auditable (every step logged), and intelligent (risk-based decision routing).
