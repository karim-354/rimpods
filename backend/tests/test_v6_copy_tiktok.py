"""Iter 6 backend tests:
- tiktok_shop_url for all 3 products points to shop-id.tokopedia.com with correct ID
- new warm-premium taglines replace old hyperbolic copy
- WhatsApp message format updated (warm-formal opener + 'Detail Pesanan' + 'Alamat Pengiriman' + closing line)
- Regression: voucher FIRSTBUY20K flat 20k + min 100k ; bundle suffix 10%
"""
import os
import requests
from urllib.parse import unquote

from dotenv import load_dotenv
load_dotenv("/app/frontend/.env")
BASE_URL = os.environ["REACT_APP_BACKEND_URL"].rstrip("/")
API = f"{BASE_URL}/api"

CONTACT = {
    "name": "TEST_Reefer V6",
    "phone": "08123456789",
    "address": "Jl. Melati 7",
    "city": "Bekasi",
    "notes": "",
}

EXPECTED_TIKTOK_IDS = {
    "rotifer-2l-phyto": "1731802588285273240",
    "paket-hemat-5r-1p": "1729681104107505816",
    "tbn-turn-back-nutrients": "1729680758563637400",
}

OLD_COPY_TOKENS = ["gila-gilaan", "worth", "gendut", "Kenapa Rimpods"]


# === TikTok Shop URL swap to shop-id.tokopedia.com ===
def test_tiktok_shop_urls_are_shop_id_deep_links():
    r = requests.get(f"{API}/products", timeout=15)
    assert r.status_code == 200
    prods = {p["id"]: p for p in r.json()["products"]}
    assert set(prods.keys()) == set(EXPECTED_TIKTOK_IDS.keys()), list(prods.keys())
    for pid, expected_id in EXPECTED_TIKTOK_IDS.items():
        url = prods[pid]["tiktok_shop_url"]
        assert url.startswith("https://shop-id.tokopedia.com/view/product/"), (pid, url)
        assert expected_id in url, (pid, url)


# === Warm-premium taglines replace old copy ===
def test_new_taglines_present_and_no_old_copy():
    r = requests.get(f"{API}/products", timeout=15)
    prods = {p["id"]: p for p in r.json()["products"]}

    # Each product must have a non-empty tagline
    for pid, p in prods.items():
        assert p.get("tagline") and isinstance(p["tagline"], str), pid
        # No old hyperbolic words anywhere in tagline/description/highlights
        blob = " ".join([
            p.get("tagline", ""),
            p.get("description", ""),
            " ".join(p.get("highlights", [])),
        ]).lower()
        for tok in OLD_COPY_TOKENS:
            assert tok.lower() not in blob, f"old copy '{tok}' still present in {pid}"

    # Spot-check known warm taglines per product
    assert "nutrisi hidup" in prods["rotifer-2l-phyto"]["tagline"].lower()
    assert "ritual feeding" in prods["paket-hemat-5r-1p"]["tagline"].lower()
    assert "parameter air" in prods["tbn-turn-back-nutrients"]["tagline"].lower()


# === WhatsApp message format: warm-formal ===
def test_whatsapp_message_warm_formal_format():
    payload = {
        "items": [{"product_id": "tbn-turn-back-nutrients", "quantity": 1}],
        "contact": CONTACT,
        "payment_channel": "whatsapp",
    }
    r = requests.post(f"{API}/orders", json=payload, timeout=15)
    assert r.status_code == 200, r.text
    o = r.json()
    msg = unquote(o["whatsapp_url"])

    # New warm-formal opener
    assert "Halo Tim Rimpods, saya ingin melanjutkan pemesanan berikut:" in msg, msg
    # Old casual opener must be gone
    assert "Halo Rimpods! Aku mau order nih" not in msg
    # Required sections
    assert "Detail Pesanan:" in msg
    assert "Alamat Pengiriman:" in msg
    # Closing line
    assert "Terima kasih, saya tunggu konfirmasinya." in msg


# === Regression: voucher FIRSTBUY20K flat 20k ===
def test_voucher_firstbuy20k_regression():
    payload = {
        "items": [{"product_id": "tbn-turn-back-nutrients", "quantity": 1}],
        "contact": CONTACT,
        "payment_channel": "whatsapp",
        "voucher_code": "FIRSTBUY20K",
    }
    r = requests.post(f"{API}/orders", json=payload, timeout=15)
    assert r.status_code == 200
    o = r.json()
    assert o["discount"] == 20000
    assert o["voucher_code"] == "FIRSTBUY20K"
    assert o["total"] == 199000 - 20000 + 18000


# === Regression: bundle suffix 10% discount ===
def test_bundle_suffix_regression():
    payload = {
        "items": [{"product_id": "tbn-turn-back-nutrients-bundle", "quantity": 1}],
        "contact": CONTACT,
        "payment_channel": "whatsapp",
    }
    r = requests.post(f"{API}/orders", json=payload, timeout=15)
    assert r.status_code == 200
    o = r.json()
    line = o["items"][0]
    assert line["price"] == 179100
    assert line["is_bundle"] is True


# === Regression: products endpoint still returns 3 with expected ids ===
def test_products_list_has_three_known_ids():
    r = requests.get(f"{API}/products", timeout=15)
    assert r.status_code == 200
    prods = r.json()["products"]
    assert len(prods) == 3
    ids = {p["id"] for p in prods}
    assert ids == set(EXPECTED_TIKTOK_IDS.keys())
