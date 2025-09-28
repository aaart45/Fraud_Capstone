import json
from django.test import Client, override_settings
from django.urls import reverse

def _make_payload():
    d = {"Time": 12345, "Amount": 50.25}
    for i in range(1, 29):
        d[f"V{i}"] = 0.0
    return d

@override_settings(CSRF_COOKIE_SECURE=False)  # allow CSRF cookie over http in tests
def test_predict_ok():
    c = Client()

    # 1) Prime a CSRF cookie. Any page that passes through CsrfViewMiddleware works.
    # If you have 'home' or 'login', either is fine:
    c.get(reverse("login"))  # or: c.get(reverse("home"))

    csrf = c.cookies.get("csrftoken")
    assert csrf, "No csrftoken cookie; make sure CsrfViewMiddleware is enabled"
    csrf = csrf.value

    # 2) Resolve the correct URL name used in urls.py
    url = reverse("api-predict")  # should be /api/predict/

    # 3) Send raw JSON bytes with proper content-type + CSRF header
    payload = _make_payload()
    r = c.generic(
        "POST",
        url,
        json.dumps(payload).encode("utf-8"),
        content_type="application/json",
        HTTP_X_CSRFTOKEN=csrf,
        HTTP_REFERER="http://testserver/",  # harmless, helps CSRF in some setups
    )

    assert r.status_code == 200, f"status={r.status_code}, body={r.content!r}"
    j = r.json()
    assert "is_fraud" in j and "model_name" in j
