import { Link, useLocation } from "react-router-dom";
import { ShoppingBag } from "lucide-react";
import { useCart } from "../lib/cart";
import { LOGO_WHITE_URL } from "../lib/brand";
import { Button } from "./ui/button";

export default function Header({ onCartClick }) {
  const { count } = useCart();
  const { pathname } = useLocation();
  const onLanding = pathname === "/";

  const goSection = (id) => (e) => {
    if (!onLanding) return;
    e.preventDefault();
    document.getElementById(id)?.scrollIntoView({ behavior: "smooth" });
  };

  return (
    <header
      data-testid="site-header"
      className="sticky top-0 z-40 backdrop-blur-md bg-[hsla(198,75%,8%,0.7)] border-b border-[hsla(174,70%,55%,0.15)]"
    >
      <div className="max-w-7xl mx-auto px-5 lg:px-10 h-16 flex items-center justify-between">
        <Link to="/" className="flex items-center gap-2 group" data-testid="brand-logo">
          <img src={LOGO_WHITE_URL} alt="Rimpods" className="h-11 lg:h-12 w-auto" />
        </Link>

        {onLanding && (
          <nav className="hidden lg:flex items-center gap-8 text-sm text-[hsl(var(--reef-foam))]/80">
            <a href="#produk" onClick={goSection("produk")} className="hover:text-[hsl(var(--reef-glow))]" data-testid="nav-produk">Produk</a>
            <a href="#cerita" onClick={goSection("cerita")} className="hover:text-[hsl(var(--reef-glow))]" data-testid="nav-cerita">Cerita</a>
            <a href="#cara-pakai" onClick={goSection("cara-pakai")} className="hover:text-[hsl(var(--reef-glow))]" data-testid="nav-cara">Cara Pakai</a>
            <a href="#testimoni" onClick={goSection("testimoni")} className="hover:text-[hsl(var(--reef-glow))]" data-testid="nav-testi">Testimoni</a>
            <a href="#faq" onClick={goSection("faq")} className="hover:text-[hsl(var(--reef-glow))]" data-testid="nav-faq">FAQ</a>
          </nav>
        )}

        <div className="flex items-center gap-3">
          <Button
            data-testid="open-cart-btn"
            onClick={onCartClick}
            variant="outline"
            className="relative bg-transparent text-[hsl(var(--reef-foam))] border-[hsla(174,70%,55%,0.35)] hover:bg-[hsla(174,70%,55%,0.12)]"
          >
            <ShoppingBag className="w-4 h-4 mr-2" />
            Keranjang
            {count > 0 && (
              <span
                data-testid="cart-count-badge"
                className="absolute -top-2 -right-2 w-5 h-5 rounded-full text-[11px] grid place-items-center coral-pill font-semibold"
              >
                {count}
              </span>
            )}
          </Button>
        </div>
      </div>
    </header>
  );
}
