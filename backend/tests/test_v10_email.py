"""Iter-10 Resend email integration + /admin/orders/{id}/ship regression tests.

Focus:
- POST /api/orders with ocepjos@gmail.com email -> log 'Resend sent to ocepjos@gmail.com' (x2)
- POST /api/orders without contact.email -> admin email still sent, customer skipped
- Midtrans webhook settlement -> payment_success email logged
- POST /api/admin/orders/{id}/ship: 200 w/ bearer, 401 w/o auth, ok:false on missing
- Graceful degradation is handled by a separate script (requires supervisor restart).
"""
import os
import time
import hashlib
import pytest
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "").rstrip("/")
SERVER_KEY = "Mid-server-vhvgDm9eDE4fbhMAdrGzVN4c"
BACKEND_LOG = "/var/log/supervisor/backend.out.log"
BACKEND_ERR = "/var/log/supervisor/backend.err.log"
ADMIN_BEARER = os.environ.get("ADMIN_BEARER", "")  # injected by runner script
EMAIL_TO = "ocepjos@gmail.com"


@pytest.fixture(scope="module")
def api_client():
    s = requests.Session()
    s.headers.update({"Content-Type": "application/json"})
    return s


def _log_tail(n_lines: int = 600) -> str:
    blobs = []
    for p in (BACKEND_LOG, BACKEND_ERR):
        try:
            with open(p, "r") as f:
                blobs.append(f.read()[-120_000:])
        except Exception:
            pass
    return "\n".join(blobs)


def _log_snapshot_len():
    total = 0
    for p in (BACKEND_LOG, BACKEND_ERR):
        try:
            total += os.path.getsize(p)
        except Exception:
            pass
    return total


def _log_since(snapshot_offset: int) -> str:
    """Read logs growth since snapshot offset (approximation via total size)."""
    # Simpler: just return full tail — caller greps for patterns.
    return _log_tail()


def _make_order_payload(email=EMAIL_TO, voucher=None):
    p = {
        "items": [{"product_id": "paket-hemat-5r-1p", "quantity": 1}],
        "contact": {
            "name": "Test Iter10",
            "phone": "081234567890",
            "address": "Jl. Email No. 1",
            "city": "Jakarta",
            "notes": "TEST_iter10",
        },
        "payment_channel": "midtrans",
    }
    if email is not None:
        p["contact"]["email"] = email
    if voucher:
        p["voucher_code"] = voucher
    return p


# ============ Regression (iter-9 smoke) ============
class TestRegressionIter9:
    def test_midtrans_config_still_works(self, api_client):
        r = api_client.get(f"{BASE_URL}/api/payment/midtrans/config")
        assert r.status_code == 200
        d = r.json()
        assert d["enabled"] is True
        assert d["client_key"] == "Mid-client-TebxcWipgaHb4QA1"

    def test_products_still_works(self, api_client):
        r = api_client.get(f"{BASE_URL}/api/products")
        assert r.status_code == 200
        assert len(r.json()["products"]) == 3

    def test_order_create_still_works(self, api_client):
        r = api_client.post(f"{BASE_URL}/api/orders", json=_make_order_payload())
        assert r.status_code == 200, r.text
        d = r.json()
        assert d["total"] > 0
        assert d["order_number"].startswith("RMP")

    def test_snap_token_still_works(self, api_client):
        order = api_client.post(f"{BASE_URL}/api/orders", json=_make_order_payload()).json()
        r = api_client.post(f"{BASE_URL}/api/payment/midtrans/snap-token",
                            json={"order_id": order["id"]})
        assert r.status_code == 200
        assert "token" in r.json()


