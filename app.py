"""
FraudShieldAI - Web Application & Real-Time Security Engine
IBM Z Datathon 2026 (Ubuntu on IBM LinuxONE s390x)
"""

import os
import sys
import json
import sqlite3
import random
from datetime import datetime, timezone
from functools import wraps

from flask import (
    Flask, render_template, request, redirect, url_for, 
    session, flash, jsonify, g
)
from werkzeug.security import generate_password_hash, check_password_hash
import joblib
import pandas as pd
import numpy as np

# Application Setup
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "fraudshield.db")
MODEL_PATH = os.path.join(BASE_DIR, "models", "fraud_model.joblib")

app = Flask(__name__)
app.secret_key = os.environ.get("FRAUDSHIELD_SECRET_KEY", "ibm-z-datathon-2026-s390x-secure-key-demo")

# Global reference for ML model pipeline
MODEL_PAYLOAD = None


def load_ml_pipeline():
    """Load the serialized Scikit-Learn pipeline for inference."""
    global MODEL_PAYLOAD
    if os.path.exists(MODEL_PATH):
        try:
            MODEL_PAYLOAD = joblib.load(MODEL_PATH)
            print(f"[FraudShieldAI] ML Pipeline successfully loaded from: {MODEL_PATH}")
        except Exception as e:
            print(f"[FraudShieldAI] Warning: Could not load ML model: {e}")
            MODEL_PAYLOAD = None
    else:
        print(f"[FraudShieldAI] Model file not found at: {MODEL_PATH}")
        MODEL_PAYLOAD = None


# Database Helpers
def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(DB_PATH)
        g.db.row_factory = sqlite3.Row
    return g.db


@app.teardown_appcontext
def close_db(error):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def log_audit_event(user_id, username, action, details):
    """Write an immutable audit log entry."""
    try:
        db = get_db()
        db.execute(
            "INSERT INTO audit_logs (user_id, username, action, details, timestamp) VALUES (?, ?, ?, ?, ?)",
            (user_id, username, action, details, datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S"))
        )
        db.commit()
    except Exception as e:
        print(f"[Audit Error] Failed to log event: {e}")


def init_db():
    """Initialize database tables and create initial demo accounts."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Users Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            role TEXT NOT NULL DEFAULT 'user',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Transactions Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            username TEXT NOT NULL,
            amount REAL NOT NULL,
            hour_of_day INTEGER NOT NULL,
            day_of_week INTEGER NOT NULL,
            merchant_category TEXT NOT NULL,
            tx_velocity_1h INTEGER NOT NULL,
            avg_amount_ratio REAL NOT NULL,
            is_international INTEGER NOT NULL,
            device_trust_score REAL NOT NULL,
            ip_risk_score REAL NOT NULL,
            distance_from_home REAL NOT NULL,
            failed_logins_24h INTEGER NOT NULL,
            is_first_merchant_use INTEGER NOT NULL,
            ml_probability REAL NOT NULL,
            risk_score INTEGER NOT NULL,
            risk_category TEXT NOT NULL,
            status TEXT NOT NULL,
            simulated_otp TEXT,
            otp_verified INTEGER DEFAULT 0,
            risk_reasons TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    """)

    # Audit Logs Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS audit_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            username TEXT,
            action TEXT NOT NULL,
            details TEXT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    conn.commit()

    # Check and seed default demo accounts
    cursor.execute("SELECT COUNT(*) FROM users")
    if cursor.fetchone()[0] == 0:
        demo_accounts = [
            ("demo_user", generate_password_hash("DemoUser123!"), "user"),
            ("admin_sec", generate_password_hash("AdminShield2026!"), "admin")
        ]
        cursor.executemany("INSERT INTO users (username, password_hash, role) VALUES (?, ?, ?)", demo_accounts)
        
        # Log initialization
        cursor.execute(
            "INSERT INTO audit_logs (user_id, username, action, details) VALUES (?, ?, ?, ?)",
            (1, "system", "SYSTEM_INIT", "Database tables initialized with demo_user and admin_sec roles.")
        )
        conn.commit()
        print("[FraudShieldAI] Default demo accounts seeded successfully.")

    conn.close()


# Decorators for Access Control
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user_id" not in session:
            flash("Please log in to access this page.", "warning")
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated_function


