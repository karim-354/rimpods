"""Iter 3 regression: tiktok_shop_url + upsell_target fields + orders regression."""
import os
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "https://coral-product-hub.preview.emergentagent.com").rstrip("/")

EXPECTED_UPSELL = {
    "rotifer-2l-phyto": "tbn-turn-back-nutrients",
    "paket-hemat-5r-1p": "tbn-turn-back-nutrients",
    "tbn-turn-back-nutrients": "rotifer-2l-phyto",
}


def test_products_has_new_fields():
    r = requests.get(f"{BASE_URL}/api/products", timeout=15)
    assert r.status_code == 200
    products = r.json()["products"]
    assert len(products) == 3
    ids = {p["id"] for p in products}
    assert ids == set(EXPECTED_UPSELL.keys())
    for p in products:
        assert "tiktok_shop_url" in p and p["tiktok_shop_url"].startswith("https://www.tiktok.com"), p["id"]
        assert p.get("upsell_target") == EXPECTED_UPSELL[p["id"]], p["id"]


def test_order_with_bundle_uses_base_price():
    payload = {
        "items": [
            {"product_id": "rotifer-2l-phyto", "quantity": 1},
            {"product_id": "tbn-turn-back-nutrients", "quantity": 1},
        ],
        "contact": {"name": "TEST_buyer", "phone": "08123", "address": "Jl Test 1", "city": "Bekasi"},
        "payment_channel": "whatsapp",
    }
    r = requests.post(f"{BASE_URL}/api/orders", json=payload, timeout=15)
    assert r.status_code == 200, r.text
    data = r.json()
    tbn = [i for i in data["items"] if i["product_id"] == "tbn-turn-back-nutrients"][0]
    assert tbn["price"] == 199000  # base, not discounted
    assert data["subtotal"] == 129999 + 199000
