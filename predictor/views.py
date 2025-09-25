import json
from pathlib import Path

import joblib, numpy as np
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login
from django.shortcuts import redirect
import json  

from django.views.decorators.csrf import ensure_csrf_cookie
from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.views.decorators.csrf import ensure_csrf_cookie, csrf_protect
from django.utils.timezone import now
from django.db import connection

from django.shortcuts import render

def docs_view(request):
    return render(request, "docs.html")

# ... other imports






from .models import Submission  # <-- history uses this

# ---- load model once ----
MODEL_PATH = Path(__file__).resolve().parents[1] / "models" / "best_v1.joblib"
BUNDLE = joblib.load(MODEL_PATH)
PIPE = BUNDLE["pipeline"]
FEATURES = BUNDLE["features"]

def validate_payload(data):
    errors = []
    clean = {}
    for field in FEATURES:
        if field not in data:
            errors.append(f"Missing field: {field}")
        else:
            try:
                clean[field] = float(data[field])
            except (ValueError, TypeError):
                errors.append(f"Field '{field}' must be numeric")
    return clean, errors

def _predict_one(payload: dict):
    missing = [f for f in FEATURES if f not in payload]
    if missing:
        return {"error": f"Missing fields: {missing}"}, 400

    try:
        x = np.array([[float(payload[f]) for f in FEATURES]], dtype=float)
    except Exception:
        return {"error": "All feature values must be numeric."}, 400

    steps = dict(PIPE.named_steps)
    Xs = steps["scaler"].transform(x) if "scaler" in steps else x
    clf = list(PIPE.named_steps.values())[-1]

    yp = clf.predict(Xs)
    is_fraud = bool(yp[0] == -1) if set(np.unique(yp)) == {-1, 1} else bool(yp[0] == 1)

    if hasattr(clf, "decision_function"):
        score = float(clf.decision_function(Xs)[0])
        if clf.__class__.__name__ == "IsolationForest":
            score = -score
    elif hasattr(clf, "score_samples"):
        score = float(-clf.score_samples(Xs)[0])
    else:
        score = 1.0 if is_fraud else 0.0

    prob = float(1 / (1 + np.exp(-score)))
    confidence = prob if is_fraud else (1 - prob)
    risk = "FRAUD" if is_fraud else "OK"

    return {
        "is_fraud": is_fraud,
        "risk": risk,
        "confidence": confidence,
        "anomaly_score": score,
        "pseudo_probability": prob,
        "model_name": BUNDLE.get("model_name", "unknown"),
        "version": BUNDLE.get("version", "best_v1"),
    }, 200

@csrf_protect
def predict_view(request):
    if request.method != "POST":
        return JsonResponse({"detail": "POST JSON to this endpoint."}, status=405)
    
    try:
        data = json.loads(request.body.decode("utf-8"))
        clean, errs = validate_payload(data)
        if errs:
            return JsonResponse({"errors": errs}, status=400)

        result, code = _predict_one(clean)
        
        if code == 200:
            is_fraud = bool(result.get("is_fraud", False))
            anomaly_score = float(result.get("anomaly_score", 0.0))
            pseudo_probability = float(result.get("pseudo_probability", 0.0))
            model_name = str(result.get("model_name", "IsolationForest"))
            version = str(result.get("version", "best_v1"))

            input_json_string = json.dumps(clean, separators=(",", ":"), sort_keys=True, ensure_ascii=False)

            Submission.objects.create(
                user=request.user if request.user.is_authenticated else None,
                is_fraud=is_fraud,
                anomaly_score=anomaly_score,
                pseudo_probability=pseudo_probability,
                model_name=model_name,
                version=version,
                input=input_json_string,
            )
        
        return JsonResponse(result, status=code)
        
    except Exception:
        return JsonResponse({"error": "Invalid JSON body."}, status=400)
    

@ensure_csrf_cookie
@login_required
def form_view(request):
    return render(request, "predictor/form.html", {"features": FEATURES})

@login_required
def history_view(request):
    rows = Submission.objects.order_by("-created_at")[:100]
    return render(request, "predictor/history.html", {"rows": rows})

def signup_view(request):
    if request.method == "POST":
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect("home")
    else:
        form = UserCreationForm()
    return render(request, "registration/signup.html", {"form": form})

def health_view(request):
    db_ok = False
    try:
        with connection.cursor() as cur:
            cur.execute("SELECT 1;")
            db_ok = True
    except Exception:
        db_ok = False

    return JsonResponse({
        "status": "ok" if db_ok else "degraded",
        "db_ok": db_ok,
        "time": now().isoformat(),
        "version": "v1"
    }, status=200 if db_ok else 503)