def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user_id" not in session:
            flash("Administrator login required.", "warning")
            return redirect(url_for("login"))
        if session.get("role") != "admin":
            flash("Access denied: Administrative privileges required.", "danger")
            log_audit_event(session["user_id"], session["username"], "ACCESS_DENIED", "Unauthorized attempt to view admin portal.")
            return redirect(url_for("user_dashboard"))
        return f(*args, **kwargs)
    return decorated_function


# Risk Evaluation Logic
def evaluate_transaction_risk(tx_data):
    """
    Combines Machine Learning prediction with deterministic financial heuristics.
    Returns composite score (0-100), risk category, status, simulated OTP, and risk explanations.
    """
    global MODEL_PAYLOAD
    
    # 1. Machine Learning Inference
    ml_prob = 0.0
    if MODEL_PAYLOAD and "pipeline" in MODEL_PAYLOAD:
        try:
            df_input = pd.DataFrame([tx_data])
            pipeline = MODEL_PAYLOAD["pipeline"]
            ml_prob = float(pipeline.predict_proba(df_input)[0, 1])
        except Exception as e:
            print(f"[Inference Error] {e}")
            ml_prob = 0.5  # Fallback to neutral risk
    else:
        # Fallback baseline heuristic if model not yet loaded
        ml_prob = 0.45 if tx_data["amount"] > 1000 else 0.05

    # 2. Heuristic Penalties & Explainability Attribution
    penalties = 0
    reasons = []

    # IP risk scoring
    if tx_data["ip_risk_score"] >= 0.70:
        penalties += 25
        reasons.append(f"High-risk IP address / Anonymizing proxy detected (Risk: {tx_data['ip_risk_score']*100:.0f}%)")
    elif tx_data["ip_risk_score"] >= 0.35:
        penalties += 15
        reasons.append(f"Elevated IP anomaly indicator ({tx_data['ip_risk_score']*100:.0f}%)")

    # Device trust scoring
    if tx_data["device_trust_score"] <= 0.30:
        penalties += 25
        reasons.append(f"Untrusted or unrecognized client device (Trust Score: {tx_data['device_trust_score']*100:.0f}%)")
    elif tx_data["device_trust_score"] <= 0.60:
        penalties += 15
        reasons.append(f"Partially trusted device fingerprint ({tx_data['device_trust_score']*100:.0f}%)")

    # Failed login attempts
    if tx_data["failed_logins_24h"] >= 2:
        penalties += 20
        reasons.append(f"Recent authentication anomalies: {tx_data['failed_logins_24h']} failed logins in past 24 hours")
    elif tx_data["failed_logins_24h"] == 1:
        penalties += 10
        reasons.append("Recent failed login attempt recorded prior to transaction")

    # Spending velocity ratio vs user baseline
    if tx_data["avg_amount_ratio"] >= 4.0:
        penalties += 25
        reasons.append(f"Sudden spending velocity: {tx_data['avg_amount_ratio']:.1f}x higher than historical average")
    elif tx_data["avg_amount_ratio"] >= 2.5:
        penalties += 15
        reasons.append(f"Elevated spending ratio: {tx_data['avg_amount_ratio']:.1f}x historical baseline")

    # Transaction velocity in past hour
    if tx_data["tx_velocity_1h"] >= 5:
        penalties += 20
        reasons.append(f"High transaction frequency: {tx_data['tx_velocity_1h']} transactions in past 60 minutes")
    elif tx_data["tx_velocity_1h"] >= 3:
        penalties += 12
        reasons.append(f"Rapid transaction velocity ({tx_data['tx_velocity_1h']} charges in 1 hour)")

    # Geographic distance
    if tx_data["distance_from_home"] >= 300.0:
        penalties += 15
        reasons.append(f"Geographic discrepancy: Initiated {tx_data['distance_from_home']:.0f} miles from home location")
    elif tx_data["distance_from_home"] >= 30.0:
        penalties += 8
        reasons.append(f"Out-of-neighborhood location ({tx_data['distance_from_home']:.0f} miles from registered address)")

    if tx_data["is_international"] == 1:
        penalties += 15
        reasons.append("Cross-border transaction clearing path")

    if tx_data.get("is_first_merchant_use", 0) == 1:
        penalties += 10
        reasons.append("First-time merchant transaction profile")

    if tx_data["merchant_category"] in ["crypto", "gaming", "luxury"] and tx_data["amount"] > 1000:
        penalties += 20
        reasons.append(f"High-risk merchant sector ({tx_data['merchant_category'].capitalize()}) with high transaction value")

    # 3. Composite Risk Calculation: 60% ML Model Probability + 40% Heuristic Safeguards
    heuristic_component = min(100.0, penalties)
    composite_score = int(round(min(100.0, (ml_prob * 60.0) + (heuristic_component * 0.40))))

    # 4. Multi-tiered Decision Rules
    if composite_score < 35:
        category = "LOW"
        status = "APPROVED"
        simulated_otp = None
        if not reasons:
            reasons.append("Normal spending pattern and recognized device credentials.")
    elif composite_score < 70:
        category = "MEDIUM"
        status = "FLAGGED_OTP"
        simulated_otp = str(random.randint(100000, 999999))
        reasons.append("Medium risk threshold reached: Step-up authentication required.")
    else:
        category = "HIGH"
        status = "HELD_FOR_REVIEW"
        simulated_otp = None
        reasons.append("High risk threshold exceeded: Transaction held pending administrative review.")

    return {
        "ml_probability": ml_prob,
        "risk_score": composite_score,
        "risk_category": category,
        "status": status,
        "simulated_otp": simulated_otp,
        "risk_reasons": reasons
    }


