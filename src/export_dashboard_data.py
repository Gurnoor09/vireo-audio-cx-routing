"""
Generate consolidated data payload for the interactive dashboard.
"""

import os
import json
import pandas as pd
import numpy as np

OUTPUT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '../outputs'))
DASHBOARD_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '../dashboard'))

def export_dashboard_data():
    clean_path = os.path.join(OUTPUT_DIR, 'clean_tickets.csv')
    df = pd.read_csv(clean_path, low_memory=False)

    # Filter to standard 2025-2026 period for standard reporting, but retain full in analytics
    # Let's inspect monthly trends
    months = sorted(df['year_month'].unique())
    # Standard months starting 2025-01
    std_months = [m for m in months if m >= '2025-01']

    # Monthly assigned volume
    monthly_assigned = df.pivot_table(index='year_month', columns='assigned_team', values='ticket_id', aggfunc='count', fill_value=0)
    monthly_resolving = df.pivot_table(index='year_month', columns='resolving_team', values='ticket_id', aggfunc='count', fill_value=0)
    monthly_category = df.pivot_table(index='year_month', columns='category', values='ticket_id', aggfunc='count', fill_value=0)

    # Convert to chart-friendly format
    teams = ['Billing', 'Logistics', 'Chat Frontline', 'Email Frontline', 'Voice Frontline', 'Returns Desk', 'Escalations & Warranty']

    monthly_charts = {
        'months': std_months,
        'assigned_by_team': {team: [int(monthly_assigned.loc[m, team]) if m in monthly_assigned.index and team in monthly_assigned.columns else 0 for m in std_months] for team in teams},
        'resolving_by_team': {team: [int(monthly_resolving.loc[m, team]) if m in monthly_resolving.index and team in monthly_resolving.columns else 0 for m in std_months] for team in teams},
        'categories': list(monthly_category.columns),
        'category_by_month': {cat: [int(monthly_category.loc[m, cat]) if m in monthly_category.index and cat in monthly_category.columns else 0 for m in std_months] for cat in monthly_category.columns}
    }

    # Transfers Matrix
    hd = df[df['source_system'] == 'helpdesk']
    transfer_matrix = pd.crosstab(hd['assigned_team'], hd['resolving_team']).to_dict(orient='index')
    # Clean inner dicts
    transfer_matrix_clean = {k: {k2: int(v2) for k2, v2 in v.items()} for k, v in transfer_matrix.items()}

    # Resolution times and CSAT by team
    res_times = {}
    for t in teams:
        sub = df[df['resolving_team'] == t]
        res_hours = sub['resolution_time_hours'].dropna()
        csat = sub['csat_score'].dropna()
        res_times[t] = {
            'mean_res_hours': round(float(res_hours.mean()), 1) if len(res_hours) else 0,
            'median_res_hours': round(float(res_hours.median()), 1) if len(res_hours) else 0,
            'pct_gt_24h': round(float((res_hours > 24).mean() * 100), 1) if len(res_hours) else 0,
            'mean_csat': round(float(csat.mean()), 2) if len(csat) else 0,
            'total_resolved': len(sub),
            'total_assigned': int((df['assigned_team'] == t).sum())
        }

    # CSAT vs Transfers
    csat_transfers = []
    for tr in [0, 1, 2]:
        sub = hd[hd['transfers'] == tr]['csat_score'].dropna()
        csat_transfers.append({
            'transfers': tr,
            'count': int(len(sub)),
            'avg_csat': round(float(sub.mean()), 2)
        })

    # Financial Waterfall
    financial_items = [
        {'name': 'Billing Headcount Avoidance', 'amount': 900000, 'category': 'Staffing', 'type': 'saving', 'details': 'Avoid hiring 2 redundant agents for Billing'},
        {'name': 'Inter-Team Transfer Waste', 'amount': 396195, 'category': 'Operations', 'type': 'waste', 'details': '1,299 hand-offs @ Rs 305/transfer'},
        {'name': 'SLA Response Breach Credits', 'amount': 469000, 'category': 'Customer Experience', 'type': 'waste', 'details': '1,340 breached tickets @ Rs 350 auto-credit'},
        {'name': 'Double-Dipping (Refund+Repl)', 'amount': 394616, 'category': 'Policy Compliance', 'type': 'waste', 'details': '74 orders received both cash refund & replacement'},
        {'name': 'Goodwill Cap Overages', 'amount': 53428, 'category': 'Policy Compliance', 'type': 'waste', 'details': '29 refunds exceeding Rs 500 limit without approval'},
        {'name': 'Repeat Contact Handling (FCR)', 'amount': 874820, 'category': 'Efficiency', 'type': 'waste', 'details': '3,187 repeat tickets within 30-day window'}
    ]

    # Pre-defined simulator scenarios
    scenarios = [
        {
            'id': 'sc-1',
            'label': 'Payment debited, order not delivered (Pulse 2)',
            'message': 'Paid via UPI, money was deducted from my account but no order confirmation was generated and nothing has arrived. Please help!',
            'bot_category': 'Billing & Payments',
            'bot_assigned': 'Billing',
            'bot_status': 'MISROUTED',
            'ai_category': 'Order Fulfillment & Logistics',
            'ai_assigned': 'Logistics',
            'ai_status': 'OPTIMAL ROUTING',
            'explanation': 'The legacy keyword bot detected "paid/money" and dumped the ticket into Billing. However, the order was never fulfilled and requires warehouse tracking and logistics intervention. The AI router routes directly to Logistics, saving Rs 305 in transfer costs and preventing a 24h triage delay.',
            'cost_saved_inr': 305,
            'sla_risk': 'High (20.5% breach risk in Billing queue)'
        },
        {
            'id': 'sc-2',
            'label': 'GST invoice request for business purchase',
            'message': 'Bought Pulse2 on vireo.in for our office. Please regenerate the invoice with my company GSTIN: 29ABCDE1234F1Z5.',
            'bot_category': 'Billing & Payments',
            'bot_assigned': 'Billing',
            'bot_status': 'CORRECT ROUTING',
            'ai_category': 'Invoicing & Tax',
            'ai_assigned': 'Billing',
            'ai_status': 'OPTIMAL ROUTING',
            'explanation': 'Both the bot and AI correctly identify this as a pure billing and tax invoice request. Resolvable within minutes by Billing agents.',
            'cost_saved_inr': 0,
            'sla_risk': 'Low'
        },
        {
            'id': 'sc-3',
            'label': 'Return pickup completed, refund status check',
            'message': 'Returned my AirLite 10 days back. The courier picked it up from my house, but refund has still not been credited to my bank account.',
            'bot_category': 'Billing & Payments',
            'bot_assigned': 'Billing',
            'bot_status': 'MISROUTED',
            'ai_category': 'Returns & Reverse Logistics',
            'ai_assigned': 'Returns Desk',
            'ai_status': 'OPTIMAL ROUTING',
            'explanation': 'The legacy bot triggered on "refund" and misrouted to Billing. Return reverse pickups and QC refund clearances are exclusively owned by Returns Desk (Policy §6). AI router saves Rs 305 transfer overhead.',
            'cost_saved_inr': 305,
            'sla_risk': 'Medium'
        },
        {
            'id': 'sc-4',
            'label': 'Right earbud dead / audio buzz defect',
            'message': 'The right earbud of my Strata 3 has a persistent buzzing sound and stopped charging entirely after 2 weeks of use.',
            'bot_category': 'Other',
            'bot_assigned': 'Chat Frontline',
            'bot_status': 'INEFFICIENT TRIAGE',
            'ai_category': 'Hardware Fault / Warranty RMA',
            'ai_assigned': 'Escalations & Warranty',
            'ai_status': 'OPTIMAL ROUTING',
            'explanation': 'The legacy bot failed to classify and dumped this into Frontline as "Other". Because it is a hardware failure requiring Tier 2 warranty replacement certification (Policy §6), frontline agents cannot approve it and must transfer it. AI router sends directly to Tier 2.',
            'cost_saved_inr': 305,
            'sla_risk': 'High'
        },
        {
            'id': 'sc-5',
            'label': 'Courier tracking stuck for over a week',
            'message': 'Order VR902188 tracking has shown "Out for delivery" by BlueDart for 7 days now. Delivery boy is not answering.',
            'bot_category': 'Other',
            'bot_assigned': 'Chat Frontline',
            'bot_status': 'INEFFICIENT TRIAGE',
            'ai_category': 'Courier Escalation & Tracking',
            'ai_assigned': 'Logistics',
            'ai_status': 'OPTIMAL ROUTING',
            'explanation': 'Another ticket dumped into "Other" by the bot that actually belongs to Logistics delivery expediting. Direct AI routing saves re-handling time and improves CSAT.',
            'cost_saved_inr': 305,
            'sla_risk': 'High'
        }
    ]

    payload = {
        'summary': {
            'total_tickets': len(df),
            'total_customers': int(df['customer_id'].nunique()),
            'total_orders': int(df['order_id'].nunique()),
            'overall_csat': round(float(df['csat_score'].dropna().mean()), 2),
            'sla_breach_rate': round(float(df['sla_breach'].mean() * 100), 1),
            'total_financial_opportunity_inr': 3198878,
            'billing_intake_count': int((df['assigned_team'] == 'Billing').sum()),
            'billing_resolved_count': int((df['resolving_team'] == 'Billing').sum()),
            'logistics_intake_count': int((df['assigned_team'] == 'Logistics').sum()),
            'logistics_resolved_count': int((df['resolving_team'] == 'Logistics').sum())
        },
        'monthly_charts': monthly_charts,
        'res_times': res_times,
        'transfer_matrix': transfer_matrix_clean,
        'csat_transfers': csat_transfers,
        'financial_items': financial_items,
        'scenarios': scenarios
    }

    output_file = os.path.join(DASHBOARD_DIR, 'data.json')
    with open(output_file, 'w') as f:
        json.dump(payload, f, indent=2)

    print(f"Consolidated dashboard data written to {output_file}")

if __name__ == '__main__':
    export_dashboard_data()
