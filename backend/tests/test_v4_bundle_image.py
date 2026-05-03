"""Iter 4 backend regression tests:
- Validate refreshed product image for rotifer-2l-phyto
- /api/products + /api/products/{id} happy + 404 path
- /api/orders create (shipping rule, wa.me/6282216594354, RMP order_number format)
- /api/orders/{id} fetch (no _id leak)
- /api/content/verify + /api/content/quick-check (natural ID + AI text)
"""
import os
import re
import requests
import pytest

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "").rstrip("/")
API = f"{BASE_URL}/api"

EXPECTED_IDS = {"rotifer-2l-phyto", "paket-hemat-5r-1p", "tbn-turn-back-nutrients"}
NEW_ROTIFER_IMG_HOST = "customer-assets.emergentagent.com"
NEW_ROTIFER_IMG_FRAGMENT = "kvng7upw_a1.jpeg"


# ===== /api/products =====
def test_list_products_returns_three_with_full_fields():
    r = requests.get(f"{API}/products", timeout=15)
    assert r.status_code == 200
    products = r.json().get("products")
    assert isinstance(products, list)
    assert len(products) == 3
    ids = {p["id"] for p in products}
    assert ids == EXPECTED_IDS

    required = {
        "image", "image_alt", "tokopedia_url", "tiktok_shop_url",
        "upsell_target", "highlights", "description", "name", "price"
    }
    for p in products:
        missing = required - set(p.keys())
        assert not missing, f"{p['id']} missing {missing}"
        assert isinstance(p["highlights"], list) and len(p["highlights"]) >= 3


def test_rotifer_2l_image_swapped_to_user_asset():
    r = requests.get(f"{API}/products/rotifer-2l-phyto", timeout=15)
    assert r.status_code == 200
    p = r.json()
    assert NEW_ROTIFER_IMG_HOST in p["image"]
    assert NEW_ROTIFER_IMG_FRAGMENT in p["image"]
    # alt should be the secondary aa.jpeg user-uploaded asset
    assert NEW_ROTIFER_IMG_HOST in p["image_alt"]
    assert "aa.jpeg" in p["image_alt"]


@pytest.mark.parametrize("pid", list(EXPECTED_IDS))
def test_get_product_by_id(pid):
    r = requests.get(f"{API}/products/{pid}", timeout=15)
    assert r.status_code == 200
    assert r.json()["id"] == pid


def test_get_product_invalid_returns_404():
    r = requests.get(f"{API}/products/does-not-exist", timeout=15)
    assert r.status_code == 404


# ===== /api/orders =====
CONTACT = {
    "name": "TEST_Reefer Joko",
    "phone": "08123456789",
    "email": "joko@example.com",
    "address": "Jl. Mawar 12",
    "city": "Bekasi",
    "notes": "Tolong packing rapih",
}


def test_create_order_below_threshold_has_shipping():
    payload = {
        "items": [{"product_id": "tbn-turn-back-nutrients", "quantity": 1}],  # 199000
        "contact": CONTACT,
        "payment_channel": "whatsapp",
    }
    r = requests.post(f"{API}/orders", json=payload, timeout=15)
    assert r.status_code == 200
    o = r.json()
    assert o["subtotal"] == 199000
    assert o["shipping"] == 18000
    assert o["total"] == 217000
    # Order number format RMP + 6-digit date + 5 hex
    assert re.match(r"^RMP\d{6}[0-9A-F]{5}$", o["order_number"]), o["order_number"]
    assert "wa.me/6282216594354" in o["whatsapp_url"]
    assert "_id" not in o


def test_create_order_above_threshold_free_shipping_and_persists():
    payload = {
        "items": [
            {"product_id": "rotifer-2l-phyto", "quantity": 2},   # 259998
        ],
        "contact": CONTACT,
        "payment_channel": "whatsapp",
    }
    r = requests.post(f"{API}/orders", json=payload, timeout=15)
    assert r.status_code == 200
    o = r.json()
    assert o["subtotal"] == 259998
    assert o["shipping"] == 0
    assert o["total"] == 259998
    assert "wa.me/6282216594354" in o["whatsapp_url"]

    # GET order to verify persistence + no _id leak
    g = requests.get(f"{API}/orders/{o['id']}", timeout=15)
    assert g.status_code == 200
    fetched = g.json()
    assert fetched["order_number"] == o["order_number"]
    assert fetched["total"] == 259998
    assert "_id" not in fetched


def test_create_order_invalid_product_returns_400():
    payload = {
        "items": [{"product_id": "ghost-product", "quantity": 1}],
        "contact": CONTACT,
    }
    r = requests.post(f"{API}/orders", json=payload, timeout=15)
    assert r.status_code == 400


def test_create_order_empty_cart_returns_400():
    r = requests.post(f"{API}/orders", json={"items": [], "contact": CONTACT}, timeout=15)
    assert r.status_code == 400


def test_get_order_invalid_id_returns_404():
    r = requests.get(f"{API}/orders/does-not-exist-xyz", timeout=15)
    assert r.status_code == 404


# ===== /api/content/* fingerprint =====
NATURAL_ID = (
    "Tank gua kemarin kelihatannya agak keruh, jadi gua ganti air dikit. "
    "Coral kayak SPS sama LPS langsung lebih happy. Polip mekar lagi, "
    "padahal cuma water change 20 persen plus tuang rotifer dikit."
)

AI_LIKE = (
    "Pada dasarnya, produk ini merupakan solusi komprehensif. "
    "Oleh karena itu, dengan demikian kami sampaikan bahwa hal ini akan "
    "mengoptimalkan eksistensi terumbu karang Anda. "
    "Demi mencapai hasil substansial, perlu diketahui bahwa hal ini merupakan investasi. "
    "Demikian, atas perhatiannya kami ucapkan terima kasih."
)


def test_quick_check_natural_indonesian_passes_55():
    r = requests.post(f"{API}/content/quick-check", json={"text": NATURAL_ID}, timeout=15)
    assert r.status_code == 200
    data = r.json()
    score = data.get("score") or data.get("total_score") or data.get("final_score")
    assert score is not None, data
    assert score >= 55, data


def test_quick_check_ai_text_flagged_lower():
    r = requests.post(f"{API}/content/quick-check", json={"text": AI_LIKE}, timeout=15)
    assert r.status_code == 200
    data = r.json()
    score = data.get("score") or data.get("total_score") or data.get("final_score")
    assert score is not None, data
    # AI-like text should score noticeably lower than natural
    assert score < 55, data


def test_verify_endpoint_returns_payload():
    r = requests.post(f"{API}/content/verify", json={"text": NATURAL_ID, "auto_fix": True}, timeout=15)
    assert r.status_code == 200
    assert isinstance(r.json(), dict)
