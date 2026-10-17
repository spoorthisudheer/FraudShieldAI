# FraudShieldAI: Intelligent Real-Time Banking Fraud Detection and Prevention System
**IBM Z Datathon 2026 Prototype**

[![Architecture: s390x](https://img.shields.io/badge/Architecture-s390x%20(IBM%20Z)-blue.svg)](#)
[![OS: Ubuntu 24.04 LTS](https://img.shields.io/badge/OS-Ubuntu%2024.04%20LTS-orange.svg)](#)
[![Python: 3.12](https://img.shields.io/badge/Python-3.12-yellow.svg)](#)
[![ML: Scikit-Learn](https://img.shields.io/badge/ML-Scikit--Learn%201.4-green.svg)](#)
[![License: Apache 2.0](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](LICENSE)

---

> ### 🛡️ Ethical Simulation & Datathon Notice
> **FraudShieldAI** is an academic prototype developed for the **IBM Z Datathon 2026** hosted on the **IBM LinuxONE Community Cloud**. 
> All transactions, accounts, and credentials are **100% synthetically simulated**. The system **never** collects real credit card numbers, actual PII, banking passwords, PINs, or live payment network clearing data.

---

## 1. Problem Statement
Digital banking volume requires transaction analysis **before settlement** with sub-second response times. High-risk transactions cannot be approved automatically without compromising consumer funds, while low-risk transactions must proceed with zero friction.

**FraudShieldAI** addresses this challenge on enterprise **IBM LinuxONE (s390x)** infrastructure by combining:
1. **Explainable Machine Learning** for anomaly and probability estimation.
2. **Progressive Heuristic Safeguards** detecting velocity spikes, geographic inconsistencies, and proxy networks.
3. **Multi-tiered Decision Triage**:
   - **Low Risk (< 35)**: Instant automated approval in simulation.
   - **Medium Risk (35 – 69)**: Step-up authentication required via simulated OTP.
   - **High Risk (>= 70)**: Immediate quarantine hold requiring human Administrator review.
4. **Role-Based Access Control (RBAC)**: Distinct Customer Portal vs. Security Operations Center (SOC).
5. **Tamper-Evident Audit Logging**: Chronological forensic recording of all system events.

---

## 2. System Architecture

```mermaid
flowchart TD
    subgraph Client["Client Interface"]
        UI_User["Customer Simulator (Presets, Form & Step-Up OTP)"]
        UI_Admin["Admin Operations Center (Quarantine Queue & Audit Log)"]
    end

    subgraph Backend["Application Server (Flask on LinuxONE s390x)"]
        Auth["Authentication & Session Manager (PBKDF2 Hash)"]
        TxIngest["Transaction Validator & Preprocessor"]
        MLPipeline["Scikit-Learn Random Forest Pipeline"]
        RulesEngine["Composite Risk Decision Engine"]
        AuditService["Audit Logger Service"]
    end

    subgraph Storage["Persistence Layer (SQLite3)"]
        DB_Users[("Users Table")]
        DB_Tx[("Transactions Table")]
        DB_Audit[("Audit Logs Table")]
        JoblibModel["Serialized Model (models/fraud_model.joblib)"]
    end

    UI_User -->|1. Submit Demo Transaction| TxIngest
    TxIngest --> MLPipeline
    MLPipeline --> JoblibModel
    MLPipeline --> RulesEngine
    RulesEngine -->|Score < 35| UI_User
    RulesEngine -->|35 <= Score < 70| UI_User
    RulesEngine -->|Score >= 70 (Hold)| UI_Admin
    UI_Admin -->|Approve / Reject Override| RulesEngine
    RulesEngine --> DB_Tx
    RulesEngine --> AuditService
    AuditService --> DB_Audit
    Auth --> DB_Users
```

---

## 3. IBM LinuxONE (s390x) Hardware Telemetry & Optimization

This prototype was deployed, trained, and tested directly on the **IBM LinuxONE Community Cloud** running **Ubuntu 24.04 LTS (Noble Numbat)** on the **s390x** mainframe architecture:

- **Hardware Architecture**: `s390x` (IBM z16 Enterprise Mainframe, Machine Type: 9175, Big Endian)
- **CPUs**: 3 dedicated vCPUs @ 5,508 MHz
- **Memory**: 7.8 GiB RAM
- **Native Open-Source Stack**: Leverages official Ubuntu native packages (`python3-sklearn`, `python3-pandas`, `python3-numpy`, `python3-scipy`) compiled with native BLAS and LAPACK vector acceleration.
- **Inference Speed**: Under 15 milliseconds per transaction on IBM z16 cores.

### Verification Command
Run the included verification script anytime:
```bash
.venv/bin/python verify_env.py
```
**Expected Verified Output:**
```text
=====================================================
  FraudShieldAI — IBM LinuxONE Environment Verification
=====================================================
System Platform : Linux 6.8.0-147-generic
Architecture    : s390x (Byte Order: BIG)
Python Version  : 3.12.3
Python Executable: /home/linux1/FraudShieldAI/.venv/bin/python
NumPy Version   : 1.26.4
Pandas Version  : 2.1.4
SciPy Version   : 1.11.4
Scikit-Learn    : 1.4.1.post1
Joblib Version  : 1.3.2
Flask Version   : 3.1.3
SQLite Version  : 3.45.1
Smoke ML Test   : PASSED (Prediction: 0)
=====================================================
```

---

## 4. Machine Learning Model & Evaluation Metrics

The core model is an ensemble **Random Forest Classifier** wrapped in a Scikit-Learn `Pipeline` with `StandardScaler` for continuous numerical features and `OneHotEncoder` for merchant categories.

### Holdout Evaluation Results (1,000 Test Records)
- **ROC-AUC**: `1.0000`
- **Confusion Matrix**:
  - True Negatives (Legitimate Approved): `930`
  - False Positives (Legitimate Flagged): `0`
  - False Negatives (Fraud Missed): `0`
  - True Positives (Fraud Caught): `70`
- **Precision (Fraud Class)**: `1.00`
- **Recall (Fraud Class)**: `1.00`
- **F1-Score (Fraud Class)**: `1.00`

### Top Global Fraud Drivers
1. **`avg_amount_ratio`** (29.03%): Disproportionate spike compared to historical customer average.
2. **`ip_risk_score`** (23.68%): IP proxy, VPN, or Tor exit node indicators.
3. **`distance_from_home`** (14.78%): Rapid geographic displacement.
4. **`device_trust_score`** (14.61%): Untrusted or unrecognized browser/hardware fingerprint.
5. **`amount`** (6.60%): High-value abnormal purchase sum.
6. **`failed_logins_24h`** (5.21%): Account credential stuffing history.

---

## 5. Quick Start Guide for IBM LinuxONE

### Prerequisites
On Ubuntu 24.04 on IBM LinuxONE:
```bash
# 1. Install system pre-compiled s390x packages
sudo apt-get update
sudo apt-get install -y python3-sklearn python3-pandas python3-numpy python3-scipy python3-pytest

# 2. Clone or navigate to repository
cd ~/FraudShieldAI

# 3. Create virtual environment with system packages enabled
python3 -m venv --system-site-packages .venv

# 4. Install lightweight web dependencies
.venv/bin/pip install flask joblib
```

### Model Training & Data Generation
```bash
.venv/bin/python train_model.py
```
This generates the 5,000 synthetic transactions in `data/synthetic_transactions.csv`, trains the model, and serializes `models/fraud_model.joblib`.

### Running Automated Test Suite
```bash
.venv/bin/python -m pytest tests/test_fraud_detection.py -v
```
All 7 unit and integration tests execute in **< 1.0 second**.

### Starting the Web Prototype
```bash
.venv/bin/python app.py
```
The application will launch on port `5000`.

### Accessing the Demo Application
If accessing via SSH port-forwarding from your local machine:
```bash
ssh -i "path/to/key.pem" -L 5000:127.0.0.1:5000 linux1@<server-ip>
```
Open your browser to: `http://localhost:5000`

---

## 6. Pre-Configured Test Credentials

| Role | Username | Password | Purpose |
| :--- | :--- | :--- | :--- |
| **Customer** | `demo_user` | `DemoUser123!` | Test transaction submission, view history, enter simulated OTP. |
| **Administrator** | `admin_sec` | `AdminShield2026!` | Review quarantine queue, approve/reject held items, view audit logs. |

*(You can also register any new custom user profile via the `/register` page)*

---

## 7. Project Structure

```text
FraudShieldAI/
├── data/
│   ├── README.md                      # Synthetic data schema & provenance
│   └── synthetic_transactions.csv     # 5,000 synthetic transaction records
├── models/
│   ├── README.md                      # Model architecture & evaluation notes
│   └── fraud_model.joblib             # Serialized Scikit-Learn pipeline
├── notebooks/
│   └── fraud_detection.ipynb          # Guided interactive Jupyter notebook
├── templates/
│   ├── base.html                      # Layout, navigation & ethical banners
│   ├── login.html                     # Demo login with one-click autofill
│   ├── register.html                  # Demo user registration
│   ├── user_dashboard.html            # Customer metrics & transaction history
│   ├── transaction.html               # Real-time risk simulator & OTP modal
│   ├── admin_dashboard.html           # SOC dashboard & quarantine queue
│   └── audit_logs.html                # Immutable security audit trail
├── static/
│   ├── css/style.css                  # Cyber-defense dark theme CSS
│   └── js/script.js                   # Client-side AJAX & risk gauge handling
├── tests/
│   └── test_fraud_detection.py        # 7 automated unit & integration tests
├── app.py                             # Core Flask backend & decision engine
├── train_model.py                     # Synthetic data & model training pipeline
├── verify_env.py                      # s390x hardware & dependency verification
├── requirements.txt                   # Dependency specification
├── README.md                          # Comprehensive project documentation
└── LICENSE                            # Apache 2.0 open-source license
```

---

## 8. Open-Source Libraries & Resources Used

| Library / Tool | Version | License | Role in FraudShieldAI |
| :--- | :--- | :--- | :--- |
| **Python** | 3.12.3 | PSF License | Core runtime environment |
| **scikit-learn** | 1.4.1 | BSD 3-Clause | Preprocessing pipeline, Random Forest model & metrics |
| **pandas** | 2.1.4 | BSD 3-Clause | Tabular data manipulation & feature framing |
| **numpy** | 1.26.4 | BSD 3-Clause | Vectorized stochastic feature generation |
| **Flask** | 3.1.3 | BSD 3-Clause | Lightweight web application backend & REST API |
| **Werkzeug** | 3.1.9 | BSD 3-Clause | PBKDF2 password hashing & secure session handling |
| **SQLite3** | 3.45.1 | Public Domain | Embedded relational database for demo users & audit logs |
| **Joblib** | 1.3.2 | BSD 3-Clause | Lightweight model serialization |
| **pytest** | 7.4.4 | MIT License | Automated unit and integration testing framework |

---

## 9. Datathon Deliverables Summary

- **Deliverable 1 (Working Prototype)**: Fully functioning Flask application running on IBM LinuxONE.
- **Deliverable 2 (Solution Architecture)**: Detailed Mermaid flowchart documented above and in artifact.
- **Deliverable 3 (README)**: This setup, architecture, and evaluation document.
- **Deliverable 4 (Open-Source List)**: Complete library, dataset, and license inventory above.
- **Deliverable 5 (IBM LinuxONE Evidence)**: Verified hardware outputs from `lscpu`, `uname -m`, and `verify_env.py`.
- **Deliverable 6 (Pitch Deck Outline)**: Structured for `[Team Name]_IBM Z Datathon 2026 Project.pdf`.
- **Deliverable 7 (Video Demo Script)**: 180-second walkthrough covering Problem, Solution, LinuxONE Architecture, and Live Triage Demo.
- **Deliverable 8 (Git Repository)**: Self-contained, clean codebase.
- **Deliverable 9 (Testing Evidence)**: 7 automated test cases passing in 0.97s on s390x.

---

## 10. License
This project is open-sourced under the **Apache License 2.0**. See the [LICENSE](LICENSE) file for details.
