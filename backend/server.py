from fastapi import FastAPI, APIRouter, HTTPException
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional
import uuid
from datetime import datetime, timezone
from urllib.parse import quote

from fingerprint_check import check as fp_check, verify_before_publish

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / ".env")

mongo_url = os.environ["MONGO_URL"]
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ["DB_NAME"]]

app = FastAPI(title="Rimpods Coral Food API")
api_router = APIRouter(prefix="/api")

# === Default config ===
DEFAULT_WA = os.environ.get("RIMPODS_WHATSAPP", "6281234567890")
TOKO_BASE = "https://www.tokopedia.com/rimpods"

# === Static product catalog (mirrors Tokopedia listing) ===
PRODUCTS = [
    {
        "id": "rotifer-2l-phyto",
        "slug": "rotifera-2l-besar",
        "name": "Rimpods Rotifera 2L BESAR + 1 Phytoplankton",
        "tagline": "Untuk tank besar 400L+, coral mekar gila-gilaan",
        "price": 129999,
        "compare_price": 159000,
        "rating": 4.9,
        "reviews": 891,
        "sold": "1rb+",
        "stock": 9370,
        "image": "https://images.unsplash.com/photo-1558642084-fd07fae5282e?w=900&q=80",
        "image_alt": "https://images.unsplash.com/photo-1582967788606-a171c1080cb0?w=900&q=80",
        "tokopedia_url": "https://www.tokopedia.com/rimpods/rimpods-rotifera-2liter-besar-dengan-1-phytoplankton-ideal-untuk-coral-mekar-dalam-tank-besar-1731802588285273240",
        "highlights": [
            "Sekali tuang langsung berasa, tank 400L+ kebanjiran nutrisi mikro hidup",
            "Sudah termasuk 1 botol Phytoplankton bonus",
            "Coral SPS, LPS, Soft, semua suka",
            "Pengiriman dari Bekasi, dipacking khusus biar rotifer tetap hidup",
        ],
        "description": (
            "Inget ya, rotifer ini bikin coral kamu mekar sampe gila-gilaan. "
            "Tank kepenuhan karena coral gendut-gendut bukan tanggung jawab kami, hehe. "
            "Cocok buat reefer yang punya display tank ukuran besar dan pengen lihat polip "
            "ekstensi maksimal. Takaran simpel: tank 400 liter ke atas, tuang 2 liter sekaligus."
        ),
    },
    {
        "id": "paket-hemat-5r-1p",
        "slug": "paket-hemat-5-rotifer-1-phyto",
        "name": "Paket Hemat 5 Rotifer + 1 Phytoplankton",
        "tagline": "Stok bulanan, hemat banyak, cocok reefer rajin",
        "price": 549000,
        "compare_price": 649995,
        "rating": 4.9,
        "reviews": 312,
        "sold": "500+",
        "stock": 240,
        "image": "https://images.unsplash.com/photo-1571687949921-1306bfb24b72?w=900&q=80",
        "image_alt": "https://images.unsplash.com/photo-1583212292454-1fe6229603b7?w=900&q=80",
        "tokopedia_url": "https://www.tokopedia.com/rimpods/paket-hemat-5-rotifer-1-phytoplankton-rotifera-pakan-coral-food",
        "highlights": [
            "5 botol rotifer + 1 botol phytoplankton, satu kirim aja",
            "Hemat sampai Rp100rb dibanding beli satuan",
            "Cocok feeding rutin selama 4-6 minggu",
            "Live shrimp & coral bakal lebih aktif tiap dosing",
        ],
        "description": (
            "Buat kamu yang udah commit kasih makan coral tiap hari, paket ini paling worth. "
            "Lima botol rotifer plus satu phyto, langsung tuang sesuai jadwal feeding. "
            "Rasanya kayak langganan susu segar buat anak-anak coral kamu, tinggal masuk kulkas, "
            "ambil kalau mau pakai."
        ),
    },
    {
        "id": "tbn-turn-back-nutrients",
        "slug": "turn-back-nutrients",
        "name": "Rimpods Turn Back Nutrients (TBN)",
        "tagline": "Tank crash? Balikin fresh seperti baru",
        "price": 199000,
        "compare_price": 229000,
        "rating": 5.0,
        "reviews": 7,
        "sold": "23+",
        "stock": 2,
        "image": "https://images.unsplash.com/photo-1559827260-dc66d52bef19?w=900&q=80",
        "image_alt": "https://images.unsplash.com/photo-1546182990-dffeafbe841d?w=900&q=80",
        "tokopedia_url": "https://www.tokopedia.com/rimpods/rimpods-turn-back-nutrients-1729680758563637400",
        "highlights": [
            "Bantu reset parameter air pasca tank crash",
            "Bekerja sama dengan filtrasi & water change",
            "Aman buat coral, ikan, invertebrata",
            "Simpan di kulkas biar awet",
        ],
        "description": (
            "Pernah tank tiba-tiba berubah keruh, parameter ngaco, coral mulai nutup? Tenang. "
            "TBN bantu kamu balikin kondisi air ke fase fresh. Cek parameter, benerin filter, "
            "water change 20-50 persen, ganti media, lalu tuang TBN. Setelah itu cek kualitas "
            "air rutin tiap minggu biar nggak kejadian lagi."
        ),
    },
]


