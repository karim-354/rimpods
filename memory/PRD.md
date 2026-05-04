# Rimpods Live Coral Food — Sales Landing Page

## Original Problem Statement
"saya ingin buat landing page sales untuk produk2 yang ada di tokopedianya Rimpods live coral food"

User clarifications:
- Produk: 3 listing Tokopedia (Rotifera 2L+Phyto, Paket Hemat 5R+1P, Turn Back Nutrients)
- Tujuan: Edukasi + sales otomatis dengan checkout flow
- Bahasa: Indonesia native & friendly (anti-AI)
- Bonus: Sistem fingerprint_check.py (24 pola robotik) sebelum publish

## Architecture
- **Backend**: FastAPI (`/api/products`, `/api/orders`, `/api/content/verify`)
  - Static catalog of 3 products (data sourced from Tokopedia listings)
  - Order creation generates WhatsApp wa.me URL + Tokopedia URL (no payment gateway integrated; user completes purchase externally)
  - Anti-AI fingerprint module: `/app/backend/fingerprint_check.py` (24 patterns, score 0-100, min pass 55, hard-block corporate, auto-naturalize)
  - CLI version: `/app/scripts/fingerprint_check.py`
- **Frontend**: React + Tailwind + shadcn/ui
  - Routes: `/` (landing), `/checkout`, `/sukses`
  - Cart in localStorage (`rimpods_cart_v1`)
  - Aquatic premium aesthetic: deep navy + coral accent + teal glow, Fraunces + Manrope fonts, glass-morphism cards, bubble + caustics animations

## User Personas
- Reefer pemula: butuh edukasi, ingin ngerti coral food itu apa
- Reefer rajin: ngincer paket hemat untuk feeding rutin
- Reefer panik: tank crash, butuh TBN segera

## What's Implemented (Dec 2025)
### v1
- Hero with stat block + marquee bar
- 3 product cards with rating/sold/highlights/Tokopedia link
- Cerita, Cara Pakai, Testimoni, FAQ, CTA sections
- Cart drawer + Checkout form + Success page
- Anti-AI fingerprint check API + CLI

### v2 (latest)
- WhatsApp number live: +6282216594354 (env `RIMPODS_WHATSAPP`)
- Brand logo Rimpods (gold + tagline) di header, sumber dari customer-assets
- **Meta Pixel** sitewide id `354153630789298` — events: PageView, ViewContent (siap dipasang per produk), AddToCart, InitiateCheckout, Lead, Purchase
- **TikTok Pixel** sitewide id `CNQDS3JC77U0SCE9DUUG` — events: page, ViewContent, AddToCart, InitiateCheckout, SubmitForm, CompletePayment (siap closing dari ads GMV Max TikTok Shop)
- Helper `/app/frontend/src/lib/tracker.js` exposes `trackAddToCart`, `trackInitiateCheckout`, `trackLead`, `trackPurchase` — guarded against ad-blocker (no-throw)

## Backlog (P1/P2)
- P1: Real photos dari Rimpods (sekarang pakai stock Unsplash)
- P1: Logo Rimpods dari Google Drive (link disediakan, perlu download manual)
- P1: Editable WhatsApp number via env (sekarang placeholder 6281234567890)
- P2: Admin dashboard untuk lihat order masuk
- P2: Email confirmation via Resend/SMTP
- P2: Pixel tracking (Meta + Google Ads) untuk conversion attribution
- P2: Stripe / Midtrans integration untuk payment di-page
- P2: Multi-bahasa (English version)

### v3 (Feb 2026)
- **TBN photo swap** ke asset asli Rimpods (customer-assets emergentagent)
- **Upsell bundle split** — accept upsell masuk sebagai cart line terpisah (`${id}-bundle`), tidak merge dengan base item
- **Countdown urgency** 10 menit di UpsellModal (MM:SS, button disable + label "Promo Habis" saat expired)
- **Rimpods 2L photo swap** ke asset Rimpods (`a1.jpeg` + `aa.jpeg` sebagai hover/alt)
- **Backend bundle recognition** — POST `/api/orders` sekarang accept `${id}-bundle` product_id dan otomatis apply 10% discount + label `(Bundle -10%)` + flag `is_bundle: true`

