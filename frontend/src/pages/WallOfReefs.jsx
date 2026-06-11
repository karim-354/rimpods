import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { Star, BadgeCheck, ExternalLink, ArrowLeft, ShoppingBag, MessageCircle } from "lucide-react";
import { Button } from "../components/ui/button";

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

function Stars({ n = 5, className = "w-3.5 h-3.5" }) {
  return (
    <div className="flex gap-0.5">
      {Array.from({ length: n }).map((_, k) => (
        <Star key={k} className={`${className} fill-[hsl(var(--reef-glow))] text-[hsl(var(--reef-glow))]`} />
      ))}
    </div>
  );
}

function TestimonialCard({ t }) {
  return (
    <figure
      className="glass-card rounded-2xl p-6 mb-5 break-inside-avoid"
      data-testid={`wall-card-${t.id}`}
    >
      <div className="flex items-center justify-between">
        <Stars n={t.rating || 5} />
        <span className="text-[10px] uppercase tracking-widest opacity-50">{t.date_label}</span>
      </div>
      <blockquote className="mt-3 leading-relaxed text-[15px]">"{t.text}"</blockquote>
      {t.photos?.length > 0 && (
        <div className="mt-4 flex gap-2 flex-wrap">
          {t.photos.map((p, i) => (
            <img
              key={i}
              src={p}
              alt={`Foto ulasan ${t.name}`}
              loading="lazy"
              className="h-20 w-20 object-cover rounded-xl border border-[hsla(174,70%,55%,0.2)]"
            />
          ))}
        </div>
      )}
      <figcaption className="mt-4 flex items-center justify-between gap-2">
        <div className="flex items-center gap-1.5 text-sm font-semibold">
          {t.name}
          <BadgeCheck className="w-4 h-4 text-[hsl(var(--reef-glow))]" title="Pembeli terverifikasi" />
        </div>
        <span className="text-[11px] opacity-60 text-right">{t.product}</span>
      </figcaption>
    </figure>
  );
}

