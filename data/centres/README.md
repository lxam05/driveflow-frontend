# Centre page data

JSON configs and CSO stats for RSA test-centre route pages.

## Canonical page structure

Every `{slug}-routes.html` should follow this order:

1. Breadcrumb → `/routes.html`
2. Header — H1, short intro, **Updated July 2026**, hero if available
3. **Snapshot** (`.centre-snapshot`, free) — pass rate, wait weeks, test length, manoeuvres, corridors; cite CSO
4. **Routes preview** (only when you have a real corridor bullet list) — `#routes-preview` + `data-routes-insert-after` + `<noscript>`. If there is no real list, skip this block and put `data-routes-insert-after` on `.centre-snapshot` instead so the unlock still sits under free stats.
5. `#routes` — paywall / unlocked Google Maps routes only (`shared.js`)
6. Where is the centre / map teaser (pin/directions only)
7. Examiner roads / hotspots (`#hotspots`)
8. Manoeuvre locations (`#manoeuvres`) — free HTML
9. Pass rate & waiting detail (`#pass-rate-waiting`) — free, CSO wording
10. Local tips (`#tips`)
11. FAQ (`#faq` + FAQ schema)
12. Nearby centres
13. Author byline — Written by Liam O'Connor → `/about.html`

## Stats source of truth

- Full CSO compile: [`cso-driving-test-stats-2026-07.json`](../cso-driving-test-stats-2026-07.json)
- Slim per-slug consumer: [`centre-stats.json`](../centre-stats.json)
- Rebuild: `python3 _agent/compile_cso_stats.py`
- Apply shell/stats to pages: `python3 _agent/migrate_centre_structure.py`

Do not invent figures for blank CSO cells. Say the value was not published that month.

## Per-centre JSON (optional depth)

1. Copy `dun-laoghaire.json` → `{slug}.json`.
2. Fill `stats`, `corridors`, `hotspots`, `manoeuvres` (RSA only: reverse / turnabout / hill start), `tips`, `faqs`, `nearby`.
3. Keep `stats.passRate` / `stats.waitingTime` aligned with `centre-stats.json`.
4. Author `{slug}-routes.html` from the config — primary answers must live in static HTML for crawlability.

Do not put paid route polylines in free HTML or map teasers. Map teaser = Google Maps centre pin / directions only.
