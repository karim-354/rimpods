import { useState, useEffect } from "react";
import { Link, useNavigate } from "react-router-dom";
import axios from "axios";
import Header from "../components/Header";
import { useCart, formatRupiah } from "../lib/cart";
import { Button } from "../components/ui/button";
import { Input } from "../components/ui/input";
import { Label } from "../components/ui/label";
import { Textarea } from "../components/ui/textarea";
import { RadioGroup, RadioGroupItem } from "../components/ui/radio-group";
import { ChevronLeft, MessageCircle, ShoppingBag, Gift, X } from "lucide-react";
import { toast } from "sonner";
import { trackInitiateCheckout, trackLead } from "../lib/tracker";
import { getVoucher, clearVoucher, VOUCHER_VALUE } from "../lib/voucher";

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;
const MIN_VOUCHER_SUBTOTAL = 100000;

export default function Checkout() {
  const navigate = useNavigate();
  const { items, subtotal, shipping, total: baseTotal, clear } = useCart();
  const [submitting, setSubmitting] = useState(false);
  const [voucher, setVoucher] = useState(getVoucher());
  const [form, setForm] = useState({
    name: "",
    phone: "",
    email: "",
    address: "",
    city: "",
    notes: "",
  });
  const [channel, setChannel] = useState("whatsapp");

  useEffect(() => {
    const sync = () => setVoucher(getVoucher());
    window.addEventListener("rimpods:voucher", sync);
    window.addEventListener("storage", sync);
    return () => {
      window.removeEventListener("rimpods:voucher", sync);
      window.removeEventListener("storage", sync);
    };
  }, []);

  const voucherEligible = !!voucher && subtotal >= MIN_VOUCHER_SUBTOTAL;
  const discount = voucherEligible ? Math.min(VOUCHER_VALUE, subtotal) : 0;
  const total = Math.max(0, baseTotal - discount);

  useEffect(() => {
    if (items.length > 0) trackInitiateCheckout(items, total);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const setF = (k) => (e) => setForm({ ...form, [k]: e.target.value });

  const submit = async (e) => {
    e.preventDefault();
    if (items.length === 0) {
      toast.error("Keranjang kamu masih kosong nih.");
      return;
    }
    if (!form.name || !form.phone || !form.address || !form.city) {
      toast.error("Lengkapi nama, nomor, alamat, dan kota dulu yaa.");
      return;
    }
    setSubmitting(true);
    try {
      const payload = {
        items: items.map((i) => ({ product_id: i.product_id, quantity: i.quantity })),
        contact: form,
        payment_channel: channel,
        voucher_code: voucherEligible ? voucher : null,
      };
      const { data } = await axios.post(`${API}/orders`, payload);
      const orderInfo = {
        order_number: data.order_number,
        whatsapp_url: data.whatsapp_url,
        tokopedia_url: data.tokopedia_url,
        items: data.items,
        total: data.total,
        channel,
      };
      sessionStorage.setItem("rimpods_last_order", JSON.stringify(orderInfo));
      trackLead(data);
      clear();
      if (voucherEligible) clearVoucher();
      navigate("/sukses");
    } catch (err) {
      toast.error("Gagal proses order, coba lagi ya.");
      console.error(err);
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="reef-grad min-h-screen text-[hsl(var(--reef-foam))]">
      <Header onCartClick={() => navigate("/checkout")} />
      <main className="max-w-6xl mx-auto px-5 lg:px-10 py-10">
        <Link to="/" className="inline-flex items-center text-sm opacity-70 hover:opacity-100 mb-6" data-testid="back-home-link">
          <ChevronLeft className="w-4 h-4 mr-1" /> Lanjut belanja
        </Link>

        <h1 className="font-display text-4xl lg:text-5xl tracking-tight">Checkout</h1>
        <p className="mt-2 opacity-70">Isi data pengiriman, kita kirim detail order ke WhatsApp atau Tokopedia.</p>

        {items.length === 0 ? (
          <div className="mt-12 glass-card rounded-2xl p-10 text-center">
            <ShoppingBag className="w-10 h-10 mx-auto opacity-50" />
            <p className="font-display text-2xl mt-4">Keranjang masih kosong.</p>
            <Link to="/" className="mt-4 inline-block">
              <Button data-testid="goto-shop-btn" className="coral-pill mt-4 rounded-full h-12 px-6">Mulai Belanja</Button>
            </Link>
          </div>
        ) : (
          <form onSubmit={submit} className="mt-10 grid lg:grid-cols-3 gap-8" data-testid="checkout-form">
            <div className="lg:col-span-2 space-y-6">
              <section className="glass-card rounded-2xl p-6">
                <h2 className="font-display text-2xl mb-4">Data Pengiriman</h2>
                <div className="grid sm:grid-cols-2 gap-4">
                  <Field label="Nama Lengkap" testid="input-name">
                    <Input data-testid="input-name" required value={form.name} onChange={setF("name")} placeholder="Nama kamu" className="bg-[hsla(192,55%,22%,0.4)] border-[hsla(174,70%,55%,0.25)]" />
                  </Field>
                  <Field label="No WhatsApp" testid="input-phone">
                    <Input data-testid="input-phone" required value={form.phone} onChange={setF("phone")} placeholder="0812..." className="bg-[hsla(192,55%,22%,0.4)] border-[hsla(174,70%,55%,0.25)]" />
                  </Field>
                  <Field label="Email (opsional)" testid="input-email">
                    <Input data-testid="input-email" type="email" value={form.email} onChange={setF("email")} placeholder="email@example.com" className="bg-[hsla(192,55%,22%,0.4)] border-[hsla(174,70%,55%,0.25)]" />
                  </Field>
                  <Field label="Kota" testid="input-city">
                    <Input data-testid="input-city" required value={form.city} onChange={setF("city")} placeholder="Jakarta / Surabaya / ..." className="bg-[hsla(192,55%,22%,0.4)] border-[hsla(174,70%,55%,0.25)]" />
                  </Field>
                  <div className="sm:col-span-2">
                    <Field label="Alamat Lengkap" testid="input-address">
                      <Textarea data-testid="input-address" required value={form.address} onChange={setF("address")} placeholder="Jl. ..., RT/RW, Kelurahan, Kecamatan, Kode Pos" rows={3} className="bg-[hsla(192,55%,22%,0.4)] border-[hsla(174,70%,55%,0.25)]" />
                    </Field>
                  </div>
                  <div className="sm:col-span-2">
                    <Field label="Catatan untuk Admin (opsional)" testid="input-notes">
                      <Textarea data-testid="input-notes" value={form.notes} onChange={setF("notes")} placeholder="Volume tank, jenis coral, request packing, dll." rows={2} className="bg-[hsla(192,55%,22%,0.4)] border-[hsla(174,70%,55%,0.25)]" />
                    </Field>
                  </div>
                </div>
              </section>

              <section className="glass-card rounded-2xl p-6">
                <h2 className="font-display text-2xl mb-4">Cara Bayar</h2>
                <RadioGroup value={channel} onValueChange={setChannel} className="space-y-3" data-testid="payment-channel">
                  <ChannelOption value="whatsapp" label="Order via WhatsApp" desc="Detail otomatis terkirim ke admin Rimpods, transfer manual." current={channel} />
                  <ChannelOption value="tokopedia" label="Lanjut bayar di Tokopedia" desc="Diarahkan ke listing Tokopedia, bayar pakai metode resmi (cicilan 0%, COD, dll)." current={channel} />
                </RadioGroup>
              </section>
            </div>

            <aside className="space-y-4 lg:sticky lg:top-24 self-start">
              <section className="glass-card rounded-2xl p-6">
                <h2 className="font-display text-2xl mb-4">Ringkasan</h2>
                <ul className="space-y-3" data-testid="order-summary">
                  {items.map((i) => (
                    <li key={i.product_id} className="flex gap-3 text-sm">
                      <img src={i.image} alt={i.name} className="w-14 h-14 rounded-lg object-cover" />
                      <div className="flex-1">
                        <div className="line-clamp-2">{i.name}</div>
                        <div className="opacity-60 text-xs">{i.quantity} × {formatRupiah(i.price)}</div>
                      </div>
                      <div className="font-medium">{formatRupiah(i.price * i.quantity)}</div>
                    </li>
                  ))}
                </ul>
                <div className="mt-4 pt-4 border-t border-[hsla(174,70%,55%,0.15)] space-y-2 text-sm">
                  <Row k="Subtotal" v={formatRupiah(subtotal)} />
                  <Row k="Ongkir" v={shipping === 0 ? "Gratis" : formatRupiah(shipping)} />
                  {voucher && (
                    <div className={`flex items-start gap-2 text-xs p-2.5 rounded-lg ${voucherEligible ? "bg-[hsla(174,70%,55%,0.1)] border border-[hsla(174,70%,55%,0.25)]" : "bg-[hsla(8,89%,64%,0.1)] border border-[hsla(8,89%,64%,0.25)]"}`} data-testid="voucher-banner">
                      <Gift className={`w-4 h-4 mt-0.5 flex-shrink-0 ${voucherEligible ? "text-[hsl(var(--reef-glow))]" : "text-[hsl(var(--reef-coral))]"}`} />
                      <div className="flex-1">
                        <div className="font-semibold">
                          Voucher <span className="font-mono">{voucher}</span>
                        </div>
                        <div className="opacity-70 text-[11px] mt-0.5">
                          {voucherEligible
                            ? `Hemat ${formatRupiah(discount)} di total.`
                            : `Min. belanja ${formatRupiah(MIN_VOUCHER_SUBTOTAL)} biar voucher aktif.`}
                        </div>
                      </div>
                      <button
                        type="button"
                        data-testid="voucher-remove"
                        onClick={() => { clearVoucher(); setVoucher(null); }}
                        className="opacity-50 hover:opacity-100 p-0.5"
                        aria-label="Hapus voucher"
                      >
                        <X className="w-3.5 h-3.5" />
                      </button>
                    </div>
                  )}
                  {voucherEligible && (
                    <Row k={`Diskon voucher`} v={`-${formatRupiah(discount)}`} />
                  )}
                  <Row k="Total" v={formatRupiah(total)} bold testId="summary-total" />
                </div>
                <Button
                  type="submit"
                  data-testid="place-order-btn"
                  disabled={submitting}
                  className="w-full mt-5 coral-pill hover:opacity-90 h-12 rounded-full font-semibold"
                >
                  {submitting ? "Memproses..." : channel === "whatsapp" ? "Buat Pesanan via WhatsApp" : "Lanjut ke Tokopedia"}
                  {channel === "whatsapp" ? <MessageCircle className="w-4 h-4 ml-2" /> : null}
                </Button>
                <p className="text-[11px] mt-3 opacity-60 text-center">
                  Dengan menekan tombol, kamu setuju order detail ini dikirim ke admin Rimpods.
                </p>
              </section>
            </aside>
          </form>
        )}
      </main>
    </div>
  );
}

function Field({ label, children }) {
  return (
    <div>
      <Label className="text-xs uppercase tracking-wider opacity-70 mb-2 block">{label}</Label>
      {children}
    </div>
  );
}

function Row({ k, v, bold, testId }) {
  return (
    <div className={`flex justify-between ${bold ? "text-base pt-2" : ""}`}>
      <span className={bold ? "font-semibold" : "opacity-70"}>{k}</span>
      <span data-testid={testId} className={bold ? "font-display text-xl text-[hsl(var(--reef-glow))]" : ""}>{v}</span>
    </div>
  );
}

function ChannelOption({ value, label, desc, current }) {
  const active = value === current;
  return (
    <label
      data-testid={`channel-${value}`}
      className={`flex items-start gap-3 p-4 rounded-xl border cursor-pointer transition ${active ? "border-[hsl(var(--reef-glow))] bg-[hsla(174,70%,55%,0.08)]" : "border-[hsla(174,70%,55%,0.2)] hover:border-[hsla(174,70%,55%,0.4)]"}`}
    >
      <RadioGroupItem value={value} className="mt-1 border-[hsla(174,70%,55%,0.5)]" />
      <div>
        <div className="font-medium">{label}</div>
        <div className="text-sm opacity-70">{desc}</div>
      </div>
    </label>
  );
}
