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

### v3 (Jun 2026)
- **Mythos Throughline embed** (`frontend/public/mythos-throughline.js` v2 + config di `public/index.html`):
  garis neon scroll-drawn dari hero H1 → kartu produk → section cerita/cara-pakai/testimoni/faq →
  **bercabang (fork) jadi 2 panah gold** menunjuk CTA "Mulai Belanja" & "Konsultasi dengan Kami".
  Eye-level sync, gradient warna per section, SPA-aware (non-aktif otomatis di /checkout /sukses /admin).
  **Comet head**: dot kelap-kelip (core putih + glow gold twinkle + ring ripple 1.6s) menempel di ujung garis
  yang sedang tergambar; saat fork di CTA, dot pecah jadi 2 mengikuti tiap cabang.
  Alur di section produk: menyentuh tombol "Masukkan Keranjang" ketiga produk berurutan (anchor yOffset -22/0/+22).
  **Touch pulse**: tombol yang sedang dilintasi comet head ikut berdenyut halus (class .mythos-touch,
  scale 1.045 + glow gold) — aktif di 3 tombol keranjang + 2 tombol CTA.
- **Optimasi performa (Jun 2026)**:
  - Code splitting React.lazy di App.js: Checkout (berisi Leaflet ~48KB gz), Success, Admin, AuthCallback
    jadi chunk terpisah — bundle awal turun ke 143KB gz.
  - Font Google dipindah dari @import CSS (render-blocking) ke <link> di head + preconnect.
  - snap.js Midtrans & emergent-main.js diberi defer.
  - Hero image: fetchPriority="high" + decoding async + <link rel="preload"> (sebelumnya loading="lazy" — buruk utk LCP).
  - Preconnect ke customer-assets.emergentagent.com. Logo header tidak lagi lazy.
  - **Logo PNG (105–135KB) → WebP lokal 5–7KB** di `frontend/public/img/` (brand.js + footer diarahkan ke /img/*.webp).
- **Mythos v3 (di bawah teks)**: cage zIndex 1 + semua container konten section diberi `relative z-10`
  → garis lewat DI BAWAH teks/kartu (terlihat di ruang kosong & samar menembus glass-card).
  Start point pindah ke badge "Pakan coral hidup" (startSide: 'bottom-left' — mulai dari kiri-bawah badge,
  keluar horizontal ke kanan via cubicH, melengkung turun ke TENGAH gambar hero — menyelam di balik gambar),
  guard clamp di lengthAtY utk segmen horizontal.
- **Mythos v4 — "di bawah teks, di atas box" (premium layering, Jun 2026)**:
  - Hierarki: background < box/kartu/gambar < garis SVG (cage z:1) < teks.
  - CSS `section :is(h1,h2,h3,h4,p,li,blockquote){position:relative;z-index:10}` di index.css mengangkat semua teks di atas garis. SEMUA `z-10` container di Landing.jsx DIHAPUS (0 tersisa).
  - Teks dlm glass-card (stacking ctx backdrop-filter) tak bisa diangkat → rute garis dirancang menghindarinya:
    produk: turun via celah antar kartu 1-2 (anchor card2 left -18, yOffset -300 & +250), dip ke tombol1,
    rise di atas harga (b.left+30, yOffset -34), dip tombol2, rise, dip tombol3, keluar bawah.
    cerita: tetap -240 (melintas di atas gambar kolase = box, diizinkan). cara-pakai: offset 660 (margin kanan luar).
    testimoni: -640 (margin kiri luar). faq: 560 (margin kanan luar).
    CTA: turun di luar kiri kartu (2 anchor cta-shop-btn left -430, yOffset -180 & -44), masuk via celah
    whitespace di bawah paragraf, forkGap 20, endGap -24 → panah & dot cabang mendarat DI tombol.
  - Fix js: epsilon 2px utk segmen horizontal datar (garis berhenti dini krn float mismatch), running-max
    monotonic di lenSamples (dukung dip/wave naik-turun kecil).
  - PELAJARAN: JANGAN edit paralel banyak search_replace pada SATU file — 2 dari 9 edit Landing.jsx hilang
    (race condition) walau dilaporkan sukses. Edit file yang sama harus berurutan + verifikasi grep.
- **Mythos v5 — Mobile fix (Jun 2026)**:
  - `CFG.mobile` override (aktif < 768px via `activeCfg()` saat buildPath): anchors lembut (offset ±110),
    TANPA fork — `endSelector: '.glass-card.p-10'` (panah tunggal menunjuk kartu CTA dari atas).
  - `clampX(10..W-10)` di semua titik path — garis tak pernah keluar frame.
  - Media query injeksi: `.glass-card{position:relative;z-index:5}` di mobile → garis menyelinap DI BAWAH
    kartu (terlihat di celah antar kartu), teks aman.
  - Kecepatan: rasio pathLength/spanY mobile = 1.02 (sebelumnya melesat krn ekskursi horizontal besar).
  - `.mythos-touch` dipisah: `a.mythos-touch{display:inline-block}` saja (display inline-block di div block
    merusak layout). Touch target singleMode = elemen endSelector.
  - Desktop tidak berubah (regresi dicek: fork 2 cabang + dots tetap jalan).
- **Meta Conversions API (CAPI) server-side**: `send_meta_capi_purchase()` di `backend/server.py`.
  Purchase event ditembak dari webhook Midtrans + admin sync-payment saat status `settlement/capture`.
  Dedup dgn pixel browser via event_id deterministik `purchase-{order_number}` (tracker.js ikut kirim eventID).
  Email/phone di-SHA256 (phone dinormalisasi 62xxx). Idempotent via flag `meta_capi_sent` di order.
  Env: `META_PIXEL_ID`, `META_CAPI_ACCESS_TOKEN`, opsional `META_CAPI_TEST_EVENT_CODE` (backend/.env).
  Token tervalidasi live; dry-run full code path OK tanpa mencatat event palsu.

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

### v11 (Feb 2026 — Production Email Domain)
- **Domain `rimpods.com` verified di Resend** — email production aktif
- **Sender**: `Rimpods <Curhat@rimpods.com>` (brand voice warm & unik)
- **Reply-to** & **EMAIL_ADMIN_NOTIFY**: `rimpods@gmail.com`
- **Rate-limit retry**: 1× auto-retry saat kena Resend 2 req/sec limit

### v12 (Feb 2026 — Brand Logo Integration)
- Logo Rimpods ke Header, Footer, Admin Dashboard, Email template, Favicon + Apple touch icon
- Meta OG + Twitter preview pakai logo gold
- Brand assets terpusat di `/app/frontend/src/lib/brand.js`

### v13 (Feb 2026 — Production Midtrans + Paid Shipping)
- **Midtrans PRODUCTION mode active** — keys: `Mid-client-E0IGvMibArVXfy3U` + `Mid-server-KMT2CoI_jECmpWUq0oL6y_Em`, Merchant `M321126389`, `IS_PRODUCTION=true` di backend + frontend `.env`. Real transactions ready.
- **Webhook test passed** by user via Midtrans Simulator (`settlement` notification with valid signature received & processed)
- **Paid Shipping (3 couriers)** menggantikan free-shipping-if-Rp250k:
  - Backend `/app/backend/shipping.py` — zone-based pricing per courier (Paxel/JNT/Tiki) dengan 4 zone Indonesia (Jabodetabek, Jawa, Sumatera+Bali, Indonesia Timur)
  - Endpoint `GET /api/shipping/rates?city=&kecamatan=` → return 3 courier options (cost + ETD)
  - Customer wajib pilih kurir sebelum checkout. Default ke kurir termurah otomatis.
  - WhatsApp message include line `Pengiriman {Courier} {Service} = Rp{cost}`
  - Order schema nambah `shipping_courier`, `shipping_service`, `shipping_etd`
- **Frontend Checkout** — field Kecamatan baru, debounced rates fetch (400ms), RadioGroup courier selector dengan ETD info + harga, summary update otomatis on courier switch
- **Image swap** — Hero (Instagram Carousel Perang Bakteri Koral 2026) + Cerita section (Dramatic 5-Photo Collage). Branded asset user upload.
- **Cart drawer** — hapus copy "gratis ongkir Jabodetabek", row Pengiriman jadi "Pilih kurir di checkout"

## Test Status
- Backend: 88/88 pytest pass (iter 4–12 cumulative)
- Frontend: 9/10 iter-12 (1 minor toast vs HTML5-required UX choice, functionally equivalent)

## ⚠️ Live Mode Notes
- Midtrans IS_PRODUCTION=true — semua call ke `/api/payment/midtrans/snap-token` akan trigger real transaction. Test orders bisa dibatalkan via Midtrans dashboard.
- Pastikan Payment Notification URL di Midtrans dashboard sudah pointing ke `https://rimpods.com/api/payment/midtrans/notification`
- Settlement T+1 ke rekening yang terdaftar di Midtrans.

### v14 (Feb 2026 — Weight-Aware Shipping + Premium Image Display)
- **Per-product weight** ditambah ke katalog:
  - Rimpods Rotifera 2L + Phyto: 3.0 kg
  - Rimpods Paket Hemat 5R+1P: 2.0 kg
  - Rimpods TBN: 0.7 kg
- **Weight-aware shipping calculator** — rate struktur sekarang `first_kg` + `next_kg` per courier per zone. Cart total weight di-compute dari product.weight_kg × quantity, rounded UP ke nearest kg (min 1kg). Formula: `total = first_kg + (billable_kg - 1) × next_kg`
- **POST /api/shipping/rates** sekarang accept `weight_kg` param. Order response include `shipping_weight_kg`.
- **Frontend Checkout** — display "Berat paket: X.X kg" di shipping section, otomatis refetch rates saat cart weight change.
- **Hero & Cerita images jadi premium** — `object-cover` diganti `object-contain` + `max-h` + soft dark background biar gambar utuh tampil, tidak terpotong. Aspect ratio asli image dipertahankan.

## Test Status
- Backend: 88/88 pytest pass + weight calc verified (3.7kg cart → 4kg billable → JNT Jakarta Rp33.000 = 15K + 3×6K)
- Frontend: lint pass, smoke tested
- **Logo Rimpods** terintegrasi ke 5 touchpoints:
  - 🌐 **Landing header** (sticky, sebelah kiri)
  - 🌐 **Landing footer** (kiri bawah dengan copyright)
  - 📊 **Admin dashboard header** (kiri atas)
  - 📧 **Email template** (top header + footer, 4 template branded)
  - 🔖 **Favicon + Apple touch icon** (tab browser)
- **Meta tags Open Graph + Twitter** untuk social preview (`og:image`, `twitter:image`, `og:title`, `og:description`) pakai versi gold logo
- **Brand assets terpusat** di `/app/frontend/src/lib/brand.js` (`LOGO_WHITE_URL`, `LOGO_GOLD_URL`, `LOGO_DARK_URL`, `BRAND` config) — future logo rotation = 1-line change
- Theme color meta tag: `#082233` (navy brand color)

## Test Status
- Backend: 78/78 pytest pass (iter 4–11 cumulative)
- Frontend: 9/9 iter-11 checks PASS (logo rendering, meta tags, regression)

## Next Action Items
1. **User**: Login `/admin` via Google dengan `rimpods@gmail.com` untuk lihat dashboard
2. **User**: Tunggu Midtrans approval production → switch `MIDTRANS_IS_PRODUCTION=true`
3. (Opsional) Cek inbox `rimpods@gmail.com` — harusnya udah ada email test dari `Curhat@rimpods.com`
- P2: Frontend — Poll `/api/payment/midtrans/status/{order_number}` di Success page realtime
- P2: Frontend — Tombol "Kirim Resi" di admin dashboard row yang hit /ship endpoint
- P2: Produk low-ticket untuk coverage voucher-ineligible
- P2: English version
- P2: Abandoned cart WhatsApp nudge
