/* ==========================================================================
   Canyoning Sri Lanka — site interactions
   ========================================================================== */
const CFG = window.CSL || { wa: "", domain: "canyoningsrilanka.com", activities: [] };
const $ = (s, r = document) => r.querySelector(s);
const $$ = (s, r = document) => [...r.querySelectorAll(s)];
const clamp = (v, a, b) => Math.min(Math.max(v, a), b);
const reduce = matchMedia("(prefers-reduced-motion: reduce)").matches;
const finePointer = matchMedia("(pointer: fine)").matches;
document.documentElement.classList.remove("no-js");

/* ------------------------------------------------------------ WhatsApp */
function waLink(text) { return `https://wa.me/${CFG.wa}?text=${encodeURIComponent(text)}`; }
function bookingMessage({ activity, date, people, name, note }) {
  const lines = ["Hi! I'd like to book:", ""];
  lines.push(`• Activity: ${activity || "Not sure yet, please advise"}`);
  if (date) lines.push(`• Date: ${formatDate(date)}`);
  if (people) lines.push(`• People: ${people}`);
  if (name) lines.push(`• Name: ${name}`);
  if (note) lines.push(`• Note: ${note}`);
  lines.push("", `Sent from ${CFG.domain}`);
  return lines.join("\n");
}
function formatDate(v) {
  const d = new Date(v + "T00:00:00");
  return isNaN(d) ? v : d.toLocaleDateString("en-GB", { day: "numeric", month: "short", year: "numeric" });
}

/* ------------------------------------------------------- Booking modal */
const modal = $("#book-modal");
if (modal) {
  const form = $("form", modal);
  const sel = $("#bk-activity", modal);
  const dateIn = $("#bk-date", modal);
  const ppl = $("#bk-people", modal);
  const today = new Date(); today.setMinutes(today.getMinutes() - today.getTimezoneOffset());
  dateIn.min = today.toISOString().slice(0, 10);
  let lastFocus = null;

  const open = (activity) => {
    lastFocus = document.activeElement;
    if (activity) {
      if (![...sel.options].some((o) => o.value === activity)) sel.add(new Option(activity, activity), 1);
      sel.value = activity;
    }
    modal.classList.add("is-open"); modal.setAttribute("aria-hidden", "false");
    document.body.style.overflow = "hidden";
    setTimeout(() => (activity ? dateIn : sel).focus({ preventScroll: true }), 60);
  };
  const close = () => {
    modal.classList.remove("is-open"); modal.setAttribute("aria-hidden", "true");
    document.body.style.overflow = "";
    lastFocus && lastFocus.focus({ preventScroll: true });
  };
  document.addEventListener("click", (e) => {
    const t = e.target.closest("[data-book]");
    if (!t) return;
    e.preventDefault();
    open(t.dataset.book || "");
  });
  $$("[data-close]", modal).forEach((b) => b.addEventListener("click", close));
  document.addEventListener("keydown", (e) => {
    if (!modal.classList.contains("is-open")) return;
    if (e.key === "Escape") close();
    if (e.key === "Tab") { // focus trap
      const f = $$("button, input, select, textarea, a[href]", modal).filter((el) => !el.disabled && el.offsetParent);
      const first = f[0], last = f[f.length - 1];
      if (e.shiftKey && document.activeElement === first) { e.preventDefault(); last.focus(); }
      else if (!e.shiftKey && document.activeElement === last) { e.preventDefault(); first.focus(); }
    }
  });
  $$("[data-step]", modal).forEach((b) => b.addEventListener("click", () => { ppl.value = clamp((+ppl.value || 1) + +b.dataset.step, 1, 60); }));
  const send = (data) => { window.open(waLink(bookingMessage(data)), "_blank", "noopener"); close(); };
  form.addEventListener("submit", (e) => {
    e.preventDefault();
    const fd = new FormData(form);
    send({ activity: fd.get("activity"), date: fd.get("date"), people: fd.get("people"), name: (fd.get("name") || "").trim(), note: (fd.get("note") || "").trim() });
  });
  $(".skip", modal).addEventListener("click", (e) => { e.preventDefault(); send({ activity: sel.value }); });
}

