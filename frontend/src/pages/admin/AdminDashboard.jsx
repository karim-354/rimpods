import { useEffect, useState } from "react";
import { useLocation } from "react-router-dom";
import axios from "axios";
import { fetchMe, logout, startGoogleLogin } from "../../lib/auth";
import { Button } from "../../components/ui/button";
import { LogOut, ShieldAlert, TrendingUp, ShoppingBag, Gift, Wallet, RefreshCcw } from "lucide-react";
import { formatRupiah } from "../../lib/cart";
import WhatsAppQuickActions from "../../components/admin/WhatsAppQuickActions";
import { toast } from "sonner";

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

function LoginGate({ error }) {
  return (
    <div className="min-h-screen grid place-items-center bg-[hsl(var(--reef-deep))] text-[hsl(var(--reef-foam))] px-5">
      <div className="glass-card rounded-[2rem] p-10 max-w-md w-full text-center" data-testid="admin-login-card">
        <div className="w-14 h-14 mx-auto rounded-2xl bg-[hsla(45,85%,55%,0.15)] grid place-items-center">
          <ShieldAlert className="w-7 h-7 text-[hsl(var(--reef-glow))]" />
        </div>
        <h1 className="font-display text-3xl mt-5">Admin Rimpods</h1>
        <p className="mt-3 opacity-70 text-sm">
          Masuk dengan akun Google yang terdaftar. Akses hanya tersedia untuk tim internal Rimpods.
        </p>
        {error && (
          <p className="mt-4 text-sm text-[hsl(var(--reef-coral))]" data-testid="admin-auth-error">
            {error}
          </p>
        )}
        <Button
          data-testid="admin-google-login-btn"
          onClick={startGoogleLogin}
          className="mt-6 coral-pill hover:opacity-90 h-12 rounded-full font-semibold w-full"
        >
          Masuk dengan Google
        </Button>
      </div>
    </div>
  );
}

function NotAuthorized({ email, onLogout }) {
  return (
    <div className="min-h-screen grid place-items-center bg-[hsl(var(--reef-deep))] text-[hsl(var(--reef-foam))] px-5">
      <div className="glass-card rounded-[2rem] p-10 max-w-md w-full text-center" data-testid="admin-not-authorized">
        <ShieldAlert className="w-14 h-14 mx-auto text-[hsl(var(--reef-coral))]" />
        <h1 className="font-display text-3xl mt-5">Akses tidak diizinkan</h1>
        <p className="mt-3 opacity-75 text-sm">
          Akun <b>{email}</b> belum terdaftar sebagai admin Rimpods. Silakan hubungi tim internal untuk penambahan akses.
        </p>
        <Button
          onClick={onLogout}
          variant="outline"
          className="mt-6 bg-transparent border-[hsla(174,70%,55%,0.4)] text-[hsl(var(--reef-foam))] hover:bg-[hsla(174,70%,55%,0.1)] h-11 rounded-full w-full"
        >
          <LogOut className="w-4 h-4 mr-2" /> Keluar
        </Button>
      </div>
    </div>
  );
}

function KpiCard({ icon: Icon, label, value, sub, testId }) {
  return (
    <div className="glass-card rounded-2xl p-5" data-testid={testId}>
      <div className="flex items-center gap-3">
        <div className="w-10 h-10 rounded-xl bg-[hsla(174,70%,55%,0.15)] grid place-items-center text-[hsl(var(--reef-glow))]">
          <Icon className="w-4 h-4" />
        </div>
        <div className="text-xs uppercase tracking-widest opacity-60">{label}</div>
      </div>
      <div className="mt-4 font-display text-3xl text-[hsl(var(--reef-glow))]">{value}</div>
      {sub && <div className="text-xs opacity-60 mt-1">{sub}</div>}
    </div>
  );
}

