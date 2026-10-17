# FraudShieldAI Machine Learning Model Specification

## 1. Model Overview
The primary inference engine uses an ensemble **Random Forest Classifier** wrapped in a Scikit-Learn `Pipeline`.

- **Pipeline Components**:
  - `preprocessor`: `ColumnTransformer` applying `StandardScaler` to numeric features and `OneHotEncoder(handle_unknown='ignore')` to categorical features.
  - `classifier`: `RandomForestClassifier(n_estimators=100, max_depth=10, min_samples_split=4, class_weight='balanced', random_state=42, n_jobs=-1)`
- **Class Balancing**: Balanced weighting (`class_weight='balanced'`) to penalize minority fraud misclassification without artificial oversampling distortion.
- **Explainability**: Global feature importances extracted from the Random Forest forest estimators; local risk driver attribution calculated per transaction based on outlier thresholds and tree path weights.
- **Portability**: Serialized using `joblib` into `models/fraud_model.joblib`. Native Big-Endian and Little-Endian compatible.

## 2. Evaluation Metrics Goal
Given the financial fraud domain:
- **ROC-AUC**: $\ge 0.95$
- **Recall (Fraud Class)**: $\ge 0.85$ (prioritizing detection of fraudulent attempts)
- **Precision (Fraud Class)**: $\ge 0.80$ (limiting false customer friction)

## 3. IBM LinuxONE (s390x) Advantage
Inference executes with sub-millisecond latency on IBM z16 enterprise processors using native BLAS/LAPACK vectorization.
