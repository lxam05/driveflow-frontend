# Centre page data

JSON configs and CSO stats for RSA test-centre route pages.

## Canonical page structure

Every `{slug}-routes.html` should follow this order:

1. Breadcrumb → `/routes.html`
2. Header — H1, short intro, **Updated July 2026**, hero if available
3. **Snapshot** (`.centre-snapshot`, free) — pass rate, wait weeks, test length, manoeuvres, corridors; cite CSO
4. **Free sample route** (`.free-route-card`, free) — turn-by-turn Route 1 prose + Google Maps CTA; data from `data/free-routes/{slug}.json` (skip centres with no backend route, e.g. `maldron-hotel`)
5. **Routes preview** (only when you have a real corridor bullet list) — `#routes-preview` + `<noscript>`. Do **not** put `data-routes-insert-after` here anymore.
6. **Paywall anchor** — empty `<div data-routes-insert-after aria-hidden="true"></div>` after the free route card (and after `#routes-preview` when present). `shared.js` moves the paywall and `#routes` immediately after this anchor.
7. `#routes` — paywall / unlocked Google Maps routes only (`shared.js`)
8. Where is the centre / map teaser (pin/directions only)
9. Examiner roads / hotspots (`#hotspots`)
10. Manoeuvre locations (`#manoeuvres`) — free HTML
11. Pass rate & waiting detail (`#pass-rate-waiting`) — free, CSO wording
12. Local tips (`#tips`)
13. FAQ (`#faq` + FAQ schema)
14. Nearby centres
15. Author byline — Written by Liam O'Connor → `/about.html`

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

## Free route 1 data

- Generated JSON: [`data/free-routes/{slug}.json`](../free-routes/)
- Regenerate: `python3 _agent/generate_free_routes.py` (requires `ANTHROPIC_API_KEY`)
- Inject HTML: `python3 _agent/inject_free_routes.py`
- Backend file map: [`_agent/backend_route_map.json`](../../_agent/backend_route_map.json)
