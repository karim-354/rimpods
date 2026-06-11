// ============================================================
// Rimpods Torch Landing — vanilla JS
// - IntersectionObserver reveal-on-scroll
// - Year auto
// - Lightweight, no external deps
// ============================================================
(function () {
  "use strict";

  // 1) Auto year
  const yearEl = document.getElementById("year");
  if (yearEl) yearEl.textContent = new Date().getFullYear();

  // 2) Reveal-on-scroll
  const els = document.querySelectorAll(".reveal");
  // Failsafe: after 1.2s, force-reveal anything still hidden (prevents blank-state on slow IO)
  setTimeout(() => els.forEach((el) => el.classList.add("in")), 1200);
  if ("IntersectionObserver" in window && els.length) {
    const io = new IntersectionObserver(
      (entries) => {
        entries.forEach((e) => {
          if (e.isIntersecting) {
            e.target.classList.add("in");
            io.unobserve(e.target);
          }
        });
      },
      { rootMargin: "0px 0px -8% 0px", threshold: 0.05 }
    );
    els.forEach((el) => io.observe(el));
  } else {
    els.forEach((el) => el.classList.add("in"));
  }

  // 3) Subtle parallax on the cyan throughline arrow (final CTA section)
  //    Increases anticipation as user nears the offer block.
  const finalSection = document.getElementById("cta-final");
  if (finalSection) {
    const path = finalSection.querySelector("#finalLine");
    if (path) {
      const onScroll = () => {
        const rect = finalSection.getBoundingClientRect();
        const vh = window.innerHeight || 800;
        const progress = Math.max(0, Math.min(1, 1 - rect.top / vh));
        // Pulse the stroke width with progress
        path.style.strokeWidth = (1.6 + progress * 1.4).toFixed(2);
      };
      window.addEventListener("scroll", onScroll, { passive: true });
      onScroll();
    }
  }
})();

