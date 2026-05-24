# DriveFlow Site Knowledge Base

Read this file before writing or editing any DriveFlow content (route pages, guides, about copy, meta tags).

---

## Tone & style

DriveFlow sounds **practical, local, and confident** — written for Irish learner drivers (roughly 17–35) preparing for the RSA driving test.

- Use **you** directly. Write like a knowledgeable friend who knows the test area, not a textbook.
- Focus on **what happens on test day**: roads, junctions, roundabouts, estates, speed-limit changes, common fail points.
- Be **specific to the test centre** — name local roads, areas, and patterns. Avoid generic advice that could apply anywhere.
- Use Irish driving terms naturally: **RSA**, **test centre**, **learner**, **roundabout**, **estate**, **national road**, **NDLS**, **EDT** (when relevant).
- Use **practice** (noun/verb) and **practicing**, never **practise** or **practising**.
- Keep **centre** and **licence** (noun) where natural for Ireland. Product/code may say "license"; match the page type.
- **No em dashes (—).** Do not use "—" or dash-as-pause between clauses. Use commas, full stops, parentheses, or separate sentences instead. Hyphens in compound words (e.g. "test-day") are fine.
- Do **not** guarantee a pass or claim examiners use one fixed route. Say examiners draw from a **local road network** with variation.
- Pass rates may be mentioned only when sourced (e.g. from RSA stats or centre-specific reports in existing copy).
- Route/product pages may mention pricing (€11.99) where `shared.js` purchase CTAs appear. Pure SEO guides should not hardcode prices unless intentional.

---

## Site URL structure

DriveFlow uses **flat HTML files** at the site root (not `/test-centres/naas`).

| Page type | URL pattern | Example |
|-----------|-------------|---------|
| Test centre routes | `/{slug}-routes.html` | `/naas-routes.html` |
| All centres picker | `/routes.html` | |
| Centres hub | `/test-centres.html` | |
| SEO guide | `/guides/{name}.html` (preferred in content plan) or `/guides/{slug}/index.html` | `/guides/raheny-fail-spots.html` |
| About | `/about.html` | |
| Home | `/index.html` or `/` | |

Canonical domain: `https://www.driveflow.ie`

---

## Content types

### 1. Route page (`type: route-page`)

**Files involved:**
- `my-frontend-new/{slug}-routes.html` — page shell
- `my-frontend-new/txt files/{content-file}.txt` — SEO guide body (markdown-like)
- `my-frontend-new/routes-config.json` — `{ "slug": { "apiSlug": "..." } }` (if licensed routes)
- `my-backend/data/{apiSlug}.json` — Google Maps route links
- `my-backend/routes/routes.js` — token/data/proxy endpoints

**Preferred pattern:** Copy `ballina-routes.html`. Body loads from `txt files/ballina.txt` via inline fetch + markdown parser. Routes load via `shared.js` using `data-route="{slug}"`.

**Txt format:**
```markdown
# {Centre} Driving Test Routes: What to Expect and Where Learners Fail

Intro paragraph(s)...

---

## About the Test Centre

...

## FAQ

**Question here?**
Answer paragraph.
```

Use `#` / `##` headings, `---` between major sections, `-` bullet lists, `**bold**` for FAQ questions.

### 2. SEO guides (`content-plan.csv` types)

Automated and manual guides live under `guides/`. The **content plan** uses these `type` values:

| type | Purpose |
|------|---------|
| `fail-spots` | Top 10 (or similar) fail locations for one test centre |
| `pass-guide` | How to pass at a specific centre; CTA to route page |
| `roundabouts` | Roundabout mistakes (often Dublin-focused) |
| `checklist` | Test-day / preparation checklist |
| `comparison` | Hardest / easiest centres (careful with pass-rate claims) |
| `city-guide` | Dublin / Cork / Galway hub linking multiple centres |
| `guide` | General educational SEO article |

Each row should include a **`published_url`** (e.g. `/guides/raheny-fail-spots.html`). The generator saves to that path exactly.