/* ---------------------------------------------------------------- Nav */
const nav = $(".nav");
let lastY = scrollY;
function onScrollNav() {
  const y = scrollY;
  nav.classList.toggle("is-solid", y > 40);
  nav.classList.toggle("is-hidden", y > lastY && y > 400 && !document.body.classList.contains("menu-open"));
  lastY = y;
}
addEventListener("scroll", onScrollNav, { passive: true }); onScrollNav();
$(".nav__burger")?.addEventListener("click", (e) => {
  const open = document.body.classList.toggle("menu-open");
  e.currentTarget.setAttribute("aria-expanded", open);
  $(".mobile-menu").setAttribute("aria-hidden", !open);
});
$$(".mobile-menu a").forEach((a) => a.addEventListener("click", () => document.body.classList.remove("menu-open")));

/* ---------------------------------------------------- Split headings */
$$("[data-split]").forEach((el) => {
  let i = 0;
  const walk = (node) => {
    [...node.childNodes].forEach((n) => {
      if (n.nodeType === 3) {
        const frag = document.createDocumentFragment();
        n.textContent.split(/(\s+)/).forEach((w) => {
          if (!w) return;
          if (/^\s+$/.test(w)) { frag.append(" "); return; }
          const o = document.createElement("span"); o.className = "split-word";
          const s = document.createElement("span"); s.style.setProperty("--i", i++); s.textContent = w;
          o.append(s); frag.append(o);
        });
        n.replaceWith(frag);
      } else if (n.nodeType === 1 && n.tagName !== "BR") walk(n);
    });
  };
  walk(el);
  if (!el.hasAttribute("data-reveal")) el.setAttribute("data-reveal", "split");
});
$$("[data-reveal='split']").forEach((el) => { el.style.opacity = 1; el.style.transform = "none"; });

/* ------------------------------------------------------- Reveal on scroll */
const io = new IntersectionObserver((entries) => entries.forEach((e) => { if (e.isIntersecting) { e.target.classList.add("is-in"); io.unobserve(e.target); } }), { rootMargin: "0px 0px -10% 0px", threshold: 0.08 });
$$("[data-reveal]").forEach((el) => io.observe(el));

/* --------------------------------------------------- Counters (stats) */
const cio = new IntersectionObserver((entries) => entries.forEach((e) => {
  if (!e.isIntersecting) return; cio.unobserve(e.target);
  const el = e.target, to = +el.dataset.count, dur = 1600, t0 = performance.now(), suf = el.dataset.suffix || "";
  const tick = (t) => { const k = clamp((t - t0) / dur, 0, 1); el.textContent = Math.round(to * (1 - Math.pow(1 - k, 4))) + suf; if (k < 1) requestAnimationFrame(tick); };
  requestAnimationFrame(tick);
}), { threshold: 0.5 });
$$("[data-count]").forEach((el) => cio.observe(el));

/* ------------------------------------------------------- Card tilt */
if (finePointer && !reduce) {
  $$("[data-tilt]").forEach((card) => {
    card.addEventListener("pointermove", (e) => {
      const r = card.getBoundingClientRect(); const x = (e.clientX - r.left) / r.width, y = (e.clientY - r.top) / r.height;
      card.style.setProperty("--ry", `${(x - 0.5) * 10}deg`); card.style.setProperty("--rx", `${(0.5 - y) * 8}deg`);
      card.style.setProperty("--mx", `${x * 100}%`); card.style.setProperty("--my", `${y * 100}%`);
    });
    card.addEventListener("pointerleave", () => { card.style.setProperty("--ry", "0deg"); card.style.setProperty("--rx", "0deg"); });
  });
  // magnetic buttons
  $$(".btn--magnet").forEach((b) => {
    b.addEventListener("pointermove", (e) => { const r = b.getBoundingClientRect(); b.style.transform = `translate(${(e.clientX - r.left - r.width / 2) * 0.25}px, ${(e.clientY - r.top - r.height / 2) * 0.35}px)`; });
    b.addEventListener("pointerleave", () => (b.style.transform = ""));
  });
}

