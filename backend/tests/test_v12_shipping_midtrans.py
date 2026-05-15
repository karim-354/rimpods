"""Iteration 12 — Paid 3-courier shipping + Midtrans production key tests.

Covers:
- /api/payment/midtrans/config returns production keys
- /api/shipping/rates for zones 1-4 and default
- /api/orders honors shipping_courier and includes courier line in WhatsApp URL
- Regression: voucher FIRSTBUY20K, bundle suffix
"""
import os
import urllib.parse
import pytest
import requests

BASE_URL = os.environ["REACT_APP_BACKEND_URL"].rstrip("/") if os.environ.get("REACT_APP_BACKEND_URL") else "https://coral-product-hub.preview.emergentagent.com"
API = f"{BASE_URL}/api"


@pytest.fixture(scope="module")
def session():
    s = requests.Session()
    s.headers.update({"Content-Type": "application/json"})
    return s


# === Midtrans config ===
class TestMidtransConfig:
    def test_config_production(self, session):
        r = session.get(f"{API}/payment/midtrans/config")
        assert r.status_code == 200, r.text
        data = r.json()
        assert data.get("enabled") is True
        assert data.get("client_key") == "Mid-client-E0IGvMibArVXfy3U"
        assert data.get("is_production") is True
        assert data.get("merchant_id") == "M321126389"


# === Shipping rates per zone ===
class TestShippingRates:
    def _get(self, session, **params):
        r = session.get(f"{API}/shipping/rates", params=params)
        assert r.status_code == 200, r.text
        return r.json()

    def test_zone1_jakarta(self, session):
        d = self._get(session, city="Jakarta")
        assert d["zone"] == 1
        rates = {r["courier"]: r for r in d["rates"]}
        assert len(d["rates"]) == 3
        assert rates["Paxel"]["cost"] == 25000
        assert rates["Paxel"]["service"] == "Same Day"
        assert rates["JNT"]["cost"] == 15000
        assert rates["Tiki"]["cost"] == 16000

    def test_zone2_surabaya(self, session):
        d = self._get(session, city="Surabaya")
        assert d["zone"] == 2
        rates = {r["courier"]: r for r in d["rates"]}
        assert rates["Paxel"]["cost"] == 45000
        assert rates["JNT"]["cost"] == 25000
        assert rates["Tiki"]["cost"] == 27000

    def test_zone3_denpasar(self, session):
        d = self._get(session, city="Denpasar")
        assert d["zone"] == 3
        rates = {r["courier"]: r for r in d["rates"]}
        assert rates["Paxel"]["cost"] == 70000
        assert rates["JNT"]["cost"] == 45000
        assert rates["Tiki"]["cost"] == 48000

    def test_zone4_jayapura(self, session):
        d = self._get(session, city="Jayapura")
        assert d["zone"] == 4
        rates = {r["courier"]: r for r in d["rates"]}
        assert rates["Paxel"]["cost"] == 100000
        assert rates["JNT"]["cost"] == 70000
        assert rates["Tiki"]["cost"] == 75000

    def test_no_city_defaults_zone3(self, session):
        d = self._get(session)
        assert d["zone"] == 3
        assert len(d["rates"]) == 3


