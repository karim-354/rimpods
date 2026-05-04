"""Iter-9 Midtrans Snap integration regression tests.

Covers:
- /api/payment/midtrans/config
- /api/payment/midtrans/snap-token (valid + 404)
- /api/payment/midtrans/notification (signature ok / mismatch / status mapping)
- /api/payment/midtrans/status/{order_number}
- Product price update for paket-hemat-5r-1p
- Smoke regression for /api/products and /api/orders
"""
import os
import hashlib
import pytest
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "https://coral-product-hub.preview.emergentagent.com").rstrip("/")
SERVER_KEY = "Mid-server-vhvgDm9eDE4fbhMAdrGzVN4c"


@pytest.fixture(scope="module")
def api_client():
    s = requests.Session()
    s.headers.update({"Content-Type": "application/json"})
    return s


# ============ Config ============
class TestMidtransConfig:
    def test_config_enabled(self, api_client):
        r = api_client.get(f"{BASE_URL}/api/payment/midtrans/config")
        assert r.status_code == 200, r.text
        d = r.json()
        assert d["enabled"] is True
        assert d["client_key"] == "Mid-client-TebxcWipgaHb4QA1"
        assert d["is_production"] is False
        assert d["merchant_id"] == "M321126389"


# ============ Product update ============
class TestPaketHematPrice:
    def test_paket_hemat_price(self, api_client):
        r = api_client.get(f"{BASE_URL}/api/products/paket-hemat-5r-1p")
        assert r.status_code == 200, r.text
        p = r.json()
        assert p["price"] == 99999
        assert p["compare_price"] == 129999
        assert p["reviews"] == 2198
        assert p["sold"] == "3rb+"
        assert any("BONUS" in h for h in p["highlights"])
        assert any("4 botol Rotifer" in h and "1 botol Phytoplankton" in h for h in p["highlights"])

    def test_products_count(self, api_client):
        r = api_client.get(f"{BASE_URL}/api/products")
        assert r.status_code == 200
        d = r.json()
        assert len(d["products"]) == 3


# ============ Helpers ============
def _make_order(api_client, items=None, voucher=None, channel="midtrans"):
    if items is None:
        items = [{"product_id": "paket-hemat-5r-1p", "quantity": 2}]
    payload = {
        "items": items,
        "contact": {
            "name": "Test Pelanggan",
            "phone": "081234567890",
            "email": "test@example.com",
            "address": "Jl. Coba No. 1",
            "city": "Jakarta",
            "notes": "TEST_iter9",
        },
        "payment_channel": channel,
    }
    if voucher:
        payload["voucher_code"] = voucher
    r = api_client.post(f"{BASE_URL}/api/orders", json=payload)
    assert r.status_code == 200, r.text
    return r.json()


# ============ Snap token ============
class TestSnapToken:
    def test_snap_token_valid(self, api_client):
        order = _make_order(api_client)
        r = api_client.post(
            f"{BASE_URL}/api/payment/midtrans/snap-token", json={"order_id": order["id"]}
        )
        assert r.status_code == 200, r.text
        d = r.json()
        assert "token" in d and isinstance(d["token"], str) and len(d["token"]) > 0
        assert "redirect_url" in d and d["redirect_url"].startswith("http")
        assert d["order_number"] == order["order_number"]

        # Verify persistence
        g = api_client.get(f"{BASE_URL}/api/payment/midtrans/status/{order['order_number']}")
        assert g.status_code == 200
        # status is still pending until webhook
        assert g.json()["status"] in ("pending",)

    def test_snap_token_invalid_order(self, api_client):
        r = api_client.post(
            f"{BASE_URL}/api/payment/midtrans/snap-token",
            json={"order_id": "nonexistent-uuid-xxxx"},
        )
        assert r.status_code == 404


# ============ Notification webhook ============
def _signature(order_id: str, status_code: str, gross_amount: str) -> str:
    raw = f"{order_id}{status_code}{gross_amount}{SERVER_KEY}"
    return hashlib.sha512(raw.encode("utf-8")).hexdigest()