export default function AdminDashboard() {
  const location = useLocation();
  const [authState, setAuthState] = useState(location.state?.user ? "authorized" : "checking");
  const [user, setUser] = useState(location.state?.user || null);
  const [authError, setAuthError] = useState(location.state?.authError || null);
  const [stats, setStats] = useState(null);
  const [orders, setOrders] = useState([]);
  const [loading, setLoading] = useState(false);
  const [syncing, setSyncing] = useState(null);

  const syncPayment = async (orderNumber) => {
    setSyncing(orderNumber);
    try {
      const { data } = await axios.post(
        `${API}/admin/orders/${orderNumber}/sync-payment`,
        {},
        { withCredentials: true }
      );
      if (data.status === "paid") {
        if (data.biteship_booked) {
          toast.success(`${orderNumber}: LUNAS • Order Biteship dibuat (AWB ${data.shipping_awb || "-"})`);
        } else if (data.biteship_error) {
          toast.warning(`${orderNumber}: LUNAS, tapi Biteship gagal: ${data.biteship_error}`);
        } else if (data.shipping_awb) {
          toast.success(`${orderNumber}: LUNAS • Biteship sudah ada`);
        } else {
          toast.success(`${orderNumber}: LUNAS`);
        }
      } else {
        toast.info(`${orderNumber}: Midtrans = ${data.transaction_status} (status: ${data.status})`);
      }
      await loadData();
    } catch (err) {
      toast.error(err?.response?.data?.detail || "Gagal cek status pembayaran");
    } finally {
      setSyncing(null);
    }
  };

  useEffect(() => {
    // If AuthCallback didn't pass a user, verify via /auth/me
    if (user) {
      setAuthState(user.is_admin ? "authorized" : "not_admin");
      return;
    }
    // Skip /me check if returning from OAuth (hash still present)
    if (window.location.hash?.includes("session_id=")) return;
    (async () => {
      try {
        const me = await fetchMe();
        setUser(me);
        setAuthState(me.is_admin ? "authorized" : "not_admin");
      } catch {
        setAuthState("login");
      }
    })();
  }, [user]);

  useEffect(() => {
    if (authState !== "authorized") return;
    loadData();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [authState]);

  const loadData = async () => {
    setLoading(true);
    try {
      const [s, o] = await Promise.all([
        axios.get(`${API}/admin/stats?days=30`, { withCredentials: true }),
        axios.get(`${API}/admin/orders?limit=50`, { withCredentials: true }),
      ]);
      setStats(s.data);
      setOrders(o.data.orders || []);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleLogout = async () => {
    await logout();
    setUser(null);
    setAuthState("login");
  };

  if (authState === "checking") {
    return (
      <div className="min-h-screen grid place-items-center bg-[hsl(var(--reef-deep))] text-white">
        <div className="w-10 h-10 border-2 border-current border-t-transparent rounded-full animate-spin opacity-60" />
      </div>
    );
  }

  if (authState === "login") {
    return <LoginGate error={authError} />;
  }

  if (authState === "not_admin") {
    return <NotAuthorized email={user?.email} onLogout={handleLogout} />;
  }

  return (
    <div className="min-h-screen bg-[hsl(var(--reef-deep))] text-[hsl(var(--reef-foam))]">
      <header className="border-b border-[hsla(174,70%,55%,0.15)] bg-[hsla(198,75%,8%,0.7)] backdrop-blur-md sticky top-0 z-30">
        <div className="max-w-7xl mx-auto px-5 lg:px-10 h-16 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <img
              data-testid="admin-brand-logo"
              src="https://customer-assets.emergentagent.com/job_coral-product-hub/artifacts/5gz4ojsf_Logo%20Transparant%20%284%29.png"
              alt="Rimpods"
              loading="lazy"
              className="h-8 w-auto"
            />
            <span className="h-4 w-px bg-[hsla(174,70%,55%,0.3)]" />
            <span className="font-display text-lg">Admin Dashboard</span>
          </div>
          <div className="flex items-center gap-3">
            <div className="hidden sm:flex items-center gap-2 text-sm opacity-80">
              {user?.picture && (
                <img src={user.picture} alt="" loading="lazy" className="w-7 h-7 rounded-full" referrerPolicy="no-referrer" />
              )}
              <span data-testid="admin-user-email">{user?.email}</span>
            </div>
            <Button
              data-testid="admin-refresh-btn"
              onClick={loadData}
              variant="outline"
              size="sm"
              className="bg-transparent border-[hsla(174,70%,55%,0.3)] text-[hsl(var(--reef-foam))] hover:bg-[hsla(174,70%,55%,0.1)] rounded-full"
              disabled={loading}
            >
              <RefreshCcw className={`w-3.5 h-3.5 mr-1.5 ${loading ? "animate-spin" : ""}`} /> Refresh
            </Button>
            <Button
              data-testid="admin-logout-btn"
              onClick={handleLogout}
              variant="ghost"
              size="sm"
              className="text-[hsl(var(--reef-foam))]/70 hover:text-[hsl(var(--reef-foam))] hover:bg-transparent"
            >
              <LogOut className="w-4 h-4" />
            </Button>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-5 lg:px-10 py-10">
        <h1 className="font-display text-3xl lg:text-4xl tracking-tight">Ringkasan Operasional</h1>
        <p className="mt-2 opacity-70 text-sm">Data live dari Rimpods. Update otomatis per refresh.</p>

        <section className="mt-8 grid sm:grid-cols-2 lg:grid-cols-4 gap-4" data-testid="admin-kpi-grid">
          <KpiCard
            icon={ShoppingBag}
            label="Total Order (30 hari)"
            value={stats?.window?.orders ?? "—"}
            sub={`Keseluruhan: ${stats?.overall?.total_orders ?? 0}`}
            testId="kpi-orders"
          />
          <KpiCard
            icon={Wallet}
            label="Pendapatan (30 hari)"
            value={stats ? formatRupiah(stats.window.revenue) : "—"}
            sub={`Total: ${stats ? formatRupiah(stats.overall.total_revenue) : "—"}`}
            testId="kpi-revenue"
          />
          <KpiCard
            icon={Gift}
            label="Voucher Ditebus"
            value={stats?.vouchers_redeemed ?? "—"}
            sub={`Nilai diskon: ${stats ? formatRupiah(stats.overall.total_discount) : "—"}`}
            testId="kpi-vouchers"
          />
          <KpiCard
            icon={TrendingUp}
            label="Kanal Dominan"
            value={
              stats?.channel_breakdown
                ? Object.entries(stats.channel_breakdown).sort((a, b) => b[1] - a[1])[0]?.[0] ?? "—"
                : "—"
            }
            sub={
              stats?.channel_breakdown
                ? Object.entries(stats.channel_breakdown).map(([k, v]) => `${k}: ${v}`).join(" · ")
                : "—"
            }
            testId="kpi-channel"
          />
        </section>

        <section className="mt-10">
          <div className="flex items-end justify-between mb-4">
            <h2 className="font-display text-2xl">Order Terbaru</h2>
            <span className="text-xs opacity-60">Menampilkan {orders.length} dari {stats?.overall?.total_orders ?? orders.length}</span>
          </div>
          <div className="glass-card rounded-2xl overflow-hidden">
            <div className="overflow-x-auto">
              <table className="min-w-full text-sm" data-testid="admin-orders-table">
                <thead className="bg-[hsla(192,55%,22%,0.5)] text-xs uppercase tracking-widest opacity-70">
                  <tr>
                    <th className="text-left px-4 py-3">Order</th>
                    <th className="text-left px-4 py-3">Tanggal</th>
                    <th className="text-left px-4 py-3">Customer</th>
                    <th className="text-left px-4 py-3">Item</th>
                    <th className="text-right px-4 py-3">Total</th>
                    <th className="text-left px-4 py-3">Voucher</th>
                    <th className="text-left px-4 py-3">Kanal</th>
                    <th className="text-left px-4 py-3">Status</th>
                    <th className="text-left px-4 py-3">Aksi</th>
                  </tr>
                </thead>
                <tbody>
                  {orders.length === 0 ? (
                    <tr>
                      <td colSpan={9} className="text-center py-12 opacity-60">
                        Belum ada order masuk.
                      </td>
                    </tr>
                  ) : (
                    orders.map((o) => (
                      <tr key={o.id} className="border-t border-[hsla(174,70%,55%,0.1)] hover:bg-[hsla(174,70%,55%,0.05)]">
                        <td className="px-4 py-3 font-mono text-xs">{o.order_number}</td>
                        <td className="px-4 py-3 text-xs opacity-80">
                          {o.created_at ? new Date(o.created_at).toLocaleString("id-ID", { dateStyle: "short", timeStyle: "short" }) : "—"}
                        </td>
                        <td className="px-4 py-3">
                          <div>{o.contact?.name || "—"}</div>
                          <div className="text-xs opacity-60">{o.contact?.phone}</div>
                        </td>
                        <td className="px-4 py-3 text-xs opacity-80 max-w-xs truncate">
                          {(o.items || []).map((i) => `${i.name} x${i.quantity}`).join(", ")}
                        </td>
                        <td className="px-4 py-3 text-right font-semibold text-[hsl(var(--reef-glow))]">
                          {formatRupiah(o.total)}
                        </td>
                        <td className="px-4 py-3 text-xs">
                          {o.voucher_code ? (
                            <span className="coral-pill rounded-full px-2 py-0.5 text-[10px] font-bold">{o.voucher_code}</span>
                          ) : (
                            <span className="opacity-40">—</span>
                          )}
                        </td>
                        <td className="px-4 py-3 text-xs capitalize">{o.payment_channel}</td>
                        <td className="px-4 py-3 text-xs">
                          <div className={`capitalize font-semibold ${o.status === "paid" ? "text-emerald-400" : o.status === "failed" ? "text-red-400" : "text-amber-400"}`}>
                            {o.status || "pending"}
                          </div>
                          {o.shipping_awb ? (
                            <div className="text-[10px] text-emerald-400/80">Biteship ✓</div>
                          ) : (
                            o.status === "paid" && <div className="text-[10px] text-amber-400/80">Biteship belum</div>
                          )}
                        </td>
                        <td className="px-4 py-3">
                          <div className="flex items-center gap-2">
                            {o.payment_channel === "midtrans" && !(o.status === "paid" && o.shipping_awb) && (
                              <Button
                                size="sm"
                                variant="outline"
                                onClick={() => syncPayment(o.order_number)}
                                disabled={syncing === o.order_number}
                                className="bg-transparent border-[hsla(174,70%,55%,0.3)] text-[hsl(var(--reef-foam))] hover:bg-[hsla(174,70%,55%,0.1)] rounded-full text-xs h-8"
                              >
                                <RefreshCcw className={`w-3 h-3 mr-1 ${syncing === o.order_number ? "animate-spin" : ""}`} />
                                {o.status === "paid" ? "Buat Kiriman" : "Cek Bayar"}
                              </Button>
                            )}
                            <WhatsAppQuickActions order={o} />
                          </div>
                        </td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>
          </div>
        </section>

        {stats?.voucher_breakdown?.length > 0 && (
          <section className="mt-10">
            <h2 className="font-display text-2xl mb-4">Voucher Performance</h2>
            <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-4" data-testid="admin-voucher-breakdown">
              {stats.voucher_breakdown.map((v) => (
                <div key={v.code} className="glass-card rounded-2xl p-5">
                  <div className="text-xs uppercase tracking-widest opacity-60">Kode</div>
                  <div className="font-mono font-bold text-xl text-[hsl(var(--reef-glow))] mt-1">{v.code}</div>
                  <div className="mt-3 flex justify-between text-sm">
                    <span className="opacity-70">Ditebus</span>
                    <span>{v.count}×</span>
                  </div>
                  <div className="mt-1 flex justify-between text-sm">
                    <span className="opacity-70">Nilai diskon</span>
                    <span>{formatRupiah(v.total_discount)}</span>
                  </div>
                </div>
              ))}
            </div>
          </section>
        )}
      </main>
    </div>
  );
}