### v4 (Feb 2026 — Conversion Polish)
- **Paket Hemat photo swap** ke asset asli Rimpods (Duo Maut + Saving Bundle)
- **Upsell countdown persistence** — timestamp di `sessionStorage[rimpods_upsell_ts_${id}]`, tidak reset saat modal ditutup-buka
- **Exit-intent popup** → voucher **FIRSTBUY20K** flat Rp20.000 off (min order Rp100.000). Trigger mouseout top viewport (desktop) / 25s timeout (mobile). Sekali per sesi.
- **Voucher backend** — `POST /api/orders` accept `voucher_code`, validate min subtotal, include diskon di WA message. Order schema sekarang punya `discount` + `voucher_code` fields.
- **Voucher frontend** — banner di Checkout (eligible/non-eligible state), auto-apply di payload, auto-clear setelah sukses, tombol remove manual.

### v5 (Feb 2026 — Premium Voice & TikTok Shop)
- **TikTok Shop deep-link asli** per produk (`shop-id.tokopedia.com/view/product/...` dengan encode_params signed) — 3 produk semua pointing ke listing resmi.
- **Rewrite copy sitewide** dengan nada warm-premium (NLP persuasive yang hangat, prestigious tapi inklusif). Target HNW tetap terjaga tanpa terkesan angkuh.
  - Hero: *"Tank yang hidup, bukan sekadar indah."*
  - Produk: *"Tiga pilihan, satu standar kualitas."*
  - Cerita: *"Coral merespons kualitas, bukan janji."*
  - Cara Pakai: *"Tiga langkah, dan coral akan bicara sendiri."*
  - CTA: *"Tank kamu siap memperlihatkan potensinya."*
  - Product taglines: Rotifer 2L ("Nutrisi hidup untuk tank yang ingin lebih dari sekadar jernih."), Paket Hemat ("Ritual feeding yang tenang untuk reefer yang menjaga konsistensi."), TBN ("Langkah tenang saat parameter air mulai bergeser.")
- **WhatsApp message refresh** — formal-warm: *"Halo Tim Rimpods, saya ingin melanjutkan pemesanan berikut…"* + penutup *"Terima kasih, saya tunggu konfirmasinya."*
- Upsell/ExitIntent/Cart/Checkout/Success semua disesuaikan dengan voice yang sama.

### v6 (Feb 2026 — Concierge + Admin Dashboard)
- **Concierge Line** WhatsApp di hero section dengan ikon Crown — link ke admin dengan pesan konsultasi pre-filled, untuk segmen HNW/premium
- **Admin Dashboard** di `/admin` dengan **Emergent Google Auth** + email whitelist (`ADMIN_EMAILS` env var)
  - Login gate: tombol "Masuk dengan Google" → redirect ke auth.emergentagent.com → callback `#session_id=` diproses via `AppRouter` + `AuthCallback` component
  - Non-whitelist email → tampilkan "Akses tidak diizinkan" dengan tombol logout
  - Dashboard KPI: total orders (30d + overall), revenue (30d + overall), voucher redemptions + nilai diskon, channel breakdown
  - Orders table: 50 terbaru dengan order_number, tanggal, customer, item summary, total, voucher, channel, status
  - Voucher performance section: breakdown per kode dengan redemption count + total discount
  - `PATCH /api/admin/orders/{id}/status` untuk update status order (pending/confirmed/shipped/delivered/cancelled)
- **Backend auth module** (`/app/backend/auth.py`): session exchange endpoint dengan Emergent, httpOnly+Secure+SameSite=None cookie, timezone-aware expiry handling, `require_admin` dependency untuk guard route
- **Backend admin module** (`/app/backend/admin.py`): orders list, stats aggregation, status patch

### v7 (Feb 2026 — Admin Actionability)
- **WhatsApp Quick Actions** per order row di admin dashboard
  - Tombol hijau pill di kolom "Aksi" → dropdown 4 template pesan
  - **Konfirmasi Order**: greeting + item summary + total + permintaan bukti transfer
  - **Cek Alamat**: konfirmasi alamat pengiriman sebelum diproses
  - **Kirim Resi**: dialog input (Kurir + No. Resi + ETA) → preview → buka WA
  - **Follow-up**: pesan post-arrival + ajakan review Tokopedia
  - Phone auto-normalize Indonesia (`08xx` / `8xx` / `62xx` → `62xxxxx`)
  - Copy template ke clipboard tanpa buka WA (tombol copy per template)
  - Disabled state kalau customer tidak punya nomor valid

