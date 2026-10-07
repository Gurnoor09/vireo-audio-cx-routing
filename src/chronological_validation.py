"""
Chronological Validation Experiment: 5-Class Functional AI Ticket Router
Testing temporal generalization (train on past, test on future).
"""

import pandas as pd
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import classification_report, confusion_matrix, accuracy_score

import os

OUTPUT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '../outputs'))
df = pd.read_csv(os.path.join(OUTPUT_DIR, 'clean_tickets.csv'), low_memory=False)


# 1. Functional department target mapping (5 classes)
def map_functional(team):
    if 'Frontline' in str(team):
        return 'Frontline'
    return team

df['functional_dept'] = df['resolving_team'].apply(map_functional)
df['bot_functional'] = df['assigned_team'].apply(map_functional)

# Sort strictly chronologically by created_dt
df['created_dt'] = pd.to_datetime(df['created_at'])
df_sorted = df.sort_values('created_dt').reset_index(drop=True)

# 80/20 Chronological Split (Identical split ratio to the random split: 9,424 train, 2,356 test)
split_idx = int(len(df_sorted) * 0.80)

train_df = df_sorted.iloc[:split_idx].copy()
test_df = df_sorted.iloc[split_idx:].copy()

print(f"Total dataset: {len(df_sorted)} tickets")
print(f"Train tickets: {len(train_df)} ({len(train_df)/len(df_sorted):.1%})")
print(f"Test tickets:  {len(test_df)} ({len(test_df)/len(df_sorted):.1%})")

print("\n--- 1. DATE RANGES ---")
print(f"Train Date Range: {train_df['created_dt'].min()} to {train_df['created_dt'].max()}")
print(f"Test Date Range:  {test_df['created_dt'].min()} to {test_df['created_dt'].max()}")

# 2. Vectorization & Training
X_train = train_df['customer_message'].fillna('')
y_train = train_df['functional_dept']

X_test = test_df['customer_message'].fillna('')
y_test = test_df['functional_dept']

vec = TfidfVectorizer(max_features=5000, ngram_range=(1, 2), stop_words='english')
X_train_vec = vec.fit_transform(X_train)
X_test_vec = vec.transform(X_test)

clf = LogisticRegression(max_iter=1000, random_state=42)
clf.fit(X_train_vec, y_train)

y_pred = clf.predict(X_test_vec)
bot_pred = test_df['bot_functional'].values

# 3. Overall Accuracy
ai_acc = accuracy_score(y_test, y_pred)
bot_acc = accuracy_score(y_test, bot_pred)

print(f"\n--- 2. OVERALL ACCURACY ---")
print(f"AI Router Chronological Test Accuracy:   {ai_acc * 100:.2f}%")
print(f"Legacy Bot Chronological Test Accuracy: {bot_acc * 100:.2f}%")

# 4. Classification Report
classes = sorted(list(clf.classes_))
print("\n--- 3. CLASSIFICATION REPORT (AI ROUTER) ---")
print(classification_report(y_test, y_pred, labels=classes, digits=4))

print("\n--- CLASSIFICATION REPORT (LEGACY BOT) ---")
print(classification_report(y_test, bot_pred, labels=classes, digits=4))

# 5. Confusion Matrices
cm_ai = pd.DataFrame(
    confusion_matrix(y_test, y_pred, labels=classes),
    index=[f"True_{c}" for c in classes],
    columns=[f"Pred_{c}" for c in classes]
)
print("\n--- 4. CONFUSION MATRIX (AI ROUTER) ---")
print(cm_ai.to_string())

cm_bot = pd.DataFrame(
    confusion_matrix(y_test, bot_pred, labels=classes),
    index=[f"True_{c}" for c in classes],
    columns=[f"Pred_{c}" for c in classes]
)
print("\n--- CONFUSION MATRIX (LEGACY BOT) ---")
print(cm_bot.to_string())

# 6. Specific Logistics Metrics
true_logistics_mask = (y_test == 'Logistics')
total_true_logistics = true_logistics_mask.sum()

bot_log_to_billing = (bot_pred[true_logistics_mask] == 'Billing').sum()
ai_log_to_billing = (y_pred[true_logistics_mask] == 'Billing').sum()

bot_log_correct = (bot_pred[true_logistics_mask] == 'Logistics').sum()
ai_log_correct = (y_pred[true_logistics_mask] == 'Logistics').sum()

bot_log_recall = bot_log_correct / total_true_logistics
ai_log_recall = ai_log_correct / total_true_logistics

print("\n--- 5. LOGISTICS WORKLOAD SPECIFICS ---")
print(f"Total True Logistics tickets in test set: {total_true_logistics}")
print(f"Legacy Bot: Sent to Billing = {bot_log_to_billing} ({bot_log_to_billing/total_true_logistics:.1%})")
print(f"AI Router:  Sent to Billing = {ai_log_to_billing} ({ai_log_to_billing/total_true_logistics:.1%})")
print(f"Legacy Bot Logistics Recall: {bot_log_recall * 100:.2f}% ({bot_log_correct}/{total_true_logistics})")
print(f"AI Router Logistics Recall:  {ai_log_recall * 100:.2f}% ({ai_log_correct}/{total_true_logistics})")

# 7. Billing Queue Specifics
bot_assigned_billing_mask = (test_df['assigned_team'] == 'Billing')
total_bot_billing = bot_assigned_billing_mask.sum()
billing_test_true = y_test[bot_assigned_billing_mask]
billing_test_ai_pred = y_pred[bot_assigned_billing_mask]
billing_test_bot_pred = bot_pred[bot_assigned_billing_mask]

print("\n--- 6. BILLING INTAKE QUEUE BREAKDOWN (TEST SET) ---")
print(f"Total tickets assigned to Billing by bot in test set: {total_bot_billing}")
print(f"Actually belonging to Billing: {(billing_test_true == 'Billing').sum()} ({(billing_test_true == 'Billing').mean():.1%})")
print(f"Actually belonging to Logistics: {(billing_test_true == 'Logistics').sum()} ({(billing_test_true == 'Logistics').mean():.1%})")
print(f"Legacy Bot accuracy on Billing queue: {accuracy_score(billing_test_true, billing_test_bot_pred)*100:.2f}%")
print(f"AI Router accuracy on Billing queue:  {accuracy_score(billing_test_true, billing_test_ai_pred)*100:.2f}%")
