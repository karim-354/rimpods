/* ============================================================
   MYTHOS THROUGHLINE — PORTABLE EMBED v2 (branching fork)
   Scroll-triggered, self-drawing neon line dengan:
   - Wrapper cage pattern (1 viewBox unit = 1 CSS px, scroll natural)
   - Eye-level sync: ujung garis SELALU di tengah layar (arc-length lookup)
   - Warna gradient dinamis per section
   - BARU v2: `branches` — garis bercabang di akhir menuju 2+ target
     (mis. dua tombol CTA), masing-masing dengan panah sendiri
   - Aman untuk React SPA (rebuild otomatis saat DOM berubah / ganti route;
     non-aktif sendiri di route yang tidak punya elemen start/end)

   KONFIGURASI via window.MYTHOS_CONFIG sebelum memuat script ini:
     startSelector : elemen awal garis (garis mulai di bawahnya)
     branches      : [{ selector: "..." }, ...] — target akhir (2+ = fork)
     endSelector   : dipakai bila `branches` kosong (mode 1 ujung)
     anchors       : [{ selector, side: "left"|"right"|"center", offset }]
     sectionColors : [[selectorSection, warna], ...]
   ============================================================ */
(function () {
  "use strict";

  var CFG = Object.assign({
    startSelector: "h1",
    endSelector: 'a[href*="checkout"]',
    branches: [],
    anchors: [],
    sectionColors: [],
    strokeWidth: 4,
    haloWidth: 12,
    haloOpacity: 0.42,
    zIndex: 50,
    viewportAnchor: 0.5,
    startGap: 24,
    endGap: 18,
    forkGap: 110,
    arrowColor: "#FFD700",
    defaultStops: [["0%", "#00E5FF"], ["50%", "#8A2BE2"], ["100%", "#FFD700"]]
  }, window.MYTHOS_CONFIG || {});

  var NS = "http://www.w3.org/2000/svg";
  var pathLength = 0, startY = 0, endY = 0, forkY = 0, branchEndY = 0, lenSamples = [];
  var branchEls = []; // { line, halo, len, dot }
  var mainDot = null; // comet head kelap-kelip di ujung garis
  var touchEls = []; // { el, y } -> tombol yang berdenyut saat disentuh comet head

  function makeDot(svg) {
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
    return g;
  }

  function placeDot(g, pt) {
    g.style.display = "";
    g.setAttribute("transform", "translate(" + pt.x.toFixed(1) + "," + pt.y.toFixed(1) + ")");
  }

  // ---------- 1. Inject styles + cage + SVG (sekali) ----------
  function ensureDom() {
    if (document.getElementById("mythos-cage")) return;

    var style = document.createElement("style");
    style.id = "mythos-style";
    style.textContent =
      "#mythos-cage{position:absolute;top:0;left:0;right:0;height:0;overflow:visible;pointer-events:none;z-index:" + CFG.zIndex + "}" +
      "#mythos-canvas{position:absolute;top:0;left:0;display:block;overflow:visible;pointer-events:none}" +
      ".mythos-line{fill:none;stroke:url(#mythosNeonGradient);stroke-width:" + CFG.strokeWidth + ";stroke-linecap:round;stroke-linejoin:round}" +
      ".mythos-halo{fill:none;stroke:url(#mythosNeonGradient);stroke-width:" + CFG.haloWidth + ";stroke-linecap:round;stroke-linejoin:round;opacity:" + CFG.haloOpacity + ";filter:blur(7px)}" +
      ".mythos-dot-core{fill:#fff;animation:mythosCorePulse 1.6s ease-in-out infinite}" +
      ".mythos-dot-glow{fill:" + CFG.arrowColor + ";filter:blur(8px);animation:mythosTwinkle 1.6s ease-in-out infinite}" +
      ".mythos-dot-ring{fill:none;stroke:" + CFG.arrowColor + ";animation:mythosRipple 1.6s ease-out infinite}" +
      "@keyframes mythosTwinkle{0%,100%{opacity:.35;r:9px}50%{opacity:1;r:15px}}" +
      "@keyframes mythosCorePulse{0%,100%{r:5px}50%{r:7px}}" +
      "@keyframes mythosRipple{0%{r:8px;opacity:1;stroke-width:3}100%{r:38px;opacity:0;stroke-width:.5}}" +
      ".mythos-touch{display:inline-block;animation:mythosBtnPulse 1.2s ease-in-out infinite}" +
      "@keyframes mythosBtnPulse{0%,100%{transform:scale(1);box-shadow:0 0 0 0 rgba(245,197,66,0)}50%{transform:scale(1.045);box-shadow:0 0 18px 4px rgba(245,197,66,.45)}}";
    document.head.appendChild(style);

    var cage = document.createElement("div");
    cage.id = "mythos-cage";
    cage.setAttribute("aria-hidden", "true");

    var svg = document.createElementNS(NS, "svg");
    svg.id = "mythos-canvas";
    svg.setAttribute("preserveAspectRatio", "none");

    var defs = document.createElementNS(NS, "defs");
    var grad = document.createElementNS(NS, "linearGradient");
    grad.id = "mythosNeonGradient";
    grad.setAttribute("gradientUnits", "userSpaceOnUse");
    grad.setAttribute("x1", "0"); grad.setAttribute("y1", "0");
    grad.setAttribute("x2", "0"); grad.setAttribute("y2", "8000");
    defs.appendChild(grad);

    var marker = document.createElementNS(NS, "marker");
    marker.id = "mythosArrow";
    marker.setAttribute("viewBox", "0 0 12 12");
    marker.setAttribute("refX", "6"); marker.setAttribute("refY", "6");
    marker.setAttribute("markerWidth", "7"); marker.setAttribute("markerHeight", "7");
    marker.setAttribute("orient", "auto-start-reverse");
    var arrow = document.createElementNS(NS, "path");
    arrow.setAttribute("d", "M 0 0 L 12 6 L 0 12 L 3 6 Z");
    arrow.setAttribute("fill", CFG.arrowColor);
    marker.appendChild(arrow);
    defs.appendChild(marker);
    svg.appendChild(defs);

    var halo = document.createElementNS(NS, "path");
    halo.id = "mythosHalo";
    halo.setAttribute("class", "mythos-halo");
    svg.appendChild(halo);

    var line = document.createElementNS(NS, "path");
    line.id = "mythosLine";
    line.setAttribute("class", "mythos-line");
    svg.appendChild(line);

    cage.appendChild(svg);
    document.body.insertBefore(cage, document.body.firstChild);
    mainDot = makeDot(svg);

    var cs = getComputedStyle(document.body);
    if (cs.position === "static") document.body.style.position = "relative";
  }

  // ---------- 2. Build path ----------
  function abs(el) {
    var r = el.getBoundingClientRect();
    return {
      top: r.top + window.scrollY, bottom: r.bottom + window.scrollY,
      left: r.left + window.scrollX, right: r.right + window.scrollX,
      cx: r.left + r.width / 2 + window.scrollX,
      cy: r.top + r.height / 2 + window.scrollY
    };
  }

  function cubic(p0, p1) {
    var rnd = function (n) { return n.toFixed(1); };
    var dy = p1.y - p0.y, k = 0.55;
    return " C " + rnd(p0.x) + " " + rnd(p0.y + dy * k) + ", " +
      rnd(p1.x) + " " + rnd(p1.y - dy * k) + ", " + rnd(p1.x) + " " + rnd(p1.y);
  }

  // Segmen pertama saat startSide 'right': keluar horizontal ke kanan,
  // lalu melengkung turun masuk ke anchor berikutnya
  function cubicH(p0, p1) {
    var rnd = function (n) { return n.toFixed(1); };
    var dx = p1.x - p0.x, dy = p1.y - p0.y;
    return " C " + rnd(p0.x + dx * 0.6) + " " + rnd(p0.y) + ", " +
      rnd(p1.x) + " " + rnd(p1.y - dy * 0.55) + ", " + rnd(p1.x) + " " + rnd(p1.y);
  }

  function buildPath() {
    var start = document.querySelector(CFG.startSelector);
    var svg = document.getElementById("mythos-canvas");
    var line = document.getElementById("mythosLine");
    var halo = document.getElementById("mythosHalo");

    // Resolve target akhir: branches (fork) atau endSelector tunggal
    var targets = [];
    if (CFG.branches.length) {
      CFG.branches.forEach(function (b) {
        var el = document.querySelector(b.selector);
        if (el) targets.push(abs(el));
      });
    }
    var singleMode = targets.length < 2;
    if (singleMode) {
      var endEl = document.querySelector(CFG.endSelector);
      targets = endEl ? [abs(endEl)] : [];
    }

    if (!start || !targets.length || !svg || !line) {
      pathLength = 0;
      if (line) line.setAttribute("d", "");
      if (halo) halo.setAttribute("d", "");
      branchEls.forEach(function (b) { b.line.setAttribute("d", ""); b.halo.setAttribute("d", ""); });
      return; // route ini tidak punya start/end -> garis non-aktif
    }

    var W = document.documentElement.clientWidth;
    var H = document.documentElement.scrollHeight;
    svg.setAttribute("viewBox", "0 0 " + W + " " + H);
    svg.setAttribute("width", W); svg.setAttribute("height", H);
    svg.style.width = W + "px"; svg.style.height = H + "px";

    // Gradient stops per section (atau default)
    var grad = document.getElementById("mythosNeonGradient");
    grad.setAttribute("y2", H);
    var stops = "";
    if (CFG.sectionColors.length) {
      CFG.sectionColors.forEach(function (pair) {
        var sec = document.querySelector(pair[0]);
        if (!sec) return;
        var off = Math.max(0, Math.min(1, abs(sec).cy / H));
        stops += '<stop offset="' + (off * 100).toFixed(2) + '%" stop-color="' + pair[1] + '"/>';
      });
    }
    if (!stops) {
      CFG.defaultStops.forEach(function (pair) {
        stops += '<stop offset="' + pair[0] + '" stop-color="' + pair[1] + '"/>';
      });
    }
    grad.innerHTML = stops;

    // Titik akhir garis utama: fork point (di atas semua target) atau target tunggal
    var minTop = Infinity, sumCx = 0;
    targets.forEach(function (t) { minTop = Math.min(minTop, t.top); sumCx += t.cx; });
    var forkPt;
    if (singleMode) {
      forkPt = { x: targets[0].cx, y: targets[0].top - CFG.endGap };
    } else {
      forkPt = { x: sumCx / targets.length, y: minTop - CFG.forkGap };
    }

    // Anchor points garis utama
    var s = abs(start);
    var pts = [
      CFG.startSide === "right"
        ? { x: s.right + CFG.startGap, y: s.cy }
        : CFG.startSide === "bottom-left"
          ? { x: s.left + 6, y: s.bottom + 12 }
          : { x: s.cx, y: s.bottom + CFG.startGap }
    ];
    touchEls.forEach(function (t) { t.el.classList.remove("mythos-touch"); });
    touchEls = [];
    CFG.anchors.forEach(function (a) {
      var el = document.querySelector(a.selector);
      if (!el) return;
      var r = abs(el), x;
      if (a.side === "right") x = r.right - (a.offset || 18);
      else if (a.side === "left") x = r.left + (a.offset || 18);
      else x = r.cx + (a.offset || 0);
      var y = r.cy + (a.yOffset || 0);
      pts.push({ x: x, y: y });
      if (a.touch) touchEls.push({ el: el, y: y });
    });
    // Target cabang (tombol CTA) juga ikut berdenyut saat dot mendarat
    if (!singleMode) {
      CFG.branches.forEach(function (b) {
        var el = document.querySelector(b.selector);
        if (el) touchEls.push({ el: el, y: abs(el).top - CFG.endGap });
      });
    }
    pts.push(forkPt);

    var d = "M " + pts[0].x.toFixed(1) + " " + pts[0].y.toFixed(1);
    for (var i = 1; i < pts.length; i++) {
      d += (i === 1 && (CFG.startSide === "right" || CFG.startSide === "bottom-left")) ? cubicH(pts[0], pts[1]) : cubic(pts[i - 1], pts[i]);
    }
    line.setAttribute("d", d);
    halo.setAttribute("d", d);
    line.setAttribute("marker-end", singleMode ? "url(#mythosArrow)" : "");

    pathLength = line.getTotalLength();
    line.style.strokeDasharray = pathLength;
    line.style.strokeDashoffset = pathLength;
    halo.style.strokeDasharray = pathLength;
    halo.style.strokeDashoffset = pathLength;

    // Cabang fork -> tiap target (masing-masing dengan panah)
    var nBranches = singleMode ? 0 : targets.length;
    while (branchEls.length < nBranches) {
      var bh = document.createElementNS(NS, "path");
      bh.setAttribute("class", "mythos-halo");
      var bl = document.createElementNS(NS, "path");
      bl.setAttribute("class", "mythos-line");
      bl.setAttribute("marker-end", "url(#mythosArrow)");
      svg.appendChild(bh); svg.appendChild(bl);
      branchEls.push({ line: bl, halo: bh, len: 0, dot: makeDot(svg) });
    }
    branchEls.forEach(function (b, idx) {
      if (idx >= nBranches) {
        b.line.setAttribute("d", ""); b.halo.setAttribute("d", ""); b.len = 0;
        b.dot.style.display = "none";
        return;
      }
      var t = targets[idx];
      var bd = "M " + forkPt.x.toFixed(1) + " " + forkPt.y.toFixed(1) +
        cubic(forkPt, { x: t.cx, y: t.top - CFG.endGap });
      b.line.setAttribute("d", bd);
      b.halo.setAttribute("d", bd);
      b.len = b.line.getTotalLength();
      b.line.style.strokeDasharray = b.len;
      b.line.style.strokeDashoffset = b.len;
      b.halo.style.strokeDasharray = b.len;
      b.halo.style.strokeDashoffset = b.len;
    });

    // Arc-length -> Y lookup (eye-level presisi di path berkelok)
    var SAMPLES = Math.max(200, Math.round(pathLength / 24));
    lenSamples = new Array(SAMPLES + 1);
    var runMaxY = -Infinity;
    for (var j = 0; j <= SAMPLES; j++) {
      var l = (pathLength * j) / SAMPLES;
      // running-max: jaga monotonic Y walau path sedikit naik (dip/wave kecil)
      runMaxY = Math.max(runMaxY, line.getPointAtLength(l).y);
      lenSamples[j] = { l: l, y: runMaxY };
    }

    startY = s.top;
    forkY = forkPt.y;
    branchEndY = 0;
    targets.forEach(function (t) { branchEndY = Math.max(branchEndY, t.top - CFG.endGap); });
    endY = branchEndY;
    update();
  }

  function lengthAtY(y) {
    if (!lenSamples.length) return 0;
    if (y <= lenSamples[0].y) return 0;
    var last = lenSamples[lenSamples.length - 1];
    if (y >= last.y) return last.l;
    var lo = 0, hi = lenSamples.length - 1;
    while (lo + 1 < hi) {
      var mid = (lo + hi) >> 1;
      if (lenSamples[mid].y <= y) lo = mid; else hi = mid;
    }
    var a = lenSamples[lo], b = lenSamples[hi];
    var t = (y - a.y) / Math.max(1e-6, b.y - a.y);
    t = Math.max(0, Math.min(1, t)); // guard utk segmen horizontal (dy ~ 0)
    return a.l + t * (b.l - a.l);
  }

  // ---------- 3. Center-viewport eye-level sync ----------
  function update() {
    if (!pathLength) return;
    var line = document.getElementById("mythosLine");
    var halo = document.getElementById("mythosHalo");
    if (!line) return;

    var viewportCenter = window.scrollY + window.innerHeight * CFG.viewportAnchor;
    // Pastikan garis bisa selesai 100% walau endY tidak terjangkau center viewport
    var maxCenter = document.documentElement.scrollHeight - window.innerHeight * (1 - CFG.viewportAnchor);
    var effectiveEnd = Math.min(endY, maxCenter - 4);
    var total = Math.max(1, effectiveEnd - startY);
    var progress = Math.max(0, Math.min(1, (viewportCenter - startY) / total));
    var targetY = startY + progress * (endY - startY);

    // Garis utama berhenti di fork. Epsilon 2px utk segmen horizontal datar
    // (pembulatan path d vs forkY float bisa bikin lengthAtY berhenti dini).
    var offset = (targetY >= forkY - 2)
      ? 0
      : pathLength - lengthAtY(Math.min(targetY, forkY));
    line.style.strokeDashoffset = offset;
    if (halo) halo.style.strokeDashoffset = offset;

    // Cabang: mulai tergambar setelah garis utama mencapai fork point
    var bp = Math.max(0, Math.min(1, (targetY - forkY) / Math.max(1, branchEndY - forkY)));
    branchEls.forEach(function (b) {
      if (!b.len) return;
      var bo = b.len * (1 - bp);
      b.line.style.strokeDashoffset = bo;
      b.halo.style.strokeDashoffset = bo;
    });

    // Comet head: dot kelap-kelip menempel di ujung garis yang sedang tergambar
    var drawnLen = pathLength - offset;
    var branchesActive = branchEls.some(function (b) { return b.len > 0; });
    if (branchesActive && bp > 0) {
      // garis sudah pecah: dot ikut pecah mengikuti ujung tiap cabang
      if (mainDot) mainDot.style.display = "none";
      branchEls.forEach(function (b) {
        if (!b.len) return;
        placeDot(b.dot, b.line.getPointAtLength(b.len * bp));
      });
    } else {
      branchEls.forEach(function (b) { if (b.dot) b.dot.style.display = "none"; });
      if (mainDot) {
        if (drawnLen > 1) placeDot(mainDot, line.getPointAtLength(drawnLen));
        else mainDot.style.display = "none";
      }
    }

    // Tombol berdenyut halus saat comet head melintas di dekatnya
    touchEls.forEach(function (t) {
      t.el.classList.toggle("mythos-touch", Math.abs(targetY - t.y) < 70);
    });
  }

  // ---------- 4. Scheduling (rAF) + SPA awareness ----------
  var scrollRaf = null;
  function onScroll() {
    if (scrollRaf) return;
    scrollRaf = requestAnimationFrame(function () { scrollRaf = null; update(); });
  }
  var buildTimer = null;
  function scheduleBuild() {
    clearTimeout(buildTimer);
    buildTimer = setTimeout(function () { ensureDom(); buildPath(); }, 120);
  }

  function init() {
    ensureDom();
    buildPath();
    window.addEventListener("scroll", onScroll, { passive: true });
    window.addEventListener("resize", scheduleBuild);
    window.addEventListener("load", scheduleBuild);

    // React SPA: rebuild saat DOM berubah (render/route) — abaikan mutasi dari cage sendiri
    if ("MutationObserver" in window) {
      var cage = document.getElementById("mythos-cage");
      new MutationObserver(function (muts) {
        for (var i = 0; i < muts.length; i++) {
          if (!cage.contains(muts[i].target)) { scheduleBuild(); return; }
        }
      }).observe(document.body, { childList: true, subtree: true });
    }
    if ("ResizeObserver" in window) {
      new ResizeObserver(scheduleBuild).observe(document.body);
    }
    document.querySelectorAll("img").forEach(function (img) {
      if (!img.complete) img.addEventListener("load", scheduleBuild, { once: true });
    });
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();
