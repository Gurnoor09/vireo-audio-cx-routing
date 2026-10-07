# Methodology Notes

## 1. Data Pipeline

### Source Files
Five CSV tables (tickets, agents, customers, orders, products) and a PDF support policy were provided as the raw dataset.

### Timezone Correction
Tickets from the legacy helpdesk system (`source_system = 'legacy_fd'`) had a systematic UTC/IST offset: `resolved_at` was stored in UTC while `created_at` was in IST. A +5h 30m offset was applied to `resolved_at` for all legacy tickets. This correction reduced negative handle-time values from 2,575 to 0.

### Handle Time vs. Resolution Time
- **`resolution_time_hours`**: Elapsed calendar time from `created_at` to `resolved_at`. This is the metric used for all reported resolution durations.
- **`handle_time_hours`**: Time from `first_response_at` to `resolved_at`. Not used in the primary analysis because it does not capture pre-first-response waiting time.
- **Important:** Neither metric represents active agent keyboard time. Logistics resolution times (median 26.1h) reflect external courier latency (BlueDart/Delhivery NDR cycles) and warehouse confirmation delays.

### Agent Joins
All agent lookups use `agent_id` (not display name) to prevent data merging errors caused by two agents sharing the name "Om Sharma" (A3006: Chat Frontline, Indore; A3033: Logistics, Bengaluru).

### Missing Order IDs
3,091 tickets (26.2%) had no `order_id`. A fallback join was executed using `customer_id + product_sku` against the orders table to recover order context where possible.

### CSAT Averaging
6,435 tickets (54.6%) had no CSAT response. Per Vireo Support Policy §8: *"Non-responses are excluded from averages."* All CSAT figures exclude nulls.

---

## 2. Defining "Resolved By"

The **resolving team** is determined by the `agent_id` on the ticket, joined to the agents roster to retrieve the agent's team. This is the team that performed the final resolution action — independent of which team the bot assigned the ticket to at intake.

A ticket is classified as **misrouted** when `assigned_team ≠ resolving_team`.

---

## 3. Workload Accounting

All workload figures (tickets per agent, per-team volumes) use **resolved ticket counts** — not intake/assigned counts. Intake counts reflect bot assignment decisions and are not a valid proxy for actual agent effort.

Agent counts per team are sourced from the agents roster, not inferred from ticket data.

---

## 4. AI Classifier Methodology

### Ground Truth Labels
The model is trained to predict the **resolving team** (not the bot-assigned team, not any manually labelled field). The resolving team is the operationally correct department for each ticket, as evidenced by which agent ultimately resolved it.

### Train / Test Split (Random)
- 80% training / 20% test
- Stratified by resolving team to preserve class proportions
- `random_state=42` for reproducibility

### Feature Engineering
- Single input feature: raw `customer_message` text
- No resolving team, assigned team, category, transfer history, agent notes, or any target-correlated field is used as input
- TF-IDF vectorisation: 5,000 max features, unigrams + bigrams, English stop words removed, sublinear TF scaling

### Model
Logistic Regression (`C=1.5`, `max_iter=1000`, `class_weight='balanced'`, `random_state=42`). Class weights are balanced to prevent the dominant Frontline class from suppressing minority class performance.

### Chronological Validation
To test temporal generalization, a separate experiment was run with a strict chronological split:
- Training: earliest 80% of tickets by `created_at` (Jan 2025 – approx. early April 2026)
- Test: most recent 20% (Q2 2026, April–June 2026, n=2,356)
- No data leakage: the vectorizer is fit only on training messages

The near-identical accuracy between random (81.32%) and chronological (81.83%) splits confirms the model is not overfit to the temporal ordering of the dataset.

### Why Overall Accuracy Is Not the Primary Metric
The class distribution is heavily skewed toward Frontline (chat + email + voice combined ~50% of tickets). The legacy bot achieves 89.60% overall accuracy largely by correctly defaulting Frontline tickets. However, it achieves only 72.39% recall on Logistics — misrouting 24.3% of true Logistics tickets into Billing. The AI router sacrifices some overall accuracy on Frontline edge cases to achieve 86.30% Logistics recall and reduce Logistics→Billing misrouting by 94.1%.

---

## 5. Financial Estimates

All financial figures are estimates derived from policy-documented cost rates applied to empirically observed event counts. They represent **addressable opportunity**, not guaranteed savings.

| Rate | Source | Value |
|------|--------|-------|
| Inter-team transfer cost | Vireo Support Policy §4 | ₹305 per transfer |
| SLA breach store credit | Vireo Support Policy §3 | ₹350 per breached resolved ticket |
| First-response SLA targets | Policy §3 | Chat: 15 min · Voice: 120 min · Social: 240 min · Email: 480 min |
| Proposed hire cost | Assessment context (Arjun quote) | ₹165/hr × 8h × 250 days = ₹3,30,000/agent/year |

**Direct routing opportunity (₹2.5–2.9L/year):**
- Transfer cost reduction: 632 Billing-originating transfers at ₹305 = ₹1,92,760; assumes ~80% addressable post-routing fix → ₹1.5–1.9L/yr
- SLA breach credit reduction: 525 Billing-queue SLA breaches × ₹350 = ₹1,83,750; assumes ~55% attributable to triage lag → ~₹1.0L/yr

**Proposed staffing decision value (~₹9L/year):**
- 2 agents × ₹3,30,000/agent/year ≈ ₹6.6L direct; fully loaded ~₹9L
- This is the cost of the proposed hires, **not** a saving claimed from this project

---

## 6. Assumptions and Limitations

| Assumption | Impact if Wrong |
|------------|----------------|
| Resolving team = correct operational owner | If agents from one team routinely pick up and resolve misrouted tickets in another team's queue, the resolving team metric would overstate cross-team displacement |
| 80% of Billing-originating transfers are avoidable post-routing fix | Financial estimate is directional; actual savings depend on deployment quality |
| Legacy bot keyword matching is stable | If bot behaviour has changed since the dataset period, the misrouting baseline may not reflect current state |
| CSAT non-response is random (not systematically biased) | If unhappy customers are more or less likely to respond, CSAT averages are biased |
| Resolution time reflects case duration not agent effort | If Logistics agents are genuinely working longer hours (not just waiting for courier updates), the workload story is even more severe |

---

## 7. What This Analysis Does NOT Claim

- The AI router is **not** claimed to be better than the legacy bot overall. The legacy bot has higher overall accuracy.
- The AI router does **not** eliminate all misrouting. 7 Logistics tickets were still sent to Billing in the Q2 2026 chronological test.
- ₹32L is **not** presented as total realised savings. The larger financial opportunity figures (repeat contacts, double-dipping) are separate audit findings, not routing-fix benefits.
- The analysis does **not** conclude Vireo needs zero new hires. It concludes that headcount decisions should be made from clean post-routing baselines.