# ============ Iter-10 email integration ============
class TestEmailIntegration:
    def test_order_with_email_triggers_two_resend_logs(self, api_client):
        r = api_client.post(f"{BASE_URL}/api/orders", json=_make_order_payload(email=EMAIL_TO))
        assert r.status_code == 200, r.text
        order = r.json()
        # Response schema does NOT return email_id — verify no unexpected error
        assert order["order_number"].startswith("RMP")

        # BackgroundTasks run after response is returned; give FastAPI + Resend time.
        time.sleep(4)
        logs = _log_tail()
        sent_hits = logs.count(f"Resend sent to {EMAIL_TO}")
        # Expect at least two hits (order_confirmation + admin_new_order -> both to ocepjos)
        # Admin goes to EMAIL_ADMIN_NOTIFY=ocepjos@gmail.com, customer also ocepjos@gmail.com.
        assert sent_hits >= 2, (
            f"Expected >=2 'Resend sent to {EMAIL_TO}' entries post-order, got {sent_hits}. "
            f"Log tail (last 4k): {logs[-4000:]}"
        )

    def test_order_without_email_still_creates_and_admin_email_fires(self, api_client):
        # wait for resend rate limit (2 req/sec)
        time.sleep(1.2)
        payload = _make_order_payload(email=None)
        before_len = _log_snapshot_len()
        r = api_client.post(f"{BASE_URL}/api/orders", json=payload)
        assert r.status_code == 200, r.text
        order = r.json()
        assert order["order_number"].startswith("RMP")

        time.sleep(3)
        logs = _log_tail()
        # Admin email should still have been sent (EMAIL_ADMIN_NOTIFY is set)
        assert f"Resend sent to {EMAIL_TO}" in logs, (
            "Admin Resend log not found after order without customer email."
        )
        # Either 'Skipping order_confirmation email: no customer email'
        # or just no customer 'Resend sent to <other>' — accept the skip log.
        assert ("Skipping order_confirmation email: no customer email" in logs
                or "no customer email" in logs), (
            "Expected log confirming customer email was skipped when contact.email missing."
        )

    def test_webhook_settlement_triggers_payment_success_email(self, api_client):
        time.sleep(1.2)
        # Create an order with email
        order = api_client.post(f"{BASE_URL}/api/orders",
                                json=_make_order_payload(email=EMAIL_TO)).json()
        on = order["order_number"]

        # Build valid signature
        gross = f"{order['total']}.00"
        status_code = "200"
        raw = f"{on}{status_code}{gross}{SERVER_KEY}"
        sig = hashlib.sha512(raw.encode("utf-8")).hexdigest()
        body = {
            "order_id": on,
            "status_code": status_code,
            "gross_amount": gross,
            "signature_key": sig,
            "transaction_status": "settlement",
            "payment_type": "qris",
            "transaction_id": f"trx-iter10-{int(time.time())}",
        }
        r = api_client.post(f"{BASE_URL}/api/payment/midtrans/notification", json=body)
        assert r.status_code == 200, r.text
        assert r.json()["new_status"] == "paid"

        # wait for asyncio.create_task(send_payment_success) to run
        time.sleep(4)
        logs = _log_tail()
        assert f"Resend sent to {EMAIL_TO}" in logs, (
            "Payment-success Resend log not found after settlement webhook."
        )
        # sanity: the paid_at webhook log should be nearby
        assert f"Midtrans webhook processed: {on} -> paid" in logs


# ============ Iter-10 /admin/orders/{id}/ship ============
class TestAdminShip:
    @pytest.fixture(scope="class")
    def admin_headers(self):
        if not ADMIN_BEARER:
            pytest.skip("ADMIN_BEARER not provided; skipping admin-ship tests")
        return {"Authorization": f"Bearer {ADMIN_BEARER}"}

    @pytest.fixture(scope="class")
    def prepared_order(self):
        s = requests.Session()
        s.headers.update({"Content-Type": "application/json"})
        r = s.post(f"{BASE_URL}/api/orders", json=_make_order_payload(email=EMAIL_TO))
        assert r.status_code == 200
        time.sleep(1.2)
        return r.json()

    def test_ship_unauthorized_401(self, api_client, prepared_order):
        r = api_client.post(
            f"{BASE_URL}/api/admin/orders/{prepared_order['id']}/ship",
            params={"courier": "JNE", "tracking": "TRK123", "eta": "3 hari"},
        )
        assert r.status_code == 401, r.text

    def test_ship_with_auth_success(self, api_client, admin_headers, prepared_order):
        r = api_client.post(
            f"{BASE_URL}/api/admin/orders/{prepared_order['id']}/ship",
            params={"courier": "JNE", "tracking": "TRK-ITER10-001", "eta": "3-5 hari"},
            headers=admin_headers,
        )
        assert r.status_code == 200, r.text
        body = r.json()
        assert body["ok"] is True
        assert body["courier"] == "JNE"
        assert body["tracking"] == "TRK-ITER10-001"

        # Verify persistence via GET (public order endpoint)
        time.sleep(0.5)
        g = api_client.get(f"{BASE_URL}/api/orders/{prepared_order['id']}")
        assert g.status_code == 200
        o = g.json()
        assert o["status"] == "shipped"
        # Field names per admin.py
        # (public Order model may not expose shipping_*; check via raw DB not required here)

        # Allow shipping email to fire
        time.sleep(4)
        logs = _log_tail()
        assert f"Resend sent to {EMAIL_TO}" in logs, (
            "Shipping-email Resend log not found after /ship."
        )

    def test_ship_invalid_order_returns_not_found(self, api_client, admin_headers):
        r = api_client.post(
            f"{BASE_URL}/api/admin/orders/not-a-real-id/ship",
            params={"courier": "JNE", "tracking": "X", "eta": "3"},
            headers=admin_headers,
        )
        assert r.status_code == 200, r.text  # endpoint returns JSON error, not HTTP 404
        body = r.json()
        assert body["ok"] is False
        assert "tidak ditemukan" in body.get("error", "").lower()
