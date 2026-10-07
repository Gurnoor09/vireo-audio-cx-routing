# Data Directory

## ⚠️ Raw Data Not Included

The raw assessment datasets were supplied **privately by Vireo Audio** as part of a take-home assessment. They contain customer contact information and are **intentionally excluded** from this public repository.

Do not commit any of these files to version control.

---

## Required Files

To reproduce the full analysis, place the following files directly in this `data/` directory:

| Filename | Description |
|----------|-------------|
| `tickets.csv` | 11,780 support tickets (Jan 2025 – Jun 2026) |
| `agents.csv` | 44-agent roster with team, site, shift, and tier |
| `customers.csv` | Customer dimension table |
| `orders.csv` | Order-level data including value and lot codes |
| `products.csv` | 14-SKU product catalogue with pricing and warranty |
| `support-policy.pdf` | Vireo Audio Support Policy v3.2 (SLA targets, cost rates, policy rules) |
| `email-thread.txt` | Stakeholder email thread (business context) |

Once these files are in place, follow the reproduction steps in the main [README.md](../README.md).

---

## Key Data Notes

- **Timezone offset:** `legacy_fd` source tickets have a `resolved_at` timestamp in UTC while `created_at` is in IST. The pipeline adds +5h30m to `resolved_at` for legacy tickets to correct handle/resolution durations.
- **Agent name collision:** Two agents share the display name "Om Sharma" (agent IDs A3006 and A3033). All joins use `agent_id`, never name strings.
- **Missing order IDs:** 3,091 tickets (26.2%) lack `order_id`. The pipeline performs a fallback join via `customer_id` + `product_sku` against `orders.csv`.
- **CSAT non-response:** 54.6% of tickets have no CSAT score. Nulls are excluded from all averages per Vireo Support Policy §8.

---

## Data Schema Reference

### tickets.csv (key columns)

| Column | Type | Notes |
|--------|------|-------|
| `ticket_id` | string | Primary key |
| `created_at` | datetime (IST) | |
| `first_response_at` | datetime (IST) | |
| `resolved_at` | datetime (UTC for legacy_fd) | See timezone note above |
| `status` | string | resolved / closed / open |
| `channel` | string | chat / email / voice / social |
| `customer_id` | string | FK → customers.csv |
| `order_id` | string | FK → orders.csv (nullable) |
| `product_sku` | string | FK → products.csv |
| `category` | string | Bot-assigned intake category (11 values) |
| `assigned_team` | string | Bot-assigned team at intake |
| `agent_id` | string | FK → agents.csv (resolving agent) |
| `transfers` | int | Recorded inter-team transfers |
| `csat_score` | float | 1–5, nullable |
| `refund_amount_inr` | float | |
| `replacement_issued` | string | Y / N |
| `customer_message` | string | Raw customer opening message |
| `agent_notes` | string | Closing resolution notes |
| `source_system` | string | helpdesk_v2 / legacy_fd |