# === Order creation with shipping_courier ===
class TestOrderShipping:
    def _contact(self, city="Jakarta", kecamatan="Setiabudi"):
        return {
            "name": "TEST_Buyer",
            "phone": "081234567890",
            "email": "test@example.com",
            "address": "Jl. TEST 1",
            "city": city,
            "kecamatan": kecamatan,
            "notes": "TEST_ITER12",
        }

    def test_order_paxel_jakarta(self, session):
        payload = {
            "items": [{"product_id": "tbn-turn-back-nutrients", "quantity": 1}],
            "contact": self._contact("Jakarta", "Setiabudi"),
            "payment_channel": "whatsapp",
            "shipping_courier": "Paxel",
        }
        r = session.post(f"{API}/orders", json=payload)
        assert r.status_code == 200, r.text
        data = r.json()
        assert data["shipping"] == 25000
        assert data["shipping_courier"] == "Paxel"
        assert data["shipping_service"] == "Same Day"
        assert data["shipping_etd"] == "Hari ini, 4-8 jam"
        assert data["total"] == data["subtotal"] + 25000 - data.get("discount", 0)

    def test_order_jnt_surabaya_whatsapp_url(self, session):
        payload = {
            "items": [{"product_id": "rotifer-2l-phyto", "quantity": 1}],
            "contact": self._contact("Surabaya", "Tegalsari"),
            "payment_channel": "whatsapp",
            "shipping_courier": "JNT",
        }
        r = session.post(f"{API}/orders", json=payload)
        assert r.status_code == 200, r.text
        data = r.json()
        assert data["shipping"] == 25000
        assert data["shipping_courier"] == "JNT"
        assert data["shipping_service"] == "Reguler"
        # Decode WA URL
        wa = urllib.parse.unquote(data["whatsapp_url"])
        assert "Pengiriman JNT Reguler = Rp25.000" in wa
        assert "Tegalsari" in wa  # kecamatan present

    def test_order_no_courier_defaults_paxel(self, session):
        payload = {
            "items": [{"product_id": "tbn-turn-back-nutrients", "quantity": 1}],
            "contact": self._contact("Jakarta", "Menteng"),
            "payment_channel": "whatsapp",
        }
        r = session.post(f"{API}/orders", json=payload)
        assert r.status_code == 200, r.text
        data = r.json()
        assert data["shipping_courier"] == "Paxel"
        assert data["shipping"] == 25000


# === Regression: voucher + bundle ===
class TestRegression:
    def test_voucher_firstbuy20k(self, session):
        payload = {
            "items": [{"product_id": "rotifer-2l-phyto", "quantity": 1}],  # 129999 >= 100000
            "contact": {
                "name": "TEST_V", "phone": "08111", "address": "addr",
                "city": "Jakarta", "kecamatan": "Setiabudi", "notes": "TEST_ITER12",
            },
            "payment_channel": "whatsapp",
            "shipping_courier": "JNT",
            "voucher_code": "FIRSTBUY20K",
        }
        r = session.post(f"{API}/orders", json=payload)
        assert r.status_code == 200, r.text
        data = r.json()
        assert data["discount"] == 20000
        assert data["voucher_code"] == "FIRSTBUY20K"
        assert data["total"] == data["subtotal"] - 20000 + data["shipping"]

    def test_bundle_suffix_10_percent(self, session):
        payload = {
            "items": [{"product_id": "tbn-turn-back-nutrients-bundle", "quantity": 1}],
            "contact": {
                "name": "TEST_B", "phone": "08111", "address": "addr",
                "city": "Jakarta", "kecamatan": "X", "notes": "TEST_ITER12",
            },
            "payment_channel": "whatsapp",
            "shipping_courier": "Paxel",
        }
        r = session.post(f"{API}/orders", json=payload)
        assert r.status_code == 200, r.text
        data = r.json()
        # TBN base 199000 → bundle 179100
        assert data["items"][0]["price"] == 179100
        assert data["items"][0]["is_bundle"] is True
        assert "Bundle -10%" in data["items"][0]["name"]

    def test_midtrans_snap_token(self, session):
        # create order first
        order_payload = {
            "items": [{"product_id": "tbn-turn-back-nutrients", "quantity": 1}],
            "contact": {
                "name": "TEST_M", "phone": "08111", "address": "addr",
                "city": "Jakarta", "kecamatan": "X", "notes": "TEST_ITER12",
            },
            "payment_channel": "midtrans",
            "shipping_courier": "Paxel",
        }
        r = session.post(f"{API}/orders", json=order_payload)
        assert r.status_code == 200, r.text
        order = r.json()
        # Request snap token (do NOT call Snap.pay against production)
        r2 = session.post(f"{API}/payment/midtrans/snap-token", json={"order_id": order["id"]})
        # Snap token call goes against Midtrans prod — could 200 if keys valid, or 4xx/5xx if not.
        # We only assert the endpoint is reachable and returns json.
        assert r2.status_code in (200, 400, 401, 502, 503), r2.text
        if r2.status_code == 200:
            data = r2.json()
            assert "token" in data
            assert "redirect_url" in data
