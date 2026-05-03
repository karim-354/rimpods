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

## Test Status
- Backend: 45/45 pytest pass (iter 4–8 cumulative — iter 8 regression only)
- Frontend: 10/10 iter-8 checks PASS, tidak ada regression

## Next Action Items
1. **Pending user input**: Email admin Google asli (update `ADMIN_EMAILS` di `/app/backend/.env`)
2. **Task 4 Pending — Midtrans**: butuh kredensial dari user (Server Key + Client Key + Merchant ID). Code skeleton siap diimplementasi saat keys tersedia.
3. **Task 3 Pending — Email SMTP**: butuh SMTP host/port/user/pass

## Backlog
- P2: Produk low-ticket (<Rp100k) untuk coverage voucher-ineligible
- P2: English version
- P2: Abandoned cart WhatsApp nudge
