#!/usr/bin/env python3
"""
Canyoning Sri Lanka — static site generator.

    python build/build.py

Reads build/content/*.json and writes every HTML page, sitemap.xml, robots.txt,
llms.txt and optimised WebP images into /site. /site is the folder you deploy
(Cloudflare Pages / Netlify: set the output directory to "site").
"""
import json, html, re, shutil, sys, datetime as dt
from pathlib import Path
from urllib.parse import quote

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "build" / "content"
OUT = ROOT / "site"
IMG = OUT / "assets" / "img"
RAW = ROOT / "source-images"          # original full-size PNG/JPG files live here

site = json.loads((SRC / "site.json").read_text(encoding="utf-8"))
data = json.loads((SRC / "activities.json").read_text(encoding="utf-8"))
guides_data = json.loads((SRC / "guides.json").read_text(encoding="utf-8"))
faqs = json.loads((SRC / "faqs.json").read_text(encoding="utf-8"))["faqs"]

CATS = data["categories"]
ACTS = data["activities"]
CAT = {c["slug"]: c for c in CATS}
DOMAIN = site["domain"].rstrip("/")
HOST = DOMAIN.split("//")[-1]
TODAY = dt.date.today().isoformat()
e = lambda s: html.escape(str(s), quote=True)

def act_url(a): return f"/{a['category']}/{a['slug']}/"
def cat_url(c): return f"/{c['slug']}/"
def acts_in(slug): return [a for a in ACTS if a["category"] == slug]
def short(a): return a.get("short") or a["name"]

# ----------------------------------------------------------------- images
def process_images():
    """Convert every PNG/JPG (in source-images/ or dropped into site/assets/img/) into 800/1600 WebP."""
    from PIL import Image
    RAW.mkdir(exist_ok=True)
    for f in list(IMG.glob("*.png")) + list(IMG.glob("*.jpg")) + list(IMG.glob("*.jpeg")):
        shutil.move(str(f), RAW / f.name)
    dims = {}
    (OUT / "assets" / "og").mkdir(parents=True, exist_ok=True)
    for f in sorted(RAW.iterdir()):
        if f.suffix.lower() not in (".png", ".jpg", ".jpeg"): continue
        name = f.stem
        im = Image.open(f).convert("RGB")
        for w in (800, 1600):
            out = IMG / f"{name}-{w}.webp"
            h = round(im.height * w / im.width)
            if not out.exists() or out.stat().st_mtime < f.stat().st_mtime:
                im.resize((w, h), Image.LANCZOS).save(out, "WEBP", quality=78, method=6)
        dims[name] = (im.width, im.height)
        og = OUT / "assets" / "og" / f"{name}.jpg"
        if not og.exists() or og.stat().st_mtime < f.stat().st_mtime:
            tw, th = 1200, 630
            r = max(tw / im.width, th / im.height)
            rs = im.resize((round(im.width * r), round(im.height * r)), Image.LANCZOS)
            l, t = (rs.width - tw) // 2, (rs.height - th) // 2
            rs.crop((l, t, l + tw, t + th)).save(og, "JPEG", quality=82, optimize=True, progressive=True)
    return dims

DIMS = process_images()

def img(name, alt, sizes="(max-width: 640px) 100vw, (max-width: 1040px) 50vw, 33vw", cls="", eager=False):
    if name not in DIMS:
        print(f"  ! missing image '{name}' (add source-images/{name}.png)")
        return f'<div class="img-missing {cls}" role="img" aria-label="{e(alt)}"></div>'
    w, h = DIMS[name]
    ratio = h / w
    load = 'fetchpriority="high" loading="eager"' if eager else 'loading="lazy"'
    return (f'<img src="/assets/img/{name}-800.webp" srcset="/assets/img/{name}-800.webp 800w, /assets/img/{name}-1600.webp 1600w" '
            f'sizes="{sizes}" width="800" height="{round(800 * ratio)}" alt="{e(alt)}" {load} decoding="async"' + (f' class="{cls}"' if cls else "") + ">")

# ------------------------------------------------------------------ icons
I = {
 "wa": '<svg viewBox="0 0 24 24" fill="currentColor" aria-hidden="true"><path d="M17.47 14.38c-.3-.15-1.76-.87-2.03-.97-.27-.1-.47-.15-.67.15-.2.3-.77.97-.94 1.17-.17.2-.35.22-.65.07-.3-.15-1.26-.46-2.4-1.48-.89-.79-1.49-1.77-1.66-2.07-.17-.3-.02-.46.13-.61.13-.13.3-.35.45-.52.15-.17.2-.3.3-.5.1-.2.05-.37-.02-.52-.08-.15-.67-1.62-.92-2.22-.24-.58-.49-.5-.67-.51h-.57c-.2 0-.52.07-.79.37-.27.3-1.04 1.02-1.04 2.48s1.07 2.88 1.21 3.08c.15.2 2.1 3.2 5.08 4.49.71.31 1.26.49 1.69.63.71.23 1.36.2 1.87.12.57-.09 1.76-.72 2.01-1.41.25-.7.25-1.29.17-1.41-.07-.13-.27-.2-.57-.35M12.05 21.5h-.01a9.4 9.4 0 0 1-4.8-1.31l-.34-.2-3.57.94.95-3.48-.22-.36a9.4 9.4 0 0 1-1.44-5.02c0-5.2 4.23-9.43 9.44-9.43a9.4 9.4 0 0 1 9.43 9.44c0 5.2-4.23 9.43-9.44 9.43m8.03-17.46A11.27 11.27 0 0 0 12.05.72C5.8.72.7 5.8.7 12.07c0 2 .52 3.95 1.52 5.67L.6 23.7l6.1-1.6a11.3 11.3 0 0 0 5.35 1.36h.01c6.26 0 11.35-5.1 11.35-11.36 0-3.03-1.18-5.88-3.33-8.03"/></svg>',
 "arrow": '<svg class="arrow" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M5 12h14M13 6l6 6-6 6"/></svg>',
 "clock": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true"><circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/></svg>',
 "age": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true"><circle cx="12" cy="7" r="4"/><path d="M4 21c0-4 4-6 8-6s8 2 8 6"/></svg>',
 "level": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" aria-hidden="true"><path d="M5 20v-4M12 20V10M19 20V4"/></svg>',
 "pin": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true"><path d="M12 22s7-6.1 7-12a7 7 0 1 0-14 0c0 5.9 7 12 7 12z"/><circle cx="12" cy="10" r="2.5"/></svg>',
 "check": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M4 12.5l5 5L20 6.5"/></svg>',
 "close": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" aria-hidden="true"><path d="M6 6l12 12M18 6L6 18"/></svg>',
 "prev": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" aria-hidden="true"><path d="M15 6l-6 6 6 6"/></svg>',
 "next": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" aria-hidden="true"><path d="M9 6l6 6-6 6"/></svg>',
 "logo": '<svg viewBox="0 0 48 48" fill="none" stroke="currentColor" stroke-width="2.6" stroke-linejoin="round" aria-hidden="true"><path d="M24 4.5 45 42H3z"/><path d="M24 15.5 37 38H11z"/><path d="M24 26.5 30 35H18z" fill="currentColor"/></svg>',
 "person": '<svg viewBox="0 0 120 100" fill="currentColor" aria-hidden="true"><circle cx="60" cy="34" r="22"/><path d="M14 100c0-26 20-42 46-42s46 16 46 42z"/></svg>',
}
LOGO_PATHS = '<path d="M24 4.5 45 42H3z"/><path d="M24 15.5 37 38H11z"/><path d="M24 26.5 30 35H18z" fill="currentColor"/>'

