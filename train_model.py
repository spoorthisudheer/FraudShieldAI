"""
FraudShieldAI - Machine Learning Model Training & Evaluation Engine
Developed for IBM Z Datathon 2026 (IBM LinuxONE s390x Architecture)
"""

import os
import sys
import numpy as np
import pandas as pd
import joblib
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report, confusion_matrix, roc_auc_score


def generate_synthetic_transactions(n_samples: int = 5000, random_state: int = 42) -> pd.DataFrame:
    """
    Generate realistic, synthetic banking transaction data with typical fraud patterns.
    Complies with data privacy regulations: zero PII or real banking credentials used.
    """
    np.random.seed(random_state)
    
    # 1. Base genuine transactions (~93%) and fraudulent transactions (~7%)
    n_fraud = int(n_samples * 0.07)
    n_genuine = n_samples - n_fraud

    # --- Genuine Transactions Simulation ---
    amounts_genuine = np.random.lognormal(mean=3.7, sigma=0.8, size=n_genuine)
    amounts_genuine = np.clip(amounts_genuine, 2.0, 1500.0)
    
    p_hours_gen = np.array([
        0.01, 0.01, 0.01, 0.01, 0.01, 0.02, 0.04, 0.06, 0.07, 0.07, 0.07, 0.07,
        0.07, 0.07, 0.07, 0.07, 0.06, 0.05, 0.05, 0.04, 0.03, 0.02, 0.01, 0.01
    ])
    p_hours_gen = p_hours_gen / p_hours_gen.sum()
    hours_genuine = np.random.choice(range(24), size=n_genuine, p=p_hours_gen)
    days_genuine = np.random.choice(range(7), size=n_genuine)
    
    categories_pool = ['grocery', 'entertainment', 'electronics', 'luxury', 'travel', 'gaming', 'crypto']
    p_cats_gen = np.array([0.35, 0.20, 0.15, 0.05, 0.10, 0.10, 0.05])
    p_cats_gen = p_cats_gen / p_cats_gen.sum()
    cats_genuine = np.random.choice(categories_pool, size=n_genuine, p=p_cats_gen)
    
    velocity_genuine = np.random.poisson(lam=1.2, size=n_genuine) + 1
    velocity_genuine = np.clip(velocity_genuine, 1, 4)
    
    avg_ratio_genuine = np.random.normal(loc=1.0, scale=0.3, size=n_genuine)
    avg_ratio_genuine = np.clip(avg_ratio_genuine, 0.2, 2.5)
    
    is_intl_genuine = np.random.choice([0, 1], size=n_genuine, p=[0.92, 0.08])
    dev_trust_genuine = np.random.beta(a=8, b=2, size=n_genuine)  # High trust (0.7 - 1.0)
    ip_risk_genuine = np.random.beta(a=1, b=8, size=n_genuine)    # Low risk (0.0 - 0.2)
    dist_home_genuine = np.random.exponential(scale=15.0, size=n_genuine)
    failed_logins_genuine = np.random.choice([0, 1, 2], size=n_genuine, p=[0.94, 0.05, 0.01])
    first_merch_genuine = np.random.choice([0, 1], size=n_genuine, p=[0.75, 0.25])

    # --- Fraudulent Transactions Simulation ---
    # Micro-probing fraud or high-value extraction fraud
    fraud_type_high = np.random.choice([True, False], size=n_fraud, p=[0.65, 0.35])
    amounts_fraud = np.where(
        fraud_type_high,
        np.random.uniform(1200.0, 7500.0, size=n_fraud),
        np.random.uniform(0.50, 4.00, size=n_fraud)
    )
    
    # Fraudsters frequently operate during nocturnal hours or weekend bursts
    p_hours_fr = np.array([
        0.08, 0.09, 0.10, 0.10, 0.09, 0.05, 0.03, 0.02, 0.02, 0.02, 0.02, 0.02,
        0.02, 0.02, 0.03, 0.03, 0.03, 0.03, 0.04, 0.04, 0.04, 0.04, 0.03, 0.04
    ])
    p_hours_fr = p_hours_fr / p_hours_fr.sum()
    hours_fraud = np.random.choice(range(24), size=n_fraud, p=p_hours_fr)
    days_fraud = np.random.choice(range(7), size=n_fraud)
    
    p_cats_fr = np.array([0.05, 0.05, 0.25, 0.25, 0.10, 0.15, 0.15])
    p_cats_fr = p_cats_fr / p_cats_fr.sum()
    cats_fraud = np.random.choice(categories_pool, size=n_fraud, p=p_cats_fr)
    
    velocity_fraud = np.random.poisson(lam=4.5, size=n_fraud) + 2
    velocity_fraud = np.clip(velocity_fraud, 2, 10)
    
    avg_ratio_fraud = np.random.normal(loc=5.5, scale=2.0, size=n_fraud)
    avg_ratio_fraud = np.clip(avg_ratio_fraud, 2.5, 15.0)
    
    is_intl_fraud = np.random.choice([0, 1], size=n_fraud, p=[0.35, 0.65])
    dev_trust_fraud = np.random.beta(a=1, b=7, size=n_fraud)  # Low trust (0.0 - 0.3)
    ip_risk_fraud = np.random.beta(a=7, b=2, size=n_fraud)    # High risk (0.6 - 1.0)
    dist_home_fraud = np.random.exponential(scale=350.0, size=n_fraud) + 50.0
    failed_logins_fraud = np.random.choice([0, 1, 2, 3, 4], size=n_fraud, p=[0.20, 0.20, 0.25, 0.20, 0.15])
    first_merch_fraud = np.random.choice([0, 1], size=n_fraud, p=[0.25, 0.75])

    # Assemble genuine and fraud dataframes
    df_genuine = pd.DataFrame({
        'amount': np.round(amounts_genuine, 2),
        'hour_of_day': hours_genuine,
        'day_of_week': days_genuine,
        'merchant_category': cats_genuine,
        'tx_velocity_1h': velocity_genuine,
        'avg_amount_ratio': np.round(avg_ratio_genuine, 2),
        'is_international': is_intl_genuine,
        'device_trust_score': np.round(dev_trust_genuine, 3),
        'ip_risk_score': np.round(ip_risk_genuine, 3),
        'distance_from_home': np.round(dist_home_genuine, 1),
        'failed_logins_24h': failed_logins_genuine,
        'is_first_merchant_use': first_merch_genuine,
        'is_fraud': 0
    })

    df_fraud = pd.DataFrame({
        'amount': np.round(amounts_fraud, 2),
        'hour_of_day': hours_fraud,
        'day_of_week': days_fraud,
        'merchant_category': cats_fraud,
        'tx_velocity_1h': velocity_fraud,
        'avg_amount_ratio': np.round(avg_ratio_fraud, 2),
        'is_international': is_intl_fraud,
        'device_trust_score': np.round(dev_trust_fraud, 3),
        'ip_risk_score': np.round(ip_risk_fraud, 3),
        'distance_from_home': np.round(dist_home_fraud, 1),
        'failed_logins_24h': failed_logins_fraud,
        'is_first_merchant_use': first_merch_fraud,
        'is_fraud': 1
    })

    df = pd.concat([df_genuine, df_fraud], ignore_index=True)
    df = df.sample(frac=1.0, random_state=random_state).reset_index(drop=True)
    return df


