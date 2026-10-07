"""
Vireo Audio Support Desk - Data Cleaning and Standardization Pipeline
"""

import os
import pandas as pd
import numpy as np

DATA_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '../data'))
OUTPUT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '../outputs'))

def load_raw_data():
    tickets = pd.read_csv(os.path.join(DATA_DIR, 'tickets.csv'), low_memory=False)
    agents = pd.read_csv(os.path.join(DATA_DIR, 'agents.csv'))
    customers = pd.read_csv(os.path.join(DATA_DIR, 'customers.csv'))
    orders = pd.read_csv(os.path.join(DATA_DIR, 'orders.csv'))
    products = pd.read_csv(os.path.join(DATA_DIR, 'products.csv'))
    return tickets, agents, customers, orders, products

def clean_and_transform():
    tickets, agents, customers, orders, products = load_raw_data()
    print(f"Loaded {len(tickets)} raw tickets.")

    # 1. Parse timestamps
    tickets['created_dt'] = pd.to_datetime(tickets['created_at'])
    tickets['first_response_dt'] = pd.to_datetime(tickets['first_response_at'])
    tickets['resolved_dt_raw'] = pd.to_datetime(tickets['resolved_at'])

    # 2. Fix UTC offset for legacy_fd resolved_at (+5 hours 30 mins)
    tickets['resolved_dt'] = tickets['resolved_dt_raw'].copy()
    is_legacy = tickets['source_system'] == 'legacy_fd'
    tickets.loc[is_legacy, 'resolved_dt'] = tickets.loc[is_legacy, 'resolved_dt_raw'] + pd.Timedelta(hours=5, minutes=30)

    # 3. Calculate Durations
    tickets['first_response_mins'] = (tickets['first_response_dt'] - tickets['created_dt']).dt.total_seconds() / 60.0
    tickets['handle_time_hours'] = (tickets['resolved_dt'] - tickets['first_response_dt']).dt.total_seconds() / 3600.0
    tickets['resolution_time_hours'] = (tickets['resolved_dt'] - tickets['created_dt']).dt.total_seconds() / 3600.0

    # 4. Map SLA targets and compute breach flags
    # Targets: Chat 15 min, Voice 120 min, Social 240 min, Email 480 min
    sla_thresholds = {'chat': 15, 'voice': 120, 'social': 240, 'email': 480}
    tickets['sla_target_mins'] = tickets['channel'].map(sla_thresholds)
    tickets['sla_breach'] = tickets['first_response_mins'] > tickets['sla_target_mins']
    # SLA credit is Rs 350 per breached ticket on resolution
    tickets['sla_credit_inr'] = np.where(tickets['sla_breach'] & tickets['status'].isin(['resolved', 'closed']), 350, 0)

    # 5. Join Agent Dimension
    # Use agent_id (not name, to prevent collision with 'Om Sharma')
    agent_info = agents[['agent_id', 'name', 'site', 'team', 'shift', 'tier']].rename(columns={
        'name': 'agent_name',
        'team': 'resolving_team',
        'site': 'agent_site',
        'shift': 'agent_shift',
        'tier': 'agent_tier'
    })
    tickets = tickets.merge(agent_info, on='agent_id', how='left')

    # 6. Flag Misrouted Tickets
    # Misrouted = assigned_team != resolving_team
    tickets['is_misrouted'] = tickets['assigned_team'] != tickets['resolving_team']

    # 7. Channel Contact Cost & Transfer Cost
    # Contact costs: chat 210, email 260, voice 520, social 240
    channel_cost_map = {'chat': 210, 'email': 260, 'voice': 520, 'social': 240}
    tickets['contact_cost_inr'] = tickets['channel'].map(channel_cost_map)
    # Transfer cost: Rs 305 per transfer (re-handling and administration)
    tickets['transfer_cost_inr'] = tickets['transfers'].fillna(0) * 305

    # 8. Fallback Order Join for missing order_id
    missing_order_mask = tickets['order_id'].isna()
    cust_sku_order_map = orders.drop_duplicates(subset=['customer_id', 'sku'])[['customer_id', 'sku', 'order_id', 'order_value_inr', 'lot_code']]
    
    # Merge order details
    tickets = tickets.merge(
        orders[['order_id', 'order_value_inr', 'lot_code', 'order_date']].drop_duplicates(subset=['order_id']),
        on='order_id',
        how='left'
    )

    # Apply fallback
    fallback_merge = tickets[missing_order_mask][['ticket_id', 'customer_id', 'product_sku']].merge(
        cust_sku_order_map,
        left_on=['customer_id', 'product_sku'],
        right_on=['customer_id', 'sku'],
        how='left'
    )
    fallback_map = fallback_merge.set_index('ticket_id')
    
    tickets.loc[missing_order_mask, 'order_id'] = tickets.loc[missing_order_mask, 'ticket_id'].map(fallback_map['order_id'])
    tickets.loc[missing_order_mask, 'order_value_inr'] = tickets.loc[missing_order_mask, 'ticket_id'].map(fallback_map['order_value_inr'])
    tickets.loc[missing_order_mask, 'lot_code'] = tickets.loc[missing_order_mask, 'ticket_id'].map(fallback_map['lot_code'])

    # 9. Join Product Dimension
    tickets = tickets.merge(
        products[['sku', 'product_name', 'family', 'unit_cost_inr', 'retail_price_inr', 'warranty_months']],
        left_on='product_sku',
        right_on='sku',
        how='left'
    )

    # 10. Flag Double Dipping (Refund + Replacement on same order)
    order_refund_totals = tickets.groupby('order_id')['refund_amount_inr'].sum()
    order_has_repl = tickets.groupby('order_id')['replacement_issued'].apply(lambda s: (s == 'Y').any())
    double_dipped_orders = set(order_refund_totals[(order_refund_totals > 0) & order_has_repl].index)
    tickets['is_double_dipped_order'] = tickets['order_id'].isin(double_dipped_orders)

    # 11. Repeat Contact (FCR calculation within 30-day window)
    tickets = tickets.sort_values(['customer_id', 'created_dt']).reset_index(drop=True)
    is_repeat_contact = np.zeros(len(tickets), dtype=bool)

    # Group by customer and check 30-day resolution window
    for cid, group in tickets.groupby('customer_id'):
        prev_res_times = []
        for idx in group.index:
            c_time = tickets.at[idx, 'created_dt']
            # Check if customer contacted within 30 days of any prior resolution
            for prt in prev_res_times:
                if 0 < (c_time - prt).total_seconds() <= 30 * 86400:
                    is_repeat_contact[idx] = True
                    break
            res_time = tickets.at[idx, 'resolved_dt']
            if pd.notna(res_time):
                prev_res_times.append(res_time)

    tickets['is_repeat_contact'] = is_repeat_contact
    tickets['repeat_cost_inr'] = np.where(tickets['is_repeat_contact'], tickets['contact_cost_inr'], 0)

    # 12. Month period for aggregations
    tickets['year_month'] = tickets['created_dt'].dt.to_period('M').astype(str)

    # Save cleaned tickets
    output_path = os.path.join(OUTPUT_DIR, 'clean_tickets.csv')
    tickets.to_csv(output_path, index=False)
    print(f"Cleaned dataset saved successfully to {output_path} ({len(tickets)} rows).")

    return tickets

if __name__ == '__main__':
    clean_and_transform()
