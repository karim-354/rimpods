"""Wall of Reefs — testimoni asli pembeli (diimpor dari Tokopedia rimpods, Jun 2026).
Public: GET /api/testimonials. Admin CRUD: /api/admin/testimonials.
Seed idempotent (upsert by id) — aman dipanggil setiap startup."""
import uuid
from datetime import datetime, timezone
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

# Statistik agregat toko Tokopedia rimpods (diverifikasi Jun 2026)
SHOP_STATS = {
    "id": "tokopedia",
    "rating": 4.9,
    "total_ratings": 6261,
    "total_reviews": 1451,
    "satisfaction_pct": 98,
    "five_star_count": 6052,
    "five_star_pct": 96.66,
    "total_sold": "15 rb+",
    "store_url": "https://www.tokopedia.com/rimpods",
    "review_url": "https://www.tokopedia.com/rimpods/review",
}

# d = date label relatif saat scraping, p = foto review (sudah diunduh ke /testimonials/)
_T = [
    # ---- Rotifer Live Coral Food ----
    {"name": "Achmad", "product": "Rotifer Live Coral Food", "d": "1+ tahun lalu",
     "text": "selalu puas belanja disini..coral jd tambah sehat dan subur..terimakasih ya",
     "p": ["achmad-1.jpg", "achmad-2.jpg", "achmad-3.jpg"]},
    {"name": "Riyan", "product": "Rotifer Live Coral Food", "d": "1+ tahun lalu",
     "text": "pelayanan oke mantep dikasih bonus LBS pula. cuma pas pengirimannya aja agak lama, tp barang aman sampe alamat dan masih bisa dipake",
     "p": ["riyan-1.jpg", "riyan-2.jpg"]},
    {"name": "Achmad", "product": "Rotifer Live Coral Food", "d": "1+ tahun lalu",
     "text": "kesekian kalinya belanja disini..selalu puas dgn barangnya..terimakasih jg buat bonusnya", "p": []},
    {"name": "solichin", "product": "Rotifer Live Coral Food", "d": "1+ tahun lalu",
     "text": "mantapp,sll bli dsini,smoga coralnya pd gemuk2,recomended seller", "p": []},
    {"name": "solichin", "product": "Rotifer Live Coral Food", "d": "9 bulan lalu",
     "text": "mantap jiwa,sll order dsini,sellernya gercep,produknya jg mantul,recomended seller👍", "p": []},
    {"name": "H***a", "product": "Rotifer Live Coral Food", "d": "1+ tahun lalu",
     "text": "barang sudah sampe cepet bangggeeeettt .. blm dicoba mudah2an bereaksi.. mantaaaap", "p": []},
    {"name": "NANANG", "product": "Rotifer Live Coral Food", "d": "1+ tahun lalu",
     "text": "mendarat dengan selamat, baru d coba semoga coral jd gendut²", "p": []},
    {"name": "Hanif", "product": "Rotifer Live Coral Food", "d": "1+ tahun lalu",
     "text": "coral2 pada makmur apalagi sinarinanya kaya donat langsung wkwk", "p": []},
    {"name": "Rian", "product": "Rotifer Live Coral Food", "d": "1+ tahun lalu",
     "text": "biar bintang yg berbicara,....👍👍👍👍👍", "p": []},
    # ---- Paket Hemat 5 Rotifer + 1 Phyto ----
    {"name": "J", "product": "Paket Hemat 5R + 1 Phyto", "d": "1+ tahun lalu",
     "text": "Good product..... Good packing .... Fast response.... Fast shipping..... Recommended seller....",
     "p": ["j-1.jpg", "j-2.jpg", "j-3.jpg"]},
    {"name": "Falisha", "product": "Paket Hemat 5R + 1 Phyto", "d": "1+ tahun lalu",
     "text": "Mantap....!!!!! 24 jam langsung mekar gendut² hahahah siap² jadi langganan nih",
     "p": ["falisha-1.jpg", "falisha-2.jpg", "falisha-3.jpg"]},
    {"name": "azharyusuf", "product": "Paket Hemat 5R + 1 Phyto", "d": "1+ tahun lalu",
     "text": "pengiriman cepat dan hasil top..semua sehat dan mekar...recomended seller", "p": []},
    {"name": "Budi", "product": "Paket Hemat 5R + 1 Phyto", "d": "1+ tahun lalu",
     "text": "paket diterima dgn baik, seller fast respon, konsultasi langsung dilayani dgn baik dan diberi penjelasan2 yg lengkap", "p": []},
    {"name": "M***a", "product": "Paket Hemat 5R + 1 Phyto", "d": "1+ tahun lalu",
     "text": "Pelayanan terbaik! Kirimnya gercep. Koral koral langsung glowing", "p": []},
    {"name": "Achmad", "product": "Paket Hemat 5R + 1 Phyto", "d": "1+ tahun lalu",
     "text": "sudah langganan belanja disini..selalu puas dgn hasilnya, coral jd tambah sehat dan gemuk2..terimakasih rimpods", "p": []},
    {"name": "S***t", "product": "Paket Hemat 5R + 1 Phyto", "d": "1+ tahun lalu",
     "text": "Mendarat dengan selamat. Paket aman dengan packing bubble tebal. Pengiriman juga wuzz... cepet sampai dari Bekasi ke Purwokerto. Terimakasih Rimpods", "p": []},
    # ---- Rotifera 2L + Phytoplankton ----
    {"name": "Aliyena", "product": "Rotifera 2L + Phyto", "d": "9 bulan lalu",
     "text": "Packing rapih dan aman. Semoga hasilnya sesuai harapan. Terima kasih.",
     "p": ["aliyena-1.jpg", "aliyena-2.jpg"]},
    {"name": "Andy", "product": "Rotifera 2L + Phyto", "d": "1+ tahun lalu",
     "text": "beli, tuang, trus gemuk2 deh..... recomended seller",
     "p": ["andy-1.jpg", "andy-2.jpg"]},
    {"name": "R***i", "product": "Rotifera 2L + Phyto", "d": "1+ tahun lalu",
     "text": "pengiriman aman, lgsg tuang biar isi tank makin joss", "p": []},
    {"name": "I***a", "product": "Rotifera 2L + Phyto", "d": "1+ tahun lalu",
     "text": "seller komunikatif, diberikan edukasi terkait produknya, barang sesuai", "p": []},
    {"name": "Benni", "product": "Rotifera 2L + Phyto", "d": "1+ tahun lalu",
     "text": "Bisa buat pengganti coral food, lebih hemat dibanding pake dari brand2 terkenal", "p": []},
    {"name": "muhamad", "product": "Rotifera 2L + Phyto", "d": "1+ tahun lalu",
     "text": "fast respon, perdana nyobain smoga coral n ikanny sehat smua...🙏🙏🙏", "p": []},
    {"name": "R***i", "product": "Rotifera 2L + Phyto", "d": "1+ tahun lalu",
     "text": "pesanan yg kesekian kali,, packing aman rapih, pengiriman jg super cepat, pesen sore pagi udh sampe", "p": []},
    {"name": "L***k", "product": "Rotifera 2L + Phyto", "d": "1+ tahun lalu",
     "text": "barang yg sangat bagus untuk aquarium laut. semoga semakin sukses", "p": []},
    {"name": "Ferry", "product": "Rotifera 2L + Phyto", "d": "1+ tahun lalu",
     "text": "respon cepat pengiriman sangat cepat dan terima kasih atas bonus lbsnya", "p": []},
    # ---- Phytoplankton ----
    {"name": "NANANG", "product": "Phytoplankton", "d": "1+ tahun lalu",
     "text": "ga perlu ditanya lagi, ini toko memang gila. beli 2 kmren dapat bonus 2 botol hanya karena vidio tuang ke MT, coral jg jd gendut².. mantap",
     "p": ["nanang-1.jpg", "nanang-2.jpg"]},
    {"name": "Bagus", "product": "Phytoplankton", "d": "1+ tahun lalu",
     "text": "pengiriman sangat cepat, respon penjual juga sangat ramah, nanya ini itu pasti dijawab dgn jelas, trimakasih",
     "p": ["bagus-1.jpg"]},
    {"name": "Teguh", "product": "Phytoplankton", "d": "1+ tahun lalu",
     "text": "sangat sangat luar biasa, best seller lah pokonya", "p": []},
    {"name": "Y***a", "product": "Phytoplankton", "d": "1+ tahun lalu",
     "text": "ga ragu klo beli disini pelayanannya super mantap", "p": []},
    {"name": "A***i", "product": "Phytoplankton", "d": "1+ tahun lalu",
     "text": "respon cpt, sesuai pesanan, segera akan dicoba", "p": []},
    {"name": "sopian", "product": "Phytoplankton", "d": "1+ tahun lalu",
     "text": "beli kemarin sore hari ini udh sampe ajj.", "p": []},
    {"name": "Junianto", "product": "Phytoplankton", "d": "1+ tahun lalu",
     "text": "cepat respon ok banget penjualnya...", "p": []},
    {"name": "Nursyamsi", "product": "Phytoplankton", "d": "1+ tahun lalu",
     "text": "kondisi sempurna 👍👍", "p": []},
    {"name": "Catur", "product": "Phytoplankton", "d": "1+ tahun lalu",
     "text": "dpt bonus lbs 🤩", "p": []},
    {"name": "ERIC", "product": "Phytoplankton", "d": "1+ tahun lalu",
     "text": "packingan mantap & admin nya jg ramah n fast respon 👍 terima kasih min, semoga hasilnya jg memuaskan ✌", "p": []},
]