Copy HTML structure from: `guides/why-learners-fail-driving-test-ireland/index.html`

Inline CSS with DriveFlow `:root` variables. No `shared.js` route loader.

### 3. Site page (`type: site-page`)

Static pages like `about.html` — card sections (`.content-section`), light header with gold accent stripe.

---

## HTML template — route page

Use this skeleton. Replace `{PLACEHOLDERS}`.

```html
<!DOCTYPE html>
<html lang="en">
<head>
<!-- Google tag (gtag.js) -->
<script async src="https://www.googletagmanager.com/gtag/js?id=G-EJB69589QP"></script>
<script>
  window.dataLayer = window.dataLayer || [];
  function gtag(){dataLayer.push(arguments);}
  gtag('js', new Date());
  gtag('config', 'G-EJB69589QP');
</script>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=5.0, user-scalable=yes">
<meta name="description" content="{META_DESCRIPTION}">
<link rel="canonical" href="https://www.driveflow.ie/{SLUG}-routes.html">
<link rel="icon" href="https://www.driveflow.ie/favicon.ico">
<link rel="icon" type="image/png" sizes="32x32" href="https://www.driveflow.ie/favicon.png">
<link rel="icon" type="image/png" sizes="192x192" href="https://www.driveflow.ie/favicon.png">
<link rel="apple-touch-icon" href="https://www.driveflow.ie/favicon.png">
<meta property="og:title" content="{OG_TITLE}">
<meta property="og:description" content="{OG_DESCRIPTION}">
<meta property="og:url" content="https://www.driveflow.ie/{SLUG}-routes.html">
<meta property="og:type" content="website">
<meta property="og:image" content="https://www.driveflow.ie/og-{SLUG}.png">
<title>{PAGE_TITLE} | DriveFlow</title>
<link rel="stylesheet" href="/shared.css">
</head>
<body>
    <div class="container">
        <div class="page-header">
            <h1>{CENTRE_NAME} Driving Test Routes</h1>
            <p>Access detailed route information for the {CENTRE_NAME} test centre</p>
            <p style="margin-top: 16px; color: var(--accent); font-weight: 600; font-size: 16px;">Used by thousands of learners around Ireland to pass their test first try</p>
            <a href="#routes" style="display: inline-block; margin-top: 20px; padding: 12px 24px; background: var(--primary); color: var(--bg-main); border-radius: 12px; text-decoration: none; font-weight: 600; font-size: 14px;">View Routes →</a>
        </div>

        <div class="info-section" id="{SLUG}Info"></div>

        <div id="routes" class="routes-section" data-route="{ROUTE_CONFIG_KEY}" style="scroll-margin-top: 120px;"></div>
        <div id="sharedPurchase"></div>
        <div id="sharedFooter"></div>
    </div>

    <!-- Optional: HowTo schema.org JSON-LD -->

    <!-- Inline script: fetch txt files/{TXT_FILE}.txt and render (copy from ballina-routes.html) -->

    <script src="/shared.js" defer></script>
</body>
</html>
```

**Reference implementation:** `ballina-routes.html`, `carlow-routes.html`, `carnmore-routes.html`

---

## HTML template — guide article

**Reference:** `guides/why-learners-fail-driving-test-ireland/index.html`

Key elements:
- GA + Google Ads tags in `<head>`
- `<meta name="description">` and `<link rel="canonical">`
- Inline `:root` CSS (`--accent: #e6b800`, `--bg-main: #fafafa`, dot pattern background)
- `<main>` with `.article-card` wrapper
- Internal links to relevant `{centre}-routes.html` pages
- `← Back to Home` or link to `/routes.html`

### Guide SEO head (required for indexing)

The content agent **post-processes** every generated guide to add any missing tags below. When writing manually, include all of them.

