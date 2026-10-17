# FraudShieldAI Synthetic Banking Dataset

## 1. Overview & Provenance
This dataset is **100% synthetically generated** for the **IBM Z Datathon 2026** to demonstrate real-time banking fraud detection and prevention on the **IBM LinuxONE (s390x)** platform.

- **Zero Real-World PII**: Does not contain any real customer names, genuine credit card numbers, CVVs, PINs, or actual bank account credentials.
- **Purpose**: Academic and hackathon prototype evaluation, benchmark model training, and latency testing.
- **Generation Method**: Stochastic feature generation modeling documented financial crime typology (e.g., velocity spikes, IP proxy hops, rapid international routing, and nocturnal transaction bursts).

## 2. Feature Schema

| Column | Type | Description |
| :--- | :--- | :--- |
| `amount` | Float | Transaction amount in USD ($1.00 – $9,500.00) |
| `hour_of_day` | Integer | Hour of the day in 24h format (0 – 23) |
| `day_of_week` | Integer | Day of week (0 = Monday, 6 = Sunday) |
| `merchant_category` | Categorical | `grocery`, `entertainment`, `electronics`, `luxury`, `travel`, `gaming`, `crypto` |
| `tx_velocity_1h` | Integer | Number of transactions initiated by user in past 1 hour |
| `avg_amount_ratio` | Float | Ratio of current transaction amount to historical 30-day average |
| `is_international` | Binary | `0` = Domestic transaction, `1` = Cross-border |
| `device_trust_score` | Float | Device trust score (`0.0` = Untrusted/new device, `1.0` = Recognized/verified) |
| `ip_risk_score` | Float | IP address risk score (`0.0` = Low risk residential, `1.0` = High risk proxy/VPN/Tor) |
| `distance_from_home`| Float | Distance in miles from user's registered home address |
| `failed_logins_24h` | Integer | Count of failed authentication attempts in previous 24 hours |
| `is_first_merchant_use` | Binary | `0` = Prior purchase history with merchant, `1` = First time purchase |
| `is_fraud` | Binary | Target label: `0` = Legitimate transaction, `1` = Fraudulent transaction |

## 3. License
This synthetic data generator and dataset are released under the **Apache License 2.0** for open-source use.