def wa_href(activity=""):
    msg = "Hi! I'd like to book" + (f": {activity}" if activity else " an adventure in Kitulgala") + f".\n\nSent from {HOST}"
    return f"https://wa.me/{site['whatsapp']}?text={quote(msg)}"

def book_btn(label="Book on WhatsApp", activity="", cls="btn btn--wa", arrow=True):
    return (f'<a class="{cls}" href="{e(wa_href(activity))}" data-book="{e(activity)}" target="_blank" rel="noopener">'
            f'{I["wa"]}<span>{e(label)}</span>{I["arrow"] if arrow else ""}</a>')

def price_html(a, small=True):
    if a.get("priceLKR"):
        usd = f' · US$ {a["priceUSD"]:,}' if a.get("priceUSD") else ""
        return f'LKR {a["priceLKR"]:,}<small> per person{usd}</small>' if small else f'LKR {a["priceLKR"]:,}{usd}'
    return 'Ask on WhatsApp<small> Price per person</small>' if small else "Ask on WhatsApp"

# ------------------------------------------------------------------ schema
BIZ_ID = f"{DOMAIN}/#business"
def business_schema():
    s = {
        "@type": ["SportsActivityLocation", "TouristAttraction"],
        "@id": BIZ_ID,
        "name": site["name"],
        "description": "Adventure company in Kitulgala, Sri Lanka, offering white water rafting, canyoning, waterfall abseiling, zip lining, jungle trekking, the Belilena cave hike and cycling.",
        "url": DOMAIN + "/",
        "logo": f"{DOMAIN}/assets/favicon.svg",
        "image": [f"{DOMAIN}/assets/og/hero-river.jpg", f"{DOMAIN}/assets/og/rafting-5km.jpg"],
        "telephone": site["whatsappDisplay"],
        "address": {"@type": "PostalAddress", "addressLocality": site["address"]["locality"], "addressRegion": site["address"]["region"], "addressCountry": site["address"]["country"]},
        "geo": {"@type": "GeoCoordinates", "latitude": site["geo"]["lat"], "longitude": site["geo"]["lng"]},
        "hasMap": f"https://www.google.com/maps?q={site['geo']['lat']},{site['geo']['lng']}",
        "openingHours": site["openingHours"],
        "areaServed": ["Kitulgala", "Sri Lanka"],
        "touristType": ["Adventure travellers", "Families", "Backpackers", "Groups"],
        "availableLanguage": ["English", "Sinhala", "Tamil"],
        "contactPoint": {"@type": "ContactPoint", "contactType": "reservations", "telephone": site["whatsappDisplay"], "url": f"https://wa.me/{site['whatsapp']}"},
        "makesOffer": [{"@type": "Offer", "itemOffered": {"@type": "TouristTrip", "name": a["name"], "url": DOMAIN + act_url(a)}} for a in ACTS],
    }
    if site.get("email"): s["email"] = site["email"]
    if site.get("social"): s["sameAs"] = site["social"]
    return s

def crumbs_schema(items):
    return {"@type": "BreadcrumbList", "itemListElement": [{"@type": "ListItem", "position": i + 1, "name": n, "item": DOMAIN + u} for i, (n, u) in enumerate(items)]}

def faq_schema(qs):
    return {"@type": "FAQPage", "mainEntity": [{"@type": "Question", "name": q["q"], "acceptedAnswer": {"@type": "Answer", "text": q["a"]}} for q in qs]}

