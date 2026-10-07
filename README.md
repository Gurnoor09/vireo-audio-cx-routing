# Vireo Audio — CX Routing Diagnostic & AI Intent Router

> **Take-Home Assessment | Data Analyst + AI Engineer Role**  
> **Author:** Gurnoor Khurana  
> **Dataset Period:** January 2025 – June 2026 (18 months, 11,780 tickets)

---

## The Business Problem

Vireo Audio's Head of CX, Priya Raman, requested data to justify **two new Billing department hires** (~₹9L/year), citing Billing as the largest support queue. The Finance Controller, Arjun Mehta, withheld sign-off pending empirical evidence. Support Ops lead, Neha Kulkarni, suspected the queue data was distorted by intake misrouting.

**The question:** Is Billing genuinely overloaded, or is the intake queue inflated by a broken routing system?

---

## Key Finding

> **33.5% of all tickets assigned to Billing were ultimately resolved by a different team.**

| Metric | Value |
|--------|-------|
| Billing-assigned tickets (by intake bot) | 2,564 |
| Resolved by a team other than Billing | **860 (33.5%)** |
| Of those, resolved by Logistics | **795 (92.4% of misrouted)** |
| Billing's actual resolved workload | 1,838 tickets |
| Logistics' actual resolved workload | **2,673 tickets** |

Raw assigned intake volume is not a valid basis for headcount allocation decisions.

---

## Workload Comparison: Billing vs. Logistics

| Metric | Billing | Logistics |
|--------|---------|-----------|
| Dedicated agents | 4 | 5 |
| Resolved tickets | 1,838 | **2,673** |
| Resolved tickets / agent | 459.5 | **534.6 (+16.3%)** |
| Median elapsed resolution time* | 1.2 hours | **26.1 hours** |
| Cases taking >24 hours | 17.1% | **59.8%** |
| Customer satisfaction (CSAT) | 3.40 / 5.0 | **2.87 / 5.0** (lowest desk) |

> \* *Elapsed calendar case duration, not active agent keyboard hours. Logistics turnaround reflects external 3PL courier latency (BlueDart / Delhivery NDRs).*

Logistics carries a meaningfully higher per-agent resolved load and dramatically longer case lifetimes — consistent with the team absorbing hundreds of misrouted delivery tickets on top of its own organic intake.

---

## Root Cause: Keyword-Based Intake Routing

The existing intake bot uses **simple keyword matching** on the customer's opening message:

- Any message containing words like **"paid", "debited", "charged", "money", "UPI"** is tagged `Billing & Payments` and routed to Billing.
- This correctly captures GST invoicing and payment gateway queries — but also sweeps in every delivery failure where the customer mentions having paid, e.g.: *"Paid via UPI but order was never delivered."*

**Evidence of the distortion in Billing's intake:**

| Keyword Category | % of Billing Intake |
|-----------------|---------------------|
| Delivery / carrier keywords (tracking, courier, not delivered) | **26.0%** |
| Return / pickup keywords (reverse pickup, RTO, refund status) | **16.2%** |

**Downstream cost of misrouting:**
- **632 recorded inter-team transfers** originated from Billing (48.7% of all helpdesk transfers).
- **20.5% first-response SLA breach rate** in Billing, caused by tickets sitting in the wrong queue before transfer.

---

## The Proposed AI Solution

**Architecture:** TF-IDF vectorisation + Logistic Regression  
**Input:** Raw customer opening message (single feature)  
**Output:** Predicted functional department (5 classes)  
**Classes:** Billing · Logistics · Returns Desk · Escalations & Warranty · Frontline  
**Inference:** Runs locally, no cloud dependency  

The model evaluates the *semantic intent* of the entire message rather than triggering on isolated payment keywords. A message like *"paid via UPI but the package never arrived"* gets routed to **Logistics** — correctly identifying a fulfilment failure rather than a payment dispute.

---

## Validation Results

### Business-Critical Metric: Logistics → Billing Misrouting

| System | Logistics tickets sent to Billing | Misrouting Rate |
|--------|----------------------------------|-----------------|
| Legacy keyword bot | 119 / 489 | **24.3%** |
| AI Intent Router | 7 / 489 | **1.4%** |
| **Reduction** | | **−94.1%** |

### Logistics Recall

| System | Recall |
|--------|--------|
| Legacy bot | 72.39% |
| AI router | **86.30%** (+13.91 pp) |

### Overall Accuracy (for context only — see note)

| Split | AI Router | Legacy Bot |
|-------|-----------|-----------|
| Random stratified (n=2,356) | **81.32%** | 89.60% |
| Chronological holdout Q2 2026 (n=2,356) | **81.83%** | 89.60% |

> **Why overall accuracy is not the primary metric:** ~50% of all tickets are routine Frontline enquiries where the legacy bot defaults correctly by volume. High overall accuracy masks catastrophic cross-department failure on Logistics tickets. The AI router is not claimed to be "better overall" — it is specifically better on the business-critical misrouting problem.