def seed_testimonials(sync_db):
    """Idempotent: upsert by stable id tkp-XXX. Pakai pymongo (sync), dipanggil saat startup."""
    try:
        for i, t in enumerate(_T, start=1):
            doc = {
                "id": f"tkp-{i:03d}",
                "name": t["name"],
                "text": t["text"],
                "product": t["product"],
                "date_label": t["d"],
                "photos": [f"/testimonials/{f}" for f in t["p"]],
                "rating": 5,
                "source": "tokopedia",
                "order": i,
            }
            sync_db.testimonials.update_one(
                {"id": doc["id"]},
                {"$set": doc, "$setOnInsert": {"visible": True, "created_at": datetime.now(timezone.utc).isoformat()}},
                upsert=True,
            )
        sync_db.shop_stats.update_one({"id": "tokopedia"}, {"$set": SHOP_STATS}, upsert=True)
        print(f"[seed_testimonials] {len(_T)} testimoni siap")
    except Exception as e:
        print(f"[seed_testimonials] warning: {e}")


class TestimonialIn(BaseModel):
    name: str
    text: str
    product: Optional[str] = None
    date_label: Optional[str] = None
    photos: List[str] = []
    rating: int = 5
    source: str = "manual"
    visible: bool = True


class TestimonialUpdate(BaseModel):
    name: Optional[str] = None
    text: Optional[str] = None
    product: Optional[str] = None
    date_label: Optional[str] = None
    photos: Optional[List[str]] = None
    rating: Optional[int] = None
    visible: Optional[bool] = None


