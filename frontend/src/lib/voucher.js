// Rimpods voucher storage — exit-intent first-buy code
const KEY = "rimpods_voucher_v1";
const SEEN_KEY = "rimpods_exit_intent_seen";

export const VOUCHER_CODE = "FIRSTBUY20K";
export const VOUCHER_VALUE = 20000; // Rp20.000 flat off

export const saveVoucher = (code = VOUCHER_CODE) => {
  localStorage.setItem(KEY, code);
  window.dispatchEvent(new Event("rimpods:voucher"));
};

export const getVoucher = () => localStorage.getItem(KEY) || null;

export const clearVoucher = () => {
  localStorage.removeItem(KEY);
  window.dispatchEvent(new Event("rimpods:voucher"));
};

export const exitIntentSeen = () => sessionStorage.getItem(SEEN_KEY) === "1";
export const markExitIntentSeen = () => sessionStorage.setItem(SEEN_KEY, "1");
