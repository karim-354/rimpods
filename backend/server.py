import os
import re
import uuid
import base64
import httpx
import pymongo
from datetime import datetime, timezone
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, ConfigDict
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv

load_dotenv()
app = FastAPI(title="Rimpods Monolith Production API")

# ==========================================
# KONEKSI DATABASE & UTILITIES
# ==========================================
MONGO_URL = os.getenv("MONGO_URL", "mongodb://localhost:27017")
DB_NAME = os.getenv("DB_NAME", "test_database")
db = pymongo.MongoClient(MONGO_URL)[DB_NAME]

BITESHIP_KEY = os.getenv("BITESHIP_KEY")
BITESHIP_API = "https://api.biteship.com/v1"
MIDTRANS_SERVER_KEY = os.getenv("MIDTRANS_SERVER_KEY")
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
        "couriers": "grab,gojek,jne,jnt,sicepat,paxel,lalamove",
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
            c_name = rate["company"].upper()
            s_name = rate["type"].upper()
            formatted_rates.append({
                "id": f"{rate['company']}_{rate['type']}",
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
    
    whatsapp_url = f"https://wa.me/{WA_ADMIN_NUMBER}?text={httpx.URL(wa_text)}"

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

async def auto_book_biteship(order):
    raw_courier = order.get("shipping_courier", "jne_reg").split("_")
    c_company = raw_courier[0]
    c_type = raw_courier[1] if len(raw_courier) > 1 else "reg"

    payload = {
        "shipper_contact_name": "Rimpods Storage",
        "shipper_contact_phone": "6282216594354",
        "shipper_contact_email": "admin@rimpods.com",
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
        if res.status_code == 200:
            db.orders.update_one(
                {"id": order["id"]},
                {"$set": {"shipping_awb": res.json().get("id"), "shipping_status": "allocated"}}
            )