The chronological holdout (training on the earliest 80%, testing on the most recent 20% of tickets by date) confirms the model generalises without accuracy decay to forward-looking data.

---

## Financial Context

Two financial categories are presented separately to avoid misleading framing:

| Category | Amount | Label |
|----------|--------|-------|
| Direct routing opportunity | **₹2.5–2.9L/year** | *Estimated opportunity from reducing avoidable transfer costs (~₹1.5–1.9L) and SLA breach store credits (~₹1.0L). Not guaranteed savings.* |
| Proposed staffing decision value | **~₹9L/year** | *Approximate annual cost of the proposed two hires. Not claimed as realised savings.* |

---

## Final Recommendation

```
Fix routing  →  Monitor for 60 days  →  Reassess staffing
```

1. **Deploy AI Intent Routing** on chat and email intake to stop delivery tickets flowing into Billing.
2. **Monitor for 60 days:** measure post-deployment transfer rates, queue shrinkage, and Logistics direct intake.
3. **Reassess staffing from clean baselines:** if Logistics remains capacity-constrained after routing is fixed, assess headcount there — not in Billing.

> *"Do not approve two Billing hires yet. Fix routing first, then reassess staffing using resolved workload and service outcomes."*

---

## Repository Structure

```
vireo-audio-cx-routing/
├── README.md                        ← This file
├── requirements.txt                 ← Python dependencies
├── .gitignore
│
├── data/
│   └── README.md                    ← Data placement instructions (raw files excluded)
│
├── src/
│   ├── pipeline.py                  ← Data cleaning, timezone fix, SLA flags, joins
│   ├── analytics.py                 ← Workload, transfer, financial analytics
│   ├── ai_classifier.py             ← TF-IDF + LR model training & benchmark
│   ├── chronological_validation.py  ← Chronological out-of-time validation
│   └── export_dashboard_data.py     ← Exports JSON for dashboard
│
├── dashboard/
│   ├── index.html                   ← Six-tab executive dashboard
│   ├── styles.css
│   ├── app.js                       ← Navigation + AI router demo
│   └── data.json                    ← Pre-computed dashboard data
│
├── outputs/
│   ├── ai_classifier_results.json   ← Model benchmark metrics
│   ├── analytics_summary.json       ← Key operational statistics
│   ├── misrouting_crosstab.csv      ← Transfer matrix by team pair
│   ├── monthly_by_assigned_team.csv
│   ├── monthly_by_resolving_team.csv
│   ├── monthly_by_category.csv
│   └── web_simulator_config.json    ← Dashboard simulator config
│
├── docs/
│   ├── EXECUTIVE_MEMO.md            ← One-page decision memo for Priya Raman
│   ├── ANALYSIS.md                  ← Full diagnostic analysis
│   ├── FINAL_EVIDENCE.md            ← Locked evidence used in submission
│   └── METHODOLOGY.md               ← Methodology, assumptions, limitations
│
└── submission/
    └── submission-form.md           ← Assessment submission answers
```

---

## Reproducing the Analysis

### Prerequisites

```bash
pip install -r requirements.txt
```

Place the raw assessment data files (supplied separately by Vireo Audio) in the `data/` directory. See [`data/README.md`](data/README.md) for the required filenames.

### Run in order

```bash
# 1. Clean and enrich the raw data
python src/pipeline.py

# 2. Generate analytics and financial metrics
python src/analytics.py

# 3. Train and benchmark the AI intent classifier
python src/ai_classifier.py

# 4. Run chronological out-of-time validation
python src/chronological_validation.py

# 5. Export dashboard data
python src/export_dashboard_data.py
```

### View the dashboard

```bash
cd dashboard
python -m http.server 8090
# Open http://localhost:8090/
```

---

## Key Limitations

- **Elapsed time ≠ agent labor hours.** Resolution time is calendar case duration. Logistics turnaround reflects 3PL courier latency, not agent effort.
- **AI router is not claimed to be better overall.** Overall accuracy favours the legacy bot due to Frontline class imbalance. The AI router is specifically better on the Logistics misrouting problem.
- **Financial estimates are indicative.** The ₹2.5–2.9L routing opportunity is an estimate derived from transfer cost rates and SLA breach data; actual realised savings depend on deployment fidelity and ticket volume.
- **Chronological test covers Q2 2026 only.** Seasonal demand patterns (e.g., Diwali Q4 surge) may shift class distributions.

---

## Stack

| Layer | Technology |
|-------|-----------|
| Language | Python 3.10+ |
| Data | pandas, numpy |
| ML | scikit-learn (TF-IDF, Logistic Regression) |
| Visualisation | Chart.js (client-side, no build step) |
| Dashboard | Vanilla HTML/CSS/JS |