# === Models ===
class ContactInfo(BaseModel):
    name: str
    phone: str
    email: Optional[str] = None
    address: str
    city: str
    notes: Optional[str] = ""


class CartItem(BaseModel):
    product_id: str
    quantity: int = Field(ge=1, le=99)


class OrderCreate(BaseModel):
    items: List[CartItem]
    contact: ContactInfo
    payment_channel: str = "whatsapp"  # 'whatsapp' or 'tokopedia'


class Order(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    order_number: str
    items: List[dict]
    contact: dict
    subtotal: int
    shipping: int
    total: int
    payment_channel: str
    whatsapp_url: str
    tokopedia_url: str
    status: str = "pending"
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class ContentCheckRequest(BaseModel):
    text: str
    auto_fix: bool = True


# === Helpers ===
def _find_product(pid: str):
    for p in PRODUCTS:
        if p["id"] == pid:
            return p
    return None


def _build_whatsapp_url(order_number: str, items: list, contact: dict, total: int) -> str:
    lines = [
        "Halo Rimpods! Aku mau order nih:",
        f"No order: *{order_number}*",
        "",
        "*Pesanan:*",
    ]
    for it in items:
        lines.append(f"- {it['name']} x{it['quantity']} = Rp{it['line_total']:,}".replace(",", "."))
    lines += [
        "",
        f"*Total:* Rp{total:,}".replace(",", "."),
        "",
        "*Kirim ke:*",
        f"{contact['name']} ({contact['phone']})",
        f"{contact['address']}, {contact['city']}",
    ]
    if contact.get("notes"):
        lines += ["", f"Catatan: {contact['notes']}"]
    msg = "\n".join(lines)
    return f"https://wa.me/{DEFAULT_WA}?text={quote(msg)}"


# === Routes ===
@api_router.get("/")
async def root():
    return {"service": "Rimpods Coral Food", "status": "ok"}


@api_router.get("/products")
async def list_products():
    return {"products": PRODUCTS}


@api_router.get("/products/{product_id}")
async def get_product(product_id: str):
    p = _find_product(product_id)
    if not p:
        raise HTTPException(status_code=404, detail="Produk tidak ditemukan")
    return p


@api_router.post("/orders", response_model=Order)
async def create_order(payload: OrderCreate):
    if not payload.items:
        raise HTTPException(status_code=400, detail="Keranjang kosong")

    detailed_items = []
    subtotal = 0
    for it in payload.items:
        prod = _find_product(it.product_id)
        if not prod:
            raise HTTPException(status_code=400, detail=f"Produk {it.product_id} tidak valid")
        line_total = prod["price"] * it.quantity
        subtotal += line_total
        detailed_items.append({
            "product_id": prod["id"],
            "name": prod["name"],
            "price": prod["price"],
            "quantity": it.quantity,
            "line_total": line_total,
            "tokopedia_url": prod["tokopedia_url"],
        })

    shipping = 0 if subtotal >= 250000 else 18000
    total = subtotal + shipping

    order_number = "RMP" + datetime.now(timezone.utc).strftime("%y%m%d") + uuid.uuid4().hex[:5].upper()
    contact_dict = payload.contact.model_dump()

    wa_url = _build_whatsapp_url(order_number, detailed_items, contact_dict, total)
    # First product Tokopedia link as primary fallback
    toko_url = detailed_items[0]["tokopedia_url"] if detailed_items else TOKO_BASE

    order = Order(
        order_number=order_number,
        items=detailed_items,
        contact=contact_dict,
        subtotal=subtotal,
        shipping=shipping,
        total=total,
        payment_channel=payload.payment_channel,
        whatsapp_url=wa_url,
        tokopedia_url=toko_url,
    )
    doc = order.model_dump()
    doc["created_at"] = doc["created_at"].isoformat()
    await db.orders.insert_one(doc)
    return order


@api_router.get("/orders/{order_id}", response_model=Order)
async def get_order(order_id: str):
    doc = await db.orders.find_one({"id": order_id}, {"_id": 0})
    if not doc:
        raise HTTPException(status_code=404, detail="Order tidak ditemukan")
    if isinstance(doc.get("created_at"), str):
        doc["created_at"] = datetime.fromisoformat(doc["created_at"])
    return Order(**doc)


@api_router.post("/content/verify")
async def verify_content(payload: ContentCheckRequest):
    """Anti-AI fingerprint check, jalankan sebelum konten dipublikasi."""
    return verify_before_publish(payload.text, auto_fix=payload.auto_fix)


@api_router.post("/content/quick-check")
async def quick_check(payload: ContentCheckRequest):
    return fp_check(payload.text, auto_fix=False)


app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get("CORS_ORIGINS", "*").split(","),
    allow_methods=["*"],
    allow_headers=["*"],
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