/* ----------------------------------------------------- Custom cursor */
if (finePointer && !reduce) {
  const ring = document.createElement("div"); ring.className = "cursor"; ring.innerHTML = '<span class="cursor-label"></span>';
  const dot = document.createElement("div"); dot.className = "cursor-dot";
  document.body.append(ring, dot); document.body.classList.add("has-cursor");
  let x = innerWidth / 2, y = innerHeight / 2, rx = x, ry = y;
  addEventListener("pointermove", (e) => { x = e.clientX; y = e.clientY; dot.style.transform = `translate(${x}px, ${y}px)`; });
  const loop = () => { rx += (x - rx) * 0.18; ry += (y - ry) * 0.18; ring.style.transform = `translate(${rx}px, ${ry}px)`; requestAnimationFrame(loop); };
  loop();
  const label = $(".cursor-label", ring);
  document.addEventListener("pointerover", (e) => {
    const t = e.target.closest("a, button, [data-cursor], summary, input, select, label");
    ring.classList.toggle("is-hover", !!t);
    const l = t && t.closest("[data-cursor]")?.dataset.cursor;
    ring.classList.toggle("has-label", !!l); if (l) label.textContent = l;
  });
  document.addEventListener("pointerleave", () => { ring.style.opacity = 0; dot.style.opacity = 0; });
  document.addEventListener("pointerenter", () => { ring.style.opacity = ""; dot.style.opacity = ""; });
}

/* --------------------------------------------------- Activity filters */
$$("[data-filters]").forEach((wrap) => {
  const grid = $(wrap.dataset.filters);
  $$(".filter", wrap).forEach((b) => b.addEventListener("click", () => {
    $$(".filter", wrap).forEach((x) => x.setAttribute("aria-pressed", x === b));
    const f = b.dataset.filter;
    if (grid.scrollWidth > grid.clientWidth) grid.scrollTo({ left: 0, behavior: reduce ? "auto" : "smooth" });
    $$(".card", grid).forEach((c, i) => {
      const show = f === "all" || c.dataset.cat === f;
      c.classList.toggle("is-hidden", !show);
      if (show && !reduce) c.animate([{ opacity: 0, transform: "translateY(24px)" }, { opacity: 1, transform: "none" }], { duration: 600, delay: i * 30, easing: "cubic-bezier(.22,1,.36,1)", fill: "backwards" });
    });
  }));
});

/* ------------------------------------------------------------ Lightbox */
const lb = $(".lightbox");
if (lb) {
  const img = $("img", lb), cap = $(".lightbox__cap", lb);
  let items = [], idx = 0;
  const show = (i) => { idx = (i + items.length) % items.length; const a = items[idx]; img.src = a.getAttribute("href"); img.alt = a.dataset.caption || ""; cap.textContent = a.dataset.caption || ""; };
  document.addEventListener("click", (e) => {
    const a = e.target.closest("[data-lightbox]"); if (!a) return;
    if (a.closest(".strip.was-dragged")) { e.preventDefault(); return; }
    e.preventDefault(); items = $$(`[data-lightbox="${a.dataset.lightbox}"]`); show(items.indexOf(a));
    lb.classList.add("is-open"); lb.setAttribute("aria-hidden", "false"); $(".lightbox__close", lb).focus();
  });
  const close = () => { lb.classList.remove("is-open"); lb.setAttribute("aria-hidden", "true"); };
  $(".lightbox__close", lb).addEventListener("click", close);
  $(".lightbox__prev", lb).addEventListener("click", () => show(idx - 1));
  $(".lightbox__next", lb).addEventListener("click", () => show(idx + 1));
  lb.addEventListener("click", (e) => { if (e.target === lb) close(); });
  document.addEventListener("keydown", (e) => {
    if (!lb.classList.contains("is-open")) return;
    if (e.key === "Escape") close(); if (e.key === "ArrowLeft") show(idx - 1); if (e.key === "ArrowRight") show(idx + 1);
  });
}

/* ---------------------------------------------------- Drag-scroll strip */
$$(".strip").forEach((s) => {
  let down = false, sx = 0, sl = 0, moved = 0;
  s.addEventListener("pointerdown", (e) => { if (e.pointerType !== "mouse") return; down = true; moved = 0; sx = e.clientX; sl = s.scrollLeft; s.classList.add("is-drag"); s.classList.remove("was-dragged"); });
  addEventListener("pointermove", (e) => { if (!down) return; const dx = e.clientX - sx; moved = Math.max(moved, Math.abs(dx)); s.scrollLeft = sl - dx; });
  addEventListener("pointerup", () => { if (!down) return; down = false; s.classList.remove("is-drag"); if (moved > 6) { s.classList.add("was-dragged"); setTimeout(() => s.classList.remove("was-dragged"), 50); } });
});

