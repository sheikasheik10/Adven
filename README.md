# canyoningsrilanka.com

A static website for an adventure company in Kitulgala. The home page opens with a full-screen video hero. Bookings go through WhatsApp, and every activity has its own search-optimised page.

## Folders

| Path | What it is |
|---|---|
| `site/` | **The website.** Deploy this folder. |
| `build/content/*.json` | All text, activities, prices, guides and FAQs. Edit these files. |
| `build/build.py` | Regenerates every page in `site/` from the content files. |
| `source-images/` | Full-size original photos. The build makes WebP versions from them. |
| `source-video/` | Original full-quality hero video files (not uploaded). |
| `Ref/` | Design references. |

## Edit → build → preview

```bash
python build/build.py                  # needs Python 3 + Pillow (pip install pillow)
cd site && python -m http.server 8765  # open http://localhost:8765
```

To replace a photo, drop `name.png` or `name.jpg` into `source-images/` (or `site/assets/img/`) using the same name as in `activities.json`, then rebuild.

## Hero video

The current clip is a free Pexels stock video ("Exciting River Rafting Adventure in Rapids" by Dilson Rodríguez, Pexels licence: free for commercial use, credit optional). The original is in `source-video/`. **Replace it with the client's own Kitulgala footage before launch.** Don't use clips downloaded from YouTube unless the client owns them or has written permission.

To swap it, export the client's clip (ideally 10–20 s, landscape, no talking) and compress it into two files with the same names:

```bash
ffmpeg -i client.mp4 -an -vf "scale=1920:-2,hqdn3d=3:2:5:4,fps=30" -c:v libx264 -preset veryslow -b:v 4600k -maxrate 7000k -bufsize 7000k -pix_fmt yuv420p -movflags +faststart site/assets/video/hero-1080.mp4
ffmpeg -i client.mp4 -an -vf "scale=1280:-2,hqdn3d=3:2:5:4,fps=30" -c:v libx264 -preset veryslow -b:v 2100k -maxrate 3200k -bufsize 3200k -pix_fmt yuv420p -movflags +faststart site/assets/video/hero-720.mp4
ffmpeg -ss 0.5 -i client.mp4 -frames:v 1 -vf scale=1920:-2 source-images/hero-video-poster.png
python build/build.py
```

Phones get the 720p file and desktops the 1080p file. The video pauses when scrolled out of view, and visitors with "reduce motion" turned on see the poster image instead.

## Before launch (client must confirm)

1. **WhatsApp number**: `whatsapp` and `whatsappDisplay` in `build/content/site.json`.
2. **Prices**: `priceLKR` / `priceUSD` in `activities.json`. While a price is `null`, the site shows "Ask on WhatsApp".
3. **Duration, minimum age and level** for every activity. The current values are reasonable estimates.
4. **Guides**: real names, roles, qualifications and photos in `guides.json`. Put photos in `site/assets/img/guides/` and set `"placeholder": false`.
5. **Real photos**: the current images are AI-generated placeholders. Replace them with the client's own action photos, which are better for trust and for Google Images.
6. **Opening hours, social links, FAQ answers**.

## Deploy (Option A: free)

Cloudflare Pages or Netlify: connect the folder or repo, set the build output directory to `site`, and add the custom domain `canyoningsrilanka.com`. The `_headers` file sets caching and security headers automatically.

## SEO already built in

- One page per activity and per category, each with its own keyword-focused title, description, H1 and copy. Example targets: "white water rafting Kitulgala", "canyoning Sri Lanka", "Sandun Ella abseiling", "things to do in Kitulgala".
- Schema.org structured data on every page: `SportsActivityLocation` / `TouristAttraction` with geo coordinates, `TouristTrip` per activity (adds `Offer` once prices are set), `BreadcrumbList`, `FAQPage` and `ItemList`.
- `sitemap.xml`, plus a `robots.txt` that explicitly welcomes Google and AI crawlers (GPTBot, ClaudeBot, PerplexityBot, Google-Extended).
- `llms.txt`: a plain-language summary that AI assistants read when answering "best rafting in Sri Lanka"-type questions.
- Open Graph images for WhatsApp and Facebook previews, geo meta tags, and fast WebP images with lazy loading.

## SEO the site can't do by itself (do these after launch)

Ranking #1 depends on things outside the code:

1. **Google Business Profile** for the Kitulgala location, using the same name, WhatsApp number and website. This matters most for map results.
2. **Google Search Console**: verify the domain and submit `https://canyoningsrilanka.com/sitemap.xml`. Do the same in Bing Webmaster Tools, which also feeds ChatGPT search.
3. **Reviews**: ask every happy group for a Google review, plus TripAdvisor. Reviews are the strongest local ranking signal.
4. **Listings and links**: TripAdvisor, GetYourGuide or Viator, Sri Lanka travel blogs, and hotels in Kitulgala, all linking to the site.
5. **Fresh content**: add new gallery photos and short videos regularly.
