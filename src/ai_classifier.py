"""
Vireo Audio Support Desk - AI/NLP Intent Classifier & Smart Router
Benchmarks machine-learning based ticket routing against the flawed legacy intake bot.
"""

import os
import json
import re
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import classification_report, accuracy_score, confusion_matrix
import pickle

OUTPUT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '../outputs'))

def build_ground_truth(df):
    """
    Derive the true operational department from the resolving team and notes,
    since the assigned_team / category was bot-polluted.
    """
    df = df.copy()
    # The true resolving team is our gold standard target
    target_teams = df['resolving_team'].values
    return df['customer_message'].fillna(''), target_teams

def train_and_evaluate():
    clean_path = os.path.join(OUTPUT_DIR, 'clean_tickets.csv')
    df = pd.read_csv(clean_path, low_memory=False)

    print(f"Loaded {len(df)} tickets for NLP classification.")

    X, y = build_ground_truth(df)

    # Train / Test split
    X_train, X_test, y_train, y_test, idx_train, idx_test = train_test_split(
        X, y, df.index, test_size=0.20, random_state=42, stratify=y
    )

    # Text preprocessing & TF-IDF
    vectorizer = TfidfVectorizer(
        max_features=5000,
        ngram_range=(1, 2),
        stop_words='english',
        sublinear_tf=True
    )
    X_train_vec = vectorizer.fit_transform(X_train)
    X_test_vec = vectorizer.transform(X_test)

    # Train high-performance calibrated classifier
    clf = LogisticRegression(max_iter=1000, C=1.5, class_weight='balanced', random_state=42)
    clf.fit(X_train_vec, y_train)

    y_pred = clf.predict(X_test_vec)
    acc = accuracy_score(y_test, y_pred)
    print(f"AI Classifier Test Accuracy: {acc * 100:.2f}%")

    # Evaluate against the Legacy Bot's accuracy on the exact same test set
    legacy_bot_pred = df.loc[idx_test, 'assigned_team'].values
    legacy_acc = accuracy_score(y_test, legacy_bot_pred)
    print(f"Legacy Bot Baseline Accuracy: {legacy_acc * 100:.2f}%")

    report = classification_report(y_test, y_pred, output_dict=True)
    legacy_report = classification_report(y_test, legacy_bot_pred, output_dict=True)

    # Specifically evaluate on Billing queue test subset
    billing_test_mask = df.loc[idx_test, 'assigned_team'] == 'Billing'
    y_test_billing = y_test[billing_test_mask]
    y_pred_billing = y_pred[billing_test_mask]
    bot_pred_billing = legacy_bot_pred[billing_test_mask]

    billing_bot_accuracy = accuracy_score(y_test_billing, bot_pred_billing)
    billing_ai_accuracy = accuracy_score(y_test_billing, y_pred_billing)

    print(f"Legacy Bot Accuracy on Billing queue: {billing_bot_accuracy * 100:.2f}%")
    print(f"AI Router Accuracy on Billing queue: {billing_ai_accuracy * 100:.2f}%")

    # Save model and artifacts
    model_path = os.path.join(OUTPUT_DIR, 'smart_router_model.pkl')
    with open(model_path, 'wb') as f:
        pickle.dump({'vectorizer': vectorizer, 'classifier': clf}, f)

    # Extract top keywords per department for transparency
    feature_names = vectorizer.get_feature_names_out()
    top_keywords_per_team = {}
    for i, class_label in enumerate(clf.classes_):
        top_indices = np.argsort(clf.coef_[i])[-10:][::-1]
        top_keywords_per_team[class_label] = [feature_names[j] for j in top_indices]

    results_payload = {
        'ai_accuracy_pct': round(acc * 100, 2),
        'legacy_bot_accuracy_pct': round(legacy_acc * 100, 2),
        'accuracy_gain_pct': round((acc - legacy_acc) * 100, 2),
        'billing_queue_bot_accuracy_pct': round(billing_bot_accuracy * 100, 2),
        'billing_queue_ai_accuracy_pct': round(billing_ai_accuracy * 100, 2),
        'misrouting_reduction_in_billing_pct': round((1 - billing_bot_accuracy - (1 - billing_ai_accuracy)) * 100, 2),
        'top_keywords': top_keywords_per_team,
        'classification_report_ai': report,
        'classification_report_legacy': legacy_report
    }

    results_json = os.path.join(OUTPUT_DIR, 'ai_classifier_results.json')
    with open(results_json, 'w') as f:
        json.dump(results_payload, f, indent=2)

    print(f"AI classifier benchmark saved to {results_json}")

    # Create lightweight inference export for JavaScript browser simulator
    export_for_web_simulator(vectorizer, clf, top_keywords_per_team)

def export_for_web_simulator(vectorizer, clf, top_keywords):
    """
    Exports a lightweight rule & keyword dictionary for client-side JavaScript execution in the dashboard.
    """
    web_config = {
        'teams': list(clf.classes_),
        'top_keywords': top_keywords,
        'sample_scenarios': [
            {
                'text': 'paid via upi, amount deducted, no order confirmation for pulse 2',
                'bot_category': 'Billing & Payments',
                'bot_team': 'Billing',
                'ai_category': 'Order Creation / Logistics',
                'ai_team': 'Logistics',
                'verdict': 'Misrouted by bot due to keyword "paid/upi". Actually an unfulfilled order creation issue.'
            },
            {
                'text': 'Dear team, Got Pulse2 from Amazon recently. My order has not been delivered yet. Can someone fix this?',
                'bot_category': 'Billing & Payments',
                'bot_team': 'Billing',
                'ai_category': 'Delivery & Shipping',
                'ai_team': 'Logistics',
                'verdict': 'Bot triggered on "paid/order". Pure delivery delay. Belonged directly to Logistics.'
            },
            {
                'text': 'Hi, bought Pulse2 on vireo.in. Please share invoice with GST number for my company.',
                'bot_category': 'Billing & Payments',
                'bot_team': 'Billing',
                'ai_category': 'Billing & Invoicing',
                'ai_team': 'Billing',
                'verdict': 'Legitimate Billing request. Correctly routed.'
            },
            {
                'text': 'Still waiting for my refund on returned AirLite. Pickup was done 10 days ago.',
                'bot_category': 'Billing & Payments',
                'bot_team': 'Billing',
                'ai_category': 'Returns & Refunds',
                'ai_team': 'Returns Desk',
                'verdict': 'Bot triggered on "refund". Return pickup & QC refund belongs to Returns Desk.'
            },
            {
                'text': 'Right earbud has constant buzzing static noise and disconnects after 5 minutes.',
                'bot_category': 'Connectivity',
                'bot_team': 'Chat Frontline',
                'ai_category': 'Audio Quality / Hardware Defect',
                'ai_team': 'Escalations & Warranty',
                'verdict': 'Persistent hardware flaw requiring Tier 2 RMA inspection.'
            }
        ]
    }
    web_json_path = os.path.join(OUTPUT_DIR, 'web_simulator_config.json')
    with open(web_json_path, 'w') as f:
        json.dump(web_config, f, indent=2)
    print(f"Web simulator config saved to {web_json_path}")

if __name__ == '__main__':
    train_and_evaluate()
