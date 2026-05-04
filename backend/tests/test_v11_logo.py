"""Iter-11 logo integration tests.

Validates:
  - email_service _LOGO_URL embeds white logo in render_order_confirmation HTML
    (header + footer occurrences)
  - Logo asset URLs (white/gold) are reachable (HTTP 200, non-empty body)
  - Regression: GET /api/products, POST /api/orders, payment endpoints respond
"""
import os
import sys
import pytest
import requests

# Allow importing backend modules
sys.path.insert(0, "/app/backend")

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "").rstrip("/")
if not BASE_URL:
    # Read from frontend .env as fallback (per system rules use REACT_APP_BACKEND_URL)
    with open("/app/frontend/.env") as f:
        for line in f:
            if line.startswith("REACT_APP_BACKEND_URL="):
                BASE_URL = line.split("=", 1)[1].strip().rstrip("/")
                break

WHITE_LOGO = "https://customer-assets.emergentagent.com/job_coral-product-hub/artifacts/5gz4ojsf_Logo%20Transparant%20%284%29.png"
GOLD_LOGO = "https://customer-assets.emergentagent.com/job_coral-product-hub/artifacts/qiztl9hf_Logo%20Transparant%20%283%29.png"


# === Logo asset reachability ===
class TestLogoAssets:
    def test_white_logo_reachable(self):
        r = requests.get(WHITE_LOGO, timeout=10)
        assert r.status_code == 200
        assert len(r.content) > 1000
        assert r.headers.get("content-type", "").startswith("image/")

    def test_gold_logo_reachable(self):
        r = requests.get(GOLD_LOGO, timeout=10)
        assert r.status_code == 200
        assert len(r.content) > 1000
        assert r.headers.get("content-type", "").startswith("image/")


# === Email template logo embed ===
class TestEmailLogoEmbed:
    def test_order_confirmation_contains_logo(self):
        from email_service import render_order_confirmation, _LOGO_URL
        assert "5gz4ojsf" in _LOGO_URL
        order = {
            "order_number": "TEST-LOGO-001",
            "contact": {"name": "Test User", "email": "x@y.z", "phone": "0812345", "address": "addr", "city": "Jakarta"},
            "items": [{"name": "Rotifer", "quantity": 1, "price": 100000, "line_total": 100000}],
            "subtotal": 100000, "shipping": 0, "discount": 0, "total": 100000,
        }
        html = render_order_confirmation(order)
        # Header + footer logo => 2 occurrences
        assert html.count(_LOGO_URL) >= 2
        assert 'alt="Rimpods"' in html

    def test_payment_success_contains_logo(self):
        from email_service import render_payment_success, _LOGO_URL
        order = {"order_number": "T1", "contact": {"name": "A"}, "items": [], "subtotal": 0, "shipping": 0, "discount": 0, "total": 0, "payment_type": "qris"}
        html = render_payment_success(order)
        assert _LOGO_URL in html


# === index.html meta tags ===
class TestIndexMeta:
    def test_index_html_has_logo_meta(self):
        with open("/app/frontend/public/index.html") as f:
            html = f.read()
        assert 'qiztl9hf' in html  # og:image gold
        assert '5gz4ojsf' in html  # favicon white
        assert 'Rimpods — Tank yang hidup, bukan sekadar indah' in html
        assert 'og:image' in html and 'twitter:image' in html
        assert 'rel="icon"' in html
        assert 'apple-touch-icon' in html


# === Regression: backend endpoints ===
class TestBackendRegression:
    def test_products(self):
        r = requests.get(f"{BASE_URL}/api/products", timeout=10)
        assert r.status_code == 200
        data = r.json()
        assert "products" in data
        assert len(data["products"]) > 0

    def test_create_order(self):
        payload = {
            "items": [{"product_id": "rotifer-2l-phyto", "quantity": 1}],
            "contact": {"name": "TEST_iter11 User", "email": "test@example.com", "phone": "081234567890",
                        "address": "Jl Test", "city": "Jakarta", "notes": "TEST_iter11"},
            "payment_channel": "midtrans",
        }
        r = requests.post(f"{BASE_URL}/api/orders", json=payload, timeout=15)
        assert r.status_code in (200, 201), f"unexpected {r.status_code}: {r.text[:200]}"
        data = r.json()
        assert "order_number" in data or "id" in data or data.get("ok") is True

    def test_midtrans_snap_token_endpoint_exists(self):
        # Just check endpoint reachable (will fail validation with empty body, that's fine)
        r = requests.post(f"{BASE_URL}/api/payment/midtrans/snap-token", json={}, timeout=10)
        assert r.status_code in (200, 400, 422, 500)  # endpoint exists, not 404

    def test_midtrans_notification_endpoint_exists(self):
        r = requests.post(f"{BASE_URL}/api/payment/midtrans/notification", json={}, timeout=10)
        assert r.status_code in (200, 400, 422, 500)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
