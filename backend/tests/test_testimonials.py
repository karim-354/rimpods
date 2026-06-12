"""Wall of Reefs (testimonials) — public + admin endpoint tests.
Public GET should return seeded data; admin endpoints must reject unauth requests."""
import os
import requests
import pytest

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "https://api-frontend-base.preview.emergentagent.com").rstrip("/")


@pytest.fixture(scope="module")
def client():
    s = requests.Session()
    s.headers.update({"Content-Type": "application/json"})
    return s


# --- Public endpoint ---
class TestPublicTestimonials:
    def test_list_public_status(self, client):
        r = client.get(f"{BASE_URL}/api/testimonials", timeout=30)
        assert r.status_code == 200, r.text

    def test_list_public_shape_and_stats(self, client):
        r = client.get(f"{BASE_URL}/api/testimonials", timeout=30)
        data = r.json()
        assert "stats" in data and "testimonials" in data
        stats = data["stats"]
        assert stats.get("rating") == 4.9
        assert stats.get("total_ratings") == 6261
        assert stats.get("satisfaction_pct") == 98
        assert stats.get("total_sold") == "15 rb+"
        assert "tokopedia.com/rimpods/review" in (stats.get("review_url") or "")

    def test_list_public_seeded_35_items(self, client):
        data = client.get(f"{BASE_URL}/api/testimonials", timeout=30).json()
        items = data["testimonials"]
        assert len(items) == 35, f"Expected 35 visible testimonials, got {len(items)}"
        # First in order should be Achmad with 3 photos
        first = items[0]
        assert first["id"] == "tkp-001"
        assert first["name"] == "Achmad"
        assert len(first["photos"]) == 3
        for p in first["photos"]:
            assert p.startswith("/testimonials/") and p.endswith(".webp")

    def test_no_mongo_objectid_leak(self, client):
        data = client.get(f"{BASE_URL}/api/testimonials", timeout=30).json()
        for t in data["testimonials"]:
            assert "_id" not in t


# --- Static photo accessibility (served by React public) ---
class TestTestimonialPhotosPublic:
    @pytest.mark.parametrize("fname", ["achmad-1.webp", "achmad-2.webp", "achmad-3.webp"])
    def test_photo_public_accessible(self, client, fname):
        r = client.get(f"{BASE_URL}/testimonials/{fname}", timeout=30)
        assert r.status_code == 200, f"{fname} -> {r.status_code}"
        assert int(r.headers.get("content-length", "1")) > 0


# --- Admin endpoints must reject unauthenticated ---
class TestAdminTestimonialsAuth:
    def _assert_blocked(self, resp):
        assert resp.status_code in (401, 403), f"Expected 401/403, got {resp.status_code}: {resp.text[:200]}"

    def test_admin_list_requires_auth(self, client):
        self._assert_blocked(client.get(f"{BASE_URL}/api/admin/testimonials", timeout=30))

    def test_admin_create_requires_auth(self, client):
        payload = {"name": "TEST_should_not_create", "text": "blocked"}
        self._assert_blocked(client.post(f"{BASE_URL}/api/admin/testimonials", json=payload, timeout=30))

    def test_admin_update_requires_auth(self, client):
        self._assert_blocked(
            client.put(f"{BASE_URL}/api/admin/testimonials/tkp-001", json={"text": "blocked"}, timeout=30)
        )

    def test_admin_delete_requires_auth(self, client):
        # IMPORTANT: must remain blocked — do NOT delete seeded data
        self._assert_blocked(client.delete(f"{BASE_URL}/api/admin/testimonials/tkp-001", timeout=30))

    def test_seed_not_mutated_after_unauth_attempts(self, client):
        # Sanity check: after unauth attempts, public list still has 35 + Achmad first
        data = client.get(f"{BASE_URL}/api/testimonials", timeout=30).json()
        assert len(data["testimonials"]) == 35
        assert data["testimonials"][0]["id"] == "tkp-001"


# --- Regression: critical existing endpoints still work ---
class TestRegressionCoreEndpoints:
    def test_products_list(self, client):
        r = client.get(f"{BASE_URL}/api/products", timeout=30)
        assert r.status_code == 200
        assert "products" in r.json()
