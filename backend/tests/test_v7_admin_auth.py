"""Backend tests for iter 7 — Emergent Google Auth + Admin dashboard."""
import os
import time
import requests
import pymongo
from datetime import datetime, timezone, timedelta

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "https://coral-product-hub.preview.emergentagent.com").rstrip("/")
API = f"{BASE_URL}/api"

MONGO_URL = "mongodb://localhost:27017"
DB_NAME = "test_database"
_client = pymongo.MongoClient(MONGO_URL)
_db = _client[DB_NAME]


def _inject_session(email: str, expires_delta_sec: int = 7 * 24 * 3600):
    uid = f"user_test_{int(time.time()*1000)}"
    token = f"test_session_{int(time.time()*1000)}_{email.split('@')[0]}"
    _db.users.insert_one({
        "user_id": uid,
        "email": email,
        "name": "Test " + email,
        "picture": "",
        "created_at": datetime.now(timezone.utc).isoformat(),
    })
    expires_at = datetime.now(timezone.utc) + timedelta(seconds=expires_delta_sec)
    _db.user_sessions.insert_one({
        "user_id": uid,
        "session_token": token,
        "expires_at": expires_at.isoformat(),
        "created_at": datetime.now(timezone.utc).isoformat(),
    })
    return uid, token


def _cleanup():
    _db.users.delete_many({"email": {"$in": ["admin@rimpods.test", "hacker@rimpods-external.com"]}})
    _db.user_sessions.delete_many({"session_token": {"$regex": "^test_session_"}})


# ---------- Auth tests ----------
class TestAuthEndpoints:
    def test_me_no_auth_401(self):
        r = requests.get(f"{API}/auth/me")
        assert r.status_code == 401

    def test_logout_no_session_idempotent_200(self):
        r = requests.post(f"{API}/auth/logout")
        assert r.status_code == 200
        assert r.json() == {"ok": True}

    def test_admin_orders_no_auth_401(self):
        r = requests.get(f"{API}/admin/orders")
        assert r.status_code == 401

    def test_admin_stats_no_auth_401(self):
        r = requests.get(f"{API}/admin/stats")
        assert r.status_code == 401


class TestAdminSession:
    @classmethod
    def setup_class(cls):
        _cleanup()
        cls.uid, cls.token = _inject_session("admin@rimpods.test")
        cls.headers = {"Authorization": f"Bearer {cls.token}"}

    @classmethod
    def teardown_class(cls):
        _cleanup()

    def test_me_returns_admin(self):
        r = requests.get(f"{API}/auth/me", headers=self.headers)
        assert r.status_code == 200
        d = r.json()
        assert d["email"] == "admin@rimpods.test"
        assert d["is_admin"] is True
        assert "_id" not in d

    def test_admin_orders_default(self):
        r = requests.get(f"{API}/admin/orders", headers=self.headers)
        assert r.status_code == 200
        d = r.json()
        assert "orders" in d and "total" in d and "skip" in d and "limit" in d
        assert d["limit"] == 100
        # Ensure no _id leaked
        for o in d["orders"]:
            assert "_id" not in o
        if d["orders"]:
            o = d["orders"][0]
            for f in ["order_number", "created_at", "total", "contact", "payment_channel", "status"]:
                assert f in o, f"missing field {f}"

    def test_admin_stats_30_days(self):
        r = requests.get(f"{API}/admin/stats?days=30", headers=self.headers)
        assert r.status_code == 200
        d = r.json()
        for k in ["overall", "window", "vouchers_redeemed", "voucher_breakdown", "channel_breakdown"]:
            assert k in d
        assert isinstance(d["voucher_breakdown"], list)
        assert isinstance(d["channel_breakdown"], dict)

    def test_admin_orders_voucher_only(self):
        r = requests.get(f"{API}/admin/orders?voucher_only=true", headers=self.headers)
        assert r.status_code == 200
        for o in r.json()["orders"]:
            assert o.get("voucher_code") is not None

    def test_admin_patch_status_valid(self):
        # Create an order via public API
        order_payload = {
            "items": [{"product_id": "tbn-turn-back-nutrients", "quantity": 1}],
            "contact": {"name": "TEST_admin", "phone": "08123", "address": "x", "city": "y"},
            "payment_channel": "whatsapp",
        }
        c = requests.post(f"{API}/orders", json=order_payload)
        assert c.status_code == 200
        order_id = c.json()["id"]

        r = requests.patch(f"{API}/admin/orders/{order_id}/status?status=confirmed", headers=self.headers)
        assert r.status_code == 200
        assert r.json().get("ok") is True

        # Verify
        r2 = requests.get(f"{API}/admin/orders?limit=200", headers=self.headers)
        found = next((o for o in r2.json()["orders"] if o["id"] == order_id), None)
        assert found and found["status"] == "confirmed"

    def test_admin_patch_status_invalid(self):
        r = requests.patch(f"{API}/admin/orders/nonexistent/status?status=bogus", headers=self.headers)
        assert r.status_code == 200
        assert r.json().get("ok") is False


class TestNonAdminSession:
    @classmethod
    def setup_class(cls):
        _cleanup()
        cls.uid, cls.token = _inject_session("hacker@rimpods-external.com")
        cls.headers = {"Authorization": f"Bearer {cls.token}"}

    @classmethod
    def teardown_class(cls):
        _cleanup()

    def test_me_non_admin(self):
        r = requests.get(f"{API}/auth/me", headers=self.headers)
        assert r.status_code == 200
        d = r.json()
        assert d["is_admin"] is False
        assert d["email"] == "hacker@rimpods-external.com"

    def test_admin_orders_forbidden(self):
        r = requests.get(f"{API}/admin/orders", headers=self.headers)
        assert r.status_code == 403

    def test_admin_stats_forbidden(self):
        r = requests.get(f"{API}/admin/stats", headers=self.headers)
        assert r.status_code == 403


class TestExpiredSession:
    @classmethod
    def setup_class(cls):
        _cleanup()
        cls.uid, cls.token = _inject_session("admin@rimpods.test", expires_delta_sec=-3600)

    @classmethod
    def teardown_class(cls):
        _cleanup()

    def test_expired_returns_401_and_deletes(self):
        r = requests.get(f"{API}/auth/me", headers={"Authorization": f"Bearer {self.token}"})
        assert r.status_code == 401
        # Session should be deleted
        s = _db.user_sessions.find_one({"session_token": self.token})
        assert s is None


# ---------- Regression ----------
class TestRegression:
    def test_products_ok(self):
        r = requests.get(f"{API}/products")
        assert r.status_code == 200
        assert len(r.json()["products"]) >= 3

    def test_orders_create_ok(self):
        payload = {
            "items": [{"product_id": "rotifer-2l-phyto", "quantity": 1}],
            "contact": {"name": "TEST_reg", "phone": "08", "address": "x", "city": "y"},
            "payment_channel": "whatsapp",
            "voucher_code": "FIRSTBUY20K",
        }
        r = requests.post(f"{API}/orders", json=payload)
        assert r.status_code == 200
        d = r.json()
        assert d["voucher_code"] == "FIRSTBUY20K"
        assert d["discount"] == 20000

    def test_content_verify_ok(self):
        r = requests.post(f"{API}/content/verify", json={"text": "Tank ini menarik dan dinamis.", "auto_fix": False})
        assert r.status_code == 200
