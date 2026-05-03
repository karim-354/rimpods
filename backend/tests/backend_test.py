import os, requests
BASE = os.environ.get("REACT_APP_BACKEND_URL", "https://coral-product-hub.preview.emergentagent.com").rstrip("/")
API = f"{BASE}/api"

def test_list_products():
    r = requests.get(f"{API}/products", timeout=20); assert r.status_code == 200
    ids = {p["id"] for p in r.json()["products"]}
    assert {"rotifer-2l-phyto","paket-hemat-5r-1p","tbn-turn-back-nutrients"} <= ids

def test_get_product():
    r = requests.get(f"{API}/products/rotifer-2l-phyto", timeout=20); assert r.status_code == 200
    d = r.json(); assert d["price"] == 129999 and d["tokopedia_url"]

def test_get_product_404():
    assert requests.get(f"{API}/products/xxx", timeout=20).status_code == 404

def _order(items, ch="whatsapp"):
    return requests.post(f"{API}/orders", json={"items": items, "contact":{"name":"TEST_x","phone":"081","address":"Jl A","city":"Jkt"}, "payment_channel": ch}, timeout=20)

def test_order_paid_shipping():
    r = _order([{"product_id":"rotifer-2l-phyto","quantity":1}]); assert r.status_code == 200
    d = r.json(); assert d["subtotal"]==129999 and d["shipping"]==18000 and d["total"]==147999 and d["whatsapp_url"].startswith("https://wa.me/") and d["tokopedia_url"]

def test_order_free_shipping():
    d = _order([{"product_id":"paket-hemat-5r-1p","quantity":1}]).json()
    assert d["shipping"] == 0 and d["total"] == 549000

def test_order_get_persist():
    d = _order([{"product_id":"tbn-turn-back-nutrients","quantity":2}]).json()
    g = requests.get(f"{API}/orders/{d['id']}", timeout=20); assert g.status_code == 200
    assert g.json()["order_number"] == d["order_number"]
    assert requests.get(f"{API}/orders/missing", timeout=20).status_code == 404

def test_order_empty_invalid():
    assert _order([]).status_code in (400,422)
    assert _order([{"product_id":"nope","quantity":1}]).status_code == 400

def test_content_block():
    r = requests.post(f"{API}/content/verify", json={"text":"Sehubungan dengan hal tersebut, demikian kami sampaikan, atas perhatiannya."}, timeout=20)
    d = r.json(); assert d["blocked"] is True and d["publish_allowed"] is False

def test_content_natural():
    r = requests.post(f"{API}/content/verify", json={"text":"Jujur ya, rotifer Rimpods bikin coral mekar gila-gilaan kok! Tank 400L cukup 2 liter, ditambah phyto sebotol. Worth it nggak? Aku rekomendasiin banget deh.","auto_fix":True}, timeout=20)
    d = r.json(); assert d.get("passed") is True and d["score"] >= 55

def test_quick_check():
    d = requests.post(f"{API}/content/quick-check", json={"text":"halo dunia ini contoh kecil aja kok"}, timeout=20).json()
    assert "score" in d and "issues" in d and "fixed_text" in d
