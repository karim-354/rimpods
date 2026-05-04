import { useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import Header from "../components/Header";
import { Button } from "../components/ui/button";
import { CheckCircle2, MessageCircle, ExternalLink, Copy } from "lucide-react";
import { toast } from "sonner";
import { formatRupiah } from "../lib/cart";
import { trackPurchase } from "../lib/tracker";

export default function Success() {
  const [order, setOrder] = useState(null);
  const navigate = useNavigate();

  useEffect(() => {
    const raw = sessionStorage.getItem("rimpods_last_order");
    if (!raw) {
      navigate("/");
      return;
    }
    const parsed = JSON.parse(raw);
    setOrder(parsed);
    trackPurchase(parsed);
    // Auto-redirect setelah 1.2s ke channel pilihan
    if (parsed.channel === "whatsapp") {
      setTimeout(() => window.open(parsed.whatsapp_url, "_blank"), 1200);
    } else if (parsed.channel === "tokopedia") {
      setTimeout(() => window.open(parsed.tokopedia_url, "_blank"), 1200);
    }
  }, [navigate]);

  if (!order) return null;

  const copyOrder = () => {
    navigator.clipboard.writeText(order.order_number);
    toast.success("Nomor order berhasil disalin.");
  };

  return (
    <div className="reef-grad min-h-screen text-[hsl(var(--reef-foam))]">
      <Header onCartClick={() => navigate("/checkout")} />
      <main className="max-w-3xl mx-auto px-5 lg:px-10 py-16">
        <div className="glass-card glow-ring rounded-[2rem] p-10 text-center" data-testid="order-success-card">
          <div className="w-16 h-16 mx-auto rounded-full bg-[hsla(174,70%,55%,0.15)] grid place-items-center">
            <CheckCircle2 className="w-8 h-8 text-[hsl(var(--reef-glow))]" />
          </div>
          <h1 className="font-display text-4xl mt-6 tracking-tight">
            {order.channel === "midtrans"
              ? "Terima kasih, pesanan kamu sudah dibuat."
              : "Terima kasih, pesanan kamu sudah kami terima."}
          </h1>
          <p className="mt-3 opacity-75">
            {order.channel === "whatsapp" && "Kami akan segera mengarahkanmu ke WhatsApp admin untuk menyelesaikan konfirmasi. Jika laman tidak terbuka secara otomatis, silakan klik tombol di bawah."}
            {order.channel === "tokopedia" && "Kami akan segera mengarahkanmu ke Tokopedia untuk menyelesaikan konfirmasi. Jika laman tidak terbuka secara otomatis, silakan klik tombol di bawah."}
            {order.channel === "midtrans" && "Status pembayaran akan terupdate otomatis begitu pembayaran selesai. Bila popup pembayaran sempat tertutup, kamu dapat melanjutkan melalui tombol di bawah."}
          </p>

          <div className="mt-8 flex items-center justify-center gap-2">
            <span className="text-sm opacity-60">No. Order:</span>
            <code data-testid="order-number" className="font-mono text-sm bg-[hsla(192,55%,22%,0.5)] px-3 py-1 rounded-lg">{order.order_number}</code>
            <button onClick={copyOrder} className="opacity-60 hover:opacity-100" data-testid="copy-order-btn">
              <Copy className="w-4 h-4" />
            </button>
          </div>

          <div className="mt-2 text-sm opacity-70">
            Total: <span className="text-[hsl(var(--reef-glow))] font-semibold">{formatRupiah(order.total)}</span>
          </div>

          <div className="mt-8 flex flex-wrap gap-3 justify-center">
            {order.channel === "whatsapp" && (
              <a href={order.whatsapp_url} target="_blank" rel="noreferrer" data-testid="open-wa-btn">
                <Button className="coral-pill hover:opacity-90 h-12 px-7 rounded-full font-semibold">
                  <MessageCircle className="w-4 h-4 mr-2" /> Buka WhatsApp Admin
                </Button>
              </a>
            )}
            {order.channel === "tokopedia" && (
              <a href={order.tokopedia_url} target="_blank" rel="noreferrer" data-testid="open-toko-btn">
                <Button className="coral-pill hover:opacity-90 h-12 px-7 rounded-full font-semibold">
                  <ExternalLink className="w-4 h-4 mr-2" /> Lanjutkan ke Tokopedia
                </Button>
              </a>
            )}
            {order.channel === "midtrans" && order.midtrans_redirect_url && (
              <a href={order.midtrans_redirect_url} target="_blank" rel="noreferrer" data-testid="open-midtrans-btn">
                <Button className="coral-pill hover:opacity-90 h-12 px-7 rounded-full font-semibold">
                  <ExternalLink className="w-4 h-4 mr-2" /> Lanjutkan Pembayaran
                </Button>
              </a>
            )}
            <Link to="/" data-testid="back-home-btn">
              <Button variant="outline" className="bg-transparent border-[hsla(174,70%,55%,0.4)] text-[hsl(var(--reef-foam))] hover:bg-[hsla(174,70%,55%,0.1)] h-12 px-7 rounded-full">
                Kembali ke Beranda
              </Button>
            </Link>
          </div>
        </div>
      </main>
    </div>
  );
}
