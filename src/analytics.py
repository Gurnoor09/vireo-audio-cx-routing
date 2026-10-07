"""
Vireo Audio Support Desk - Core Analytics & Financial Modeling Engine
"""

import os
import json
import pandas as pd
import numpy as np

OUTPUT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '../outputs'))

def run_analytics():
    clean_path = os.path.join(OUTPUT_DIR, 'clean_tickets.csv')
    df = pd.read_csv(clean_path, low_memory=False)

    print(f"Loaded {len(df)} cleaned tickets for analytics.")

    # 1. Monthly Volume by Category (Priya's requested view)
    monthly_category = df.pivot_table(
        index='year_month',
        columns='category',
        values='ticket_id',
        aggfunc='count',
        fill_value=0
    )
    monthly_category.to_csv(os.path.join(OUTPUT_DIR, 'monthly_by_category.csv'))

    # 2. Monthly Volume by Assigned Team (Priya's requested view)
    monthly_assigned = df.pivot_table(
        index='year_month',
        columns='assigned_team',
        values='ticket_id',
        aggfunc='count',
        fill_value=0
    )
    monthly_assigned.to_csv(os.path.join(OUTPUT_DIR, 'monthly_by_assigned_team.csv'))

    # 3. Monthly Volume by Resolving Team (The TRUE Operational View)
    monthly_resolving = df.pivot_table(
        index='year_month',
        columns='resolving_team',
        values='ticket_id',
        aggfunc='count',
        fill_value=0
    )
    monthly_resolving.to_csv(os.path.join(OUTPUT_DIR, 'monthly_by_resolving_team.csv'))

    # 4. Misrouting Matrix (Assigned vs Resolving Team)
    misrouting_ct = pd.crosstab(df['assigned_team'], df['resolving_team'], margins=True)
    misrouting_ct.to_csv(os.path.join(OUTPUT_DIR, 'misrouting_crosstab.csv'))

    # Misrouting rates per assigned team
    misrouting_stats = {}
    for team, grp in df.groupby('assigned_team'):
        total = len(grp)
        misrouted = (grp['assigned_team'] != grp['resolving_team']).sum()
        misrouting_stats[team] = {
            'total_intake': int(total),
            'misrouted_count': int(misrouted),
            'misrouting_rate_pct': round((misrouted / total) * 100, 2),
            'resolved_by_own_team': int((grp['assigned_team'] == grp['resolving_team']).sum()),
            'top_destinations': grp[grp['assigned_team'] != grp['resolving_team']]['resolving_team'].value_counts().to_dict()
        }

    # 5. Team Capacity & Workload Comparison
    team_workload = {}
    agents_count_map = {
        'Chat Frontline': 15,
        'Email Frontline': 7,
        'Escalations & Warranty': 6,
        'Logistics': 5,
        'Voice Frontline': 4,
        'Billing': 4,
        'Returns Desk': 3
    }

    for team in agents_count_map.keys():
        assigned_count = int((df['assigned_team'] == team).sum())
        resolved_count = int((df['resolving_team'] == team).sum())
        num_agents = agents_count_map.get(team, 0)
        
        # Subsets for resolution times
        res_subset = df[df['resolving_team'] == team]['resolution_time_hours'].dropna()
        csat_subset = df[df['resolving_team'] == team]['csat_score'].dropna()
        
        team_workload[team] = {
            'agent_count': num_agents,
            'assigned_intake': assigned_count,
            'resolved_workload': resolved_count,
            'resolved_per_agent': round(resolved_count / num_agents, 1) if num_agents else 0,
            'net_workload_vs_assigned': resolved_count - assigned_count,
            'mean_resolution_hours': round(float(res_subset.mean()), 2) if len(res_subset) else 0,
            'median_resolution_hours': round(float(res_subset.median()), 2) if len(res_subset) else 0,
            'pct_over_24h': round(float((res_subset > 24).mean() * 100), 2) if len(res_subset) else 0,
            'csat_mean': round(float(csat_subset.mean()), 2) if len(csat_subset) else 0,
            'csat_count': int(len(csat_subset))
        }

    # 6. Transfers Analysis
    helpdesk_df = df[df['source_system'] == 'helpdesk']
    total_transfers = int(helpdesk_df['transfers'].sum())
    transfer_cost_total = total_transfers * 305
    transfers_by_assigned = helpdesk_df.groupby('assigned_team')['transfers'].agg(['count', 'sum', 'mean']).to_dict(orient='index')
    
    # CSAT by transfers
    csat_by_transfers = helpdesk_df.groupby('transfers')['csat_score'].agg(['count', 'mean']).dropna().to_dict(orient='index')

    # 7. SLA Breaches & Credits
    sla_total_breaches = int(df['sla_breach'].sum())
    sla_breach_rate = round(float(df['sla_breach'].mean() * 100), 2)
    sla_credits_total = sla_total_breaches * 350
    
    sla_by_channel = df.groupby('channel').agg(
        total=('ticket_id', 'count'),
        breaches=('sla_breach', 'sum'),
        breach_rate=('sla_breach', lambda s: round(float(s.mean() * 100), 2)),
        credits_inr=('sla_credit_inr', 'sum')
    ).to_dict(orient='index')

    sla_by_assigned = df.groupby('assigned_team').agg(
        total=('ticket_id', 'count'),
        breaches=('sla_breach', 'sum'),
        breach_rate=('sla_breach', lambda s: round(float(s.mean() * 100), 2)),
        credits_inr=('sla_credit_inr', 'sum')
    ).to_dict(orient='index')

    # 8. Double-Dipping Audit
    double_dipped_tickets = df[df['is_double_dipped_order']]
    unique_dd_orders = double_dipped_tickets.drop_duplicates(subset=['order_id'])
    dd_order_count = int(len(unique_dd_orders))
    dd_refund_total = float(unique_dd_orders['refund_amount_inr'].sum())
    dd_replacement_cost = float((unique_dd_orders['unit_cost_inr'] + 340).sum())
    dd_total_loss = dd_refund_total + dd_replacement_cost

    # 9. Goodwill Overages Audit
    gw_tickets = df[df['refund_reason_code'] == 'GW-OTHER']
    gw_overages = gw_tickets[gw_tickets['refund_amount_inr'] > 500]
    gw_overage_count = int(len(gw_overages))
    gw_overage_loss = float((gw_overages['refund_amount_inr'] - 500).sum())

    # 10. Repeat Contacts (FCR)
    repeat_total_count = int(df['is_repeat_contact'].sum())
    repeat_total_cost = float(df['repeat_cost_inr'].sum())
    repeat_rate = round(float(df['is_repeat_contact'].mean() * 100), 2)

    # 11. Consolidated Financial Leakage Summary
    financial_summary = {
        'misallocated_billing_hires': {
            'description': 'Cost of hiring 2 unnecessary agents for Billing',
            'amount_inr': 900000,
            'source': 'Arjun Mehta quote & Policy §4 (2 hires @ Rs 4.5L/yr)'
        },
        'internal_transfer_waste': {
            'description': 'Internal hand-offs across teams (helpdesk period)',
            'amount_inr': transfer_cost_total,
            'count': total_transfers,
            'unit_cost': 305
        },
        'sla_breach_credits': {
            'description': 'Store credits automatically paid out for response breaches',
            'amount_inr': sla_credits_total,
            'count': sla_total_breaches,
            'unit_credit': 350
        },
        'double_dipping_violations': {
            'description': 'Prohibited orders receiving both refund and replacement',
            'amount_inr': dd_total_loss,
            'orders_count': dd_order_count,
            'refunds_paid': dd_refund_total,
            'replacement_cost': dd_replacement_cost
        },
        'goodwill_cap_overages': {
            'description': 'Unapproved refunds exceeding Rs 500 goodwill limit',
            'amount_inr': gw_overage_loss,
            'count': gw_overage_count
        },
        'repeat_contact_costs': {
            'description': 'Handling costs for return contacts within 30 days of resolution',
            'amount_inr': repeat_total_cost,
            'count': repeat_total_count
        },
        'total_addressable_leakage_inr': round(
            900000 + transfer_cost_total + sla_credits_total + dd_total_loss + gw_overage_loss + repeat_total_cost, 2
        )
    }

    # Compile comprehensive analytics payload
    analytics_payload = {
        'total_tickets': len(df),
        'team_workload': team_workload,
        'misrouting_stats': misrouting_stats,
        'transfers': {
            'total_transfers_recorded': total_transfers,
            'transfer_cost_total_inr': transfer_cost_total,
            'by_assigned_team': transfers_by_assigned,
            'csat_by_transfers': csat_by_transfers
        },
        'sla_performance': {
            'total_breaches': sla_total_breaches,
            'breach_rate_pct': sla_breach_rate,
            'total_credits_inr': sla_credits_total,
            'by_channel': sla_by_channel,
            'by_assigned_team': sla_by_assigned
        },
        'policy_violations': {
            'double_dipped_orders': dd_order_count,
            'double_dipped_total_waste_inr': dd_total_loss,
            'goodwill_overage_count': gw_overage_count,
            'goodwill_overage_waste_inr': gw_overage_loss
        },
        'fcr_repeat_contacts': {
            'repeat_count': repeat_total_count,
            'repeat_rate_pct': repeat_rate,
            'repeat_cost_total_inr': repeat_total_cost
        },
        'financial_summary': financial_summary
    }

    # Save to JSON
    json_path = os.path.join(OUTPUT_DIR, 'analytics_summary.json')
    with open(json_path, 'w') as f:
        json.dump(analytics_payload, f, indent=2)

    print(f"Analytics successfully computed and exported to {json_path}")
    print(f"Total Quantifiable Financial Leakage: Rs {financial_summary['total_addressable_leakage_inr']:,}")

if __name__ == '__main__':
    run_analytics()