/* ---------------------------------------------- WhatsApp phone typing */
const bubble = $("[data-typewriter]");
if (bubble) {
  const text = bubble.dataset.typewriter.replace(/\\n/g, "\n");
  const start = () => {
    if (reduce) { bubble.textContent = text; return; }
    let i = 0; bubble.innerHTML = '<span class="caret"></span>';
    const caret = $(".caret", bubble);
    const step = () => { if (i <= text.length) { caret.before(text.slice(i, i + 1)); i++; setTimeout(step, text[i - 1] === "\n" ? 180 : 28 + Math.random() * 40); } else caret.remove(); };
    step();
  };
  const tio = new IntersectionObserver((en) => { if (en[0].isIntersecting) { tio.disconnect(); setTimeout(start, 400); } }, { threshold: 0.5 });
  tio.observe(bubble);
}

/* ---------------------------------------------- Sticky mobile book bar */
const bookbar = $(".bookbar");
if (bookbar) {
  document.body.classList.add("has-bookbar");
  const hero = $(".page-hero");
  const bio = new IntersectionObserver((en) => { const on = !en[0].isIntersecting; bookbar.classList.toggle("is-visible", on); document.body.classList.toggle("bookbar-on", on); }, { threshold: 0 });
  bio.observe(hero);
}

/* ------------------------------------------------- Hero parallax (inner) */
const heroBg = $(".page-hero__bg"), heroWord = $(".page-hero__word");
if (heroBg && !reduce) {
  addEventListener("scroll", () => {
    const y = scrollY; if (y > innerHeight) return;
    heroBg.style.transform = `translate3d(0, ${y * 0.3}px, 0)`;
    if (heroWord) heroWord.style.transform = `translate(-50%, calc(-50% + ${y * 0.15}px))`;
  }, { passive: true });
}

/* ============================================================ VIDEO HERO */
const vhero = $(".vhero");
if (vhero) {
  const v = $(".vhero__video", vhero), btn = $(".vhero__toggle", vhero), icon = $("span", btn);
  const conn = navigator.connection || {};
  const small = innerWidth < 900 || conn.saveData || /(^|-)2g$/.test(conn.effectiveType || "");
  let userPaused = false;
  const setIcon = (playing) => { icon.className = playing ? "i-pause" : "i-play"; btn.setAttribute("aria-label", playing ? "Pause background video" : "Play background video"); btn.setAttribute("aria-pressed", String(!playing)); };
  if (reduce) { v.removeAttribute("autoplay"); userPaused = true; setIcon(false); }
  v.src = small ? v.dataset.srcSm : v.dataset.srcLg;
  if (!reduce) v.play().catch(() => setIcon(false));
  v.addEventListener("play", () => setIcon(true)); v.addEventListener("pause", () => setIcon(false));
  btn.addEventListener("click", () => { if (v.paused) { userPaused = false; v.play(); } else { userPaused = true; v.pause(); } });
  // save battery: pause when the hero is off-screen or the tab is hidden
  new IntersectionObserver((en) => { if (userPaused) return; en[0].isIntersecting ? v.play().catch(() => {}) : v.pause(); }, { threshold: 0.05 }).observe(vhero);
  document.addEventListener("visibilitychange", () => { if (userPaused) return; document.hidden ? v.pause() : v.play().catch(() => {}); });
  // gentle parallax + fade of the content as you scroll away
  const content = $(".vhero__inner", vhero);
  if (!reduce) addEventListener("scroll", () => {
    const y = scrollY, h = vhero.offsetHeight; if (y > h) return;
    v.style.transform = `scale(1.08) translate3d(0, ${y * 0.18}px, 0)`;
    content.style.opacity = String(Math.max(0, 1 - y / (h * 0.75)));
    content.style.transform = `translate3d(0, ${y * -0.12}px, 0)`;
  }, { passive: true });
}

/* ------------------------------------------------------------- Year */
$$("[data-year]").forEach((el) => (el.textContent = new Date().getFullYear()));