```html
<meta name="robots" content="index, follow, max-image-preview:large">
<meta name="description" content="...">
<link rel="canonical" href="https://www.driveflow.ie/guides/{slug}.html">
<link rel="icon" href="https://www.driveflow.ie/favicon.ico">
<link rel="icon" type="image/png" sizes="32x32" href="https://www.driveflow.ie/favicon.png">
<link rel="icon" type="image/png" sizes="192x192" href="https://www.driveflow.ie/favicon.png">
<link rel="apple-touch-icon" href="https://www.driveflow.ie/favicon.png">
<meta property="og:title" content="...">
<meta property="og:description" content="...">
<meta property="og:url" content="https://www.driveflow.ie/guides/{slug}.html">
<meta property="og:type" content="article">
<meta property="og:image" content="https://www.driveflow.ie/favicon.png">
<meta property="og:site_name" content="DriveFlow">
<meta property="og:locale" content="en_IE">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="...">
<meta name="twitter:description" content="...">
<meta name="twitter:url" content="https://www.driveflow.ie/guides/{slug}.html">
<meta name="twitter:image" content="https://www.driveflow.ie/favicon.png">
<script type="application/ld+json">… Article schema with datePublished, author DriveFlow …</script>
```

After each guide is published, **`sitemap.xml`** must list the canonical URL (`priority` 0.8, `changefreq` monthly). The generator appends this automatically.

Also add the guide to **`guides-index.json`** (title, url, short description) so `/guides.html` lists it. `generate_article.py` does this automatically; manual publishes must update the JSON by hand.

---

## Internal link map — test centres

Display name → published URL (use these exact paths in links).

| Centre | URL |
|--------|-----|
| Athlone | /athlone-routes.html |
| Ballina | /ballina-routes.html |
| Ballincollig | /ballincollig-routes.html |
| Birr – County Arms Hotel | /birr-county-arms-hotel-routes.html |
| Buncrana | /buncrana-routes.html |
| Carlow | /carlow-routes.html |
| Carlow – Talbot Hotel | /carlow-talbot-hotel-routes.html |
| Carnmore | /carnmore-routes.html |
| Carrick-on-Shannon | /carrick-on-shannon-routes.html |
| Castlebar | /castlebar-routes.html |
| Cavan | /cavan-routes.html |
| Clifden | /clifden-routes.html |
| Clonmel | /clonmel-routes.html |
| Clybaun (Galway) | /clybaun-routes.html |
| Donegal | /donegal-routes.html |
| Dun Laoghaire | /dun-laoghaire-routes.html |
| Dundalk | /dundalk-routes.html |
| Dungarvan | /dungarvan-routes.html |
| Ennis | /ennis-routes.html |
| Finglas | /finglas-routes.html |
| Gorey | /gorey-routes.html |
| Kilkenny – Government Buildings | /kilkenny-government-buildings-routes.html |
| Kilkenny – O'Loughlin Gaels | /kilkenny-oloughlin-gaels-routes.html |
| Killarney | /killarney-routes.html |
| Killester | /killester-routes.html |
| Kilrush | /kilrush-routes.html |
| Letterkenny | /letterkenny-routes.html |
| Limerick – Castlemungret | /limerick-castlemungret-routes.html |
| Longford | /longford-routes.html |
| Loughrea | /loughrea-routes.html |
| Maldron Hotel | /maldron-hotel-routes.html |
| Mallow | /mallow-routes.html |
| Maple House | /maple-house-routes.html |
| Mitchelstown | /mitchelstown-routes.html |
| Monaghan | /monaghan-routes.html |
| Mulhuddart | /mulhuddart-routes.html |
| Mullingar | /mullingar-routes.html |
| Naas | /naas-routes.html |
| Navan | /navan-routes.html |
| Nenagh | /nenagh-routes.html |
| Newcastle West | /newcastle-west-routes.html |
| Newcastle West – Longcourt House Hotel | /newcastle-west-longcourt-house-hotel-routes.html |
| Portlaoise | /portlaoise-routes.html |
| Raheny | /raheny-routes.html |
| Roscommon | /roscommon-routes.html |
| Shannon | /shannon-routes.html |
| Skibbereen | /skibbereen-routes.html |
| Sligo | /sligo-routes.html |
| Tallaght | /tallaght-routes.html |
| Thurles | /thurles-routes.html |
| Tipperary | /tipperary-routes.html |
| Tralee | /tralee-routes.html |
| Tuam | /tuam-routes.html |
| Tullamore | /tullamore-routes.html |
| Waterford | /waterford-routes.html |
| Westside (Galway) | /westside-routes.html |
| Wexford | /wexford-routes.html |
| Wicklow | /wicklow-routes.html |
| Wilton | /wilton-routes.html |
| Woodview | /woodview-routes.html |

