import platform, sys, os
import numpy as np
import pandas as pd
import scipy
import sklearn
from sklearn.ensemble import RandomForestClassifier
import joblib
import flask
import sqlite3

print('=====================================================')
print('  FraudShieldAI — IBM LinuxONE Environment Verification')
print('=====================================================')
print(f'System Platform : {platform.system()} {platform.release()}')
print(f'Architecture    : {platform.machine()} (Byte Order: {sys.byteorder.upper()})')
print(f'Python Version  : {sys.version.split()[0]}')
print(f'Python Executable: {sys.executable}')
print(f'NumPy Version   : {np.__version__}')
print(f'Pandas Version  : {pd.__version__}')
print(f'SciPy Version   : {scipy.__version__}')
print(f'Scikit-Learn    : {sklearn.__version__}')
print(f'Joblib Version  : {joblib.__version__}')
print(f'Flask Version   : {flask.__version__}')
print(f'SQLite Version  : {sqlite3.sqlite_version}')

# Smoke test: Small ML Fit & Predict on s390x
X = np.array([[10.0, 1.0], [500.0, 9.0], [15.0, 0.0], [750.0, 8.0]])
y = np.array([0, 1, 0, 1])
rf = RandomForestClassifier(n_estimators=5, random_state=42)
rf.fit(X, y)
pred = rf.predict([[20.0, 0.5]])
print(f'Smoke ML Test   : PASSED (Prediction: {pred[0]})')
print('=====================================================')