def train_and_evaluate_model():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    data_dir = os.path.join(base_dir, 'data')
    models_dir = os.path.join(base_dir, 'models')
    os.makedirs(data_dir, exist_ok=True)
    os.makedirs(models_dir, exist_ok=True)

    csv_path = os.path.join(data_dir, 'synthetic_transactions.csv')
    model_path = os.path.join(models_dir, 'fraud_model.joblib')

    print("[1/5] Generating synthetic transaction dataset (5,000 samples)...")
    df = generate_synthetic_transactions(n_samples=5000, random_state=42)
    df.to_csv(csv_path, index=False)
    print(f"      Dataset saved to: {csv_path}")
    print(f"      Total records: {len(df)} | Fraudulent: {df['is_fraud'].sum()} ({df['is_fraud'].mean()*100:.2f}%)")

    # Define feature lists
    numeric_features = [
        'amount', 'hour_of_day', 'day_of_week', 'tx_velocity_1h', 
        'avg_amount_ratio', 'is_international', 'device_trust_score', 
        'ip_risk_score', 'distance_from_home', 'failed_logins_24h', 
        'is_first_merchant_use'
    ]
    categorical_features = ['merchant_category']

    X = df[numeric_features + categorical_features]
    y = df['is_fraud']

    print("[2/5] Performing stratified train/test split (80% train / 20% test)...")
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.20, random_state=42, stratify=y
    )

    # Build preprocessing and model pipeline
    preprocessor = ColumnTransformer(
        transformers=[
            ('num', StandardScaler(), numeric_features),
            ('cat', OneHotEncoder(handle_unknown='ignore', sparse_output=False), categorical_features)
        ]
    )

    classifier = RandomForestClassifier(
        n_estimators=100,
        max_depth=10,
        min_samples_split=4,
        class_weight='balanced',
        random_state=42,
        n_jobs=-1
    )

    pipeline = Pipeline(steps=[
        ('preprocessor', preprocessor),
        ('classifier', classifier)
    ])

    print("[3/5] Training Random Forest Classifier on IBM LinuxONE s390x...")
    pipeline.fit(X_train, y_train)

    print("[4/5] Evaluating model performance on holdout test set...")
    y_pred = pipeline.predict(X_test)
    y_proba = pipeline.predict_proba(X_test)[:, 1]

    roc_auc = roc_auc_score(y_test, y_proba)
    cm = confusion_matrix(y_test, y_pred)
    
    print("\n---------------- MODEL EVALUATION REPORT ----------------")
    print(f"ROC-AUC Score: {roc_auc:.4f}")
    print("\nConfusion Matrix:")
    print(f"  True Negatives : {cm[0, 0]}  | False Positives: {cm[0, 1]}")
    print(f"  False Negatives: {cm[1, 0]}  | True Positives : {cm[1, 1]}")
    print("\nDetailed Classification Report:")
    print(classification_report(y_test, y_pred, target_names=['Legitimate (0)', 'Fraud (1)']))
    print("---------------------------------------------------------\n")

    # Feature Importance extraction
    rf = pipeline.named_steps['classifier']
    cat_encoder = pipeline.named_steps['preprocessor'].named_transformers_['cat']
    cat_feature_names = list(cat_encoder.get_feature_names_out(categorical_features))
    all_feature_names = numeric_features + cat_feature_names

    importances = rf.feature_importances_
    sorted_idx = np.argsort(importances)[::-1]

    print("Top 6 Fraud Prediction Drivers (Global Feature Importance):")
    for i in range(min(6, len(sorted_idx))):
        idx = sorted_idx[i]
        print(f"  {i+1}. {all_feature_names[idx]:<24} : {importances[idx]*100:.2f}%")

    print(f"\n[5/5] Serializing model pipeline to: {model_path}...")
    model_payload = {
        'pipeline': pipeline,
        'numeric_features': numeric_features,
        'categorical_features': categorical_features,
        'feature_names': all_feature_names,
        'roc_auc': float(roc_auc),
        'metrics_summary': classification_report(y_test, y_pred, output_dict=True)
    }
    joblib.dump(model_payload, model_path)
    print("Model successfully saved. Ready for real-time inference!\n")

    # Smoke Test: Single Transaction Inference
    sample_safe_tx = pd.DataFrame([{
        'amount': 35.50,
        'hour_of_day': 14,
        'day_of_week': 2,
        'merchant_category': 'grocery',
        'tx_velocity_1h': 1,
        'avg_amount_ratio': 1.05,
        'is_international': 0,
        'device_trust_score': 0.95,
        'ip_risk_score': 0.05,
        'distance_from_home': 5.2,
        'failed_logins_24h': 0,
        'is_first_merchant_use': 0
    }])
    
    sample_fraud_tx = pd.DataFrame([{
        'amount': 4200.00,
        'hour_of_day': 3,
        'day_of_week': 6,
        'merchant_category': 'crypto',
        'tx_velocity_1h': 6,
        'avg_amount_ratio': 8.50,
        'is_international': 1,
        'device_trust_score': 0.05,
        'ip_risk_score': 0.92,
        'distance_from_home': 1450.0,
        'failed_logins_24h': 3,
        'is_first_merchant_use': 1
    }])

    p_safe = pipeline.predict_proba(sample_safe_tx)[0, 1]
    p_fraud = pipeline.predict_proba(sample_fraud_tx)[0, 1]

    print(f"Inference Verification Test:")
    print(f"  Safe Transaction  -> Fraud Probability: {p_safe*100:.1f}%")
    print(f"  Risky Transaction -> Fraud Probability: {p_fraud*100:.1f}%\n")


if __name__ == '__main__':
    train_and_evaluate_model()