### Other key pages

| Page | URL |
|------|-----|
| Home | /index.html |
| All test centres (picker) | /routes.html |
| Test centres hub | /test-centres.html |
| About DriveFlow | /about.html |
| Why learners fail (guide) | /guides/why-learners-fail-driving-test-ireland/ |
| Payment | /payment.html |
| Login | /login.html |

---

## Slug & naming rules

- **HTML filename:** lowercase, hyphens, `{slug}-routes.html`
- **Payment/licence name:** must match `routes.html` `testCentres[].name` exactly (e.g. `"Carlow – Talbot Hotel"` with en-dash)
- **`data-route` / routes-config key:** usually lowercase slug (e.g. `carlow`, `dun-laoghaire`)
- **`apiSlug` in routes-config.json:** may differ from page slug (e.g. `dun-laoghaire` → `"apiSlug": "dunla"`)
- **Backend JSON:** `my-backend/data/{apiSlug}.json`

---

## End-to-end checklist — new centre with live routes

1. Write `txt files/{name}.txt` (SEO guide)
2. Create/update `{slug}-routes.html` (loads txt + `data-route`)
3. Add entry to `routes-config.json`
4. Add `my-backend/data/{apiSlug}.json` with route links
5. Wire backend in `routes.js` (`generate-{apiSlug}-token`, `{apiSlug}-data`, `{apiSlug}-route`)
6. Add to `routes.html` `testCentres` array + click handler in `selectCentre`
7. Add to `dashboard.html` `centreToPage` map
8. Add to `sitemap.xml`

---

## What NOT to do

- Do **not** invent URL paths like `/test-centres/naas` — use `/{slug}-routes.html`
- Do **not** guarantee exact examiner routes or a pass
- Do **not** recommend specific driving instructors by name (unless on a dedicated featured page)
- Do **not** use invalid HTML tags — always use standard elements (`<div>`, `<section>`, etc.)
- When linking to the RSA, use `https://www.rsa.ie`
- Do **not** copy generic driving tips without local centre detail
- Do **not** use em dashes (—) or write **practise** / **practising** (use **practice** / **practicing**)
- Do **not** add prices to guide articles unless explicitly requested
- Do **not** skip canonical URLs and meta descriptions on new pages
- Do **not** forget to deploy **backend** changes to Railway for route buttons to work in production

---

## Agent workflow

### Manual (Cursor / local)

1. Read `my-frontend-new/_agent/site-knowledge.md` (this file)
2. Read `my-frontend-new/_agent/content-plan.csv` — pick first `planned` row (generator sorts by priority: high → medium → low)
3. Write content using the correct `type` template
4. Update the CSV row: set `status = done`, fill `published_url` and `content_file`
5. If backend/routes wiring needed, follow the end-to-end checklist above

### Automated (GitHub Actions)

- Workflow: `.github/workflows/content-agent.yml`
- Script: `my-frontend-new/_agent/generate_article.py`
- Secret: `ANTHROPIC_API_KEY`
- Auto-generates all SEO types in the plan: `fail-spots`, `pass-guide`, `roundabouts`, `checklist`, `comparison`, `city-guide`, `guide`, `article`
- Saves to the path in **`published_url`** (e.g. `guides/raheny-fail-spots.html`)
- Injects full SEO head tags (robots, OG, Twitter, Article JSON-LD, Google Ads) if the model omitted any
- Appends the page to **`sitemap.xml`** and **`guides-index.json`** (committed with the guide in CI)
- Does **not** write centre `route-content` (`.txt` on `*-routes.html` pages) — not in the current plan