### v8 (Feb 2026 — Midtrans Payment + Price Correction)
- **Midtrans Snap** end-to-end payment integration
  - Backend `/app/backend/payment.py`: Snap transaction creation, webhook handler dengan SHA512 signature verification (constant-time compare), status polling endpoint
  - Frontend `/app/frontend/src/lib/midtrans.js`: Snap.js dynamic loader (idempotent), promise-based `paySnap()` wrapper
  - Channel Midtrans jadi **default** di checkout — menggantikan WhatsApp sebagai opsi utama
  - Support semua bank lokal (BCA/Mandiri/BNI/BRI/CIMB/BSI) via VA, QRIS, e-wallets (GoPay/OVO/DANA/ShopeePay), cicilan 0%
  - Order schema nambah: `midtrans_token`, `midtrans_redirect_url`, `midtrans_transaction_id`, `midtrans_fraud_status`, `payment_type`, `paid_at`
  - Success page dengan fallback "Lanjutkan Pembayaran" kalau popup ditutup user
- **Paket Hemat price correction** — dari Rp549.000 (salah) ke Rp99.999 (+ compare_price Rp129.999 buat framing diskon ke depan)
- **Rating update** — Paket Hemat: 2198 reviews, sold "3rb+" (sesuai data Tokopedia asli)
- **ADMIN_EMAILS** update ke `rimpods@gmail.com`
- **Highlights & description** Paket Hemat diupdate: "4 botol Rotifer + 1 botol Phytoplankton, plus 1 botol Rotifer BONUS" (match Tokopedia)

### v9 (Feb 2026 — Email via Resend)
- **Resend email integration** dengan 4 template branded (dark navy + coral accent, warm-premium Indonesian tone):
  1. **Order Confirmation** — ke customer setelah order dibuat
  2. **Payment Success** — otomatis ter-trigger saat webhook Midtrans confirm "paid"
  3. **Shipping Notification** — ke customer saat admin hit POST `/api/admin/orders/{id}/ship` dengan courier+tracking+ETA
  4. **Admin New Order** — notifikasi ke `EMAIL_ADMIN_NOTIFY` tiap ada order baru, include CTA "Chat di WhatsApp"
- **Non-blocking**: FastAPI `BackgroundTasks` untuk order emails, `asyncio.create_task` untuk webhook/ship. Failure tidak block order flow.
- **Graceful fallback**: jika `RESEND_API_KEY` kosong atau Resend API error, log warning + return None, order creation tetap sukses.
- **HTML template** full inline CSS (email-client safe), branded header/footer dengan order number block, items table, summary rows, address block, CTA button.
- **New endpoint**: `POST /api/admin/orders/{id}/ship?courier=JNE&tracking=CNT123&eta=3-5+hari` — admin-protected, update order status ke `shipped` + auto-kirim email resi

## Test Status
- Backend: 69/69 pytest pass (iter 4–10 cumulative)
- Frontend: no changes (iter-10 backend-only)

## ⚠️ Known Config (Resend Testing Mode)
Akun Resend didaftarkan dengan `ocepjos@gmail.com`. Dalam **testing mode**, Resend hanya kirim ke alamat pemilik akun. Untuk production:
1. Verify domain di https://resend.com/domains (tambah DNS records ke registrar)
2. Setelah verified, ganti `RESEND_FROM_EMAIL` di `/app/backend/.env` dari `onboarding@resend.dev` ke `hello@yourdomain.com`
3. `EMAIL_ADMIN_NOTIFY` bisa dikembalikan ke `rimpods@gmail.com` (atau email lain)
4. Email customer akan otomatis terkirim ke alamat di `contact.email`

Saat ini `EMAIL_ADMIN_NOTIFY=ocepjos@gmail.com` supaya testing bisa jalan. Restart backend setelah ganti env.

## Next Action Items
1. **User**: verify domain di Resend (tambah DNS records) supaya email bisa kirim ke customer manapun
2. **User**: tunggu Midtrans approval production, lalu switch `MIDTRANS_IS_PRODUCTION=true`
3. **User**: login `/admin` via Google dengan `rimpods@gmail.com`

## Backlog
- P2: Frontend — Poll `/api/payment/midtrans/status/{order_number}` di Success page realtime
- P2: Frontend — Tombol "Kirim Resi" di admin dashboard row yang hit /ship endpoint
- P2: Produk low-ticket untuk coverage voucher-ineligible
- P2: English version
- P2: Abandoned cart WhatsApp nudge
