# Submission Form — Vireo Audio Take-Home Assessment

**Candidate:** Gurnoor Khurana  
**Role Applied:** Data Analyst + AI Engineer  
**Submission Date:** October 7, 2026  
**Dataset Period:** January 2025 – June 2026 (11,780 tickets)

---

## Part 1: Business Problem & Recommendation

### What is the core business question?

Should Vireo Audio approve two new Billing department hires (~₹9L/year) based on Billing being the "largest" support queue?

### What is your recommendation?

**Do not approve the two proposed Billing hires yet. Fix routing first, then reassess staffing using resolved workload and service outcomes.**

Billing's apparent dominance (22% of intake) is an artefact of a keyword-based intake bot that misroutes delivery and fulfilment failures into Billing whenever customers mention payment language. 33.5% of Billing-assigned tickets were ultimately resolved by another team — primarily Logistics.

---

## Part 2: Key Analytical Findings

### Finding 1: Billing intake is distorted by misrouting

- 860 of 2,564 Billing-assigned tickets (33.5%) were resolved by a different team
- 795 of those were resolved by Logistics
- The cause is keyword-based routing: messages containing "paid", "debited", or "charged" are tagged as Billing regardless of actual issue type

### Finding 2: Logistics carries a higher real workload per agent

| | Billing | Logistics |
|--|---------|-----------|
| Resolved tickets | 1,838 | 2,673 |
| Agents | 4 | 5 |
| Resolved / agent | 459.5 | **534.6** |
| Median resolution time | 1.2h | **26.1h** |
| CSAT | 3.40 | **2.87** (lowest desk) |

### Finding 3: The AI intent router reduces the specific Logistics→Billing misrouting by 94.1%

- Legacy bot: 119 of 489 true Logistics tickets sent to Billing (24.3%)
- AI router: 7 of 489 true Logistics tickets sent to Billing (1.4%)
- Logistics recall: 72.39% → 86.30% (+13.91 pp)

---

## Part 3: Model Details

| Property | Value |
|----------|-------|
| Algorithm | TF-IDF + Logistic Regression |
| Input | Customer opening message only |
| Target | Resolving team (5 functional classes) |
| Train/test split | 80/20 stratified random + chronological holdout |
| Random test accuracy | 81.32% (n=2,356) |
| Chronological test accuracy | 81.83% (n=2,356, Q2 2026) |
| Legacy bot overall accuracy | 89.60% |
| Primary evaluation metric | Logistics recall and Logistics→Billing misrouting rate |

**Why overall accuracy is not the primary metric:** The legacy bot achieves 89.60% overall by correctly defaulting ~50% of routine Frontline tickets. It achieves only 72.39% Logistics recall. The AI router targets the specific misrouting failure mode, not overall accuracy maximisation.

---

## Part 4: Financial Summary

| Category | Amount | Label |
|----------|--------|-------|
| Direct routing opportunity | ₹2.5–2.9L/year | Estimated (transfer costs + SLA credits). Not guaranteed savings. |
| Proposed staffing decision value | ~₹9L/year | Cost of proposed 2 hires. Not claimed as project savings. |

---

## Part 5: Validation Methodology

1. **Ground truth:** Resolving team (not bot-assigned team, not manually labelled)
2. **No feature leakage:** Model trained on `customer_message` only; resolving team, category, agent notes, and transfer data excluded from input
3. **Two validation experiments:**
   - Random stratified split (80/20, stratified by resolving team, seed=42)
   - Chronological holdout: train on earliest 80% by date, test on Q2 2026

Chronological accuracy (81.83%) essentially matches random accuracy (81.32%), confirming no temporal overfitting.

---

## Part 6: Dashboard

An interactive six-screen executive dashboard is included in `dashboard/`. It can be run with:

```bash
cd dashboard && python -m http.server 8090
```

Open `http://localhost:8090/` in any browser. No build step required.

The dashboard presents: Executive Summary → Workload & Staffing → Routing Diagnostic → AI Intent Router (interactive) → Validation → Business Impact.

---

## Part 7: Key Limitations Declared

- Elapsed resolution time ≠ agent labor hours
- AI router is not claimed better overall (legacy bot has higher overall accuracy)
- Financial opportunity figures are estimates, not guaranteed savings
- ₹9L is the proposed hire cost, not a claimed saving from this project
- Chronological test covers Q2 2026 only; Q4 festive surge patterns may differ