export default function WallOfReefs() {
  const [data, setData] = useState(null);

  useEffect(() => {
    document.title = "Wall of Reefs — Ulasan Asli Pembeli Rimpods";
    fetch(`${API}/testimonials`)
      .then((r) => r.json())
      .then(setData)
      .catch(console.error);
    window.scrollTo(0, 0);
  }, []);

  const s = data?.stats;

  return (
    <div className="min-h-screen bg-[hsl(var(--reef-deep))] text-[hsl(var(--reef-foam))]">
      {/* Header */}
      <header className="border-b border-[hsla(174,70%,55%,0.15)] bg-[hsla(198,75%,8%,0.7)] backdrop-blur-md sticky top-0 z-30">
        <div className="max-w-7xl mx-auto px-5 lg:px-10 h-16 flex items-center justify-between">
          <Link to="/" className="flex items-center gap-2 text-sm opacity-80 hover:opacity-100" data-testid="wall-back-home">
            <ArrowLeft className="w-4 h-4" /> Kembali ke Rimpods
          </Link>
          <Link to="/checkout?add=rotifer-2l-phyto" data-testid="wall-header-cta">
            <Button className="coral-pill hover:opacity-90 h-10 px-5 rounded-full font-semibold text-sm">
              <ShoppingBag className="w-4 h-4 mr-2" /> Belanja Sekarang
            </Button>
          </Link>
        </div>
      </header>

      {/* Trust hero */}
      <section className="py-16 lg:py-24 relative overflow-hidden">
        <div className="max-w-5xl mx-auto px-5 lg:px-10 text-center">
          <span className="inline-block rounded-full px-4 py-1 text-xs font-bold tracking-widest uppercase bg-[hsla(174,70%,55%,0.15)] text-[hsl(var(--reef-glow))] border border-[hsla(174,70%,55%,0.3)]">
            Wall of Reefs
          </span>
          <h1 className="font-display text-4xl sm:text-5xl lg:text-6xl tracking-tight mt-5">
            Ribuan reefer sudah membuktikan.
          </h1>
          <p className="mt-4 max-w-2xl mx-auto opacity-75">
            Semua ulasan di bawah ini asli dari pembeli di Tokopedia — bisa kamu verifikasi langsung.
          </p>

          <div className="mt-10 glass-card rounded-[2rem] p-8 lg:p-10" data-testid="wall-stats-banner">
            <div className="grid grid-cols-2 lg:grid-cols-4 gap-8 items-center">
              <div>
                <div className="font-display text-5xl text-[hsl(var(--reef-glow))]">{s?.rating ?? "4.9"}<span className="text-2xl opacity-60">/5</span></div>
                <div className="flex justify-center mt-2"><Stars className="w-4 h-4" /></div>
                <div className="text-xs opacity-60 mt-2">{(s?.total_ratings ?? 6261).toLocaleString("id-ID")} rating</div>
              </div>
              <div>
                <div className="font-display text-5xl text-[hsl(var(--reef-glow))]">{s?.satisfaction_pct ?? 98}%</div>
                <div className="text-xs opacity-60 mt-2">pembeli merasa puas</div>
              </div>
              <div>
                <div className="font-display text-5xl text-[hsl(var(--reef-glow))]">{s?.total_sold ?? "15 rb+"}</div>
                <div className="text-xs opacity-60 mt-2">produk terjual</div>
              </div>
              <div>
                <div className="font-display text-5xl text-[hsl(var(--reef-glow))]">{(s?.five_star_count ?? 6052).toLocaleString("id-ID")}</div>
                <div className="text-xs opacity-60 mt-2">memberi bintang 5 ({s?.five_star_pct ?? 96.7}%)</div>
              </div>
            </div>
            <a
              href={s?.review_url || "https://www.tokopedia.com/rimpods/review"}
              target="_blank"
              rel="noreferrer"
              data-testid="wall-tokopedia-link"
              className="inline-flex items-center gap-2 mt-8 text-sm font-semibold text-[hsl(var(--reef-glow))] hover:underline"
            >
              Cek langsung di Tokopedia <ExternalLink className="w-4 h-4" />
            </a>
          </div>
        </div>
      </section>

      {/* Reviews masonry */}
      <section className="pb-20">
        <div className="max-w-6xl mx-auto px-5 lg:px-10">
          {!data ? (
            <div className="grid place-items-center py-20">
              <div className="w-10 h-10 border-2 border-current border-t-transparent rounded-full animate-spin opacity-60" />
            </div>
          ) : (
            <div className="columns-1 sm:columns-2 lg:columns-3 gap-5" data-testid="wall-grid">
              {data.testimonials.map((t) => (
                <TestimonialCard key={t.id} t={t} />
              ))}
            </div>
          )}
          <p className="text-center text-xs opacity-50 mt-8">
            Ulasan diimpor apa adanya dari Tokopedia (Tokopedia & TikTok Shop by Tokopedia).
          </p>
        </div>
      </section>

      {/* CTA */}
      <section className="pb-24">
        <div className="max-w-4xl mx-auto px-5 lg:px-10">
          <div className="glass-card rounded-[2rem] p-10 text-center">
            <h2 className="font-display text-3xl lg:text-4xl tracking-tight">Giliran tank kamu yang bicara.</h2>
            <p className="mt-3 opacity-75 max-w-lg mx-auto">Gabung dengan ribuan reefer yang coral-nya sudah mekar maksimal bareng Rimpods.</p>
            <div className="mt-7 flex flex-wrap gap-3 justify-center">
              <Link to="/checkout?add=rotifer-2l-phyto" data-testid="wall-cta-checkout">
                <Button className="coral-pill hover:opacity-90 h-12 px-7 rounded-full font-semibold">
                  <ShoppingBag className="w-4 h-4 mr-2" /> Belanja Sekarang
                </Button>
              </Link>
              <a href="https://wa.me/6282216594354" target="_blank" rel="noreferrer" data-testid="wall-cta-wa">
                <Button variant="outline" className="bg-transparent border-[hsla(174,70%,55%,0.4)] text-[hsl(var(--reef-foam))] hover:bg-[hsla(174,70%,55%,0.1)] h-12 px-7 rounded-full">
                  <MessageCircle className="w-4 h-4 mr-2" /> Tanya Dulu
                </Button>
              </a>
            </div>
          </div>
        </div>
      </section>
    </div>
  );
}
