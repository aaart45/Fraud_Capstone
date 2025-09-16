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



from .models import Submission  # <-- history uses this

# ---- load model once ----
MODEL_PATH = Path(__file__).resolve().parents[1] / "models" / "best_v1.joblib"
BUNDLE = joblib.load(MODEL_PATH)
PIPE = BUNDLE["pipeline"]
FEATURES = BUNDLE["features"]

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

@csrf_exempt
def predict_view(request):
    if request.method != "POST":
        return JsonResponse({"detail": "POST JSON to this endpoint."}, status=405)
    try:
        data = json.loads(request.body.decode("utf-8"))
    except Exception:
        return JsonResponse({"error": "Invalid JSON body."}, status=400)

    result, code = _predict_one(data)

    if code == 200:
        Submission.objects.create(
            input_json=data,
            is_fraud=result["is_fraud"],
            risk=result["risk"],
            confidence=result["confidence"],
            anomaly_score=result["anomaly_score"],
            model_name=result["model_name"],
            version=result["version"],
        )
    return JsonResponse(result, status=code)

def form_view(request):
    return render(request, "predictor/form.html", {"features": FEATURES})

def history_view(request):        # <-- THIS is what urls.py imports
    rows = Submission.objects.order_by("-created_at")[:100]
    return render(request, "predictor/history.html", {"rows": rows})
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
            login(request, user)      # auto-login after signup
            return redirect("home")
    else:
        form = UserCreationForm()
    return render(request, "registration/signup.html", {"form": form})