def ld(*objs):
    return '<script type="application/ld+json">' + json.dumps({"@context": "https://schema.org", "@graph": list(objs)}, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/") + "</script>"

# ------------------------------------------------------------------ layout
NAV = [("Home", "/"), ("Activities", "/activities/"), ("Guides", "/guides/"), ("Gallery", "/gallery/"), ("About", "/about/")]

def head(title, desc, path, og_img="hero-river", schema="", preload="", extra=""):
    canonical = DOMAIN + path
    return f"""<!doctype html>
<html lang="en" class="no-js">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>{e(title)}</title>
<meta name="description" content="{e(desc)}">
<link rel="canonical" href="{canonical}">
<meta name="robots" content="index, follow, max-image-preview:large, max-snippet:-1">
<meta name="theme-color" content="#0a1113">
<meta name="geo.region" content="LK-9">
<meta name="geo.placename" content="Kitulgala">
<meta name="geo.position" content="{site['geo']['lat']};{site['geo']['lng']}">
<meta name="ICBM" content="{site['geo']['lat']}, {site['geo']['lng']}">
<meta property="og:type" content="website">
<meta property="og:site_name" content="{e(site['name'])}">
<meta property="og:title" content="{e(title)}">
<meta property="og:description" content="{e(desc)}">
<meta property="og:url" content="{canonical}">
<meta property="og:image" content="{DOMAIN}/assets/og/{og_img}.jpg">
<meta property="og:image:width" content="1200"><meta property="og:image:height" content="630">
<meta property="og:locale" content="en_GB">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="{e(title)}">
<meta name="twitter:description" content="{e(desc)}">
<meta name="twitter:image" content="{DOMAIN}/assets/og/{og_img}.jpg">
<link rel="icon" href="/assets/favicon.svg" type="image/svg+xml">
<link rel="apple-touch-icon" href="/assets/apple-touch-icon.png">
<link rel="manifest" href="/site.webmanifest">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&family=Poppins:wght@600;700;800&display=swap">
<link rel="stylesheet" href="/assets/css/main.css">
{preload}{extra}
{schema}
</head>"""

def header(active):
    links = "".join(f'<a href="{u}"' + (' aria-current="page"' if active == u else "") + f">{n}</a>" for n, u in NAV)
    mm = "".join(f'<a class="mm-link" href="{u}"><span>0{i+1}</span>{n}</a>' for i, (n, u) in enumerate(NAV))
    return f"""<body>
<a class="skip-link" href="#main">Skip to content</a>
<header class="nav">
  <div class="container nav__inner">
    <a class="brand" href="/" aria-label="{e(site['name'])} home">{I['logo']}<span>Canyoning<small>Sri Lanka</small></span></a>
    <nav class="nav__links" aria-label="Main">{links}</nav>
    <div class="nav__cta">{book_btn("Book Now", cls="btn btn--wa btn--sm btn--magnet", arrow=False)}</div>
    <button class="nav__burger" aria-label="Menu" aria-expanded="false" aria-controls="mobile-menu"><span></span></button>
  </div>
</header>
<div class="mobile-menu" id="mobile-menu" aria-hidden="true">{mm}{book_btn("Book on WhatsApp", cls="btn btn--wa btn--lg")}</div>
"""

def footer():
    act_links = "".join(f'<li><a href="{cat_url(c)}">{e(c["name"])}</a></li>' for c in CATS)
    pop = "".join(f'<li><a href="{act_url(a)}">{e(short(a))}</a></li>' for a in ACTS[:6])
    email = f'<li><a href="mailto:{e(site["email"])}">{e(site["email"])}</a></li>' if site.get("email") else ""
    opts = "".join(f'<option value="{e(a["name"])}">{e(a["name"])}</option>' for a in ACTS)
    return f"""
<footer class="footer">
  <div class="container">
    <div class="footer__grid">
      <div class="footer__about">
        <a class="brand" href="/">{I['logo']}<span>Canyoning<small>Sri Lanka</small></span></a>
        <p>White water rafting, canyoning, waterfall abseiling and jungle adventures in Kitulgala, Sri Lanka. All bookings are confirmed by our team on WhatsApp.</p>
        {book_btn("Chat on WhatsApp", cls="btn btn--wa btn--sm mt-1", arrow=False)}
      </div>
      <div><h4>Adventures</h4><ul>{act_links}</ul></div>
      <div><h4>Popular</h4><ul>{pop}</ul></div>
      <div><h4>Visit</h4><ul>
        <li><a href="/about/#location">Kitulgala, {e(site['address']['countryName'])}</a></li>
        <li><a href="https://wa.me/{site['whatsapp']}" target="_blank" rel="noopener">WhatsApp {e(site['whatsappDisplay'])}</a></li>
        {email}
        <li><a href="/about/#faq">FAQs &amp; safety</a></li>
        <li><a href="/guides/">Meet the guides</a></li>
      </ul></div>
    </div>
    <div class="footer__giant" aria-hidden="true">KITULGALA</div>
    <div class="footer__bottom"><span>© <span data-year>{dt.date.today().year}</span> {e(site['name'])}. All rights reserved.</span><span>Kitulgala · Kegalle District · Sri Lanka</span></div>
  </div>
</footer>

<a class="wa-float" href="{e(wa_href())}" data-book="" target="_blank" rel="noopener" aria-label="Book on WhatsApp">{I['wa']}<span>Book</span></a>

<div class="modal" id="book-modal" aria-hidden="true" role="dialog" aria-modal="true" aria-labelledby="bk-title">
  <div class="modal__scrim" data-close></div>
  <div class="modal__box">
    <button class="modal__close" data-close aria-label="Close">{I['close']}</button>
    <h2 id="bk-title">Book on WhatsApp</h2>
    <p class="sub">Add a few details and WhatsApp opens with your message ready to send. Takes 10 seconds. Nothing is stored on this website.</p>
    <form novalidate>
      <div class="field"><label for="bk-activity">Activity</label>
        <select id="bk-activity" name="activity"><option value="">Not sure yet, help me choose</option>{opts}</select></div>
      <div class="field-row">
        <div class="field"><label for="bk-date">Date</label><input id="bk-date" name="date" type="date"></div>
        <div class="field"><label for="bk-people">People</label>
          <div class="stepper"><button type="button" data-step="-1" aria-label="Fewer people">−</button><input id="bk-people" name="people" type="number" min="1" max="60" value="2" inputmode="numeric"><button type="button" data-step="1" aria-label="More people">+</button></div></div>
      </div>
      <div class="field"><label for="bk-name">Your name</label><input id="bk-name" name="name" type="text" autocomplete="given-name" placeholder="e.g. Kasun"></div>
      <div class="field"><label for="bk-note">Anything else? <span style="text-transform:none;letter-spacing:0;opacity:.7">(optional)</span></label><textarea id="bk-note" name="note" placeholder="Pickup from Colombo, preferred guide, kids' ages…"></textarea></div>
      <button class="btn btn--wa btn--block btn--lg" type="submit">{I['wa']}<span>Open WhatsApp</span>{I['arrow']}</button>
      <a href="#" class="skip">Skip, just open WhatsApp</a>
      <p class="fineprint">Our team confirms availability, pickup and payment with you in the chat.</p>
    </form>
  </div>
</div>

<div class="lightbox" aria-hidden="true" role="dialog" aria-label="Photo viewer">
  <img src="data:image/gif;base64,R0lGODlhAQABAAAAACw=" alt="">
  <p class="lightbox__cap"></p>
  <button class="lightbox__btn lightbox__close" aria-label="Close">{I['close']}</button>
  <button class="lightbox__btn lightbox__prev" aria-label="Previous photo">{I['prev']}</button>
  <button class="lightbox__btn lightbox__next" aria-label="Next photo">{I['next']}</button>
</div>

<script>window.CSL={json.dumps({"wa": site["whatsapp"], "domain": HOST})};</script>
<script type="module" src="/assets/js/main.js"></script>
</body>
</html>
"""

def page(path, title, desc, body, active, og_img="hero-river", schema="", preload_img=None, extra=""):
    pre = ""
    if preload_img and preload_img in DIMS:
        pre = f'<link rel="preload" as="image" href="/assets/img/{preload_img}-1600.webp" imagesrcset="/assets/img/{preload_img}-800.webp 800w, /assets/img/{preload_img}-1600.webp 1600w" imagesizes="100vw">\n'
    doc = head(title, desc, path, og_img, schema, pre, extra) + "\n" + header(active) + '<main id="main">' + body + "</main>" + footer()
    target = OUT / path.strip("/") / "index.html" if path != "/404" else OUT / "404.html"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(doc, encoding="utf-8")
    PAGES.append(path)

PAGES = []

# ---------------------------------------------------------------- partials
def meta_row(a):
    return (f'<div class="card__meta"><span>{I["clock"]}{e(a["duration"])}</span><span>{I["age"]}{e(a["minAge"])}+ yrs</span>'
            f'<span>{I["level"]}{e(a["level"])}</span></div>')

def card(a, i=0):
    adv = '<span class="chip chip--gold">Advanced</span>' if a.get("advanced") else ""
    return f"""<article class="card" data-tilt data-cat="{a['category']}" data-reveal style="--d:{(i % 3) * 0.08:.2f}s" data-cursor="View">
  <div class="card__media">{img(a['image'], a['alt'])}</div>
  <div class="card__shine"></div>
  <div class="card__top"><span class="chip chip--cyan">{I['pin'].replace('<svg', '<svg width="12" height="12"')} Kitulgala</span>{adv}</div>
  <div class="card__body">
    <h3 class="card__title"><a href="{act_url(a)}">{e(a['name'])}</a></h3>
    <p class="card__text">{e(a['card'])}</p>
    {meta_row(a)}
    <div class="card__actions"><div class="card__price">{price_html(a)}</div>{book_btn("Book", a["name"], cls="btn btn--wa btn--sm")}</div>
  </div>
</article>"""

def filters(grid_id):
    btns = f'<button class="filter" data-filter="all" aria-pressed="true">All<b>{len(ACTS)}</b></button>'
    btns += "".join(f'<button class="filter" data-filter="{c["slug"]}" aria-pressed="false">{e(c["name"])}<b>{len(acts_in(c["slug"]))}</b></button>' for c in CATS)
    return f'<div class="filters" data-filters="#{grid_id}" role="group" aria-label="Filter activities">{btns}</div>'

def faq_block(qs, heading="Questions, answered", kicker="FAQ", id_="faq"):
    items = "".join(f'<details data-reveal><summary>{e(q["q"])}<i></i></summary><div class="answer">{e(q["a"])}</div></details>' for q in qs)
    return f"""<section class="section" id="{id_}"><div class="container">
  <div class="section-head"><span class="kicker">{kicker}</span><h2 class="h-xl" data-split>{heading}</h2></div>
  <div class="faq">{items}</div>
</div></section>"""

def cta_band(img_name="rafting-10km", title="Ready to get <span class='gold'>soaked?</span>", text="Pick your adventure, choose a date and send us a message. Our team replies fast on WhatsApp."):
    return f"""<section class="section--tight"><div class="container">
  <div class="cta-band" data-reveal="scale">{img(img_name, "", sizes="100vw")}
    <span class="kicker">Book in one tap</span>
    <h2 class="h-xl" data-split>{title}</h2>
    <p>{text}</p>
    <div class="row-actions">{book_btn("Book on WhatsApp", cls="btn btn--wa btn--lg btn--magnet")}<a class="btn btn--ghost btn--lg" href="/activities/">See all activities</a></div>
  </div>
</div></section>"""

def crumbs_html(items):
    lis = "".join((f'<li><a href="{u}">{e(n)}</a></li>' if i < len(items) - 1 else f'<li aria-current="page">{e(n)}</li>') for i, (n, u) in enumerate(items))
    return f'<nav aria-label="Breadcrumb"><ol class="crumbs">{lis}</ol></nav>'

def page_hero(image, alt, word, crumbs, h1, lead, actions="", short_=False):
    return f"""<section class="page-hero{' page-hero--short' if short_ else ''}">
  <div class="page-hero__bg">{img(image, alt, sizes="100vw", eager=True)}</div>
  <div class="page-hero__word" aria-hidden="true">{e(word)}</div>
  <div class="container">
    {crumbs_html(crumbs)}
    <h1 data-split>{h1}</h1>
    <p class="lead" data-reveal style="--d:.3s">{lead}</p>
    {f'<div class="page-hero__actions" data-reveal style="--d:.45s">{actions}</div>' if actions else ''}
  </div>
</section>"""

def guide_card(g, i):
    photo = f'<img src="/assets/img/guides/{e(g["photo"])}" alt="{e(g["name"])}, {e(g["role"])}" loading="lazy">' if g.get("photo") else I["person"]
    quals = "".join(f"<li>{e(q)}</li>" for q in g["qualifications"]) + f'<li>{e(", ".join(g["languages"]))}</li>'
    leads = "".join(f'<span class="chip">{e(l)}</span>' for l in g.get("leads", []))
    return f"""<article class="guide" data-reveal style="--d:{i * 0.08:.2f}s">
  <div class="guide__photo">{photo}<span class="guide__years">{g['years']} yrs experience</span></div>
  <div class="guide__body"><h3 class="guide__name">{e(g['name'])}</h3><p class="guide__role">{e(g['role'])} · {g['years']} yrs</p>
  <ul class="ticks">{quals}</ul><div class="guide__leads">{leads}</div></div>
</article>"""

def gallery_items(cls="gallery__item", group="g"):
    items = [("hero-river", "Kelani River valley at sunrise, Kitulgala")] + [(a["image"], a["name"] + ", Kitulgala") for a in ACTS]
    seen, out = set(), []
    for name, cap in items:
        if name in seen or name not in DIMS: continue
        seen.add(name)
        out.append(f'<a class="{cls}" href="/assets/img/{name}-1600.webp" data-lightbox="{group}" data-caption="{e(cap)}" data-cursor="Open"><figure style="margin:0">{img(name, cap, sizes="(max-width: 900px) 50vw, 25vw")}<figcaption>{e(cap)}</figcaption></figure></a>')
    return "".join(out)

MAP_SVG = """<svg viewBox="0 0 400 420" role="img" aria-label="Map showing Kitulgala between Colombo, Kandy and Nuwara Eliya">
  <defs><radialGradient id="mg" cx="50%" cy="50%" r="50%"><stop offset="0" stop-color="#e8b04a" stop-opacity=".45"/><stop offset="1" stop-color="#e8b04a" stop-opacity="0"/></radialGradient></defs>
  <path d="M168 18c38 8 70 40 96 74 30 40 66 78 78 128 14 58-6 118-46 158-26 26-64 40-100 38-44-2-80-28-104-64-22-34-30-74-40-112-10-40-24-80-14-120 12-50 62-110 130-102z" fill="#173336" stroke="rgba(255,255,255,.12)" stroke-width="1.5"/>
  <path d="M20 250 C 90 240, 120 210, 168 214 S 230 196, 262 168" fill="none" stroke="#3cc0c8" stroke-opacity=".35" stroke-width="3"/>
  <g font-family="Inter, sans-serif" font-size="12" fill="#a3b5b2">
    <path class="route" d="M74 262 L 120 238 L 170 214" stroke="#e8b04a" stroke-width="2.5" fill="none"/>
    <path class="route" d="M170 214 L 230 150" stroke="#e8b04a" stroke-width="2" fill="none" opacity=".6"/>
    <path class="route" d="M170 214 L 252 236" stroke="#e8b04a" stroke-width="2" fill="none" opacity=".6"/>
    <circle cx="74" cy="262" r="5" fill="#eef4f2"/><text x="30" y="288">Colombo · 87 km</text>
    <circle cx="230" cy="150" r="5" fill="#eef4f2"/><text x="240" y="146">Kandy · 60 km</text>
    <circle cx="252" cy="236" r="5" fill="#eef4f2"/><text x="262" y="240">Nuwara Eliya</text>
    <circle cx="215" cy="238" r="3.5" fill="#a3b5b2"/><text x="196" y="262" font-size="11">Hatton</text>
  </g>
  <circle cx="170" cy="214" r="46" fill="url(#mg)"/>
  <g class="map-pin"><path d="M170 214c0 0-16-15-16-27a16 16 0 1 1 32 0c0 12-16 27-16 27z" fill="#e8b04a"/><circle cx="170" cy="187" r="6" fill="#0a1113"/></g>
  <text x="170" y="236" text-anchor="middle" font-family="Poppins, sans-serif" font-weight="700" font-size="15" fill="#eef4f2">Kitulgala</text>
  <text x="300" y="400" font-family="Inter" font-size="10" fill="#6f8582" letter-spacing="2">SRI LANKA</text>
</svg>"""

def location_block():
    dist = "".join(f'<li><b>{e(d["from"])}</b><span>{e(d["km"])} km · {e(d["time"])}</span><small>{e(d["route"])}</small></li>' for d in site["distances"])
    return f"""<section class="section" id="location"><div class="glow glow--cyan" style="right:-20vw;top:10%"></div><div class="container rel"><div class="location">
  <div>
    <span class="kicker">Location</span>
    <h2 class="h-xl" data-split>Find us in <span class="gold">Kitulgala.</span></h2>
    <p class="lead mt-2" data-reveal>Kitulgala is a rainforest village on the Kelani River, on the A7 road between Colombo and Hatton. It's an easy day trip from Colombo or a stop on the way to the hill country, Nuwara Eliya and Adam's Peak.</p>
    <ul class="distances" data-reveal>{dist}</ul>
    <div class="row-actions mt-2" data-reveal>{book_btn("Ask about pickup", "Transport / pickup", cls="btn btn--wa")}<a class="btn btn--ghost" target="_blank" rel="noopener" href="https://www.google.com/maps/search/?api=1&amp;query={site['geo']['lat']},{site['geo']['lng']}">{I['pin']}<span>Open in Google Maps</span></a></div>
  </div>
  <div class="map-card" data-reveal="scale">{MAP_SVG}</div>
</div></div></section>"""

WHY = ["Most local and tourist customers already use WhatsApp", "Every booking reaches one business number", "You know exactly which activity and date they want", "No booking software or payment fees"]

def booking_block():
    msg = "Hi! I'd like to book:\\n\\n● Activity: Marvel Canyoning (Advanced)\\n● Date: 14 Dec 2026\\n● People: 4\\n● Name: Kasun\\n\\nSent from " + HOST
    steps = [("Pick an activity", "Choose your adventure and tap <b>Book on WhatsApp</b>."),
             ("Add quick details", "Name, date and group size. It takes 10 seconds and nothing is stored on this site."),
             ("WhatsApp opens, message ready", "On phone or desktop, your booking message is already written. Just press send."),
             ("We confirm in chat", "Availability, pickup, advance payment and final confirmation, all in WhatsApp.")]
    st = "".join(f'<li class="step" data-reveal style="--d:{i*0.08:.2f}s"><span class="step__n">{i+1}</span><div><h3>{t}</h3><p>{d}</p></div></li>' for i, (t, d) in enumerate(steps))
    return f"""<section class="section bg-2" id="booking"><div class="container"><div class="booking">
  <div>
    <span class="kicker">How booking works</span>
    <h2 class="h-xl" data-split>Book in one tap. <span class="gold">Confirm in chat.</span></h2>
    <p class="lead mt-2" data-reveal>No forms, no online payments, no waiting for emails. Every booking goes straight to our team on WhatsApp.</p>
    <ol class="steps mt-3">{st}</ol>
    <div class="mt-2" data-reveal>{book_btn("Start a booking", cls="btn btn--wa btn--lg btn--magnet")}</div>
  </div>
  <div data-reveal="scale">
    <div class="phone" aria-hidden="true"><div class="phone__screen">
      <div class="phone__head"><span class="phone__avatar">CS</span><span class="phone__name">{e(site['name'])}<small>Business account</small></span></div>
      <div class="phone__chat"><span class="phone__day">Today</span><div class="bubble" data-time="09:41" data-typewriter="{e(msg)}"></div><div class="bubble bubble--in" data-time="09:42">Hi Kasun! 🙌 14 Dec is available for 4. Shall we arrange pickup?</div></div>
      <div class="phone__input">Message<i>➤</i></div>
    </div></div>
  </div>
</div></div></section>"""

# =================================================================== PAGES
def build_home():
    names = [a["name"] for a in ACTS]
    cards = "".join(card(a, i) for i, a in enumerate(ACTS))
    hero_book = book_btn("Book on WhatsApp", cls="btn btn--wa btn--lg btn--magnet")
    hero_cats = "".join(f'<li><a href="{cat_url(c)}"><span class="vhero__num">0{i+1}</span><b>{e(c["name"])}</b><small>{len(acts_in(c["slug"]))} options</small></a></li>' for i, c in enumerate(CATS))
    marquee_words = ["White Water Rafting", "Canyoning", "Waterfall Abseiling", "Zip Lining", "Jungle Trekking", "Belilena Cave", "Cycling"]
    mq = "".join(f'<span class="marquee__item">{w}</span>' for w in marquee_words) * 2
    guides = "".join(guide_card(g, i) for i, g in enumerate(guides_data["guides"][:3]))

    body = f"""
<section class="vhero" aria-label="White water rafting in Kitulgala">
  <div class="vhero__media">
    <video class="vhero__video" autoplay muted loop playsinline preload="metadata" poster="/assets/img/hero-video-poster-1600.webp" aria-hidden="true"
      data-src-sm="/assets/video/hero-720.mp4" data-src-lg="/assets/video/hero-1080.mp4"></video>
  </div>
  <div class="vhero__shade"></div>
  <div class="container vhero__inner">
    <div class="vhero__content">
      <p class="kicker" data-reveal>Kitulgala · Sri Lanka</p>
      <h1 class="hero-title"><span class="line" data-split>Adventure</span><span class="line" data-split>starts in</span><span class="line gold" data-split>Kitulgala.</span></h1>
      <p class="hero-sub" data-reveal style="--d:.45s">White water rafting, canyoning and waterfall abseiling in Sri Lanka's rainforest. Book in one tap on WhatsApp.</p>
      <div class="vhero__actions" data-reveal style="--d:.6s">{hero_book}<a class="btn btn--ghost btn--lg" href="#activities">Explore activities</a></div>
    </div>
    <ul class="vhero__cats" data-reveal style="--d:.8s">{hero_cats}</ul>
  </div>
  <button class="vhero__toggle" type="button" aria-label="Pause background video" aria-pressed="false"><span class="i-pause"></span></button>
</section>

<div class="marquee" aria-hidden="true"><div class="marquee__track">{mq}</div></div>

<section class="section" id="activities"><div class="glow glow--gold" style="left:-30vw;top:0"></div><div class="container rel">
  <div class="section-head section-head--split">
    <div><span class="kicker">Everything on offer</span><h2 class="h-xl" data-split>12 adventures. <span class="gold">One valley.</span></h2></div>
    <p class="lead" data-reveal>Every activity happens in Kitulgala, Sri Lanka's adventure capital. Each one is led by trained guides with all safety gear included. Tap <b>Book</b> and finish in WhatsApp.</p>
  </div>
  {filters("home-grid")}
  <div class="cards" id="home-grid">{cards}</div>
</div></section>

<section class="section--tight"><div class="container">
  <div class="stat-row" data-reveal>
    <div class="stat"><b data-count="12">12</b><span>adventures in one valley</span></div>
    <div class="stat"><b data-count="10" data-suffix=" km">10 km</b><span>of Kelani white water</span></div>
    <div class="stat"><b data-count="3">3</b><span>waterfalls to abseil</span></div>
    <div class="stat"><b data-count="1" data-suffix=" tap">1 tap</b><span>to book on WhatsApp</span></div>
  </div>
</div></section>

{booking_block()}

<section class="section" id="guides"><div class="container">
  <div class="section-head section-head--split">
    <div><span class="kicker">Your guides</span><h2 class="h-xl" data-split>People you can <span class="gold">trust.</span></h2></div>
    <p class="lead" data-reveal>Our guides are trained in swift-water rescue, rope access and first aid, and they know every rapid, pool and trail in Kitulgala. <a class="link-arrow" href="/guides/">Meet the team {I['arrow']}</a></p>
  </div>
  <div class="guides">{guides}</div>
</div></section>

<section class="section--tight" id="gallery">
  <div class="container"><div class="section-head section-head--split"><div><span class="kicker">Gallery</span><h2 class="h-xl" data-split>Wet, wild &amp; <span class="gold">wonderful.</span></h2></div><p class="lead" data-reveal>Drag to explore, or tap a photo to open it. <a class="link-arrow" href="/gallery/">Full gallery {I['arrow']}</a></p></div></div>
  <div class="strip" data-reveal>{gallery_items()}</div>
</section>

{location_block()}
{faq_block(faqs[:6])}
{cta_band()}
"""
    schema = ld(business_schema(),
                {"@type": "WebSite", "@id": f"{DOMAIN}/#website", "url": DOMAIN + "/", "name": site["name"], "publisher": {"@id": BIZ_ID}, "inLanguage": "en"},
                faq_schema(faqs[:6]))
    page("/", "Canyoning Sri Lanka | White Water Rafting, Canyoning & Abseiling in Kitulgala",
         "White water rafting, canyoning, waterfall abseiling, zip lining and jungle trekking in Kitulgala, Sri Lanka. Book in one tap on WhatsApp.",
         body, "/", schema=schema, extra='<link rel="preload" as="image" href="/assets/img/hero-video-poster-1600.webp" fetchpriority="high">')

def build_activities():
    tiles = ""
    for i, c in enumerate(CATS):
        kids = acts_in(c["slug"])
        chips = "".join(f'<li><span class="chip">{e(short(a))}</span></li>' for a in kids)
        tiles += f"""<a class="cat-tile" href="{cat_url(c)}" data-reveal style="--d:{(i%2)*0.1:.1f}s" data-cursor="Explore">{img(c['image'], c['name'] + ' in Kitulgala', sizes="(max-width: 800px) 100vw, 50vw")}
  <span class="count">0{len(kids)}</span><div><span class="kicker">{e(c['kicker'])}</span><h3>{e(c['name'])}</h3><ul>{chips}</ul><span class="link-arrow">Explore {I['arrow']}</span></div></a>"""
    cards = "".join(card(a, i) for i, a in enumerate(ACTS))
    body = page_hero("watagala-canyoning", "Canyoners in a rainforest gorge in Sri Lanka", "Adventure", [("Home", "/"), ("Activities", "/activities/")],
                     "Things to do in <span class='gold'>Kitulgala.</span>",
                     "White water rafting, canyoning, waterfall abseiling, zip lining, jungle trekking, a prehistoric cave hike and cycling. Twelve adventures, one valley, all bookable on WhatsApp.",
                     book_btn("Book on WhatsApp", cls="btn btn--wa btn--lg"), short_=True)
    body += f"""<section class="section"><div class="container"><div class="cat-grid">{tiles}</div></div></section>
<section class="section bg-2"><div class="container">
  <div class="section-head"><span class="kicker">All activities</span><h2 class="h-xl" data-split>Choose your <span class="gold">adventure.</span></h2></div>
  {filters("all-grid")}<div class="cards" id="all-grid">{cards}</div>
</div></section>
{cta_band("marvel-canyoning")}"""
    schema = ld(business_schema(), crumbs_schema([("Home", "/"), ("Activities", "/activities/")]),
                {"@type": "ItemList", "name": "Adventure activities in Kitulgala", "itemListElement": [{"@type": "ListItem", "position": i + 1, "url": DOMAIN + act_url(a), "name": a["name"]} for i, a in enumerate(ACTS)]})
    page("/activities/", "Things to Do in Kitulgala | All Adventure Activities | Canyoning Sri Lanka",
         "Things to do in Kitulgala, Sri Lanka: white water rafting, canyoning, waterfall abseiling, zip lining, jungle trekking, Belilena hike and cycling.",
         body, "/activities/", og_img="watagala-canyoning", schema=schema, preload_img="watagala-canyoning")

def build_category(c):
    kids = acts_in(c["slug"])
    cards = "".join(card(a, i) for i, a in enumerate(kids))
    word = c["short"]
    paras = "".join(f"<p>{e(p)}</p>" for p in c["body"])
    others = "".join(f'<a class="btn btn--ghost btn--sm" href="{cat_url(o)}">{e(o["name"])}</a>' for o in CATS if o is not c)
    body = page_hero(c["image"], c["name"] + " in Kitulgala, Sri Lanka", word, [("Home", "/"), ("Activities", "/activities/"), (c["name"], cat_url(c))],
                     e(c["h1"]), e(c["intro"]), book_btn(f"Book {c['short'].lower()}", cls="btn btn--wa btn--lg") + '<a class="btn btn--ghost btn--lg" href="#options">See options</a>')
    body += f"""<section class="section" id="options"><div class="container">
  <div class="section-head section-head--split"><div><span class="kicker">{e(c['kicker'])}</span><h2 class="h-xl" data-split>Choose your <span class="gold">{e(c['short'].lower())}</span> trip.</h2></div>
  <div class="prose" data-reveal>{paras}</div></div>
  <div class="cards">{cards}</div>
  <div class="row-actions mt-3" data-reveal><span class="kicker" style="margin:0 12px 0 0;align-self:center">Also in Kitulgala</span>{others}</div>
</div></section>
{faq_block(c['faqs'], heading=f"{e(c['name'])}: your questions")}
{cta_band(kids[-1]['image'])}"""
    schema = ld(business_schema(), crumbs_schema([("Home", "/"), ("Activities", "/activities/"), (c["name"], cat_url(c))]),
                {"@type": "CollectionPage", "name": c["h1"], "description": c["metaDescription"], "url": DOMAIN + cat_url(c),
                 "mainEntity": {"@type": "ItemList", "itemListElement": [{"@type": "ListItem", "position": i + 1, "url": DOMAIN + act_url(a), "name": a["name"]} for i, a in enumerate(kids)]}},
                faq_schema(c["faqs"]))
    page(cat_url(c), c["seoTitle"], c["metaDescription"], body, "/activities/", og_img=c["image"], schema=schema, preload_img=c["image"])

def build_activity(a):
    c = CAT[a["category"]]
    sib = [x for x in ACTS if x["category"] == a["category"] and x is not a]
    rel = (sib + [x for x in ACTS if x["category"] != a["category"]])[:3]
    about = "".join(f"<p>{e(p)}</p>" for p in a["about"])
    hl = "".join(f'<li>{I["check"]}{e(h)}</li>' for h in a["highlights"])
    tl = "".join(f'<li data-n="{i+1}"><b>{e(t)}</b><span>{e(d)}</span></li>' for i, (t, d) in enumerate(a["steps"]))
    inc = "".join(f"<li>{e(x)}</li>" for x in a["included"])
    bring = "".join(f"<li>{e(x)}</li>" for x in a["bring"])
    adv = ' <span class="chip chip--gold" style="vertical-align:middle">Advanced</span>' if a.get("advanced") else ""
    word = (a.get("short") or a["name"]).split("(")[0].replace("White Water ", "").strip()
    lead = e(a["card"]) + " All activities take place in Kitulgala, Sri Lanka."
    body = page_hero(a["image"], a["alt"], word, [("Home", "/"), (c["name"], cat_url(c)), (short(a), act_url(a))],
                     e(a["name"]) + adv, lead, book_btn("Book on WhatsApp", a["name"], cls="btn btn--wa btn--lg btn--magnet"))
    body += f"""<div class="container"><div class="facts" data-reveal>
  <div class="fact"><small>Duration</small><b>{e(a['duration'])}</b></div>
  <div class="fact"><small>Minimum age</small><b>{e(a['minAge'])}+ years</b></div>
  <div class="fact"><small>Level</small><b>{e(a['level'])}</b></div>
  <div class="fact"><small>Price</small><b>{price_html(a, small=False)}</b></div>
</div></div>
<section class="section"><div class="container"><div class="detail">
  <div class="prose">
    <span class="kicker">{e(c['name'])} · Kitulgala</span>
    <h2 data-split>About this adventure</h2>
    <div data-reveal>{about}</div>
    <ul class="highlights">{hl}</ul>
    <h3>How the day runs</h3>
    <ol class="timeline" data-reveal>{tl}</ol>
    <div class="two-col mt-2">
      <div class="panel" data-reveal><h3>What's included</h3><ul class="ticks">{inc}</ul></div>
      <div class="panel" data-reveal style="--d:.1s"><h3>What to bring</h3><ul class="ticks ticks--gold">{bring}</ul></div>
    </div>
  </div>
  <aside class="aside" aria-label="Book this activity">
    <div class="book-card" data-reveal>
      <span class="kicker">Book this trip</span>
      <div class="price">{price_html(a)}</div>
      <ul class="ticks">
        <li>{e(a['duration'])}</li><li>Minimum age {e(a['minAge'])}+</li><li>Level: {e(a['level'])}</li><li>Kitulgala, Sri Lanka</li>
      </ul>
      {book_btn("Book on WhatsApp", a["name"], cls="btn btn--wa btn--block btn--lg")}
      <p class="note">No online payment. We confirm everything with you in the chat.</p>
    </div>
  </aside>
</div></div></section>
{faq_block(c['faqs'], heading="Good to know")}
<section class="section bg-2"><div class="container">
  <div class="section-head"><span class="kicker">Keep exploring</span><h2 class="h-xl" data-split>You might <span class="gold">also love.</span></h2></div>
  <div class="cards">{''.join(card(x, i) for i, x in enumerate(rel))}</div>
</div></section>
{cta_band(a['image'], title=f"Ready for {e(short(a))}?")}
<div class="bookbar"><div><b>{e(short(a))}</b><small>{e(a['duration'])} · {e(a['minAge'])}+ yrs</small></div>{book_btn("Book", a["name"], cls="btn btn--wa btn--sm")}</div>
"""
    trip = {"@type": "TouristTrip", "@id": DOMAIN + act_url(a) + "#trip", "name": a["name"], "description": a["metaDescription"],
            "url": DOMAIN + act_url(a), "image": f"{DOMAIN}/assets/og/{a['image']}.jpg",
            "touristType": "Adventure travellers", "provider": {"@id": BIZ_ID},
            "itinerary": {"@type": "ItemList", "itemListElement": [{"@type": "ListItem", "position": i + 1, "name": t, "description": d} for i, (t, d) in enumerate(a["steps"])]},
            "location": {"@type": "Place", "name": "Kitulgala, Sri Lanka", "geo": {"@type": "GeoCoordinates", "latitude": site["geo"]["lat"], "longitude": site["geo"]["lng"]}}}
    if a.get("priceLKR"):
        trip["offers"] = {"@type": "Offer", "price": a["priceLKR"], "priceCurrency": "LKR", "availability": "https://schema.org/InStock", "url": DOMAIN + act_url(a)}
    schema = ld(trip, business_schema(), crumbs_schema([("Home", "/"), (c["name"], cat_url(c)), (short(a), act_url(a))]), faq_schema(c["faqs"]))
    page(act_url(a), a["seoTitle"], a["metaDescription"], body, "/activities/", og_img=a["image"], schema=schema, preload_img=a["image"])

def build_guides():
    gs = "".join(guide_card(g, i) for i, g in enumerate(guides_data["guides"]))
    ph = '<p class="placeholder-note">Sample layout. Names and qualifications are placeholders until the team photos arrive.</p>' if guides_data.get("placeholder") else ""
    body = page_hero("sandun-ella", "Guide abseiling beside a waterfall in Kitulgala", "Guides", [("Home", "/"), ("Guides", "/guides/")],
                     "Meet your <span class='gold'>guides.</span>",
                     "The people who'll run your rapids, check your ropes and show you the jungle: trained, experienced and local to Kitulgala.", short_=True)
    body += f"""<section class="section"><div class="container">
  <div class="guides">{gs}</div>{ph}
  <div class="center mt-3" data-reveal>{book_btn("Want to go with one of our guides? Book on WhatsApp", "Guide request", cls="btn btn--wa btn--lg")}</div>
  <p class="notice" data-reveal>Every booking for a guide goes through our <b>business WhatsApp</b>. Mention the guide's name in your message and we'll do our best to match you.</p>
</div></section>
{cta_band("rafting-5km", title="Adventure is a <span class='gold'>team sport.</span>")}"""
    schema = ld(business_schema(), crumbs_schema([("Home", "/"), ("Guides", "/guides/")]))
    page("/guides/", "Our Guides | Certified Rafting & Canyoning Guides in Kitulgala | Canyoning Sri Lanka",
         "Meet the certified guides behind Canyoning Sri Lanka: swift-water rescue, rope access and first aid trained rafting, canyoning and trekking guides in Kitulgala.",
         body, "/guides/", og_img="sandun-ella", schema=schema, preload_img="sandun-ella")

def build_gallery():
    body = page_hero("hero-river", "Kelani River valley in Kitulgala at sunrise", "Gallery", [("Home", "/"), ("Gallery", "/gallery/")],
                     "The <span class='gold'>gallery.</span>", "Rapids, waterfalls, canyons and jungle. A taste of a day in Kitulgala.", short_=True)
    body += f"""<section class="section"><div class="container"><div class="gallery">{gallery_items()}</div>
<p class="placeholder-note">Action photos and short videos from real trips will be added here.</p></div></section>{cta_band("mannakathi-ella")}"""
    schema = ld(business_schema(), crumbs_schema([("Home", "/"), ("Gallery", "/gallery/")]))
    page("/gallery/", "Photo Gallery | Rafting, Canyoning & Waterfalls in Kitulgala | Canyoning Sri Lanka",
         "Photos of white water rafting, canyoning, waterfall abseiling and jungle adventures in Kitulgala, Sri Lanka.",
         body, "/gallery/", schema=schema, preload_img="hero-river")

def build_about():
    body = page_hero("hero-river", "Kelani River valley in Kitulgala, Sri Lanka", "Kitulgala", [("Home", "/"), ("About", "/about/")],
                     "Sri Lanka's <span class='gold'>adventure valley.</span>",
                     "Kitulgala is a small rainforest village on the Kelani River, famous for white water rafting and as a filming location of the classic 1957 film <i>The Bridge on the River Kwai</i>. We're the local team who'll show you its rapids, waterfalls and jungle.",
                     book_btn("Plan your trip on WhatsApp", cls="btn btn--wa btn--lg"))
    body += f"""<section class="section"><div class="container">
  <div class="section-head section-head--split"><div><span class="kicker">Why Kitulgala</span><h2 class="h-xl" data-split>Rainforest, rapids &amp; <span class="gold">waterfalls.</span></h2></div>
  <div class="prose" data-reveal><p>Kitulgala sits in one of the wettest parts of Sri Lanka, between the hill country and the coast. That rain feeds the Kelani River, one of the island's longest rivers, and dozens of jungle streams and waterfalls. The result is the best white water rafting in Sri Lanka, natural canyons and waterfalls you can abseil, all within a short drive of each other.</p>
  <p>The surrounding Kitulgala and Makandawa forests are lowland rainforest, home to many of Sri Lanka's endemic birds. Nearby Belilena cave is one of the most important prehistoric sites in South Asia.</p></div></div>
  <div class="stat-row" data-reveal>
    <div class="stat"><b data-count="87" data-suffix=" km">87 km</b><span>from Colombo</span></div>
    <div class="stat"><b data-count="12">12</b><span>adventures</span></div>
    <div class="stat"><b data-count="3">3</b><span>waterfalls to abseil</span></div>
    <div class="stat"><b data-count="4">4</b><span>adventure categories</span></div>
  </div>
</div></section>
<section class="section bg-2" id="safety"><div class="container">
  <div class="section-head section-head--split"><div><span class="kicker">Safety</span><h2 class="h-xl" data-split>Wild, not <span class="gold">reckless.</span></h2></div>
  <p class="lead" data-reveal>Adventure should feel wild but never be reckless. This is how we keep every trip safe.</p></div>
  <div class="two-col">
    <div class="panel" data-reveal><h3>On every trip</h3><ul class="ticks"><li>Safety briefing before you start</li><li>Helmets, life jackets, harnesses and ropes as needed</li><li>Guides trained in rescue and first aid</li><li>Small groups, with the right number of guides for each one</li></ul></div>
    <div class="panel" data-reveal style="--d:.1s"><h3>Conditions first</h3><ul class="ticks ticks--gold"><li>River and weather checked every morning</li><li>Trips moved or changed if water levels aren't safe</li><li>Minimum ages and fitness levels for each activity</li><li>Honest advice on which trip suits your group</li></ul></div>
  </div>
</div></section>
{location_block()}
{faq_block(faqs)}
{cta_band("kataran-ella")}"""
    schema = ld(business_schema(), crumbs_schema([("Home", "/"), ("About", "/about/")]), faq_schema(faqs),
                {"@type": "AboutPage", "url": DOMAIN + "/about/", "name": "About Kitulgala & Canyoning Sri Lanka", "about": {"@id": BIZ_ID}})
    page("/about/", "About Kitulgala | Location, Safety & FAQs | Canyoning Sri Lanka",
         "How to get to Kitulgala from Colombo, Kandy and Nuwara Eliya, our safety standards, and answers to common questions about rafting, canyoning and abseiling in Sri Lanka.",
         body, "/about/", schema=schema, preload_img="hero-river")

def build_404():
    body = page_hero("watagala-canyoning", "Canyon in Sri Lanka", "404", [("Home", "/")], "Lost in the <span class='gold'>jungle?</span>",
                     "This page has floated downstream. Let's get you back on the trail.",
                     '<a class="btn btn--lg" href="/">Back to home</a><a class="btn btn--ghost btn--lg" href="/activities/">All activities</a>')
    page("/404", "Page not found | Canyoning Sri Lanka", "Page not found.", body, "")

# -------------------------------------------------------------- SEO files
def build_seo_files():
    urls = [p for p in PAGES if p != "/404"]
    prio = lambda p: "1.0" if p == "/" else "0.9" if p.count("/") == 2 and p not in ("/guides/", "/gallery/", "/about/") else "0.8"
    sm = '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
    sm += "".join(f"  <url><loc>{DOMAIN}{p}</loc><lastmod>{TODAY}</lastmod><priority>{prio(p)}</priority></url>\n" for p in urls)
    (OUT / "sitemap.xml").write_text(sm + "</urlset>\n", encoding="utf-8")

    (OUT / "robots.txt").write_text(f"""# Search engines and AI assistants are welcome.
User-agent: *
Allow: /

User-agent: GPTBot
Allow: /
User-agent: OAI-SearchBot
Allow: /
User-agent: ChatGPT-User
Allow: /
User-agent: ClaudeBot
Allow: /
User-agent: Claude-SearchBot
Allow: /
User-agent: PerplexityBot
Allow: /
User-agent: Google-Extended
Allow: /
User-agent: Applebot-Extended
Allow: /

Sitemap: {DOMAIN}/sitemap.xml
""", encoding="utf-8")

    # llms.txt: a plain-language summary for AI assistants (ChatGPT, Claude, Perplexity, Gemini…)
    lines = [f"# {site['name']}", "",
             f"> {site['name']} ({HOST}) is an adventure company in Kitulgala, Sri Lanka, on the Kelani River about 87 km (2.5–3 hours) from Colombo. "
             "It offers white water rafting (5 km and 10 km), canyoning (Normal, Marvel and Watagala), waterfall abseiling (Sandun Ella, Mannakathi Ella, Kataran Ella), "
             "a 200 m zip line, Makandawa jungle trekking, the Belilena cave hike and cycling. All bookings are made through the business WhatsApp "
             f"(https://wa.me/{site['whatsapp']}). There is no online payment.", "",
             "## Activities"]
    for c in CATS:
        lines.append(f"### {c['name']}")
        lines.append(f"- [{c['h1']}]({DOMAIN}{cat_url(c)}): {c['intro']}")
        for a in acts_in(c["slug"]):
            price = f"LKR {a['priceLKR']:,} per person" if a.get("priceLKR") else "price on request via WhatsApp"
            lines.append(f"- [{a['name']}]({DOMAIN}{act_url(a)}): {a['card']} Duration {a['duration']}; minimum age {a['minAge']}+; level {a['level']}; {price}.")
        lines.append("")
    lines += ["## Visiting", f"- [About Kitulgala, safety & FAQs]({DOMAIN}/about/)", f"- [Guides]({DOMAIN}/guides/)", f"- [Gallery]({DOMAIN}/gallery/)", "",
              "## Getting there"] + [f"- From {d['from']}: {d['km']} km, {d['time']} ({d['route']})" for d in site["distances"]] + ["", "## FAQ"] + [f"- **{q['q']}** {q['a']}" for q in faqs]
    (OUT / "llms.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")

    (OUT / "site.webmanifest").write_text(json.dumps({"name": site["name"], "short_name": "Canyoning SL", "start_url": "/", "display": "standalone",
        "background_color": "#0a1113", "theme_color": "#0a1113", "icons": [{"src": "/assets/favicon.svg", "sizes": "any", "type": "image/svg+xml"}, {"src": "/assets/apple-touch-icon.png", "sizes": "180x180", "type": "image/png"}]}, indent=2), encoding="utf-8")

    (OUT / "assets" / "favicon.svg").write_text(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 48 48"><rect width="48" height="48" rx="11" fill="#0a1113"/><g transform="translate(6 7) scale(.75)" fill="none" stroke="#e8b04a" stroke-width="3.2" stroke-linejoin="round">{LOGO_PATHS.replace("currentColor", "#e8b04a")}</g></svg>', encoding="utf-8")
    try:
        from PIL import Image, ImageDraw
        im = Image.new("RGB", (180, 180), "#0a1113"); d = ImageDraw.Draw(im)
        for pts, w in ((((90, 22), (164, 152), (16, 152)), 9), (((90, 62), (136, 140), (44, 140)), 9)): d.polygon(pts, outline="#e8b04a", width=w)
        d.polygon(((90, 102), (110, 132), (70, 132)), fill="#e8b04a")
        im.save(OUT / "assets" / "apple-touch-icon.png")
    except Exception as ex: print("  ! touch icon:", ex)

    # Cloudflare Pages / Netlify headers: long cache for assets, security headers everywhere
    (OUT / "_headers").write_text("""/*
  X-Content-Type-Options: nosniff
  Referrer-Policy: strict-origin-when-cross-origin
  X-Frame-Options: SAMEORIGIN
  Permissions-Policy: camera=(), microphone=(), geolocation=()

/assets/img/*
  Cache-Control: public, max-age=2592000
/assets/og/*
  Cache-Control: public, max-age=2592000
/assets/vendor/*
  Cache-Control: public, max-age=31536000, immutable
/assets/css/*
  Cache-Control: public, max-age=3600, must-revalidate
/assets/js/*
  Cache-Control: public, max-age=3600, must-revalidate
""", encoding="utf-8")

# ------------------------------------------------------------------- run
if __name__ == "__main__":
    build_home(); build_activities()
    for c in CATS: build_category(c)
    for a in ACTS: build_activity(a)
    build_guides(); build_gallery(); build_about(); build_404()
    build_seo_files()
    todo = []
    if site["whatsapp"].startswith("9477000"): todo.append("WhatsApp number is still the placeholder (build/content/site.json)")
    if guides_data.get("placeholder"): todo.append("Guides are placeholders (build/content/guides.json)")
    if not any(a.get("priceLKR") for a in ACTS): todo.append("No prices set, so cards show 'Ask on WhatsApp' (build/content/activities.json)")
    print(f"Built {len(PAGES)} pages + sitemap.xml, robots.txt, llms.txt into {OUT}")
    for t in todo: print("  TODO:", t)
