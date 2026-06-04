import os
import re
import uuid
import base64
import httpx
import pymongo
from urllib.parse import quote
from datetime import datetime, timezone
from fastapi import FastAPI, HTTPException, Request, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, ConfigDict
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient
from auth import build_auth_router
from admin import build_admin_router

load_dotenv()
app = FastAPI(title="Rimpods Monolith Production API")

# ==========================================
# KONEKSI DATABASE & UTILITIES
# ==========================================
MONGO_URL = os.getenv("MONGO_URL", "mongodb://localhost:27017")
DB_NAME = os.getenv("DB_NAME", "test_database")
db = pymongo.MongoClient(MONGO_URL)[DB_NAME]
# Async client (motor) used only by the modular auth + admin routers
async_db = AsyncIOMotorClient(MONGO_URL)[DB_NAME]

BITESHIP_KEY = os.getenv("BITESHIP_KEY")
BITESHIP_API = "https://api.biteship.com/v1"
MIDTRANS_SERVER_KEY = os.getenv("MIDTRANS_SERVER_KEY")
MIDTRANS_IS_PRODUCTION = os.getenv("MIDTRANS_IS_PRODUCTION", "true").lower() == "true"
MIDTRANS_STATUS_BASE = "https://api.midtrans.com" if MIDTRANS_IS_PRODUCTION else "https://api.sandbox.midtrans.com"
WA_ADMIN_NUMBER = os.getenv("WA_ADMIN_NUMBER", "6282216594354")

ORIGIN_LAT = -6.259636
ORIGIN_LON = 106.906426
ORIGIN_POSTAL = "17411"

