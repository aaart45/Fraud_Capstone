Fraud Detector (Django + Isolation Forest)

Live demo: https://fraud-capstone-web.onrender.com

UI: / • History: /history/ • (optional) Docs: /docs/

git clone https://github.com/<you>/<repo>.git
cd <repo>

python -m venv .venv
# Windows: .\.venv\Scripts\Activate.ps1
# macOS/Linux: source .venv/bin/activate

pip install -U pip && pip install -r requirements.txt

# Put your model here:
# ./models/best_v1.joblib  (scikit-learn Pipeline)

python manage.py migrate
python manage.py runserver 127.0.0.1:8000


Open:

UI: http://127.0.0.1:8000/

History: http://127.0.0.1:8000/history/

API (POST /api/predict)

Request (JSON):

{
  "Time": 15232,
  "V1": -0.4347, "V2": -0.5361, "V3": -0.2355,
  "V4": -0.5195, "V5": 0.5822, "V6": 0.514, "V7": -0.464,
  "V8": 0.6017, "V9": -0.0552, "V10": -0.0703, "V11": 0.3502,
  "V12": -0.2672, "V13": 0.9162, "V14": -0.3858, "V15": 1.0431,
  "V16": 0.4525, "V17": -0.2311, "V18": 0.2692, "V19": -0.9576,
  "V20": -0.6014, "V21": -0.6053, "V22": -0.2813, "V23": 0.6608,
  "V24": -0.2996, "V25": 0.2954, "V26": -0.7845, "V27": -1.0184,
  "V28": -0.3506, "Amount": 45.05
}


Response:

{
  "is_fraud": true,
  "risk": "FRAUD",
  "confidence": 0.44,
  "anomaly_score": -0.228,
  "pseudo_probability": 0.44,
  "model_name": "IsolationForest",
  "version": "best_v1"
}

cURL:
curl -s -X POST http://127.0.0.1:8000/api/predict \
  -H "Content-Type: application/json" \
  -d @sample.json

Update the Model

Replace ./models/best_v1.joblib with your latest artifact (sklearn Pipeline). Restart the server.

Troubleshooting

Model missing → ensure ./models/best_v1.joblib exists.

Connection refused → start server: python manage.py runserver 127.0.0.1:8000.

Windows script blocked → PowerShell:
Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned -Force.

Deploy (Render)

Build:
pip install -r requirements.txt && python manage.py collectstatic --noinput && python manage.py migrate
Start:
gunicorn fraudsite.wsgi:application --bind 0.0.0.0:$PORT
Set env: ALLOWED_HOSTS, CSRF_TRUSTED_ORIGINS, DJANGO_SECRET_KEY, DEBUG=0.