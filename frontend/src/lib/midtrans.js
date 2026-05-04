// Midtrans Snap.js loader + pay helper
let snapLoadPromise = null;

const getScriptUrl = () => {
  const isProd =
    (process.env.REACT_APP_MIDTRANS_IS_PRODUCTION || "").toLowerCase() === "true";
  return isProd
    ? "https://app.midtrans.com/snap/snap.js"
    : "https://app.sandbox.midtrans.com/snap/snap.js";
};

export const loadSnap = () => {
  if (typeof window === "undefined") return Promise.resolve(null);
  if (window.snap) return Promise.resolve(window.snap);
  if (snapLoadPromise) return snapLoadPromise;

  const clientKey = process.env.REACT_APP_MIDTRANS_CLIENT_KEY;
  if (!clientKey) {
    return Promise.reject(new Error("REACT_APP_MIDTRANS_CLIENT_KEY tidak diset"));
  }

  snapLoadPromise = new Promise((resolve, reject) => {
    const existing = document.querySelector('script[data-rimpods="snap"]');
    if (existing) {
      existing.addEventListener("load", () => resolve(window.snap));
      existing.addEventListener("error", () => reject(new Error("Snap.js gagal dimuat")));
      return;
    }
    const s = document.createElement("script");
    s.src = getScriptUrl();
    s.setAttribute("data-client-key", clientKey);
    s.setAttribute("data-rimpods", "snap");
    s.async = true;
    s.onload = () => resolve(window.snap);
    s.onerror = () => {
      snapLoadPromise = null;
      reject(new Error("Snap.js gagal dimuat"));
    };
    document.head.appendChild(s);
  });
  return snapLoadPromise;
};

export const paySnap = (token, callbacks = {}) =>
  new Promise(async (resolve, reject) => {
    try {
      const snap = await loadSnap();
      if (!snap) return reject(new Error("Snap.js tidak tersedia"));
      snap.pay(token, {
        onSuccess: (r) => { callbacks.onSuccess?.(r); resolve({ outcome: "success", result: r }); },
        onPending: (r) => { callbacks.onPending?.(r); resolve({ outcome: "pending", result: r }); },
        onError: (r) => { callbacks.onError?.(r); reject(r); },
        onClose: () => { callbacks.onClose?.(); resolve({ outcome: "closed" }); },
      });
    } catch (e) {
      reject(e);
    }
  });
