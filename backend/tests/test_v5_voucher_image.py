"""Iter 5 backend tests:
- paket-hemat-5r-1p image must be customer-assets ...f12ycsla_ and image_alt ...h18wqlnd_
- POST /api/orders w/ FIRSTBUY20K + subtotal>=100k => discount=20000, voucher_code persisted, total math right, wa contains '-Rp20.000' and 'FIRSTBUY20K'
- POST /api/orders w/ FAKECODE => discount=0, voucher_code=null
- POST /api/orders w/o voucher_code => discount=0, voucher_code=null (regression)
- bundle suffix regression: tbn-...-bundle => 179100, is_bundle=true
"""
import os
import requests

from dotenv import load_dotenv
load_dotenv("/app/frontend/.env")
BASE_URL = os.environ["REACT_APP_BACKEND_URL"].rstrip("/")
API = f"{BASE_URL}/api"

CONTACT = {
    "name": "TEST_Reefer V5",
    "phone": "08123456789",
    "address": "Jl. Mawar 12",
    "city": "Bekasi",
    "notes": "",
}


# === Image asset swap ===
def test_paket_hemat_image_user_assets():
    r = requests.get(f"{API}/products/paket-hemat-5r-1p", timeout=15)
    assert r.status_code == 200
    p = r.json()
    assert "customer-assets.emergentagent.com" in p["image"]
    assert "f12ycsla_" in p["image"], p["image"]
    assert "customer-assets.emergentagent.com" in p["image_alt"]
    assert "h18wqlnd_" in p["image_alt"], p["image_alt"]


# === Voucher: valid + eligible ===
def test_voucher_firstbuy20k_eligible_applies_flat_20k():
    payload = {
        "items": [{"product_id": "tbn-turn-back-nutrients", "quantity": 1}],  # subtotal 199000
        "contact": CONTACT,
        "payment_channel": "whatsapp",
        "voucher_code": "FIRSTBUY20K",
    }
    r = requests.post(f"{API}/orders", json=payload, timeout=15)
    assert r.status_code == 200, r.text
    o = r.json()
    assert o["subtotal"] == 199000
    assert o["discount"] == 20000
    assert o["voucher_code"] == "FIRSTBUY20K"
    assert o["shipping"] == 18000  # 199000 < 250000
    # total = subtotal - discount + shipping
    assert o["total"] == 199000 - 20000 + 18000 == 197000
    assert "FIRSTBUY20K" in o["whatsapp_url"]
    assert "-Rp20.000" in requests.utils.unquote(o["whatsapp_url"])


def test_voucher_lowercase_normalised():
    payload = {
        "items": [{"product_id": "tbn-turn-back-nutrients", "quantity": 1}],
        "contact": CONTACT,
        "payment_channel": "whatsapp",
        "voucher_code": "firstbuy20k",
    }
    r = requests.post(f"{API}/orders", json=payload, timeout=15)
    assert r.status_code == 200
    o = r.json()
    assert o["voucher_code"] == "FIRSTBUY20K"
    assert o["discount"] == 20000


# === Voucher: invalid / fake ===
def test_voucher_fakecode_no_discount():
    payload = {
        "items": [{"product_id": "tbn-turn-back-nutrients", "quantity": 1}],
        "contact": CONTACT,
        "payment_channel": "whatsapp",
        "voucher_code": "FAKECODE",
    }
    r = requests.post(f"{API}/orders", json=payload, timeout=15)
    assert r.status_code == 200
    o = r.json()
    assert o["discount"] == 0
    assert o["voucher_code"] is None
    assert o["total"] == o["subtotal"] + o["shipping"]


# === Voucher: present but subtotal too low — pick lowest priced item bundle to fall under 100k ===
# We don't have a single product < 100k base. Use the bundle suffix path on tbn -> 179100 still > 100k.
# So we cannot create subtotal < 100k with current catalog. Skip via FAKECODE check above.
# Confirm with rotifer x0... not allowed (qty>=1). Acceptable: rely on FAKECODE coverage.


# === No voucher field -> regression ===
def test_no_voucher_field_normal_behaviour():
    payload = {
        "items": [{"product_id": "tbn-turn-back-nutrients", "quantity": 1}],
        "contact": CONTACT,
        "payment_channel": "whatsapp",
    }
    r = requests.post(f"{API}/orders", json=payload, timeout=15)
    assert r.status_code == 200
    o = r.json()
    assert o["discount"] == 0
    assert o["voucher_code"] is None
    assert o["total"] == 217000


# === Bundle suffix regression (iter4) ===
def test_bundle_suffix_still_works():
    payload = {
        "items": [{"product_id": "tbn-turn-back-nutrients-bundle", "quantity": 1}],
        "contact": CONTACT,
        "payment_channel": "whatsapp",
    }
    r = requests.post(f"{API}/orders", json=payload, timeout=15)
    assert r.status_code == 200
    o = r.json()
    line = o["items"][0]
    # 199000 * 0.9 = 179100
    assert line["price"] == 179100
    assert line["is_bundle"] is True
    assert o["subtotal"] == 179100


# === Voucher above threshold w/ free shipping path ===
def test_voucher_with_free_shipping():
    payload = {
        "items": [{"product_id": "rotifer-2l-phyto", "quantity": 2}],  # 259998
        "contact": CONTACT,
        "payment_channel": "whatsapp",
        "voucher_code": "FIRSTBUY20K",
    }
    r = requests.post(f"{API}/orders", json=payload, timeout=15)
    assert r.status_code == 200
    o = r.json()
    assert o["subtotal"] == 259998
    assert o["shipping"] == 0
    assert o["discount"] == 20000
    assert o["voucher_code"] == "FIRSTBUY20K"
    assert o["total"] == 259998 - 20000


# === GET order persistence with voucher ===
def test_voucher_order_persists_via_get():
    payload = {
        "items": [{"product_id": "tbn-turn-back-nutrients", "quantity": 1}],
        "contact": CONTACT,
        "voucher_code": "FIRSTBUY20K",
    }
    r = requests.post(f"{API}/orders", json=payload, timeout=15)
    assert r.status_code == 200
    oid = r.json()["id"]
    g = requests.get(f"{API}/orders/{oid}", timeout=15)
    assert g.status_code == 200
    fetched = g.json()
    assert fetched["discount"] == 20000
    assert fetched["voucher_code"] == "FIRSTBUY20K"
    assert "_id" not in fetched