// ============================================================
// MYTHOS THROUGHLINE — full-page, scroll-triggered self-drawing line
// - Canvas is a body-level absolute SVG sized to documentElement.scrollHeight
// - Path starts at the bottom-center of the Hero <h1>
// - Weaves through Stress Matrix cards + Biological Engine bullets
// - Ends at the top-center of the final Direct-Checkout CTA (with arrow marker)
// - stroke-dashoffset is mapped linearly to scroll progress (hero h1 → CTA)
// - 100% solid stroke. No dashed pattern. No auto comet.
// ============================================================
(function () {
  "use strict";

  const ANCHOR_IDS = [
    "stressor-1", "solution-1",
    "stressor-2", "solution-2",
    "stressor-3", "solution-3",
    "stressor-4", "solution-4",
    "engine-bullet-1", "engine-bullet-2", "engine-bullet-3"
  ];

  let pathLength = 0;
  let startY = 0; // absolute Y of hero h1 top (page coords) — progress 0
  let endY   = 0; // absolute Y of CTA button top — progress 1
  let lenSamples = []; // arc-length -> Y lookup, so the drawing tip tracks eye-level exactly

  // Per-section colors: gradient stops are positioned dynamically at each
  // section's center Y, so the line changes color as it passes each section.
  const SECTION_COLORS = [
    ["hero",      "#00F0FF"], // cyan — hero glow
    ["rules",     "#F5C542"], // gold — "3 Aturan Emas"
    ["matrix",    "#FF5A5A"], // red — stress factor matrix
    ["engine",    "#00F0FF"], // cyan — biological engine (solusi)
    ["gallery",   "#8A2BE2"], // violet — torch showcase
    ["proof",     "#7DF9FF"], // cyan-glow — hasil pelanggan
    ["cta-final", "#FFD700"]  // gold — final CTA
  ];

  function buildMythosPath() {
    const svg  = document.getElementById("mythos-canvas");
    const line = document.getElementById("mythosLine");
    const halo = document.getElementById("mythosHalo");
    if (!svg || !line) return;

    const hero = document.querySelector("#hero h1");
    const cta  = document.querySelector('[data-testid="final-cta-checkout"]');
    if (!hero || !cta) return;

    // Wrapper-cage sizing: the SVG lives inside #mythos-cage (absolute, height:0,
    // overflow:visible) and is sized in REAL CSS PIXELS to match the document,
    // so 1 viewBox unit === 1 CSS px. The line scrolls naturally with the page.
    const W = document.documentElement.clientWidth;
    const H = document.documentElement.scrollHeight;
    svg.setAttribute("viewBox", `0 0 ${W} ${H}`);
    svg.setAttribute("width", W);
    svg.setAttribute("height", H);
    svg.style.width  = W + "px";
    svg.style.height = H + "px";

    // Stretch the userSpaceOnUse gradient over the full canvas and rebuild
    // its stops at each section's center Y → color follows the section.
    const grad = document.getElementById("neonGradient");
    if (grad) {
      grad.setAttribute("y2", H);
      let stopsHtml = "";
      SECTION_COLORS.forEach(([id, color]) => {
        const sec = document.getElementById(id);
        if (!sec) return;
        const sr = sec.getBoundingClientRect();
        const cy = sr.top + sr.height / 2 + window.scrollY;
        const off = Math.max(0, Math.min(1, cy / H));
        stopsHtml += `<stop offset="${(off * 100).toFixed(2)}%" stop-color="${color}"/>`;
      });
      if (stopsHtml) grad.innerHTML = stopsHtml;
    }

    const abs = (el) => {
      const r = el.getBoundingClientRect();
      return {
        top:    r.top + window.scrollY,
        bottom: r.bottom + window.scrollY,
        left:   r.left + window.scrollX,
        right:  r.right + window.scrollX,
        cx:     r.left + r.width / 2 + window.scrollX,
        cy:     r.top  + r.height / 2 + window.scrollY,
        width:  r.width,
        height: r.height,
      };
    };

    // --- Build anchor list (page coords) ---
    const pts = [];

    // 1. Start: bottom-center of Hero <h1>
    const h = abs(hero);
    pts.push({ x: h.cx, y: h.bottom + 24 });

    // 2. Weaving through Matrix + Engine cards
    const mids = [];
    ANCHOR_IDS.forEach((id) => {
      const el = document.querySelector(`[data-testid="${id}"]`);
      if (!el) return;
      const r = abs(el);
      let x;
      if (id.startsWith("stressor"))      x = r.right - 18;
      else if (id.startsWith("solution")) x = r.left  + 18;
      else {
        const idx = parseInt(id.split("-").pop(), 10) || 1;
        x = r.cx + (idx % 2 === 0 ? 140 : -140);
      }
      mids.push({ x: Math.max(24, Math.min(W - 24, x)), y: r.cy });
    });

    // CRITICAL: sort by page Y so the path always flows downward. On mobile
    // the two matrix columns stack vertically, so DOM order != visual order —
    // without sorting the line loops up/down and tangles over itself.
    mids.sort((a, b) => a.y - b.y);

    let filtered = mids;
    if (W < 768) {
      // Narrow screens: cards stack full-width.
      // 1) Drop anchors that sit too close vertically (kinks/loops).
      filtered = [];
      mids.forEach((p) => {
        if (!filtered.length || p.y - filtered[filtered.length - 1].y > 90) {
          filtered.push(p);
        }
      });
      // 2) Edge-hugging X coords would swing the line across the whole
      //    screen — replace with a gentle center weave.
      const amp = Math.min(W * 0.17, 72);
      filtered.forEach((p, i) => {
        p.x = W / 2 + (i % 2 === 0 ? -amp : amp);
      });
    }

    filtered.forEach((p) => pts.push(p));

    // 3. End: top-center of CTA button (slightly above so arrow lands on it)
    const c = abs(cta);
    pts.push({ x: c.cx, y: c.top - 18 });

    // --- Smooth cubic-bezier path ---
    const r = (n) => n.toFixed(1);
    let d = `M ${r(pts[0].x)} ${r(pts[0].y)}`;
    for (let i = 1; i < pts.length; i++) {
      const p0 = pts[i - 1], p1 = pts[i];
      const dy = p1.y - p0.y;
      const k = 0.55;
      const c1x = p0.x, c1y = p0.y + dy * k;
      const c2x = p1.x, c2y = p1.y - dy * k;
      d += ` C ${r(c1x)} ${r(c1y)}, ${r(c2x)} ${r(c2y)}, ${r(p1.x)} ${r(p1.y)}`;
    }
    line.setAttribute("d", d);
    if (halo) halo.setAttribute("d", d);

    // --- Prep scroll-triggered draw ---
    pathLength = line.getTotalLength();
    line.style.strokeDasharray  = pathLength;
    line.style.strokeDashoffset = pathLength;
    if (halo) {
      halo.style.strokeDasharray  = pathLength;
      halo.style.strokeDashoffset = pathLength;
    }

    // Arc-length -> Y lookup table. The path weaves horizontally, so length
    // is NOT proportional to Y. Sampling lets us place the drawing tip at an
    // exact page Y (the viewport center = the reader's eye-level).
    const SAMPLES = Math.max(200, Math.round(pathLength / 24));
    lenSamples = new Array(SAMPLES + 1);
    for (let i = 0; i <= SAMPLES; i++) {
      const l = (pathLength * i) / SAMPLES;
      lenSamples[i] = { l: l, y: line.getPointAtLength(l).y };
    }

    startY = h.top;   // progress 0: headline reaches viewport center
    endY   = c.top;   // progress 1: CTA button reaches viewport center

    updateScrollProgress();
  }

  // Binary search: path length at which the path crosses page-coordinate Y.
  function lengthAtY(y) {
    if (!lenSamples.length) return 0;
    if (y <= lenSamples[0].y) return 0;
    const last = lenSamples[lenSamples.length - 1];
    if (y >= last.y) return last.l;
    let lo = 0, hi = lenSamples.length - 1;
    while (lo + 1 < hi) {
      const mid = (lo + hi) >> 1;
      if (lenSamples[mid].y <= y) lo = mid; else hi = mid;
    }
    const a = lenSamples[lo], b = lenSamples[hi];
    const t = (y - a.y) / Math.max(1e-6, b.y - a.y);
    return a.l + t * (b.l - a.l);
  }

  // ---- Scroll progress (CENTER-VIEWPORT eye-level sync) ----
  function updateScrollProgress() {
    if (!pathLength) return;
    const line = document.getElementById("mythosLine");
    const halo = document.getElementById("mythosHalo");
    if (!line) return;

    // The reader's current eye-level (center of the viewport, page coords)
    const viewportCenter = window.scrollY + window.innerHeight * 0.5;

    // Pure linear progress between headline and CTA — no easing, no lag.
    const totalDistance    = Math.max(1, endY - startY);
    const scrolledDistance = viewportCenter - startY;
    let progress = scrolledDistance / totalDistance;
    progress = Math.max(0, Math.min(1, progress));

    // Eye-level mapping: the drawing tip must sit exactly at the (clamped)
    // viewport center. Convert that target Y into path length via lookup.
    const targetY = startY + progress * totalDistance;
    const drawn   = lengthAtY(targetY);
    const offset  = pathLength - drawn;

    line.style.strokeDashoffset = offset;
    if (halo) halo.style.strokeDashoffset = offset;
  }

  // ---- Throttled handlers ----
  let scrollRaf = null;
  function onScroll() {
    if (scrollRaf) return;
    scrollRaf = requestAnimationFrame(() => {
      scrollRaf = null;
      updateScrollProgress();
    });
  }
  let buildRaf = null;
  function scheduleBuild() {
    if (buildRaf) cancelAnimationFrame(buildRaf);
    buildRaf = requestAnimationFrame(buildMythosPath);
  }

  // ---- Init ----
  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", scheduleBuild);
  } else {
    scheduleBuild();
  }
  window.addEventListener("load", scheduleBuild);
  window.addEventListener("resize", scheduleBuild);
  window.addEventListener("scroll", onScroll, { passive: true });

  // Rebuild after images load (layout shifts)
  document.querySelectorAll("img").forEach((img) => {
    if (!img.complete) img.addEventListener("load", scheduleBuild, { once: true });
  });

  if ("ResizeObserver" in window) {
    new ResizeObserver(scheduleBuild).observe(document.body);
  }
})();