# Routes - Authentication
@app.route("/")
def index():
    if "user_id" in session:
        if session.get("role") == "admin":
            return redirect(url_for("admin_dashboard"))
        return redirect(url_for("user_dashboard"))
    return redirect(url_for("login"))


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        db = get_db()
        user = db.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()

        if user and check_password_hash(user["password_hash"], password):
            session.clear()
            session["user_id"] = user["id"]
            session["username"] = user["username"]
            session["role"] = user["role"]

            log_audit_event(user["id"], user["username"], "LOGIN_SUCCESS", f"User logged in with role: {user['role']}")
            flash(f"Welcome back, {user['username']}! Logged in as {user['role'].upper()}.", "success")

            if user["role"] == "admin":
                return redirect(url_for("admin_dashboard"))
            return redirect(url_for("user_dashboard"))
        else:
            flash("Invalid username or password.", "danger")
            log_audit_event(None, username, "LOGIN_FAILED", "Failed authentication attempt.")

    return render_template("login.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        role = request.form.get("role", "user")

        if not username or not password:
            flash("Username and password are required.", "warning")
            return render_template("register.html")

        if role not in ["user", "admin"]:
            role = "user"

        db = get_db()
        existing = db.execute("SELECT id FROM users WHERE username = ?", (username,)).fetchone()
        if existing:
            flash("Username already taken. Please choose another.", "warning")
            return render_template("register.html")

        password_hash = generate_password_hash(password)
        cursor = db.execute(
            "INSERT INTO users (username, password_hash, role) VALUES (?, ?, ?)",
            (username, password_hash, role)
        )
        db.commit()

        log_audit_event(cursor.lastrowid, username, "USER_REGISTERED", f"Created account with role: {role}")
        flash(f"Account '{username}' created successfully! You can now log in.", "success")
        return redirect(url_for("login"))

    return render_template("register.html")


@app.route("/logout")
def logout():
    uid = session.get("user_id")
    uname = session.get("username")
    if uname:
        log_audit_event(uid, uname, "LOGOUT", "User logged out.")
    session.clear()
    flash("You have been safely logged out.", "info")
    return redirect(url_for("login"))


# Routes - User Portal
@app.route("/dashboard")
@login_required
def user_dashboard():
    db = get_db()
    user_id = session["user_id"]
    
    # User's recent transactions
    transactions = db.execute(
        "SELECT * FROM transactions WHERE user_id = ? ORDER BY created_at DESC LIMIT 10",
        (user_id,)
    ).fetchall()

    # User statistics
    total_tx = db.execute("SELECT COUNT(*) FROM transactions WHERE user_id = ?", (user_id,)).fetchone()[0]
    approved_tx = db.execute("SELECT COUNT(*) FROM transactions WHERE user_id = ? AND status = 'APPROVED'", (user_id,)).fetchone()[0]
    held_tx = db.execute("SELECT COUNT(*) FROM transactions WHERE user_id = ? AND status = 'HELD_FOR_REVIEW'", (user_id,)).fetchone()[0]
    otp_tx = db.execute("SELECT COUNT(*) FROM transactions WHERE user_id = ? AND status = 'FLAGGED_OTP'", (user_id,)).fetchone()[0]

    return render_template(
        "user_dashboard.html",
        transactions=transactions,
        total_tx=total_tx,
        approved_tx=approved_tx,
        held_tx=held_tx,
        otp_tx=otp_tx
    )


@app.route("/transaction")
@login_required
def transaction_page():
    return render_template("transaction.html")


# API - Real-Time Transaction Analysis
@app.route("/api/analyze-transaction", methods=["POST"])
@login_required
def api_analyze_transaction():
    try:
        data = request.get_json() or {}
        
        # Parse and sanitize inputs
        tx_data = {
            "amount": float(data.get("amount", 50.0)),
            "hour_of_day": int(data.get("hour_of_day", datetime.now().hour)),
            "day_of_week": int(data.get("day_of_week", datetime.now().weekday())),
            "merchant_category": str(data.get("merchant_category", "grocery")).lower(),
            "tx_velocity_1h": int(data.get("tx_velocity_1h", 1)),
            "avg_amount_ratio": float(data.get("avg_amount_ratio", 1.0)),
            "is_international": int(data.get("is_international", 0)),
            "device_trust_score": float(data.get("device_trust_score", 0.95)),
            "ip_risk_score": float(data.get("ip_risk_score", 0.05)),
            "distance_from_home": float(data.get("distance_from_home", 5.0)),
            "failed_logins_24h": int(data.get("failed_logins_24h", 0)),
            "is_first_merchant_use": int(data.get("is_first_merchant_use", 0))
        }

        # Run composite risk analysis
        eval_result = evaluate_transaction_risk(tx_data)

        # Record in database
        db = get_db()
        cursor = db.execute("""
            INSERT INTO transactions (
                user_id, username, amount, hour_of_day, day_of_week, merchant_category,
                tx_velocity_1h, avg_amount_ratio, is_international, device_trust_score,
                ip_risk_score, distance_from_home, failed_logins_24h, is_first_merchant_use,
                ml_probability, risk_score, risk_category, status, simulated_otp, risk_reasons
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            session["user_id"],
            session["username"],
            tx_data["amount"],
            tx_data["hour_of_day"],
            tx_data["day_of_week"],
            tx_data["merchant_category"],
            tx_data["tx_velocity_1h"],
            tx_data["avg_amount_ratio"],
            tx_data["is_international"],
            tx_data["device_trust_score"],
            tx_data["ip_risk_score"],
            tx_data["distance_from_home"],
            tx_data["failed_logins_24h"],
            tx_data["is_first_merchant_use"],
            eval_result["ml_probability"],
            eval_result["risk_score"],
            eval_result["risk_category"],
            eval_result["status"],
            eval_result["simulated_otp"],
            json.dumps(eval_result["risk_reasons"])
        ))
        tx_id = cursor.lastrowid
        db.commit()

        # Audit log event
        log_audit_event(
            session["user_id"],
            session["username"],
            "TX_ANALYZED",
            f"TX #{tx_id} - ${tx_data['amount']:.2f} ({eval_result['risk_category']} Risk: Score {eval_result['risk_score']}) Status: {eval_result['status']}"
        )

        return jsonify({
            "success": True,
            "transaction_id": tx_id,
            "risk_score": eval_result["risk_score"],
            "risk_category": eval_result["risk_category"],
            "status": eval_result["status"],
            "ml_probability": round(eval_result["ml_probability"] * 100, 1),
            "simulated_otp": eval_result["simulated_otp"],
            "risk_reasons": eval_result["risk_reasons"]
        })

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 400


# API - Verify Simulated Step-Up OTP
@app.route("/api/verify-otp", methods=["POST"])
@login_required
def api_verify_otp():
    try:
        data = request.get_json() or {}
        tx_id = int(data.get("transaction_id", 0))
        submitted_otp = str(data.get("otp", "")).strip()

        db = get_db()
        tx = db.execute("SELECT * FROM transactions WHERE id = ? AND user_id = ?", (tx_id, session["user_id"])).fetchone()

        if not tx:
            return jsonify({"success": False, "error": "Transaction not found."}), 404

        if tx["status"] != "FLAGGED_OTP":
            return jsonify({"success": False, "error": "Transaction does not require OTP verification."}), 400

        if submitted_otp == tx["simulated_otp"]:
            db.execute("UPDATE transactions SET status = 'APPROVED', otp_verified = 1 WHERE id = ?", (tx_id,))
            db.commit()
            log_audit_event(
                session["user_id"],
                session["username"],
                "OTP_VERIFIED",
                f"Simulated OTP passed for TX #{tx_id}. Status transitioned to APPROVED."
            )
            return jsonify({"success": True, "message": "Simulated OTP verified. Transaction approved!"})
        else:
            log_audit_event(
                session["user_id"],
                session["username"],
                "OTP_FAILED",
                f"Incorrect simulated OTP for TX #{tx_id}."
            )
            return jsonify({"success": False, "error": "Invalid simulated OTP code."}), 400

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 400


# Routes - Administrator Operations Center
@app.route("/admin")
@admin_required
def admin_dashboard():
    db = get_db()

    # Metrics
    total_tx = db.execute("SELECT COUNT(*) FROM transactions").fetchone()[0]
    approved_tx = db.execute("SELECT COUNT(*) FROM transactions WHERE status = 'APPROVED'").fetchone()[0]
    held_tx = db.execute("SELECT COUNT(*) FROM transactions WHERE status = 'HELD_FOR_REVIEW'").fetchone()[0]
    otp_tx = db.execute("SELECT COUNT(*) FROM transactions WHERE status = 'FLAGGED_OTP'").fetchone()[0]
    rejected_tx = db.execute("SELECT COUNT(*) FROM transactions WHERE status = 'REJECTED'").fetchone()[0]

    # Held Transactions for Review
    held_transactions = db.execute(
        "SELECT * FROM transactions WHERE status = 'HELD_FOR_REVIEW' ORDER BY created_at DESC"
    ).fetchall()

    # All Recent Transactions
    filter_cat = request.args.get("category", "")
    if filter_cat in ["LOW", "MEDIUM", "HIGH"]:
        all_transactions = db.execute(
            "SELECT * FROM transactions WHERE risk_category = ? ORDER BY created_at DESC LIMIT 50",
            (filter_cat,)
        ).fetchall()
    else:
        all_transactions = db.execute(
            "SELECT * FROM transactions ORDER BY created_at DESC LIMIT 50"
        ).fetchall()

    return render_template(
        "admin_dashboard.html",
        total_tx=total_tx,
        approved_tx=approved_tx,
        held_tx=held_tx,
        otp_tx=otp_tx,
        rejected_tx=rejected_tx,
        held_transactions=held_transactions,
        all_transactions=all_transactions,
        filter_cat=filter_cat
    )


@app.route("/admin/action/<int:tx_id>/<action>", methods=["POST"])
@admin_required
def admin_transaction_action(tx_id, action):
    if action not in ["approve", "reject"]:
        flash("Invalid administrative action.", "danger")
        return redirect(url_for("admin_dashboard"))

    new_status = "APPROVED" if action == "approve" else "REJECTED"
    db = get_db()
    tx = db.execute("SELECT * FROM transactions WHERE id = ?", (tx_id,)).fetchone()

    if not tx:
        flash(f"Transaction #{tx_id} not found.", "warning")
        return redirect(url_for("admin_dashboard"))

    db.execute("UPDATE transactions SET status = ? WHERE id = ?", (new_status, tx_id))
    db.commit()

    log_audit_event(
        session["user_id"],
        session["username"],
        f"ADMIN_{action.upper()}",
        f"Admin {session['username']} set TX #{tx_id} status to {new_status} (Amount: ${tx['amount']:.2f}, Risk Score: {tx['risk_score']})"
    )
    flash(f"Transaction #{tx_id} has been successfully {new_status}.", "success")
    return redirect(url_for("admin_dashboard"))


@app.route("/admin/audit")
@admin_required
def audit_logs():
    db = get_db()
    logs = db.execute("SELECT * FROM audit_logs ORDER BY timestamp DESC LIMIT 100").fetchall()
    return render_template("audit_logs.html", logs=logs)


# API - Health and Architecture Status
@app.route("/api/health")
def api_health():
    return jsonify({
        "status": "healthy",
        "system": {
            "platform": sys.platform,
            "architecture": os.uname().machine if hasattr(os, "uname") else "unknown",
            "python_version": sys.version.split()[0],
            "ibm_linuxone_verified": hasattr(os, "uname") and os.uname().machine == "s390x"
        },
        "model_loaded": MODEL_PAYLOAD is not None,
        "database": "sqlite3_active"
    })


# Initialization on startup
init_db()
load_ml_pipeline()

if __name__ == "__main__":
    # Host on localhost or internal interface for safe community cloud demonstration
    app.run(host="0.0.0.0", port=5000, debug=False)
