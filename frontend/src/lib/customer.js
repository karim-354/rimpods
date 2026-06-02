// Memori pelanggan ringan (sisi browser) untuk sapaan pembeli lama.
// Tidak menyimpan data sensitif — hanya nama & nomor HP untuk personalisasi.
const KEY = "rimpods_customer";

export const saveReturningCustomer = (name, phone) => {
  try {
    if (!name && !phone) return;
    localStorage.setItem(
      KEY,
      JSON.stringify({ name: name || "", phone: phone || "", savedAt: Date.now() })
    );
  } catch (e) {
    /* localStorage tidak tersedia — abaikan */
  }
};

export const getReturningCustomer = () => {
  try {
    const raw = localStorage.getItem(KEY);
    if (!raw) return null;
    const data = JSON.parse(raw);
    if (!data || (!data.name && !data.phone)) return null;
    return data;
  } catch (e) {
    return null;
  }
};

export const clearReturningCustomer = () => {
  try {
    localStorage.removeItem(KEY);
  } catch (e) {
    /* abaikan */
  }
};

// Ambil nama panggilan (kata pertama) untuk sapaan yang akrab.
export const firstName = (name) => {
  if (!name) return "";
  return name.trim().split(/\s+/)[0];
};
