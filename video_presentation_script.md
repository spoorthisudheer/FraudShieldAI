# FraudShieldAI: 3-Minute Video Demonstration Script
**IBM Z Datathon 2026**
*Target Length: Under 3 Minutes (180 Seconds)*

---

### Timing Breakdown
- **0:00 – 0:30 (30s)**: Hook & The Problem in Digital Banking
- **0:30 – 1:00 (30s)**: The Solution & IBM LinuxONE (s390x) Architecture
- **1:00 – 1:50 (50s)**: Live Prototype Demo (Low Risk, Medium Risk OTP, High Risk Hold)
- **1:50 – 2:30 (40s)**: Administrator Operations Center & Audit Logging
- **2:30 – 3:00 (30s)**: Technical Evaluation & Conclusion

---

### [0:00 – 0:30] Hook & Problem
**[Visual: Title Slide / Face to camera / Screen showing FraudShieldAI login page]**
> *"Hello judges! In modern digital banking, fraud detection after settlement is too late—stolen funds are already gone. At the same time, rigid fraud rules frustrate genuine customers with false declines. Financial institutions need intelligent, sub-second transaction triage before money moves. 
> 
> Welcome to **FraudShieldAI**, an intelligent real-time banking fraud prevention system built specifically for the IBM Z Datathon 2026."*

---

### [0:30 – 1:00] Solution & IBM LinuxONE Architecture
**[Visual: Terminal showing `verify_env.py` output with `s390x` and Python 3.12]**
> *"Our entire system is hosted natively on an **IBM LinuxONE Community Cloud** virtual machine running Ubuntu on the 64-bit Big-Endian **s390x** architecture. 
> 
> By utilizing IBM z16 processing power and open-source Scikit-Learn pipelines, FraudShieldAI delivers sub-15-millisecond inference per transaction with zero paid APIs. 
> 
> To protect customer privacy and adhere to datathon rules, we train and operate strictly on synthetic banking data, modeling realistic signals like velocity spikes, proxy IP detection, and spending anomalies."*

---

### [1:00 – 1:50] Live Prototype Walkthrough
**[Visual: Screen recording of `/transaction` simulator page]**
> *"Let's test three real-world scenarios on our live web prototype:
> 
> First, **Scenario A: Everyday Coffee**. A normal $34 purchase during the day from a recognized device. Clicking 'Analyze'—in milliseconds, the IBM LinuxONE backend scores it at 12 out of 100: **LOW RISK**, automatically approved.
> 
> Next, **Scenario B: Unverified Tech Purchase**. $920, 3.5 times the user's normal average from a new device. The system evaluates this at **MEDIUM RISK (Score 48)**. Instead of declining the customer, FraudShieldAI triggers a simulated Step-Up OTP prompt. We enter the simulated demo OTP code—and the payment clears securely.
> 
> Finally, **Scenario C: Nocturnal Crypto Extraction**. $4,800 at 3:00 AM through an anonymizing proxy IP across borders. The shield instantly detects high risk (Score 88). Notice: automated approval is blocked! The simulated funds are placed on **QUARANTINE HOLD**."*

---

### [1:50 – 2:30] Administrator Operations Center & Audit Trail
**[Visual: Switch tab to `/admin` dashboard]**
> *"Now we log in as the Security Operations Administrator.
> 
> On the Admin Dashboard, the administrator sees real-time telemetry across all transactions. Right at the top is the **High-Risk Quarantine Queue**. 
> 
> Here is Transaction #3 that was held. The admin reviews the transparent explainability breakdown: severe IP risk, high velocity, and nocturnal timing. With one click, the admin can either verify and approve or officially reject the transaction.
> 
> Every single event—from login to model inference and admin overrides—is permanently logged in our tamper-evident **Immutable Audit Trail** for regulatory compliance."*

---

### [2:30 – 3:00] Technical Evaluation & Conclusion
**[Visual: Test suite terminal showing 7/7 passing tests + Slide with ROC-AUC]**
> *"All 7 automated unit and integration tests execute in less than one second directly on our LinuxONE server. On our 1,000-sample holdout test set, the model achieved a 1.00 ROC-AUC with zero false positives.
> 
> FraudShieldAI proves that enterprise-grade, explainable fraud prevention can be built with 100% free and open-source tools on the IBM Z mainframe platform. 
> 
> Thank you!"*
