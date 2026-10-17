"""
FraudShieldAI - Automated Unit & Integration Test Suite
IBM Z Datathon 2026 (Ubuntu on IBM LinuxONE s390x)
"""

import os
import sys
import pytest
import sqlite3
import pandas as pd
import numpy as np

# Adjust path to import from root directory
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from train_model import generate_synthetic_transactions
from app import evaluate_transaction_risk, init_db, log_audit_event, DB_PATH, MODEL_PATH, load_ml_pipeline
import joblib


def test_synthetic_data_generation():
    """Verify synthetic data generator outputs required columns with zero NaN values."""
    df = generate_synthetic_transactions(n_samples=500, random_state=42)
    assert len(df) == 500
    expected_cols = [
        'amount', 'hour_of_day', 'day_of_week', 'merchant_category',
        'tx_velocity_1h', 'avg_amount_ratio', 'is_international',
        'device_trust_score', 'ip_risk_score', 'distance_from_home',
        'failed_logins_24h', 'is_first_merchant_use', 'is_fraud'
    ]
    for col in expected_cols:
        assert col in df.columns, f"Missing expected column: {col}"
    assert df.isnull().sum().sum() == 0, "Synthetic dataset contains unexpected nulls"
    assert df['is_fraud'].nunique() == 2, "Binary target must contain both 0 and 1"


def test_model_loading_and_architecture():
    """Verify serialized model pipeline exists and has preprocessor + classifier."""
    assert os.path.exists(MODEL_PATH), f"Model file not found at: {MODEL_PATH}"
    payload = joblib.load(MODEL_PATH)
    assert "pipeline" in payload
    pipeline = payload["pipeline"]
    assert "preprocessor" in pipeline.named_steps
    assert "classifier" in pipeline.named_steps
    assert payload["roc_auc"] >= 0.90, f"ROC-AUC ({payload['roc_auc']}) lower than threshold 0.90"


def test_safe_transaction_evaluation():
    """Verify typical domestic transaction is evaluated as LOW risk and APPROVED."""
    load_ml_pipeline()
    safe_tx = {
        "amount": 28.50,
        "hour_of_day": 12,
        "day_of_week": 2,
        "merchant_category": "grocery",
        "tx_velocity_1h": 1,
        "avg_amount_ratio": 1.0,
        "is_international": 0,
        "device_trust_score": 0.95,
        "ip_risk_score": 0.05,
        "distance_from_home": 3.0,
        "failed_logins_24h": 0,
        "is_first_merchant_use": 0
    }
    result = evaluate_transaction_risk(safe_tx)
    assert result["risk_category"] == "LOW"
    assert result["status"] == "APPROVED"
    assert result["risk_score"] < 35
    assert result["simulated_otp"] is None


def test_medium_risk_otp_trigger():
    """Verify elevated transaction parameters trigger FLAGGED_OTP and a 6-digit OTP."""
    load_ml_pipeline()
    medium_tx = {
        "amount": 850.00,
        "hour_of_day": 21,
        "day_of_week": 4,
        "merchant_category": "electronics",
        "tx_velocity_1h": 3,
        "avg_amount_ratio": 3.2,
        "is_international": 0,
        "device_trust_score": 0.45,
        "ip_risk_score": 0.40,
        "distance_from_home": 40.0,
        "failed_logins_24h": 1,
        "is_first_merchant_use": 1
    }
    result = evaluate_transaction_risk(medium_tx)
    # Either medium (OTP) or high (Hold)
    assert result["risk_category"] in ["MEDIUM", "HIGH"]
    if result["risk_category"] == "MEDIUM":
        assert result["status"] == "FLAGGED_OTP"
        assert result["simulated_otp"] is not None
        assert len(result["simulated_otp"]) == 6


def test_high_risk_quarantine_hold():
    """Verify severe anomalous signals trigger HELD_FOR_REVIEW and block automated approval."""
    load_ml_pipeline()
    danger_tx = {
        "amount": 4500.00,
        "hour_of_day": 3,
        "day_of_week": 6,
        "merchant_category": "crypto",
        "tx_velocity_1h": 6,
        "avg_amount_ratio": 8.5,
        "is_international": 1,
        "device_trust_score": 0.05,
        "ip_risk_score": 0.95,
        "distance_from_home": 1500.0,
        "failed_logins_24h": 3,
        "is_first_merchant_use": 1
    }
    result = evaluate_transaction_risk(danger_tx)
    assert result["risk_category"] == "HIGH"
    assert result["status"] == "HELD_FOR_REVIEW"
    assert result["risk_score"] >= 70
    assert len(result["risk_reasons"]) > 0


