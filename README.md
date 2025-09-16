# Fraud Detector — Django + Anomaly Model

A tiny web/API app that loads a saved anomaly-detection model (`best_v1.joblib`) and:
- exposes a **REST endpoint**: `POST /api/predict`
- serves a **simple UI** at `/` to submit values
- stores each prediction and shows a **history** at `/history/`

Built for the credit-card fraud dataset shape: **Time, V1..V28, Amount** (30 numeric features).

## Quickstart (Windows PowerShell)

> If PowerShell blocks activation:  
> `Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned -Force`

```powershell
# clone (if needed)
git clone https://github.com/<you>/<repo>.git
cd <repo>

# venv
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# deps
pip install -U pip
pip install -r requirements.txt  # or: pip install django djangorestframework joblib numpy scikit-learn

# model file
# place at: .\models\best_v1.joblib

# db & run
python manage.py migrate
python manage.py runserver 127.0.0.1:8000
Open:

UI: http://127.0.0.1:8000/

History: http://127.0.0.1:8000/history/

API

POST /api/predict → JSON with 30 fields (Time, V1..V28, Amount)
Returns { is_fraud, risk, confidence, anomaly_score, pseudo_probability, model_name, version }

Update the model

Replace models/best_v1.joblib with your latest bundle (pipeline + features), restart the server.

Troubleshooting

Connection refused → start server: python manage.py runserver 127.0.0.1:8000

Script blocked → set execution policy (see above)

Template not found → path must be predictor/templates/predictor/form.html

Model missing → ensure ./models/best_v1.joblib exists



Open:

UI: http://127.0.0.1:8000/

History: http://127.0.0.1:8000/history/

API

POST /api/predict → JSON with 30 fields (Time, V1..V28, Amount)
Returns { is_fraud, risk, confidence, anomaly_score, pseudo_probability, model_name, version }

Update the model

Replace models/best_v1.joblib with your latest bundle (pipeline + features), restart the server.

Troubleshooting

Connection refused → start server: python manage.py runserver 127.0.0.1:8000

Script blocked → set execution policy (see above)

Template not found → path must be predictor/templates/predictor/form.html

Model missing → ensure ./models/best_v1.joblib exists
'@ | Set-Content -Encoding utf8 README.md

git add README.md
git commit -m "Add README with run instructions"
git push
