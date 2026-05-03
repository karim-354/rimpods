import { useEffect, useState } from "react";
import axios from "axios";
import Header from "../components/Header";
import CartDrawer from "../components/CartDrawer";
import { useCart, formatRupiah } from "../lib/cart";
import { Button } from "../components/ui/button";
import { Badge } from "../components/ui/badge";
import { Accordion, AccordionContent, AccordionItem, AccordionTrigger } from "../components/ui/accordion";
import { Star, Sparkles, Droplets, Shield, Waves, ChevronRight, Truck, MessageCircle, Heart } from "lucide-react";
import { toast } from "sonner";

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
  const { add } = useCart();

  useEffect(() => {
    axios.get(`${API}/products`).then((r) => setProducts(r.data.products || [])).catch(() => {
      toast.error("Gagal muat produk, coba refresh.");
    });
  }, []);

  const handleAdd = (p) => {
    add(p, 1);
    toast.success(`${p.name.split("+")[0].trim()} masuk keranjang!`);
  };

  return (
    <div className="reef-grad min-h-screen text-[hsl(var(--reef-foam))]">
      <Header onCartClick={() => setCartOpen(true)} />
      <CartDrawer open={cartOpen} onOpenChange={setCartOpen} />

      {/* HERO */}
      <section className="relative overflow-hidden">
        <Bubbles />
        <div className="caustics absolute inset-0" />
        <div className="relative max-w-7xl mx-auto px-5 lg:px-10 pt-16 pb-24 lg:pt-28 lg:pb-32 grid lg:grid-cols-12 gap-12 items-center">
          <div className="lg:col-span-7 rise-in">
            <Badge data-testid="hero-badge" className="bg-[hsla(174,70%,55%,0.15)] text-[hsl(var(--reef-glow))] border border-[hsla(174,70%,55%,0.35)] rounded-full px-4 py-1 mb-6">
              <Sparkles className="w-3.5 h-3.5 mr-2" />
              Pakan coral live, langsung kirim dari Bekasi
            </Badge>
            <h1 data-testid="hero-title" className="font-display text-5xl sm:text-6xl lg:text-7xl leading-[1.02] tracking-tight">
              Bikin coral kamu <span className="text-[hsl(var(--reef-coral))]">mekar</span> sampai gila-gilaan.
            </h1>
            <p className="mt-6 text-lg max-w-xl text-[hsl(var(--reef-foam))]/80 leading-relaxed">
              Rotifer hidup, phytoplankton segar, plus formula pemulih air pasca crash. Tank kamu nggak cuma cantik, tapi hidup. Beneran hidup.
            </p>
            <div className="mt-8 flex flex-wrap gap-3">
              <Button
                data-testid="hero-shop-btn"
                onClick={() => document.getElementById("produk")?.scrollIntoView({ behavior: "smooth" })}
                className="coral-pill hover:opacity-90 h-12 px-7 rounded-full font-semibold"
              >
                Lihat Produk <ChevronRight className="w-4 h-4 ml-1" />
              </Button>
              <Button
                data-testid="hero-story-btn"
                onClick={() => document.getElementById("cerita")?.scrollIntoView({ behavior: "smooth" })}
                variant="outline"
                className="bg-transparent border-[hsla(174,70%,55%,0.4)] text-[hsl(var(--reef-foam))] hover:bg-[hsla(174,70%,55%,0.1)] h-12 px-7 rounded-full"
              >
                Kenapa Rimpods?
              </Button>
            </div>

            <div className="mt-10 grid grid-cols-3 gap-6 max-w-md">
              <Stat value="6.2K" label="Rating Toko" />
              <Stat value="4.9★" label="Avg Review" />
              <Stat value="1rb+" label="Reefer Puas" />
            </div>
          </div>

          <div className="lg:col-span-5 relative rise-in">
            <div className="glass-card glow-ring rounded-[2rem] p-3 rotate-1">
              <img
                src="https://images.unsplash.com/photo-1559827260-dc66d52bef19?w=1100&q=85"
                alt="Reef tank coral mekar"
                className="rounded-[1.6rem] w-full h-[420px] lg:h-[520px] object-cover"
              />
              <div className="absolute -bottom-6 -left-6 hidden lg:block glass-card rounded-2xl px-5 py-4">
                <div className="flex items-center gap-3">
                  <Heart className="w-5 h-5 text-[hsl(var(--reef-coral))]" />
                  <div>
                    <div className="text-xs opacity-70">Reefer comment</div>
                    <div className="text-sm">"Polip ekstensi maksimal dari hari ke-3."</div>
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
                <span>· Live Rotifer</span>
                <span>· Phytoplankton Segar</span>
                <span>· Coral Mekar Maksimal</span>
                <span>· Tank Crash Rescue</span>
                <span>· 4.9★ di Tokopedia</span>
                <span>· Kirim dari Bekasi</span>
                <span>· Reefer Indonesia</span>
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
              <h2 data-testid="produk-title" className="font-display text-4xl lg:text-5xl tracking-tight">Tiga andalan, satu tujuan.</h2>
              <p className="mt-3 max-w-xl text-[hsl(var(--reef-foam))]/75">
                Pilih yang paling cocok sama tank kamu. Ragu-ragu? Chat aja, kita bantu.
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
                      + Keranjang
                    </Button>
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
              src="https://images.unsplash.com/photo-1582967788606-a171c1080cb0?w=1000&q=85"
              alt="Coral close up"
              className="rounded-[1.8rem] w-full h-[460px] object-cover glow-ring"
            />
          </div>
          <div>
            <Badge className="bg-[hsla(174,70%,55%,0.15)] text-[hsl(var(--reef-glow))] border border-[hsla(174,70%,55%,0.3)] rounded-full px-4 py-1 mb-4">
              Cerita Kami
            </Badge>
            <h2 className="font-display text-4xl lg:text-5xl tracking-tight">
              Karena reefer butuh pakan yang hidup, bukan cuma label.
            </h2>
            <p className="mt-5 text-[hsl(var(--reef-foam))]/80 leading-relaxed">
              Kita kultur sendiri rotifer dan phytoplankton di Bekasi, dengan kontrol kualitas air yang ketat. Tiap botol dipanen segar, dipacking khusus biar nyampe rumah kamu masih hidup, dan siap dilahap polip-polip lapar.
            </p>
            <div className="mt-8 grid grid-cols-2 gap-5">
              {[
                { icon: Droplets, t: "Live Culture", d: "Bukan beku, bukan kering. Hidup dan aktif." },
                { icon: Shield, t: "Aman 100%", d: "Tested di tank kami sendiri." },
                { icon: Waves, t: "Reef-Safe", d: "SPS, LPS, soft, semua aman." },
                { icon: Truck, t: "Packing Khusus", d: "Tahan perjalanan H+1 ke seluruh Indonesia." },
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
            <h2 className="font-display text-4xl lg:text-5xl tracking-tight">Tiga langkah, coral langsung happy.</h2>
          </div>
          <div className="grid md:grid-cols-3 gap-6">
            {[
              { n: "01", t: "Cek volume tank", d: "Hitung liter air laut. Tank 400L+ pakai 2 liter rotifer sekaligus, tank kecil sesuaikan." },
              { n: "02", t: "Tuang langsung", d: "Matikan skimmer 30 menit. Tuang rotifer + phyto pelan-pelan dekat aliran arus utama." },
              { n: "03", t: "Pantau & ulangi", d: "Lihat polip ekstensi 2-3 hari. Lanjut feeding rutin tiap minggu untuk hasil maksimal." },
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
            <h2 className="font-display text-4xl lg:text-5xl tracking-tight">Nggak cuma kata kami.</h2>
          </div>
          <div className="grid md:grid-cols-3 gap-6">
            {[
              { n: "Bayu, Jakarta", q: "Polip Acro langsung mekar maksimal hari ke-3 setelah dosing rutin. Recommended banget sih!" },
              { n: "Sari, Surabaya", q: "Tank pernah crash, pakai TBN parameter balik normal dalam seminggu. Ngebantu banget kok." },
              { n: "Reza, Bandung", q: "Paket hemat worth it. Kulkas penuh, coral kenyang. Beneran investasi buat reefer rajin." },
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
            <h2 className="font-display text-4xl lg:text-5xl tracking-tight">Pertanyaan yang sering muncul.</h2>
          </div>
          <Accordion type="single" collapsible className="space-y-3" data-testid="faq-accordion">
            {[
              { q: "Rotifer ini hidup pas nyampe rumah?", a: "Iya banget. Kita pack pakai metode khusus biar rotifer tetap aktif sampai 48-72 jam dalam perjalanan. Begitu nyampe, langsung tuang aja ke tank." },
              { q: "Bisa disimpan di kulkas?", a: "Phytoplankton dan TBN bisa masuk kulkas. Rotifer hidup sebaiknya langsung dipakai biar nutrisinya maksimal, tapi kalau perlu, simpan max 3-5 hari di suhu 18-22°C." },
              { q: "Cocok buat tank brackish atau air tawar?", a: "Produk Rimpods difokuskan untuk reef tank air laut. Untuk freshwater, ada baiknya konsultasi dulu lewat WhatsApp ya." },
              { q: "Ongkir gimana?", a: "Dikirim dari Bekasi pakai kurir kargo. Belanja Rp250rb up gratis ongkir Jabodetabek. Luar kota tetap aman, kita rapihin packing-nya." },
              { q: "Bisa COD atau cicilan?", a: "Untuk pembelian via Tokopedia langsung, tersedia cicilan 0% dan promo bebas ongkir. Order via web ini diteruskan ke admin via WhatsApp atau langsung redirect ke listing Tokopedia." },
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
            <h2 className="font-display text-4xl lg:text-5xl tracking-tight relative">Tank kamu tinggal nunggu polip mekar.</h2>
            <p className="mt-4 max-w-xl mx-auto text-[hsl(var(--reef-foam))]/80 relative">
              Mulai dari satu botol aja udah keliatan bedanya. Yuk pilih dulu, nanti kita bantu sampai coral kamu happy.
            </p>
            <div className="mt-8 flex flex-wrap gap-3 justify-center relative">
              <Button
                data-testid="cta-shop-btn"
                onClick={() => document.getElementById("produk")?.scrollIntoView({ behavior: "smooth" })}
                className="coral-pill hover:opacity-90 h-12 px-7 rounded-full font-semibold"
              >
                Belanja Sekarang
              </Button>
              <a
                href="https://wa.me/6281234567890"
                target="_blank"
                rel="noreferrer"
                data-testid="cta-wa-btn"
              >
                <Button variant="outline" className="bg-transparent border-[hsla(174,70%,55%,0.4)] text-[hsl(var(--reef-foam))] hover:bg-[hsla(174,70%,55%,0.1)] h-12 px-7 rounded-full">
                  <MessageCircle className="w-4 h-4 mr-2" /> Chat Admin
                </Button>
              </a>
            </div>
          </div>
        </div>
      </section>

      <footer className="py-10 border-t border-[hsla(174,70%,55%,0.15)] text-sm text-[hsl(var(--reef-foam))]/60">
        <div className="max-w-7xl mx-auto px-5 lg:px-10 flex flex-col md:flex-row justify-between gap-3">
          <div>© {new Date().getFullYear()} Rimpods. Live coral food, Bekasi.</div>
          <div className="flex gap-5">
            <a href="https://www.tokopedia.com/rimpods" target="_blank" rel="noreferrer" className="hover:text-[hsl(var(--reef-glow))]">Tokopedia</a>
            <a href="https://wa.me/6281234567890" target="_blank" rel="noreferrer" className="hover:text-[hsl(var(--reef-glow))]">WhatsApp</a>
          </div>
        </div>
      </footer>
    </div>
  );
}
