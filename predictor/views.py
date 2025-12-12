# predictor/views.py
import json
import logging
from pathlib import Path

import joblib
import numpy as np
from django.http import JsonResponse
from django.shortcuts import render, redirect
from django.views.decorators.csrf import csrf_protect, ensure_csrf_cookie
from django.views.decorators.http import require_POST
from django.contrib.auth import login
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.decorators import login_required

from .models import Submission

logger = logging.getLogger(__name__)

# ---------------------------
# Docs page (static template)
# ---------------------------
def docs_view(request):
    return render(request, "docs.html")


# ---------------------------
# Load model once
# ---------------------------
MODEL_PATH = Path(__file__).resolve().parents[1] / "models" / "best_v1.joblib"
BUNDLE = joblib.load(MODEL_PATH)     # expects keys: pipeline, features, (optional) model_name, version
PIPE = BUNDLE["pipeline"]
FEATURES = BUNDLE["features"]


# ---------------------------
# Helpers
# ---------------------------
def validate_payload(data: dict):
    """
    Ensure all expected FEATURES are present and numeric.
    Returns (clean_dict, list_of_error_messages)
    """
    errors = []
    clean = {}
    for f in FEATURES:
        if f not in data:
            errors.append(f"Missing field: {f}")
            continue
        try:
            clean[f] = float(data[f])
        except (ValueError, TypeError):
            errors.append(f"Field '{f}' must be numeric")
    return clean, errors


def _predict_one(payload: dict):
    """
    Run the preloaded pipeline on one sample (dict of feature->value).
    Returns (result_dict, http_status).
    """
    # verify nothing is missing (extra safety — validate_payload should have covered this)
    missing = [f for f in FEATURES if f not in payload]
    if missing:
        return {"error": f"Missing fields: {missing}"}, 400

    try:
        x = np.array([[float(payload[f]) for f in FEATURES]], dtype=float)
    except Exception:
        return {"error": "All feature values must be numeric."}, 400

    # split scaler + final estimator when present
    steps = dict(PIPE.named_steps)
    Xs = steps["scaler"].transform(x) if "scaler" in steps else x
    clf = list(PIPE.named_steps.values())[-1]

    # anomaly decision
    yp = clf.predict(Xs)
    
    # Fix: IsolationForest/Anomaly Detectors return -1 for outliers (Fraud) and 1 for inliers (Normal)
    if clf.__class__.__name__ == "IsolationForest" or (hasattr(clf, "classes_") and -1 in clf.classes_):
        is_fraud = bool(yp[0] == -1)
    else:
        # Standard binary classification (1 = Fraud)
        is_fraud = bool(yp[0] == 1)

    # anomaly score (normalized to "higher=worse")
    if hasattr(clf, "decision_function"):
        score = float(clf.decision_function(Xs)[0])
        # IsolationForest convention: more negative = more anomalous → flip sign
        if clf.__class__.__name__ == "IsolationForest":
            score = -score
    elif hasattr(clf, "score_samples"):
        score = float(-clf.score_samples(Xs)[0])
    else:
        score = 1.0 if is_fraud else 0.0

    # pseudo-probability + confidence
    prob = float(1 / (1 + np.exp(-score)))
    confidence = prob if is_fraud else (1 - prob)
    risk = "FRAUD" if is_fraud else "OK"

    return {
        "is_fraud": is_fraud,
        "risk": risk,
        "confidence": confidence,
        "anomaly_score": score,
        "pseudo_probability": prob,
        "model_name": BUNDLE.get("model_name", "IsolationForest"),
        "version": BUNDLE.get("version", "best_v1"),
    }, 200


# ---------------------------
# API: /api/predict  (POST JSON)
# ---------------------------
@csrf_protect
@require_POST
def predict_view(request):
    # 1) Parse JSON (clear error if truly invalid JSON)
    try:
        raw = (request.body or b"").decode("utf-8")
        data = json.loads(raw)
    except json.JSONDecodeError as e:
        return JsonResponse({"error": "Invalid JSON body.", "detail": str(e)}, status=400)

    # 2) Validate fields (show exactly what's wrong)
    clean, errs = validate_payload(data)
    if errs:
        return JsonResponse({"errors": errs}, status=400)

    # 3) Predict
    result, code = _predict_one(clean)
    if code != 200:
        return JsonResponse(result, status=code)

    # 4) Best-effort: save the submission (don't break API if DB insert fails)
    try:
        Submission.objects.create(
            user=request.user if request.user.is_authenticated else None,
            is_fraud=bool(result.get("is_fraud", False)),
            anomaly_score=float(result.get("anomaly_score", 0.0)),
            pseudo_probability=float(result.get("pseudo_probability", 0.0)),
            model_name=str(result.get("model_name", "IsolationForest")),
            version=str(result.get("version", "best_v1")),
            input=json.dumps(clean, separators=(",", ":"), sort_keys=True, ensure_ascii=False),
        )
    except Exception as e:
        logger.exception("Failed to save Submission: %s", e)

    return JsonResponse(result, status=200)


# ---------------------------
# UI: form + history + signup + health
# ---------------------------
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
    return JsonResponse({"status": "ok"}, status=200)
