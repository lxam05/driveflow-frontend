# Centre page data

JSON configs for RSA test-centre route pages. **Dun Laoghaire** (`dun-laoghaire.json`) is the reference shape.

## Usage

1. Copy `dun-laoghaire.json` → `{slug}.json`.
2. Fill `stats`, `corridors`, `hotspots`, `manoeuvres` (RSA only: reverse / turnabout / hill start), `tips`, `faqs`, `nearby`.
3. Author `{slug}-routes.html` from the config — primary answers must live in static HTML for crawlability.
4. Put the corridor preview (or snapshot) on the element with `data-routes-insert-after`, then `#routes` with `data-route="{routeKey}"`. `shared.js` inserts the paywall immediately after that anchor so free HTML stays above unlock.

Do not put paid route polylines in free HTML or map teasers. Map teaser = centre pin / directions only.