def build_testimonials_router(db, require_admin) -> APIRouter:
    router = APIRouter(prefix="/api", tags=["testimonials"])

    @router.get("/testimonials")
    async def list_public():
        stats = await db.shop_stats.find_one({"id": "tokopedia"}, {"_id": 0})
        items = await db.testimonials.find({"visible": True}, {"_id": 0}).sort("order", 1).to_list(200)
        return {"stats": stats or SHOP_STATS, "testimonials": items}

    @router.get("/admin/testimonials")
    async def list_all(admin=Depends(require_admin)):
        items = await db.testimonials.find({}, {"_id": 0}).sort("order", 1).to_list(500)
        return {"testimonials": items}

    @router.post("/admin/testimonials")
    async def create(body: TestimonialIn, admin=Depends(require_admin)):
        last = await db.testimonials.find_one({}, {"_id": 0, "order": 1}, sort=[("order", -1)])
        doc = body.model_dump()
        doc["id"] = f"man-{uuid.uuid4().hex[:8]}"
        doc["order"] = (last["order"] + 1) if last else 1
        doc["created_at"] = datetime.now(timezone.utc).isoformat()
        await db.testimonials.insert_one(dict(doc))
        doc.pop("_id", None)
        return {"ok": True, "testimonial": doc}

    @router.put("/admin/testimonials/{tid}")
    async def update(tid: str, body: TestimonialUpdate, admin=Depends(require_admin)):
        changes = {k: v for k, v in body.model_dump().items() if v is not None}
        if not changes:
            raise HTTPException(400, "Tidak ada perubahan")
        result = await db.testimonials.update_one({"id": tid}, {"$set": changes})
        if result.matched_count == 0:
            raise HTTPException(404, "Testimoni tidak ditemukan")
        return {"ok": True}

    @router.delete("/admin/testimonials/{tid}")
    async def delete(tid: str, admin=Depends(require_admin)):
        result = await db.testimonials.delete_one({"id": tid})
        return {"ok": result.deleted_count > 0}

    return router