class TestWebhookNotification:
    @pytest.fixture(scope="class")
    def fresh_order(self):
        # local session for class
        s = requests.Session()
        s.headers.update({"Content-Type": "application/json"})
        return _make_order(s)

    def _post_notif(self, api_client, order_number, trx_status, status_code="200",
                    gross_amount=None, signature_override=None, fraud=None):
        if gross_amount is None:
            gross_amount = "217998.00"  # not strictly checked by backend; signature uses string as-is
        sig = signature_override or _signature(order_number, status_code, gross_amount)
        body = {
            "order_id": order_number,
            "status_code": status_code,
            "gross_amount": gross_amount,
            "signature_key": sig,
            "transaction_status": trx_status,
            "payment_type": "qris",
            "transaction_id": f"trx-{trx_status}",
        }
        if fraud:
            body["fraud_status"] = fraud
        return api_client.post(f"{BASE_URL}/api/payment/midtrans/notification", json=body)

    def test_signature_mismatch(self, api_client, fresh_order):
        r = self._post_notif(api_client, fresh_order["order_number"], "settlement",
                             signature_override="deadbeef")
        assert r.status_code == 200
        assert r.json()["status"] == "signature_mismatch"
        # Order status MUST NOT change
        g = api_client.get(f"{BASE_URL}/api/payment/midtrans/status/{fresh_order['order_number']}")
        assert g.json()["status"] == "pending"

    def test_settlement_paid(self, api_client, fresh_order):
        r = self._post_notif(api_client, fresh_order["order_number"], "settlement")
        assert r.status_code == 200, r.text
        assert r.json()["status"] == "ok"
        assert r.json()["new_status"] == "paid"
        g = api_client.get(f"{BASE_URL}/api/payment/midtrans/status/{fresh_order['order_number']}")
        assert g.status_code == 200
        d = g.json()
        assert d["status"] == "paid"
        assert d["midtrans_transaction_status"] == "settlement"

    def test_pending_status(self, api_client):
        order = _make_order(api_client)
        r = self._post_notif(api_client, order["order_number"], "pending")
        assert r.json()["new_status"] == "pending"

    def test_deny_failed(self, api_client):
        order = _make_order(api_client)
        r = self._post_notif(api_client, order["order_number"], "deny")
        assert r.json()["new_status"] == "failed"

    def test_cancel_cancelled(self, api_client):
        order = _make_order(api_client)
        r = self._post_notif(api_client, order["order_number"], "cancel")
        assert r.json()["new_status"] == "cancelled"

    def test_expire_expired(self, api_client):
        order = _make_order(api_client)
        r = self._post_notif(api_client, order["order_number"], "expire")
        assert r.json()["new_status"] == "expired"


# ============ Status endpoint ============
class TestStatusEndpoint:
    def test_status_404(self, api_client):
        r = api_client.get(f"{BASE_URL}/api/payment/midtrans/status/RMP-NOTEXIST")
        assert r.status_code == 404


# ============ Regression ============
class TestRegression:
    def test_voucher_and_bundle_in_order(self, api_client):
        # Bundle: 'tbn-turn-back-nutrients-bundle' = 199000 * 0.9 = 179100
        # plus paket: 99999 * 2 = 199998 ; subtotal = 379098 -> shipping 0
        # voucher FIRSTBUY20K -> -20000 ; total = 359098
        items = [
            {"product_id": "tbn-turn-back-nutrients-bundle", "quantity": 1},
            {"product_id": "paket-hemat-5r-1p", "quantity": 2},
        ]
        order = _make_order(api_client, items=items, voucher="FIRSTBUY20K")
        assert order["voucher_code"] == "FIRSTBUY20K"
        assert order["discount"] == 20000
        # bundle line check
        bundle_item = next(i for i in order["items"] if i["is_bundle"])
        assert bundle_item["price"] == 179100
        assert order["shipping"] == 0

    def test_root(self, api_client):
        r = api_client.get(f"{BASE_URL}/api/")
        assert r.status_code == 200
        assert r.json()["status"] == "ok"
