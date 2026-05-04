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
from auth import build_auth_router
from admin import build_admin_router
from payment import build_payment_router

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
        "name": "Rimpods Rotifera 2L + Phytoplankton",
        "tagline": "Nutrisi hidup untuk tank yang ingin lebih dari sekadar jernih.",
        "price": 129999,
        "compare_price": 159000,
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
        "price": 99999,
        "compare_price": 129999,
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
    voucher_code: Optional[str] = None


class Order(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    order_number: str
    items: List[dict]
    contact: dict
    subtotal: int
    shipping: int
    discount: int = 0
    voucher_code: Optional[str] = None
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
BUNDLE_SUFFIX = "-bundle"
BUNDLE_DISCOUNT = 0.10  # 10% off when ordered as upsell bundle
VOUCHERS = {
    # code -> (flat discount in IDR, min subtotal to activate)
    "FIRSTBUY20K": (20000, 100000),
}


def _find_product(pid: str):
    for p in PRODUCTS:
        if p["id"] == pid:
            return p
    return None


def _resolve_cart_item(pid: str):
    """Resolve a cart product_id into (product, effective_price, display_name, is_bundle).

    Accepts both base ids (e.g. 'tbn-turn-back-nutrients') and bundle ids
    (e.g. 'tbn-turn-back-nutrients-bundle'). Bundle items get 10% off.
    """
    is_bundle = pid.endswith(BUNDLE_SUFFIX)
    base_id = pid[: -len(BUNDLE_SUFFIX)] if is_bundle else pid
    prod = _find_product(base_id)
    if not prod:
        return None, 0, "", False
    if is_bundle:
        price = round(prod["price"] * (1 - BUNDLE_DISCOUNT))
        name = f"{prod['name']} (Bundle -10%)"
    else:
        price = prod["price"]
        name = prod["name"]
    return prod, price, name, is_bundle


def _build_whatsapp_url(order_number: str, items: list, contact: dict, total: int,
                        discount: int = 0, voucher_code: Optional[str] = None) -> str:
    lines = [
        "Halo Tim Rimpods, saya ingin melanjutkan pemesanan berikut:",
        f"No. Order: *{order_number}*",
        "",
        "*Detail Pesanan:*",
    ]
    for it in items:
        lines.append(f"- {it['name']} x{it['quantity']} = Rp{it['line_total']:,}".replace(",", "."))
    if discount > 0 and voucher_code:
        lines.append(f"- Voucher {voucher_code} = -Rp{discount:,}".replace(",", "."))
    lines += [
        "",
        f"*Total:* Rp{total:,}".replace(",", "."),
        "",
        "*Alamat Pengiriman:*",
        f"{contact['name']} ({contact['phone']})",
        f"{contact['address']}, {contact['city']}",
    ]
    if contact.get("notes"):
        lines += ["", f"Catatan tambahan: {contact['notes']}"]
    lines += ["", "Terima kasih, saya tunggu konfirmasinya."]
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
        prod, price, name, is_bundle = _resolve_cart_item(it.product_id)
        if not prod:
            raise HTTPException(status_code=400, detail=f"Produk {it.product_id} tidak valid")
        line_total = price * it.quantity
        subtotal += line_total
        detailed_items.append({
            "product_id": it.product_id,
            "name": name,
            "price": price,
            "quantity": it.quantity,
            "line_total": line_total,
            "tokopedia_url": prod["tokopedia_url"],
            "is_bundle": is_bundle,
        })

    shipping = 0 if subtotal >= 250000 else 18000

    # Apply voucher discount (never below 0, and never discounts shipping)
    discount = 0
    voucher_code = (payload.voucher_code or "").strip().upper() or None
    if voucher_code and voucher_code in VOUCHERS:
        flat, min_sub = VOUCHERS[voucher_code]
        if subtotal >= min_sub:
            discount = min(flat, subtotal)
        else:
            voucher_code = None
    else:
        voucher_code = None  # ignore invalid codes silently

    total = subtotal - discount + shipping

    order_number = "RMP" + datetime.now(timezone.utc).strftime("%y%m%d") + uuid.uuid4().hex[:5].upper()
    contact_dict = payload.contact.model_dump()

    wa_url = _build_whatsapp_url(order_number, detailed_items, contact_dict, total,
                                 discount=discount, voucher_code=voucher_code)
    # First product Tokopedia link as primary fallback
    toko_url = detailed_items[0]["tokopedia_url"] if detailed_items else TOKO_BASE

    order = Order(
        order_number=order_number,
        items=detailed_items,
        contact=contact_dict,
        subtotal=subtotal,
        shipping=shipping,
        discount=discount,
        voucher_code=voucher_code,
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

# === Google Auth (Emergent) + Admin Dashboard ===
_auth_router, _current_user, _require_admin = build_auth_router(db)
app.include_router(_auth_router)
app.include_router(build_admin_router(db, _require_admin))
app.include_router(build_payment_router(db))

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
