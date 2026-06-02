import { useEffect, useState } from "react";
import axios from "axios";
import Header from "../components/Header";
import CartDrawer from "../components/CartDrawer";
import { useCart, formatRupiah } from "../lib/cart";
import { Button } from "../components/ui/button";
import { Badge } from "../components/ui/badge";
import { Accordion, AccordionContent, AccordionItem, AccordionTrigger } from "../components/ui/accordion";
import { Star, Sparkles, Droplets, Shield, Waves, ChevronRight, Truck, MessageCircle, Heart, ExternalLink, Crown } from "lucide-react";
import { toast } from "sonner";
import { trackAddToCart } from "../lib/tracker";
import UpsellModal from "../components/UpsellModal";
import ExitIntentModal from "../components/ExitIntentModal";
import { getReturningCustomer, firstName } from "../lib/customer";

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

const Bubbles = () => (
  <div className="absolute inset-0 overflow-hidden pointer-events-none">
    {Array.from({ length: 14 }).map((_, i) => {
      const size = 6 + Math.random() * 22;
      return (
        <span
          key={i}
          className="bubble"
          style={{
            left: `${Math.random() * 100}%`,
            width: size,
            height: size,
            animationDuration: `${10 + Math.random() * 14}s`,
            animationDelay: `${Math.random() * 8}s`,
          }}
        />
      );
    })}
  </div>
);

const Stat = ({ value, label }) => (
  <div className="text-left">
    <div className="font-display text-3xl lg:text-4xl text-[hsl(var(--reef-glow))]">{value}</div>
    <div className="text-xs uppercase tracking-[0.2em] opacity-60 mt-1">{label}</div>
  </div>
);