// ============================================================
// PIXEL TRACKING — Meta (354153630789298) + TikTok (CNQDS3JC77U0SCE9DUUG)
// Funnel di landing /torch/ :
//   PageView         -> otomatis saat load (di-init dari <head>)
//   ViewContent      -> di <head> (immediate) + saat section penawaran terlihat
//   AddToCart        -> saat klik CTA checkout mana pun (hero/final/footer/sticky)
//   InitiateCheckout -> di rimpods.com/checkout (React SPA, pixel ID sama)
//   Purchase         -> di rimpods.com/sukses + server-side via Meta CAPI
//                       (event_id deterministik utk dedup)
// ============================================================
(function () {
  "use strict";

  var PRODUCT = {
    id: "rotifer-2l-phyto",
    name: "Rimpods Rotifera 2L + Phytoplankton",
    price: 129999,
    currency: "IDR"
  };

  function fbTrack(event, params) {
    if (typeof window.fbq === "function") {
      window.fbq("track", event, params);
    }
  }
  function ttTrack(event, params) {
    if (window.ttq && typeof window.ttq.track === "function") {
      window.ttq.track(event, params);
    }
  }

  var fbParams = {
    content_ids: [PRODUCT.id],
    content_type: "product",
    content_name: PRODUCT.name,
    value: PRODUCT.price,
    currency: PRODUCT.currency,
    num_items: 1
  };
  var ttParams = {
    contents: [{ content_id: PRODUCT.id, content_type: "product", content_name: PRODUCT.name, quantity: 1, price: PRODUCT.price }],
    value: PRODUCT.price,
    currency: PRODUCT.currency
  };

  // 1) ViewContent — initial fire sudah dilakukan inline di <head> (lebih cepat,
  //    tidak nunggu DOMContentLoaded). Skip di sini agar tidak ada event duplikat.

  // 2) ViewContent kedua (sinyal kuat) — saat section penawaran masuk layar
  var offerSeen = false;
  var offer = document.getElementById("cta-final");
  if (offer && "IntersectionObserver" in window) {
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (e) {
        if (e.isIntersecting && !offerSeen) {
          offerSeen = true;
          fbTrack("ViewContent", Object.assign({}, fbParams, { content_category: "offer-section" }));
          ttTrack("ViewContent", ttParams);
          io.disconnect();
        }
      });
    }, { threshold: 0.4 });
    io.observe(offer);
  }

  // 3) AddToCart — klik CTA checkout mana pun di /torch/ landing
  //    Funnel: PageView → ViewContent → AddToCart (klik) → InitiateCheckout (di /checkout)
  //    InitiateCheckout & Purchase di-fire oleh React SPA di rimpods.com/checkout & /sukses
  //    (pixel ID sama → atribusi tetap satu induk).
  var CTA_IDS = ["hero-cta-checkout", "final-cta-checkout", "footer-cta", "sticky-mobile-cta"];
  var atcFired = false;
  function fireAddToCart() {
    if (atcFired) return;          // dedup double-click
    atcFired = true;
    fbTrack("AddToCart", fbParams);
    ttTrack("AddToCart", ttParams);
    // reset setelah 1.5s biar fire lagi kalo user balik & klik tombol lain
    setTimeout(function () { atcFired = false; }, 1500);
  }
  CTA_IDS.forEach(function (id) {
    var el = document.querySelector('[data-testid="' + id + '"]');
    if (!el) return;
    el.addEventListener("click", function (e) {
      var href = el.getAttribute("href") || "";
      // Kalau anchor internal (#cta-final dll) atau tanpa /checkout, skip ATC
      if (href.indexOf("/checkout") === -1) {
        fireAddToCart(); // tetap fire untuk nav-cta yg scroll ke offer (intent kuat)
        return;
      }
      // Modifier/middle/right click: fire & biarin browser handle (new tab dll)
      if (e.metaKey || e.ctrlKey || e.shiftKey || e.altKey || (e.button && e.button !== 0)) {
        fireAddToCart();
        return;
      }
      e.preventDefault();
      fireAddToCart();
      // Beri 200ms supaya beacon pixel ke-flush sebelum navigasi cross-origin
      setTimeout(function () { window.location.href = el.href; }, 200);
    });
  });
})();

