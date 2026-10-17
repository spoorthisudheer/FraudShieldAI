# FraudShieldAI Pitch Deck Blueprint
**File Submission Name:** `[Team Name]_IBM Z Datathon 2026 Project.pdf`

---

### Slide 1: Title & Executive Summary
- **Title**: FraudShieldAI — Intelligent Real-Time Banking Fraud Detection & Prevention System
- **Subtitle**: Sub-second pre-clearing risk triage powered by IBM LinuxONE (s390x)
- **Track**: IBM Z Datathon 2026
- **Team**: [Your Team Name / Member Names]
- **Key Takeaway**: A privacy-compliant, zero-cost, open-source security prototype protecting digital banking transactions before funds settle.

---

### Slide 2: The Core Problem in Digital Banking
- **The Challenge**: Card-not-present (CNP) and account takeover (ATO) fraud are rising rapidly.
- **The Vulnerability**: Post-transaction detection arrives too late—funds have already moved.
- **The Dilemma**: High friction drives customers away; low friction exposes bank capital to catastrophic loss.
- **The Need**: Pre-settlement inference, calibrated multi-tiered risk scoring, and explainable decision attribution.

---

### Slide 3: Solution Architecture & IBM Z Alignment
- **Enterprise Mainframe Hosting**: Deployed on **IBM LinuxONE (s390x)** community cloud running Ubuntu 24.04 LTS.
- **Hardware Acceleration**: Leveraging IBM z16 processing power for sub-15ms ML inference per transaction.
- **Explainable Ensemble Model**: Scikit-Learn Random Forest Classifier + Progressive Business Rule Safeguards.
- **Multi-tiered Decision Framework**:
  - **Low Risk (< 35)**: Frictionless auto-clearance.
  - **Medium Risk (35–69)**: Step-up authentication via simulated OTP.
  - **High Risk (>= 70)**: Pre-settlement quarantine hold awaiting human Admin triage.

---

### Slide 4: Data Integrity & Ethical Compliance
- **100% Synthetic Banking Transactions**: 5,000 realistic records modeling financial crime typology (velocity, IP proxy hops, nocturnal spikes, distance anomalies).
- **Strict Privacy**: Zero real PII, zero actual account numbers, zero real credentials or real OTPs collected.
- **Open-Source & Free**: Built entirely with free and open-source tools (Python 3.12, Scikit-Learn, Pandas, NumPy, Flask, SQLite3).

---

### Slide 5: Technical Evaluation & Benchmark Metrics
- **Holdout Test Set**: 1,000 transactions (stratified 20% holdout).
- **Metrics**:
  - **ROC-AUC**: `1.0000`
  - **Precision (Fraud Class)**: `1.00`
  - **Recall (Fraud Class)**: `1.00`
  - **F1-Score (Fraud Class)**: `1.00`
- **Top Fraud Risk Drivers**:
  1. `avg_amount_ratio` (29.03%): Deviation from historical baseline.
  2. `ip_risk_score` (23.68%): Anonymized proxy and Tor routing.
  3. `distance_from_home` (14.78%): Unrealistic geographic travel.
  4. `device_trust_score` (14.61%): Unrecognized browser/device fingerprint.

---

### Slide 6: Product Workflow & Live UI Experience
- **Customer Simulator**: Interactive sliders and 3 live presets (Safe Grocery, Medium Tech, High-Risk Crypto).
- **Step-Up Verification**: In-flight simulated OTP modal for medium-risk transactions.
- **Security Operations Center (SOC)**: Administrative dashboard with quarantine review queue, one-click release/reject, and tamper-evident audit logs.

---

### Slide 7: Security Governance & Tamper-Evident Audit Trail
- **Role-Based Access Control (RBAC)**: Distinct Customer vs. SOC Administrator access.
- **Password Security**: Irreversible PBKDF2 hashing via Werkzeug.
- **Immutable Audit Trail**: Append-only event journaling for compliance and forensics.

---

### Slide 8: Future Roadmap & Impact
- **Scale on IBM Z**: Expanding to IBM Z Integrated Accelerator for AI (z16 on-chip AI accelerator).
- **Integration**: Pluggable REST APIs for open banking gateways.
- **Summary**: Real-time protection, explainable AI, zero proprietary cost, built on IBM Z.
