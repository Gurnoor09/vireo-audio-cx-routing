# EXECUTIVE DECISION MEMO

**To:** Priya Raman, Head of Customer Experience, Vireo Audio  
**From:** Kabir Nanda & Analytics Engagement Team  
**Date:** October 7, 2026  
**Subject:** Headcount Allocation & Support Queue Diagnostic: Billing vs. Logistics  
**Source of Truth:** [`FINAL_EVIDENCE.md`](file:///Users/gurnoorkhurana/.gemini/antigravity-ide/scratch/vireo_audio/FINAL_EVIDENCE.md)  

---

### 1. Decision & Recommendation
**Do not approve the two proposed Billing hires yet. Correct routing first, then reassess staffing using resolved workload and service outcomes.**

Committing the proposed two-hire budget (**approximately ₹9L/year** [Decision-Value]) to Billing would allocate resources to an artificially inflated queue. We recommend deploying intelligent intake routing immediately, establishing clean workload baselines, and evaluating whether seasonal capacity is needed in Logistics ahead of the Q4 festive peak.

---

### 2. What We Found
An audit of all 11,780 support tickets demonstrates that raw intake queue size does not reflect actual operational workload:
* **The Billing Queue is an Artifact [Observed Fact]:** **33.5% of Billing-assigned tickets** (860 of 2,564) were ultimately resolved by another team—predominantly Logistics (795 tickets).
* **Actual Resolved Workload [Observed Fact]:** Billing resolved **1,838 tickets**, whereas Logistics resolved **2,673 tickets** (+45.4% higher volume).
* **Workload per Agent [Observed Fact]:** Billing’s 4 agents handled **459.5 resolved tickets/agent**, while Logistics’ 5 agents carried **534.6 resolved tickets/agent** (+16.3% higher burden per head).
* **Case Aging & Turnaround [Observed Fact]:** Logistics median elapsed resolution turnaround is **26.1 hours** (59.8% spanning >24h), compared to **1.2 hours** for Billing. *(Note: This reflects elapsed calendar case duration, not active agent keyboard hours).*
* **Customer Experience [Observed Fact]:** Logistics exhibits both the longest median elapsed turnaround time (26.1h) and the company’s lowest customer satisfaction (**2.87 / 5.0** vs. Billing’s **3.40 / 5.0**).

---

### 3. Root Cause
The intake bot relies on crude keyword matching [Observed Fact]. When customers submit inquiries containing words like *"paid"*, *"debited"*, or *"charged"* (e.g., *"paid via UPI but order was never delivered"*), the bot mechanically tags them as `Billing & Payments` and assigns them to Billing. 
* **26.0%** of Billing intake messages contained explicit delivery/carrier keywords; **16.2%** contained return/pickup keywords [Observed Fact].
* This misrouting generated 632 recorded transfers out of Billing and caused a **20.5% first-response SLA breach rate** in the Billing queue due to triage lag [Observed Fact].

---

### 4. Intervention
Replace simplistic keyword rules with a semantic **AI Intent Router** on chat and email intake that evaluates the customer’s full message context to dispatch delivery and return issues directly to their owning departments.

---

### 5. Validation
We validated the model on a strict chronological out-of-time test set of **2,356 tickets from Q2 2026** (April–June 2026) [Observed Fact]:
* **Why Overall Accuracy is Not the Primary Metric:** The legacy bot achieved a higher overall headline accuracy (**89.60%** vs. AI's **81.83%** [Model Estimate]) solely because ~50% of the desk consists of routine Frontline queries where the bot defaults correctly. However, headline accuracy masks catastrophic cross-department failure.
* **Cross-Team Precision [Model Estimate]:** Among true Logistics tickets (489 tickets in Q2 2026):
  * The legacy bot misrouted **119 tickets (24.3%)** into Billing.
  * The AI router misrouted only **7 tickets (1.4%)** into Billing.
  * This represents a **94.1% reduction** in this specific misrouting failure mode and improves Logistics recall from **72.39% to 86.30%**.

---

### 6. Business Impact
* **Proposed Two-Hire Cost Avoidance [Decision-Value]:** Pausing the proposed two hires preserves an uncommitted budget of **approximately ₹9L/year**, preventing misallocation into a queue that resolved only 1,838 tickets.
* **Estimated Direct Annual Routing Opportunity [Model Estimate]:** Correcting misrouting delivers an estimated **₹2.5L to ₹2.9L/year** in direct operational savings by eliminating avoidable Billing transfer fees (~₹1.5–1.9L/yr @ ₹305/transfer per Policy §4) and preventing triage-lag SLA breach store credits (~₹1.0L/yr @ ₹350/ticket per Policy §3).

---

### 7. Next Steps
1. **Deploy AI Intent Routing:** Transition chat and email intake to intent classification to halt the flow of delivery tickets into Billing.
2. **Monitor for 60 Days:** Measure post-deployment transfer rates, Billing queue shrinkage, and Logistics direct intake.
3. **Reassess Staffing for Festive Surge:** Using clean, post-routing workload metrics, evaluate whether additional seasonal support is required in Logistics ahead of Diwali.

---

### 8. Key Limitations
* **Elapsed Time $\neq$ Labor Hours:** Logistics resolution turnaround (26.1h median) reflects external carrier latency (BlueDart/Delhivery NDRs) and warehouse updates, not continuous agent working time.
* **Residual Misrouting:** While the AI router reduces Logistics-to-Billing misrouting by 94.1%, it does not eliminate all transfer errors (7 Logistics tickets were still sent to Billing in Q2 2026).
* **Desk-Wide Capacity:** Correcting routing eliminates artificial triage friction, but it does not determine whether Vireo requires zero new hires desk-wide during peak volume months.