// ============================================================
// COMET HEAD — adopsi tampilan SVG induk rimpods.com:
// dot kelap-kelip (core putih berdenyut + glow gold twinkle +
// ring ripple sonar 1.6s) menempel di ujung garis yang sedang
// tergambar. Add-on mandiri: tidak mengubah logika garis di atas.
// ============================================================
(function () {
  "use strict";
  var NS = "http://www.w3.org/2000/svg";
  var GOLD = "#FFD700";

  var style = document.createElement("style");
  style.textContent =
    ".mythos-dot-core{fill:#fff;animation:mythosCorePulse 1.6s ease-in-out infinite}" +
    ".mythos-dot-glow{fill:" + GOLD + ";filter:blur(8px);animation:mythosTwinkle 1.6s ease-in-out infinite}" +
    ".mythos-dot-ring{fill:none;stroke:" + GOLD + ";animation:mythosRipple 1.6s ease-out infinite}" +
    "@keyframes mythosTwinkle{0%,100%{opacity:.35;r:9px}50%{opacity:1;r:15px}}" +
    "@keyframes mythosCorePulse{0%,100%{r:5px}50%{r:7px}}" +
    "@keyframes mythosRipple{0%{r:8px;opacity:1;stroke-width:3}100%{r:38px;opacity:0;stroke-width:.5}}";
  document.head.appendChild(style);

  function init() {
    var svg = document.getElementById("mythos-canvas");
    var line = document.getElementById("mythosLine");
    if (!svg || !line) return;

    var g = document.createElementNS(NS, "g");
    g.style.display = "none";
    var ring = document.createElementNS(NS, "circle");
    ring.setAttribute("class", "mythos-dot-ring");
    ring.setAttribute("r", "8");
    var glow = document.createElementNS(NS, "circle");
    glow.setAttribute("class", "mythos-dot-glow");
    glow.setAttribute("r", "12");
    var core = document.createElementNS(NS, "circle");
    core.setAttribute("class", "mythos-dot-core");
    core.setAttribute("r", "5");
    g.appendChild(ring); g.appendChild(glow); g.appendChild(core);
    svg.appendChild(g);

    var prevKey = "";
    function tick() {
      var d = line.getAttribute("d") || "";
      var offset = parseFloat(line.style.strokeDashoffset || "0");
      var key = d.length + "|" + offset.toFixed(1);
      if (key !== prevKey) {
        prevKey = key;
        if (!d) {
          g.style.display = "none";
        } else {
          var total = line.getTotalLength();
          var drawn = total - offset;
          if (drawn > 1) {
            var pt = line.getPointAtLength(Math.min(drawn, total));
            g.style.display = "";
            g.setAttribute("transform", "translate(" + pt.x.toFixed(1) + "," + pt.y.toFixed(1) + ")");
          } else {
            g.style.display = "none";
          }
        }
      }
      requestAnimationFrame(tick);
    }
    requestAnimationFrame(tick);
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();