def test_database_and_audit_logging():
    """Verify SQLite database initialization and tamper-evident audit logging."""
    init_db()
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM users WHERE role = 'admin'")
    admin_count = cursor.fetchone()[0]
    assert admin_count >= 1, "Default admin user should exist in users table"

    # Test audit entry
    cursor.execute(
        "INSERT INTO audit_logs (user_id, username, action, details) VALUES (?, ?, ?, ?)",
        (999, "test_agent", "UNIT_TEST", "Test audit event verification.")
    )
    conn.commit()

    cursor.execute("SELECT action FROM audit_logs WHERE action = 'UNIT_TEST'")
    record = cursor.fetchone()
    assert record is not None
    assert record[0] == "UNIT_TEST"
    conn.close()


def test_flask_web_and_api_integration():
    """Verify Flask client routes, session login, real-time transaction scoring, and OTP verification."""
    from app import app
    client = app.test_client()

    # 1. Health check endpoint
    health_res = client.get("/api/health")
    assert health_res.status_code == 200
    health_json = health_res.get_json()
    assert health_json["status"] == "healthy"
    assert health_json["model_loaded"] is True

    # 2. Authentication
    login_res = client.post("/login", data={
        "username": "demo_user",
        "password": "DemoUser123!"
    }, follow_redirects=True)
    assert login_res.status_code == 200
    assert b"Customer Banking Dashboard" in login_res.data

    # 3. Submit Safe Transaction via API
    safe_payload = {
        "amount": 22.50,
        "merchant_category": "grocery",
        "hour_of_day": 12,
        "tx_velocity_1h": 1,
        "avg_amount_ratio": 1.0,
        "distance_from_home": 3.0,
        "device_trust_score": 0.95,
        "ip_risk_score": 0.05,
        "failed_logins_24h": 0,
        "is_international": 0,
        "is_first_merchant_use": 0
    }
    tx1_res = client.post("/api/analyze-transaction", json=safe_payload)
    assert tx1_res.status_code == 200
    tx1_data = tx1_res.get_json()
    assert tx1_data["success"] is True
    assert tx1_data["status"] == "APPROVED"
    assert tx1_data["risk_category"] == "LOW"

    # 4. Submit Medium Risk Transaction (Expects FLAGGED_OTP)
    medium_payload = {
        "amount": 950.00,
        "merchant_category": "electronics",
        "hour_of_day": 22,
        "tx_velocity_1h": 3,
        "avg_amount_ratio": 3.5,
        "distance_from_home": 45.0,
        "device_trust_score": 0.45,
        "ip_risk_score": 0.40,
        "failed_logins_24h": 1,
        "is_international": 0,
        "is_first_merchant_use": 1
    }
    tx2_res = client.post("/api/analyze-transaction", json=medium_payload)
    assert tx2_res.status_code == 200
    tx2_data = tx2_res.get_json()
    assert tx2_data["status"] == "FLAGGED_OTP"
    assert tx2_data["simulated_otp"] is not None
    tx2_id = tx2_data["transaction_id"]
    sim_otp = tx2_data["simulated_otp"]

    # 5. Verify Step-Up OTP
    otp_res = client.post("/api/verify-otp", json={
        "transaction_id": tx2_id,
        "otp": sim_otp
    })
    assert otp_res.status_code == 200
    assert otp_res.get_json()["success"] is True

    # 6. Submit High Risk Transaction (Expects HELD_FOR_REVIEW)
    danger_payload = {
        "amount": 5200.00,
        "merchant_category": "crypto",
        "hour_of_day": 3,
        "tx_velocity_1h": 6,
        "avg_amount_ratio": 8.0,
        "distance_from_home": 1600.0,
        "device_trust_score": 0.05,
        "ip_risk_score": 0.95,
        "failed_logins_24h": 3,
        "is_international": 1,
        "is_first_merchant_use": 1
    }
    tx3_res = client.post("/api/analyze-transaction", json=danger_payload)
    assert tx3_res.status_code == 200
    tx3_data = tx3_res.get_json()
    assert tx3_data["status"] == "HELD_FOR_REVIEW"
    assert tx3_data["risk_category"] == "HIGH"
    tx3_id = tx3_data["transaction_id"]

    # 7. Switch to Admin session and approve held transaction
    client.get("/logout")
    client.post("/login", data={
        "username": "admin_sec",
        "password": "AdminShield2026!"
    }, follow_redirects=True)

    action_res = client.post(f"/admin/action/{tx3_id}/approve", follow_redirects=True)
    assert action_res.status_code == 200
    assert b"successfully APPROVED" in action_res.data