export default function Landing() {
  const [products, setProducts] = useState([]);
  const [cartOpen, setCartOpen] = useState(false);
  const [upsellTarget, setUpsellTarget] = useState(null);
  const [returningCustomer, setReturningCustomer] = useState(null);
  const { add } = useCart();

  useEffect(() => {
    setReturningCustomer(getReturningCustomer());
  }, []);

  useEffect(() => {
    axios.get(`${API}/products`).then((r) => setProducts(r.data.products || [])).catch(() => {
      toast.error("Gagal muat produk, coba refresh.");
    });
  }, []);

  const handleAdd = (p) => {
    add(p, 1);
    trackAddToCart(p, 1);
    toast.success(`${p.name.split("+")[0].trim()} siap di keranjang kamu.`);
    // Trigger upsell after a short delay if there's a cross-sell target
    const targetId = p.upsell_target;
    if (targetId) {
      const target = products.find((x) => x.id === targetId);
      if (target) setTimeout(() => setUpsellTarget(target), 700);
    }
  };

  return (
    <div className="reef-grad min-h-screen text-[hsl(var(--reef-foam))]">
      <Header onCartClick={() => setCartOpen(true)} />
      <CartDrawer open={cartOpen} onOpenChange={setCartOpen} />
      <UpsellModal open={!!upsellTarget} onOpenChange={(o) => !o && setUpsellTarget(null)} target={upsellTarget} />
      <ExitIntentModal />

      {/* HERO */}
      <section className="relative overflow-hidden">
        <Bubbles />
        <div className="caustics absolute inset-0" />
        <div className="relative max-w-7xl mx-auto px-5 lg:px-10 pt-16 pb-24 lg:pt-28 lg:pb-32 grid lg:grid-cols-12 gap-12 items-center">
          <div className="lg:col-span-7 rise-in">
            {returningCustomer && (returningCustomer.name || returningCustomer.phone) && (
              <div
                data-testid="returning-greeting"
                className="mb-5 flex items-center gap-3 rounded-2xl border border-[hsla(174,70%,55%,0.35)] bg-[hsla(174,70%,55%,0.10)] px-5 py-3 backdrop-blur-sm max-w-xl"
              >
                <span className="text-2xl shrink-0" aria-hidden="true">🪸</span>
                <div className="leading-snug">
                  <p className="font-display text-base sm:text-lg text-[hsl(var(--reef-glow))]">
                    {returningCustomer.name
                      ? `Senang menyambut Anda kembali, Kak ${firstName(returningCustomer.name)} 🙏`
                      : "Senang menyambut Anda kembali 🙏"}
                  </p>
                  <p className="text-sm text-[hsl(var(--reef-foam))]/75">
                    Terima kasih sudah mempercayai Rimpods lagi. Saat checkout, alamat Anda kami isi otomatis — tinggal pilih ongkir &amp; bayar.
                  </p>
                </div>
              </div>
            )}
            <Badge data-testid="hero-badge" className="bg-[hsla(174,70%,55%,0.15)] text-[hsl(var(--reef-glow))] border border-[hsla(174,70%,55%,0.35)] rounded-full px-4 py-1 mb-6">
              <Sparkles className="w-3.5 h-3.5 mr-2" />
              Pakan coral hidup — kultur langsung di Jakarta, hadir untuk reefer di seluruh Indonesia
            </Badge>
            <h1 data-testid="hero-title" className="font-display text-5xl sm:text-6xl lg:text-7xl leading-[1.02] tracking-tight">
              Gonio Sultan <span className="text-[hsl(var(--reef-coral))]">Numpang Mati?</span><br />Selamatkan dengan Pakan 50 Mikron.
            </h1>
            <p className="mt-6 text-lg max-w-xl text-[hsl(var(--reef-foam))]/80 leading-relaxed">
              Pelet biasa terlalu besar, membusuk dan bikin air spike. Rimpods memberikan zooplankton hidup instingtif yang langsung disambar koral .
            </p>
            <div className="mt-8 flex flex-wrap gap-3">
              <Button
                data-testid="hero-shop-btn"
                onClick={() => document.getElementById('produk')?.scrollIntoView({ behavior: 'smooth' })}
                className="coral-pill hover:opacity-90 h-12 px-7 rounded-full font-semibold"
              >
                Beli Bundel Gonio <ChevronRight className="w-4 h-4 ml-1" />
              </Button>
            </div>

            <div className="mt-10 grid grid-cols-3 gap-6 max-w-md">
              <Stat value="6.2K" label="Rating Toko" />
              <Stat value="4.9★" label="Avg Review" />
              <Stat value="1rb+" label="Reefer Dipercaya" />
            </div>

            <a
              href={`https://wa.me/6282216594354?text=${encodeURIComponent("Halo Tim Rimpods, saya ingin berkonsultasi langsung mengenai setup pakan coral untuk tank saya. Mohon bantuannya.")}`}
              target="_blank"
              rel="noreferrer"
              data-testid="hero-concierge-link"
              className="mt-8 inline-flex items-center gap-3 group"
            >
              <span className="w-10 h-10 rounded-full bg-[hsla(45,85%,55%,0.12)] border border-[hsla(45,85%,55%,0.35)] grid place-items-center group-hover:bg-[hsla(45,85%,55%,0.2)] transition">
                <Crown className="w-4 h-4 text-[hsl(var(--reef-glow))]" />
              </span>
              <div className="text-left">
                <div className="text-xs uppercase tracking-[0.25em] opacity-60 group-hover:opacity-80">Concierge Line</div>
                <div className="text-sm text-[hsl(var(--reef-foam))]/85 group-hover:text-[hsl(var(--reef-foam))]">
                  Konsultasi langsung dengan tim kami
                  <ChevronRight className="w-3.5 h-3.5 inline ml-1 opacity-60 group-hover:translate-x-0.5 transition" />
                </div>
              </div>
            </a>
          </div>

          <div className="lg:col-span-5 relative rise-in">
            <div className="glass-card glow-ring rounded-[2rem] p-3 rotate-1 bg-[hsla(8,30%,15%,0.4)]">
              <img
                src="/aaaaa.png"
                alt="Reef tank coral mekar"
                className="rounded-[1.6rem] w-full h-auto object-contain max-h-[600px]"
              />
              <div className="absolute -bottom-6 -left-6 hidden lg:block glass-card rounded-2xl px-5 py-4">
                <div className="flex items-center gap-3">
                  <Heart className="w-5 h-5 text-[hsl(var(--reef-coral))]" />
                  <div>
                    <div className="text-xs opacity-70">Catatan reefer</div>
                    <div className="text-sm">"Ekstensi polip terlihat maksimal sejak hari ketiga."</div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Marquee */}
        <div className="border-y border-[hsla(174,70%,55%,0.15)] py-5 overflow-hidden">
          <div className="marquee-track text-sm uppercase tracking-[0.25em] opacity-70">
            {Array.from({ length: 2 }).map((_, k) => (
              <div key={k} className="flex gap-12">
                <span>· Live Rotifer Harian</span>
                <span>· Phytoplankton Segar</span>
                <span>· Coral yang Ekspresif</span>
                <span>· Pemulih Pasca Perubahan Parameter</span>
                <span>· 4.9★ di Tokopedia</span>
                <span>· Dikirim dari Bekasi</span>
                <span>· Komunitas Reefer Indonesia</span>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* PRODUK */}
      <section id="produk" className="relative py-24 lg:py-32">
        <div className="max-w-7xl mx-auto px-5 lg:px-10">
          <div className="flex flex-col lg:flex-row lg:items-end justify-between gap-6 mb-12">
            <div>
              <Badge className="bg-[hsla(8,89%,64%,0.15)] text-[hsl(var(--reef-coral))] border border-[hsla(8,89%,64%,0.4)] rounded-full px-4 py-1 mb-4">
                Katalog
              </Badge>
              <h2 data-testid="produk-title" className="font-display text-4xl lg:text-5xl tracking-tight">Tiga pilihan, satu standar kualitas.</h2>
              <p className="mt-3 max-w-xl text-[hsl(var(--reef-foam))]/75">
                Setiap tank punya cerita berbeda. Kami bantu kamu menemukan yang paling selaras dengan ritme tank kamu — kalau masih ragu, langsung sapa kami di chat.
              </p>
            </div>
          </div>

          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-7">
            {products.map((p, idx) => (
              <article
                key={p.id}
                data-testid={`product-card-${p.id}`}
                className="glass-card rounded-[1.6rem] overflow-hidden flex flex-col group hover:-translate-y-1 transition-transform duration-500"
                style={{ animationDelay: `${idx * 80}ms` }}
              >
                <div className="relative aspect-[4/3] overflow-hidden">
                  <img src={p.image} alt={p.name} className="w-full h-full object-cover group-hover:scale-105 transition duration-700" />
                  <div className="absolute top-3 left-3 flex gap-2">
                    {p.compare_price > p.price && (
                      <Badge className="coral-pill rounded-full px-3 py-1 text-xs font-semibold">
                        Hemat {Math.round(((p.compare_price - p.price) / p.compare_price) * 100)}%
                      </Badge>
                    )}
                  </div>
                  <div className="absolute bottom-3 right-3 flex items-center gap-1 bg-[hsla(198,75%,8%,0.7)] px-3 py-1 rounded-full text-xs">
                    <Star className="w-3 h-3 fill-[hsl(var(--reef-glow))] text-[hsl(var(--reef-glow))]" />
                    {p.rating} · {p.sold} terjual
                  </div>
                </div>

                <div className="p-6 flex-1 flex flex-col">
                  <h3 className="font-display text-2xl leading-snug">{p.name}</h3>
                  <p className="mt-1 text-sm text-[hsl(var(--reef-foam))]/70">{p.tagline}</p>

                  <ul className="mt-4 space-y-2 text-sm">
                    {p.highlights.slice(0, 3).map((h, i) => (
                      <li key={i} className="flex gap-2">
                        <Sparkles className="w-3.5 h-3.5 text-[hsl(var(--reef-glow))] mt-0.5 flex-shrink-0" />
                        <span className="opacity-80">{h}</span>
                      </li>
                    ))}
                  </ul>

                  <div className="mt-auto pt-6 flex items-end justify-between">
                    <div>
                      <div className="font-display text-3xl text-[hsl(var(--reef-glow))]">{formatRupiah(p.price)}</div>
                      {p.compare_price > p.price && (
                        <div className="text-xs line-through opacity-50">{formatRupiah(p.compare_price)}</div>
                      )}
                    </div>
                    <Button
                      data-testid={`add-to-cart-${p.id}`}
                      onClick={() => handleAdd(p)}
                      className="coral-pill hover:opacity-90 rounded-full px-5 h-11 font-semibold"
                    >
                      + Masukkan Keranjang
                    </Button>
                  </div>

                  <div className="mt-4 pt-4 border-t border-[hsla(174,70%,55%,0.15)] flex gap-2">
                    <a
                      href={p.tokopedia_url}
                      target="_blank"
                      rel="noreferrer"
                      data-testid={`toko-link-${p.id}`}
                      className="flex-1 text-center text-xs py-2 rounded-full border border-[hsla(174,70%,55%,0.3)] hover:bg-[hsla(174,70%,55%,0.1)] inline-flex items-center justify-center gap-1.5 transition"
                    >
                      <ExternalLink className="w-3 h-3" /> Tokopedia
                    </a>
                    <a
                      href={p.tiktok_shop_url}
                      target="_blank"
                      rel="noreferrer"
                      data-testid={`tiktok-link-${p.id}`}
                      className="flex-1 text-center text-xs py-2 rounded-full border border-[hsla(8,89%,64%,0.4)] hover:bg-[hsla(8,89%,64%,0.1)] inline-flex items-center justify-center gap-1.5 transition"
                    >
                      <ExternalLink className="w-3 h-3" /> TikTok Shop
                    </a>
                  </div>
                </div>
              </article>
            ))}
          </div>
        </div>
      </section>

      {/* CERITA */}
      <section id="cerita" className="relative py-24 lg:py-32 bg-[hsl(var(--reef-mid))]">
        <div className="max-w-6xl mx-auto px-5 lg:px-10 grid lg:grid-cols-2 gap-12 items-center">
          <div className="relative">
            <img
              src="https://customer-assets.emergentagent.com/job_coral-product-hub/artifacts/wmdlkyuf_Dramatic%205-Photo%20Visual%20Collage.png"
              alt="Coral close up"
              className="rounded-[1.8rem] w-full h-auto object-contain max-h-[640px] glow-ring bg-[hsla(8,30%,15%,0.4)]"
            />
          </div>
          <div>
            <Badge className="bg-[hsla(174,70%,55%,0.15)] text-[hsl(var(--reef-glow))] border border-[hsla(174,70%,55%,0.3)] rounded-full px-4 py-1 mb-4">
              Cerita Kami
            </Badge>
            <h2 className="font-display text-4xl lg:text-5xl tracking-tight">
              Coral merespons kualitas, bukan janji.
            </h2>
            <p className="mt-5 text-[hsl(var(--reef-foam))]/80 leading-relaxed">
              Kami merawat kultur rotifer dan phytoplankton sendiri di fasilitas kami di Bekasi, dengan parameter air yang kami jaga seketat tank display kami. Tiap botol dipanen pada titik kesegarannya yang matang, lalu dikemas dengan metode yang kami uji sendiri — agar sampai di tank kamu, isinya masih hidup, masih aktif, dan siap ditemui polip yang menunggu.
            </p>
            <div className="mt-8 grid grid-cols-2 gap-5">
              {[
                { icon: Droplets, t: "Kultur Hidup", d: "Bukan beku, bukan kering. Aktif dan responsif di botol." },
                { icon: Shield, t: "Terverifikasi", d: "Diuji dulu di tank kami, sebelum masuk ke tank kamu." },
                { icon: Waves, t: "Selaras Reef", d: "Cocok untuk SPS, LPS, dan soft coral — tanpa kejutan." },
                { icon: Truck, t: "Kemasan Terjaga", d: "Metode kemasan kami menjaga kualitas sampai H+1 di seluruh Indonesia." },
              ].map((it, i) => (
                <div key={i} className="flex gap-3">
                  <div className="w-10 h-10 rounded-xl bg-[hsla(174,70%,55%,0.15)] grid place-items-center text-[hsl(var(--reef-glow))]">
                    <it.icon className="w-4 h-4" />
                  </div>
                  <div>
                    <div className="font-medium">{it.t}</div>
                    <div className="text-sm opacity-70">{it.d}</div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </section>

      {/* CARA PAKAI */}
      <section id="cara-pakai" className="py-24 lg:py-32">
        <div className="max-w-6xl mx-auto px-5 lg:px-10">
          <div className="text-center max-w-2xl mx-auto mb-14">
            <Badge className="bg-[hsla(8,89%,64%,0.15)] text-[hsl(var(--reef-coral))] border border-[hsla(8,89%,64%,0.4)] rounded-full px-4 py-1 mb-4">
              Cara Pakai
            </Badge>
            <h2 className="font-display text-4xl lg:text-5xl tracking-tight">Tiga langkah, dan coral akan bicara sendiri.</h2>
          </div>
          <div className="grid md:grid-cols-3 gap-6">
            {[
              { n: "01", t: "Kenali volume tank kamu", d: "Hitung volume air yang aktif. Tank 400 liter ke atas, tuang 2 liter sekaligus. Tank lebih kecil, sesuaikan proporsinya dengan tenang." },
              { n: "02", t: "Tuang dengan tenang", d: "Pause skimmer sekitar 30 menit. Alirkan rotifer dan phytoplankton dekat arus utama, biarkan sebaran mengalir secara alami." },
              { n: "03", t: "Amati, lalu ulangi", d: "Perhatikan ekstensi polip pada hari ke-2 hingga ke-3. Lanjutkan ritme feeding mingguan — konsistensi yang akan memberi hasil." },
            ].map((s, i) => (
              <div key={i} className="glass-card rounded-2xl p-7">
                <div className="font-display text-5xl text-[hsl(var(--reef-coral))] opacity-80">{s.n}</div>
                <h3 className="font-display text-2xl mt-3">{s.t}</h3>
                <p className="mt-2 opacity-80 text-sm leading-relaxed">{s.d}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* TESTIMONI */}
      <section id="testimoni" className="py-24 lg:py-32 bg-[hsl(var(--reef-mid))]">
        <div className="max-w-6xl mx-auto px-5 lg:px-10">
          <div className="text-center max-w-2xl mx-auto mb-14">
            <Badge className="bg-[hsla(174,70%,55%,0.15)] text-[hsl(var(--reef-glow))] border border-[hsla(174,70%,55%,0.3)] rounded-full px-4 py-1 mb-4">
              Suara Reefer
            </Badge>
            <h2 className="font-display text-4xl lg:text-5xl tracking-tight">Reefer lain berkata begini.</h2>
          </div>
          <div className="grid md:grid-cols-3 gap-6">
            {[
              { n: "Bayu, Jakarta", q: "Acro saya menunjukkan ekstensi polip yang ekspresif sejak hari ketiga. Konsistensinya yang saya apresiasi." },
              { n: "Sari, Surabaya", q: "Saat parameter air saya sempat bergeser, TBN membantu mengembalikan ketenangan di tank. Terima kasih, Rimpods." },
              { n: "Reza, Bandung", q: "Paket hemat menjadi pilihan rutin saya. Satu kiriman, satu bulan tenang, dan coral terlihat benar-benar nyaman." },
            ].map((t, i) => (
              <figure key={i} className="glass-card rounded-2xl p-7">
                <div className="flex gap-1 mb-3">
                  {Array.from({ length: 5 }).map((_, k) => (
                    <Star key={k} className="w-4 h-4 fill-[hsl(var(--reef-glow))] text-[hsl(var(--reef-glow))]" />
                  ))}
                </div>
                <blockquote className="text-lg leading-relaxed">"{t.q}"</blockquote>
                <figcaption className="mt-4 text-sm opacity-70">— {t.n}</figcaption>
              </figure>
            ))}
          </div>
        </div>
      </section>

      {/* FAQ */}
      <section id="faq" className="py-24 lg:py-32">
        <div className="max-w-3xl mx-auto px-5 lg:px-10">
          <div className="text-center mb-12">
            <h2 className="font-display text-4xl lg:text-5xl tracking-tight">Pertanyaan yang sering dititipkan.</h2>
          </div>
          <Accordion type="single" collapsible className="space-y-3" data-testid="faq-accordion">
            {[
              { q: "Rotifernya masih hidup saat sampai di rumah saya?", a: "Iya. Metode packing kami menjaga rotifer tetap aktif hingga 48–72 jam dalam perjalanan. Begitu sampai, kamu bisa langsung mengalirkannya ke tank tanpa perlu aklimatisasi panjang." },
              { q: "Apakah bisa disimpan di kulkas?", a: "Phytoplankton dan TBN aman masuk kulkas. Rotifer sebaiknya digunakan segera agar nutrisinya terjaga maksimal. Bila perlu disimpan, 3–5 hari di suhu 18–22°C adalah jendela yang kami sarankan." },
              { q: "Cocok untuk tank brackish atau air tawar?", a: "Formula Rimpods dirancang khusus untuk reef tank air laut. Untuk kebutuhan freshwater, silakan ngobrol dulu dengan kami di WhatsApp — kami bantu arahkan ke yang paling tepat." },
              { q: "Bagaimana dengan pengiriman?", a: "Kami kirim dari Bekasi menggunakan kurir kargo terpilih. Mulai Rp250.000, pengiriman Jabodetabek gratis ongkir. Pengiriman luar kota tetap kami pantau hingga sampai dengan aman." },
              { q: "Tersedia COD atau cicilan?", a: "Melalui Tokopedia tersedia opsi cicilan 0% dan berbagai promo resmi. Pesanan via website ini akan kami teruskan ke admin via WhatsApp, atau kamu dapat langsung menyelesaikan pembayaran di listing Tokopedia." },
            ].map((f, i) => (
              <AccordionItem
                key={i}
                value={`item-${i}`}
                data-testid={`faq-item-${i}`}
                className="glass-card rounded-2xl border-0 px-5"
              >
                <AccordionTrigger className="text-left font-display text-lg hover:no-underline">{f.q}</AccordionTrigger>
                <AccordionContent className="text-[hsl(var(--reef-foam))]/80 leading-relaxed">{f.a}</AccordionContent>
              </AccordionItem>
            ))}
          </Accordion>
        </div>
      </section>

      {/* CTA */}
      <section className="py-20">
        <div className="max-w-5xl mx-auto px-5 lg:px-10">
          <div className="glass-card rounded-[2rem] p-10 lg:p-14 text-center relative overflow-hidden">
            <Bubbles />
            <h2 className="font-display text-4xl lg:text-5xl tracking-tight relative">Tank kamu siap memperlihatkan potensinya.</h2>
            <p className="mt-4 max-w-xl mx-auto text-[hsl(var(--reef-foam))]/80 relative">
              Mulai dari satu botol, polip akan memberi tahu selisihnya. Kami di sini menemani, sampai coral kamu benar-benar menemukan ritmenya.
            </p>
            <div className="mt-8 flex flex-wrap gap-3 justify-center relative">
              <Button
                data-testid="cta-shop-btn"
                onClick={() => document.getElementById("produk")?.scrollIntoView({ behavior: "smooth" })}
                className="coral-pill hover:opacity-90 h-12 px-7 rounded-full font-semibold"
              >
                Mulai Belanja
              </Button>
              <a
                href="https://wa.me/6282216594354"
                target="_blank"
                rel="noreferrer"
                data-testid="cta-wa-btn"
              >
                <Button variant="outline" className="bg-transparent border-[hsla(174,70%,55%,0.4)] text-[hsl(var(--reef-foam))] hover:bg-[hsla(174,70%,55%,0.1)] h-12 px-7 rounded-full">
                  <MessageCircle className="w-4 h-4 mr-2" /> Konsultasi dengan Kami
                </Button>
              </a>
            </div>
          </div>
        </div>
      </section>

      <footer className="py-10 border-t border-[hsla(174,70%,55%,0.15)] text-sm text-[hsl(var(--reef-foam))]/60">
        <div className="max-w-7xl mx-auto px-5 lg:px-10 flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
          <div className="flex items-center gap-3">
            <img
              src="https://customer-assets.emergentagent.com/job_coral-product-hub/artifacts/5gz4ojsf_Logo%20Transparant%20%284%29.png"
              alt="Rimpods"
              className="h-8 w-auto opacity-80"
            />
            <span>© {new Date().getFullYear()} · Dikultur dengan penuh perhatian di Bekasi</span>
          </div>
          <div className="flex gap-5">
            <a href="https://www.tokopedia.com/rimpods" target="_blank" rel="noreferrer" className="hover:text-[hsl(var(--reef-glow))]">Tokopedia</a>
            <a href="https://wa.me/6282216594354" target="_blank" rel="noreferrer" className="hover:text-[hsl(var(--reef-glow))]">WhatsApp</a>
          </div>
        </div>
      </footer>
    </div>
  );
}