_cors_raw = os.getenv("CORS_ORIGINS", "*")
_cors_list = [o.strip() for o in _cors_raw.split(",") if o.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_list if _cors_list else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ==========================================
# MODULAR ROUTERS: AUTH (Google) + ADMIN (order monitoring)
# ==========================================
_auth_router, _current_user, _require_admin = build_auth_router(async_db)
app.include_router(_auth_router)
app.include_router(build_admin_router(async_db, _require_admin))

# ==========================================
# PRODUCT CATALOG (source of truth) + idempotent seed
# ==========================================
PRODUCTS = [
    {
        "id": "rotifer-2l-phyto",
        "slug": "rotifera-2l-besar",
        "name": "Rimpods Rotifera 2L + Phytoplankton",
        "tagline": "Nutrisi hidup untuk tank yang ingin lebih dari sekadar jernih.",
        "price": 129999,
        "compare_price": 159000,
        "weight_kg": 3.0,
        "rating": 4.9,
        "reviews": 891,
        "sold": "1rb+",
        "stock": 9370,
        "image": "https://customer-assets.emergentagent.com/job_coral-product-hub/artifacts/kvng7upw_a1.jpeg",
        "image_alt": "https://customer-assets.emergentagent.com/job_coral-product-hub/artifacts/r5m9fr4a_aa.jpeg",
        "tokopedia_url": "https://www.tokopedia.com/rimpods/rimpods-rotifera-2liter-besar-dengan-1-phytoplankton-ideal-untuk-coral-mekar-dalam-tank-besar-1731802588285273240",
        "tiktok_shop_url": "https://shop-id.tokopedia.com/view/product/1731802588285273240?encode_params=MIIBPwQM1nt56rSgUGmzMv8TBIIBGwaUatQ26awirmatcvftdKZiMMCLdfwPP0Vt_jjIWQWI7c_AvEPiFZyNqPCi3Kp1qWOsrDWvt8J_5nsDA5NgnjVFS0AA1-kxfjcCegpoAegD7Afld469BIBHbb7750vkS2xOOpgKRMdr_PVqIMAh4o42h0RZZfXOsqHH_SKAOzSSEMq7oIMlyvvb2HxTPj3GibfGrIZIKDUYgt8o5ZXUXctEIKqGNgNe8uHJ15NVZGRlEE3OhygovK3Q6CbdPb0_FMF-VzwsEE-KYyf1mBVcRllRsYwWFxWi_d5BiAExtoGzo9Y5qiST06mn60ctavRonXxtJq2uBmFmL5r2sJByYXG_h2EeUe3-F7NSVW-yqTRO-rkNK6LY-v7O8aYEEDVEKVjohiI_MkEolKE7WMo%3D",
        "upsell_target": "tbn-turn-back-nutrients",
        "highlights": [
            "Kultur live dari fasilitas Bekasi, dipanen saat kesegarannya paling matang",
            "Satu paket lengkap: 2 liter rotifer aktif plus 1 botol phytoplankton pendamping",
            "Selaras untuk SPS, LPS, dan soft coral — satu formula untuk seluruh koloni",
            "Dikemas dengan metode suhu-terjaga, agar sampai di tangan kamu masih hidup",
        ],
        "description": (
            "Tank dengan kapasitas di atas 400 liter punya ritme yang khas: ruang yang luas, "
            "arus yang dinamis, dan coral yang ingin merespons lebih ekspresif. Di titik itulah "
            "rotifer 2 liter ini kami siapkan. Satu kali tuang, kamu akan melihat polip mulai "
            "mencari, lalu memanjang dengan tenang. Tak perlu dramatisasi — hasilnya akan bicara "
            "sendiri pada hari kedua dan ketiga."
        ),
    },
    {
        "id": "paket-hemat-5r-1p",
        "slug": "paket-hemat-5-rotifer-1-phyto",
        "name": "Paket Hemat 5 Rotifer + 1 Phytoplankton",
        "tagline": "Ritual feeding yang tenang untuk reefer yang menjaga konsistensi.",
        "price": 89999,
        "compare_price": 129999,
        "weight_kg": 2.0,
        "rating": 4.9,
        "reviews": 2198,
        "sold": "3rb+",
        "stock": 98967,
        "image": "https://customer-assets.emergentagent.com/job_coral-product-hub/artifacts/f12ycsla_WhatsApp%20Image%202026-05-03%20at%208.19.10%20PM%20%283%29.jpeg",
        "image_alt": "https://customer-assets.emergentagent.com/job_coral-product-hub/artifacts/h18wqlnd_WhatsApp%20Image%202026-05-03%20at%208.19.10%20PM%20%282%29.jpeg",
        "tokopedia_url": "https://www.tokopedia.com/rimpods/paket-hemat-5-rotifer-1-phytoplankton-rotifera-pakan-coral-food",
        "tiktok_shop_url": "https://shop-id.tokopedia.com/view/product/1729681104107505816?encode_params=MIIBPwQMtSyEzExlVv5-1n7BBIIBGzAUXHLTRG_vnYZLWo-tdTZh8mOnGI_-yYjw1_2fax1aV-gtHdLeOf0irSqA63YYRxYQQbDw5eopIeUY6po_T9YkMa56OOf4cNEiNROicGUyl3gwyM__DWLoh5hvNDpKWonYk6pTm4WNjPuhK5faLARdq6CrTuEDwee6GpePdtfVceNxZgtRfoDYwsA-ItNzSxUsFoT15Ma_ksplFTLK9VCxh8qqdNjwcEXeRUrzcszutaH7KAoXHrdkoIO9D3J95TZOKL1-QWGpEvEu7byRBV78nHlnsvHlJ-iJt7ZbMWPtf1VPjTjcjEC4LCBGiflcA_tb6_1vBkKPI-rDVZr_raWuOo3M4LRKCiFLTh-xs3YD9JOTtLBw7JnkriUEEJDrsMWZg6SUSTpWc4iyZM0%3D",
        "upsell_target": "tbn-turn-back-nutrients",
        "highlights": [
            "4 botol Rotifer + 1 botol Phytoplankton, plus 1 botol Rotifer BONUS — total 5R + 1P",
            "Stok yang cukup untuk satu siklus feeding yang rapi",
            "Simpan di kulkas, tuang sesuai jadwal, biarkan coral menemukan ritmenya",
            "Pilihan favorit reefer yang menjaga display tank mereka setiap pekan",
        ],
        "description": (
            "Kalau kamu sudah menemukan ritme feeding yang cocok untuk tank kamu, paket ini "
            "dirancang untuk menjaga ritme itu tetap ringan. Lima botol rotifer (4 botol + "
            "1 botol bonus) dan satu phytoplankton datang dalam satu kiriman yang rapi — siap "
            "menemani rutinitas dosing kamu selama beberapa minggu ke depan. Tidak ada yang "
            "terburu-buru, tidak ada yang terlewat. Hanya konsistensi yang tenang."
        ),
    },
    {
        "id": "tbn-turn-back-nutrients",
        "slug": "turn-back-nutrients",
        "name": "Rimpods Turn Back Nutrients (TBN)",
        "tagline": "Langkah tenang saat parameter air mulai bergeser.",
        "price": 199000,
        "compare_price": 229000,
        "weight_kg": 0.7,
        "rating": 5.0,
        "reviews": 7,
        "sold": "23+",
        "stock": 2,
        "image": "https://customer-assets.emergentagent.com/job_coral-product-hub/artifacts/quds6vg4_WhatsApp%20Image%202026-05-03%20at%208.19.10%20PM%20%281%29.jpeg",
        "image_alt": "https://customer-assets.emergentagent.com/job_coral-product-hub/artifacts/y598w8ty_WhatsApp%20Image%202026-05-03%20at%208.19.08%20PM.jpeg",
        "tokopedia_url": "https://www.tokopedia.com/rimpods/rimpods-turn-back-nutrients-1729680758563637400",
        "tiktok_shop_url": "https://shop-id.tokopedia.com/view/product/1729680758563637400?encode_params=MIIBPwQMqbROjEM3BPHLuhnJBIIBG3uhbqbT5XCAw9NxrkY0TOfMuwVzgf7nroyqHalMgEFU-CepQc9GPBqvGT78nKS8rOav9rZzPpIwssJ0fYfP7nP7EWo3reZC8937ufvMyKXI9EldDd49nCsU5vjwzZ3nkfK-73vvQwAUi9QrUyp_7a33mERjsrknUxB1JS4EjxZo1UqIkmEeDjScWnWoQWNeIXAwXJDmtTLlf4N9j00N6f8PkhpJf8Jq4VV-u4vDv-t2tw2JP6csNUqYPisDbCbV13ZMZIDf6jynixQx7Odfms4rP57kFPjI42XyRHOV-e4G9zwIjJ0tgg2g3zBLzjUreCocHd0btJA6W96LhXy2uQREGzmwgzqd0Y4_1heOM-_374hBZEWrXS9mOYIEEBteNEV4QU9WvizaAjm5-KI%3D",
        "upsell_target": "rotifer-2l-phyto",
        "highlights": [
            "Diformulasikan untuk mendampingi stabilisasi air pasca perubahan signifikan",
            "Bekerja berdampingan dengan filtrasi dan water change — bukan pengganti",
            "Aman untuk koloni coral sensitif, ikan, dan invertebrata",
            "Stok kami jaga terbatas, supaya setiap botol selalu dalam batch terbaru",
        ],
        "description": (
            "Ada momen ketika tank yang tenang tiba-tiba berubah ritmenya — air sedikit "
            "keruh, parameter bergeser, polip mulai menutup. Pada momen itu, kamu butuh "
            "langkah yang terukur, bukan panik. TBN hadir untuk membantu kamu mengembalikan "
            "fase fresh secara bertahap: cek parameter, perbaiki filtrasi, lakukan water "
            "change 20–50 persen, ganti media, lalu tuang TBN. Setelah itu, pantau kualitas "
            "air secara rutin — dan biarkan tank kamu kembali menemukan ketenangannya."
        ),
    },
]

def _seed_products():
    """Idempotent upsert of catalog into db.products (used by order price validation)."""
    try:
        for _p in PRODUCTS:
            db.products.update_one({"_id": _p["id"]}, {"$set": _p}, upsert=True)
    except Exception as e:
        print(f"[seed_products] warning: {e}")

_seed_products()


@app.get("/api/products")
async def list_products():
    return {"products": PRODUCTS}


@app.get("/api/products/{product_id}")
async def get_product(product_id: str):
    for p in PRODUCTS:
        if p["id"] == product_id or p.get("slug") == product_id:
            return p
    raise HTTPException(status_code=404, detail="Produk tidak ditemukan")

def clean_phone_number(phone: str) -> str:
    cleaned = re.sub(r'\D', '', phone)
    if cleaned.startswith("0"):
        return "62" + cleaned[1:]
    if cleaned.startswith("62"):
        return cleaned
    return "62" + cleaned if cleaned else "6282216594354"

def sanitize_name(name: str) -> str:
    return name.ljust(3, '.') if len(name) < 3 else name

def calculate_item_weight(name: str) -> int:
    n = name.lower()
    if "2 liter" in n or "2l" in n:
        return 3500
    elif "hemat" in n:
        return 1800
    elif "tbn" in n or "turn back" in n:
        return 800
    return 1000

# ==========================================
# PYDANTIC DATA MODELS
# ==========================================
class CartItem(BaseModel):
    product_id: str
    quantity: int
    name: Optional[str] = "Live Coral Food"
    price: Optional[int] = 0

class ContactInfo(BaseModel):
    model_config = ConfigDict(extra="allow")
    name: str
    phone: str
    email: Optional[str] = "pelanggan@rimpods.com"
    address: str
    city: str
    kecamatan: str
    postalCode: str
    latitude: Optional[str] = ""
    longitude: Optional[str] = ""

class RatesRequest(BaseModel):
    items: List[CartItem]
    postalCode: str
    latitude: Optional[str] = ""
    longitude: Optional[str] = ""

class OrderRequest(BaseModel):
    items: List[CartItem]
    contact: ContactInfo
    payment_channel: str
    shipping_courier: str
    voucher_code: Optional[str] = None

class MidtransRequest(BaseModel):
    order_id: str

# ==========================================
# 1. ENGINE RETENSI (MEMORI PEMBELI LAMA)
# ==========================================
@app.get("/api/customer/lookup")
async def lookup_customer(phone: str):
    safe_phone = clean_phone_number(phone)
    last_order = db.orders.find_one(
        {"contact.phone": safe_phone},
        sort=[("created_at", pymongo.DESCENDING)]
    )
    if not last_order:
        return {"found": False}
    return {
        "found": True,
        "contact": last_order["contact"]
    }

# ==========================================
# 2. RADAR PENCARI KECAMATAN SILUMAN
# ==========================================
@app.get("/api/shipping/search-area")
async def search_area(query: str):
    if len(query) < 3:
        return {"areas": []}
    headers = {"Authorization": f"Bearer {BITESHIP_KEY}"}
    async with httpx.AsyncClient() as client:
        resp = await client.get(f"{BITESHIP_API}/maps/areas?input={query}", headers=headers)
        if resp.status_code == 200:
            return {"areas": resp.json().get("areas", [])}
        return {"areas": []}

# ==========================================
# 3. MESIN HITUNG ONGKIR AKURAT NASIONAL & OJOL
# ==========================================
@app.post("/api/shipping/rates")
async def get_rates(req: RatesRequest):
    total_weight = 0
    biteship_items = []
    
    for item in req.items:
        w = calculate_item_weight(item.name)
        total_weight += w * item.quantity
        biteship_items.append({
            "name": item.name[:40],
            "value": item.price if item.price > 0 else 89999,
            "weight": w,
            "quantity": item.quantity
        })

    payload = {
        "origin_latitude": ORIGIN_LAT,
        "origin_longitude": ORIGIN_LON,
        "origin_postal_code": int(ORIGIN_POSTAL),
        "couriers": "lalamove,gojek,grab,tiki,jne,jnt,paxel",
        "items": biteship_items
    }

    if req.latitude and req.longitude and str(req.latitude) != "0" and str(req.latitude) != "":
        payload["destination_latitude"] = float(req.latitude)
        payload["destination_longitude"] = float(req.longitude)
    else:
        payload["destination_postal_code"] = int(req.postalCode)

    headers = {"Authorization": f"Bearer {BITESHIP_KEY}", "Content-Type": "application/json"}
    
    async with httpx.AsyncClient() as client:
        resp = await client.post(f"{BITESHIP_API}/rates/couriers", json=payload, headers=headers)
        if resp.status_code != 200:
            raise HTTPException(status_code=400, detail="Gagal menarik tarif kurir dari platform logistik.")
        
        raw_data = resp.json()
        formatted_rates = []
        for rate in raw_data.get("pricing", []):
            company = rate["company"]
            ctype = rate["type"]
            # Paxel: hanya tampilkan Medium & Large (sembunyikan Small)
            if company == "paxel" and ctype == "small":
                continue
            c_name = company.upper()
            s_name = ctype.upper()
            formatted_rates.append({
                "id": f"{company}_{ctype}",
                "courier": c_name,
                "service": s_name,
                "cost": rate["price"],
                "etd": rate.get("shipment_duration_range", "Estimasi tidak tersedia")
            })
        return {"rates": formatted_rates}

# ==========================================
# 4. SISTEM KASIR KUNCI ORDER (ANTI-CHEAT)
# ==========================================
@app.post("/api/orders")
async def create_order(req: OrderRequest):
    order_id = str(uuid.uuid4())
    order_number = f"RMP{datetime.now(timezone.utc).strftime('%y%m%d')}{uuid.uuid4().hex[:5].upper()}"
    
    subtotal = 0
    total_weight_grams = 0
    validated_items = []

    for item in req.items:
        db_product = db.products.find_one({"_id": item.product_id})
        if not db_product:
            try:
                from bson import ObjectId
                db_product = db.products.find_one({"_id": ObjectId(item.product_id)})
            except:
                pass
        
        p_price = db_product["price"] if db_product else (item.price if item.price > 0 else 89999)
        p_name = db_product["name"] if db_product else item.name
        
        subtotal += p_price * item.quantity
        total_weight_grams += calculate_item_weight(p_name) * item.quantity
        validated_items.append({
            "product_id": item.product_id,
            "name": p_name,
            "price": p_price,
            "quantity": item.quantity,
            "line_total": p_price * item.quantity
        })

    discount = 0
    if req.voucher_code and subtotal >= 100000:
        discount = 20000

    shipping_cost = 0
    try:
        rates_response = await get_rates(RatesRequest(
            items=[CartItem(product_id=i["product_id"], quantity=i["quantity"], name=i["name"], price=i["price"]) for i in validated_items],
            postalCode=req.contact.postalCode,
            latitude=req.contact.latitude,
            longitude=req.contact.longitude
        ))
        for rate in rates_response.get("rates", []):
            if rate["id"] == req.shipping_courier:
                shipping_cost = rate["cost"]
                break
    except:
        raise HTTPException(status_code=400, detail="Konfigurasi rute kurir salah.")

    total = max(0, subtotal - discount + shipping_cost)
    
    req.contact.phone = clean_phone_number(req.contact.phone)
    req.contact.name = sanitize_name(req.contact.name)

    order_document = {
        "_id": order_id,
        "id": order_id,
        "order_number": order_number,
        "status": "pending",
        "items": validated_items,
        "contact": req.contact.dict(),
        "subtotal": subtotal,
        "discount": discount,
        "shipping": shipping_cost,
        "total": total,
        "payment_channel": req.payment_channel,
        "shipping_courier": req.shipping_courier,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    db.orders.insert_one(order_document)

    item_summary = "\n".join([f"- {i['name']} x{i['quantity']}" for i in validated_items])
    wa_text = (
        f"Halo Tim Rimpods, saya ingin melanjutkan pemesanan berikut:\n"
        f"No. Order: {order_number}\n\n"
        f"Detail Pesanan:\n{item_summary}\n"
        f"Pengiriman: {req.shipping_courier.replace('_', ' ').upper()} = Rp{shipping_cost:,}\n\n"
        f"Total: Rp{total:,}\n\n"
        f"Alamat Pengiriman:\n{req.contact.name} ({req.contact.phone})\n"
        f"{req.contact.address}, {req.contact.kecamatan}, {req.contact.city}"
    ).replace(",", ".")
    
    whatsapp_url = f"https://wa.me/{WA_ADMIN_NUMBER}?text={quote(wa_text)}"

    return {
        "id": order_id,
        "order_number": order_number,
        "whatsapp_url": whatsapp_url,
        "tokopedia_url": "https://www.tokopedia.com/rimpods",
        "items": validated_items,
        "total": total
    }

# ==========================================
# 5. INTEGRASI PAYMENT GATEWAY & WEBHOOK
# ==========================================
@app.post("/api/payment/midtrans/snap-token")
async def get_snap_token(req: MidtransRequest):
    order = db.orders.find_one({"id": req.order_id})
    if not order:
        raise HTTPException(status_code=404, detail="Order tidak ditemukan")

    auth_string = base64.b64encode(f"{MIDTRANS_SERVER_KEY}:".encode()).decode()
    
    midtrans_payload = {
        "transaction_details": {
            "order_id": order["order_number"],
            "gross_amount": int(order["total"])
        },
        "customer_details": {
            "first_name": order["contact"]["name"],
            "phone": order["contact"]["phone"],
            "email": order["contact"]["email"]
        }
    }

    async with httpx.AsyncClient() as client:
        resp = await client.post(
            "https://app.midtrans.com/snap/v1/transactions",
            json=midtrans_payload,
            headers={"Authorization": f"Basic {auth_string}", "Content-Type": "application/json"}
        )
        if resp.status_code != 201:
            raise HTTPException(status_code=resp.status_code, detail=resp.text)
        return resp.json()

@app.post("/api/payment/midtrans/webhook")
async def midtrans_webhook(request: Request):
    data = await request.json()
    order_number = data.get("order_id")
    status = data.get("transaction_status")
    
    new_status = "pending"
    if status in ["settlement", "capture"]:
        new_status = "paid"
    elif status in ["deny", "expire", "cancel"]:
        new_status = "failed"

    # PROTEKSI FATAL: Eksekusi Biteship tidak boleh merusak proses Midtrans
    if new_status == "paid":
        order_data = db.orders.find_one({"order_number": order_number})
        if order_data and not order_data.get("shipping_awb"):
            try:
                await auto_book_biteship(order_data)
            except Exception as e:
                print(f"Biteship auto-book gagal: {e}")

    db.orders.update_one(
        {"order_number": order_number},
        {"$set": {"status": new_status, "updated_at": datetime.now(timezone.utc).isoformat()}}
    )
    return {"status": "ok"}


@app.post("/api/admin/orders/{order_number}/sync-payment")
async def admin_sync_payment(order_number: str, admin=Depends(_require_admin)):
    """Tanya status pembayaran langsung ke Midtrans. Jika lunas -> set paid + booking Biteship.
    Jaring pengaman bila webhook Midtrans terlewat."""
    order = db.orders.find_one({"order_number": order_number})
    if not order:
        raise HTTPException(status_code=404, detail="Order tidak ditemukan")

    auth_string = base64.b64encode(f"{MIDTRANS_SERVER_KEY}:".encode()).decode()
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            f"{MIDTRANS_STATUS_BASE}/v2/{order_number}/status",
            headers={"Authorization": f"Basic {auth_string}", "Accept": "application/json"},
        )
    try:
        pay = resp.json()
    except Exception:
        raise HTTPException(status_code=502, detail="Respons Midtrans tidak valid")

    tstatus = pay.get("transaction_status")
    if not tstatus:
        raise HTTPException(
            status_code=400,
            detail=f"Midtrans: {pay.get('status_message', 'transaksi belum ada / belum dibayar')}",
        )

    if tstatus in ["settlement", "capture"]:
        new_status = "paid"
    elif tstatus in ["deny", "expire", "cancel"]:
        new_status = "failed"
    else:
        new_status = "pending"

    booked = False
    biteship_error = None
    if new_status == "paid" and not order.get("shipping_awb"):
        try:
            await auto_book_biteship(order)
            booked = True
        except Exception as e:
            biteship_error = str(e)

    db.orders.update_one(
        {"order_number": order_number},
        {"$set": {"status": new_status, "updated_at": datetime.now(timezone.utc).isoformat()}},
    )
    refreshed = db.orders.find_one({"order_number": order_number}, {"_id": 0}) or {}
    return {
        "order_number": order_number,
        "transaction_status": tstatus,
        "status": new_status,
        "biteship_booked": booked,
        "biteship_error": biteship_error,
        "shipping_awb": refreshed.get("shipping_awb"),
    }

@app.post("/api/shipping/biteship/webhook")
async def biteship_webhook(request: Request):
    """Terima update status pengiriman dari Biteship (event order.status) dan
    perbarui status order berdasarkan AWB/Biteship order id. Verifikasi signature
    bersifat opsional (aktif hanya bila BITESHIP_WEBHOOK_SECRET diset di env)."""
    expected = os.getenv("BITESHIP_WEBHOOK_SECRET")
    header_name = os.getenv("BITESHIP_WEBHOOK_HEADER", "X-Biteship-Signature")
    if expected:
        if request.headers.get(header_name) != expected:
            raise HTTPException(status_code=401, detail="Invalid signature")

    try:
        data = await request.json()
    except Exception:
        return {"status": "ignored"}

    biteship_order_id = data.get("order_id") or data.get("id")
    status = data.get("status") or (data.get("courier") or {}).get("status")
    waybill = data.get("courier_waybill_id") or data.get("waybill_id")

    if biteship_order_id:
        update = {"shipping_updated_at": datetime.now(timezone.utc).isoformat()}
        if status:
            update["shipping_status"] = status
        if waybill:
            update["shipping_waybill"] = waybill
        db.orders.update_one({"shipping_awb": biteship_order_id}, {"$set": update})

    return {"status": "ok"}


async def auto_book_biteship(order):
    raw_courier = order.get("shipping_courier", "jne_reg")
    c_company, _, c_type = raw_courier.partition("_")
    if not c_type:
        c_type = "reg"

    payload = {
        "shipper_contact_name": "Rimpods Storage",
        "shipper_contact_phone": "6282216594354",
        "shipper_contact_email": "admin@rimpods.com",
        "origin_contact_name": "Rimpods Storage",
        "origin_contact_phone": "6282216594354",
        "origin_coordinate": {"latitude": ORIGIN_LAT, "longitude": ORIGIN_LON},
        "origin_address": "Ruko Nirmala Jl Radar Selatan No 83, Pondok Gede, Bekasi",
        "origin_postal_code": int(ORIGIN_POSTAL),
        "destination_contact_name": order["contact"]["name"],
        "destination_contact_phone": order["contact"]["phone"],
        "destination_contact_email": order["contact"]["email"],
        "destination_address": order["contact"]["address"],
        "courier_company": c_company,
        "courier_type": c_type,
        "delivery_type": "now",
        "items": [{
            "name": i["name"][:40],
            "weight": calculate_item_weight(i["name"]),
            "quantity": i["quantity"],
            "value": i["price"]
        } for i in order["items"]]
    }
    
    if order["contact"].get("latitude") and order["contact"].get("longitude"):
        payload["destination_coordinate"] = {
            "latitude": float(order["contact"]["latitude"]),
            "longitude": float(order["contact"]["longitude"])
        }
    else:
        payload["destination_postal_code"] = int(order["contact"]["postalCode"])

    headers = {"Authorization": f"Bearer {BITESHIP_KEY}", "Content-Type": "application/json"}
    async with httpx.AsyncClient() as client:
        res = await client.post(f"{BITESHIP_API}/orders", json=payload, headers=headers)
        if res.status_code != 200:
            raise Exception(f"Biteship {res.status_code}: {res.text[:250]}")
        db.orders.update_one(
            {"id": order["id"]},
            {"$set": {"shipping_awb": res.json().get("id"), "shipping_status": "allocated"}}
        )
        return res.json().get("id")