#!/usr/bin/env python3
"""Compile CSO ROA CSVs into data/cso-driving-test-stats-<PERIOD>.json and data/centre-stats.json.

To refresh: export the three CSVs for the new month into _agent/data/cso/, then update the
PERIOD constants below and run this script.
"""
from __future__ import annotations

import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CSO = Path(__file__).resolve().parent / "data" / "cso"

PERIOD = "2026-09"
MONTH_LABEL = "2026 September"  # as written in the CSO "Month" column
PERIOD_LABEL = "September 2026"
PERIOD_END_DATE = "2026-09-30"

MANUAL = {
    "All driving test centres": None,
    "Athlone, Co. Westmeath": "athlone",
    "Ballina, Co. Mayo": "ballina",
    "Birr, Co. Offaly": None,
    "Birr (County Arms Hotel), Co. Offaly": "birr-county-arms-hotel",
    "Buncrana, Co. Donegal": "buncrana",
    "Carlow, Co. Carlow": "carlow",
    "Carlow Talbot Hotel, Co. Carlow": "carlow-talbot-hotel",
    "Carrick On Shannon, Co. Leitrim": "carrick-on-shannon",
    "Castlebar, Co. Mayo": "castlebar",
    "Cavan, Co. Cavan": "cavan",
    "Charlestown (Dublin), Co. Dublin": None,
    "Clifden, Co. Galway": "clifden",
    "Clonmel, Co. Tipperary": "clonmel",
    "Cork (Ballincollig), Co. Cork": "ballincollig",
    "Cork (St. Finbarr's GAA Club Togher), Co. Cork": None,
    "Cork (Wilton), Co. Cork": "wilton",
    "Donegal, Co. Donegal": "donegal",
    "Drogheda, Co. Louth": None,
    "Dun Laoghaire / Deansgrange, Co. Dublin": "dun-laoghaire",
    "Dundalk, Co. Louth": "dundalk",
    "Dungarvan, Co. Waterford": "dungarvan",
    "Ennis, Co. Clare": "ennis",
    "Finglas, Co. Dublin": "finglas",
    "Galway (Carnmore), Co. Galway": "carnmore",
    "Galway (Westside), Co. Galway": "westside",
    "Gorey, Co. Wexford": "gorey",
    "Kilkenny (Govt Buildings), Co. Kilkenny": "kilkenny-government-buildings",
    "Kilkenny (O'Loughlin Gaels), Co. Kilkenny": "kilkenny-oloughlin-gaels",
    "Killarney, Co. Kerry": "killarney",
    "Killester, Co. Dublin": "killester",
    "Kilrush, Co. Clare": "kilrush",
    "Letterkenny, Co. Donegal": "letterkenny",
    "Limerick - Castlemungret, Co. Limerick": "limerick-castlemungret",
    "Limerick - Woodview, Co. Limerick": "woodview",
    "Limerick (Roxboro), Co. Limerick": None,
    "Longford, Co. Longford": "longford",
    "Loughrea, Co. Galway": "loughrea",
    "Loughrea (Lough Rea Hotel & Spa), Co. Galway": None,
    "Mallow, Co. Cork": None,
    "Mallow (Cork Racecourse Mallow), Co. Cork": "mallow",
    "Monaghan, Co. Monaghan": "monaghan",
    "Mulhuddart, Co. Dublin": "mulhuddart",
    "Mulhuddart (Carlton Hotel), Co. Dublin": None,
    "Mulhuddart Maple House, Co. Dublin": "maple-house",
    "Mullingar, Co. Westmeath": "mullingar",
    "Naas, Co. Kildare": "naas",
    "Navan, Co. Meath": "navan",
    "Nenagh, Co. Tipperary": "nenagh",
    "Newcastle West, Co. Limerick": "newcastle-west",
    "Newcastle West (Longcourt House Hotel), Co. Limerick": "newcastle-west-longcourt-house-hotel",
    "Portlaoise, Co. Laois": "portlaoise",
    "Portlaoise (Maldron Hotel), Co. Laois": "maldron-hotel",
    "Raheny, Co. Dublin": "raheny",
    "Roscommon, Co. Roscommon": "roscommon",
    "Shannon, Co. Clare": "shannon",
    "Skibbereen, Co. Cork": "skibbereen",
    "Sligo, Co. Sligo": "sligo",
    "Tallaght, Co. Dublin": "tallaght",
    "Thurles, Co. Tipperary": "thurles",
    "Tipperary, Co. Tipperary": "tipperary",
    "Tralee, Co. Kerry": "tralee",
    "Tralee (HGV's), Co. Kerry": None,
    "Tuam, Co. Galway": "tuam",
    "Tullamore, Co. Offaly": "tullamore",
    "Waterford, Co. Waterford": "waterford",
    "Wexford, Co. Wexford": "wexford",
    "Wicklow, Co. Wicklow": "wicklow",
    "Galway (Clybaun Hotel), Co. Galway": "clybaun",
    "Sandyford, Co. Dublin": None,
    "Drogheda – Southgate, Co. Louth": "drogheda",
    "Mitchelstown, Co. Cork": "mitchelstown",
}

DISPLAY = {
    "athlone": "Athlone",
    "ballina": "Ballina",
    "ballincollig": "Ballincollig",
    "birr-county-arms-hotel": "Birr (County Arms Hotel)",
    "buncrana": "Buncrana",
    "carlow": "Carlow",
    "carlow-talbot-hotel": "Carlow Talbot Hotel",
    "carnmore": "Galway (Carnmore)",
    "carrick-on-shannon": "Carrick-on-Shannon",
    "castlebar": "Castlebar",
    "cavan": "Cavan",
    "clifden": "Clifden",
    "clonmel": "Clonmel",
    "clybaun": "Galway (Clybaun)",
    "donegal": "Donegal",
    "drogheda": "Drogheda (Southgate)",
    "dun-laoghaire": "Dun Laoghaire",
    "dundalk": "Dundalk",
    "dungarvan": "Dungarvan",
    "ennis": "Ennis",
    "finglas": "Finglas",
    "gorey": "Gorey",
    "kilkenny-government-buildings": "Kilkenny (Government Buildings)",
    "kilkenny-oloughlin-gaels": "Kilkenny (O'Loughlin Gaels)",
    "killarney": "Killarney",
    "killester": "Killester",
    "kilrush": "Kilrush",
    "letterkenny": "Letterkenny",
    "limerick-castlemungret": "Limerick Castlemungret",
    "longford": "Longford",
    "loughrea": "Loughrea",
    "maldron-hotel": "Portlaoise (Maldron Hotel)",
    "mallow": "Mallow",
    "maple-house": "Maple House (Mulhuddart)",
    "mitchelstown": "Mitchelstown",
    "monaghan": "Monaghan",
    "mulhuddart": "Mulhuddart",
    "mullingar": "Mullingar",
    "naas": "Naas",
    "navan": "Navan",
    "nenagh": "Nenagh",
    "newcastle-west": "Newcastle West",
    "newcastle-west-longcourt-house-hotel": "Newcastle West (Longcourt House Hotel)",
    "portlaoise": "Portlaoise",
    "raheny": "Raheny",
    "roscommon": "Roscommon",
    "shannon": "Shannon",
    "skibbereen": "Skibbereen",
    "sligo": "Sligo",
    "tallaght": "Tallaght",
    "thurles": "Thurles",
    "tipperary": "Tipperary",
    "tralee": "Tralee",
    "tuam": "Tuam",
    "tullamore": "Tullamore",
    "waterford": "Waterford",
    "westside": "Galway (Westside)",
    "wexford": "Wexford",
    "wicklow": "Wicklow",
    "wilton": "Cork (Wilton)",
    "woodview": "Limerick Woodview",
}

REGION = {
    "dun-laoghaire": "Dublin",
    "finglas": "Dublin",
    "tallaght": "Dublin",
    "raheny": "Dublin",
    "killester": "Dublin",
    "mulhuddart": "Dublin",
    "maple-house": "Dublin",
    "wilton": "Cork",
    "ballincollig": "Cork",
    "mallow": "Cork",
    "skibbereen": "Cork",
    "mitchelstown": "Cork",
    "carnmore": "Galway",
    "westside": "Galway",
    "clybaun": "Galway",
    "tuam": "Galway",
    "loughrea": "Galway",
    "clifden": "Galway",
    "woodview": "Limerick",
    "limerick-castlemungret": "Limerick",
    "newcastle-west": "Limerick",
    "newcastle-west-longcourt-house-hotel": "Limerick",
}


def parse_num(v: str | None):
    v = (v or "").strip()
    if not v:
        return None
    f = float(v)
    return int(f) if f == int(f) else f


def read_csv(path: Path) -> dict:
    out = {}
    with path.open(newline="", encoding="utf-8-sig") as fh:
        for row in csv.DictReader(fh):
            out[row["Driving Test Centre"]] = parse_num(row.get("VALUE"))
    return out


def main() -> None:
    pass_rates = read_csv(CSO / f"ROA30-pass-rates-{PERIOD}.csv")
    abandoned = read_csv(CSO / f"ROA30-abandoned-{PERIOD}.csv")
    waits = read_csv(CSO / f"ROA36-waiting-times-{PERIOD}.csv")
    all_names = sorted(set(pass_rates) | set(abandoned) | set(waits))

    unmapped = []
    centres = []
    by_slug = {}
    national = None

    for name in all_names:
        if name not in MANUAL:
            unmapped.append(name)
            slug = None
        else:
            slug = MANUAL[name]
        entry = {
            "csoName": name,
            "slug": slug,
            "displayName": DISPLAY.get(slug) if slug else name.split(",")[0],
            "url": f"/{slug}-routes.html" if slug else None,
            "region": REGION.get(slug) if slug else None,
            "passRate": pass_rates.get(name),
            "waitWeeks": waits.get(name),
            "abandoned": abandoned.get(name),
            "passRatePublished": pass_rates.get(name) is not None,
            "waitWeeksPublished": waits.get(name) is not None,
        }
        if name == "All driving test centres":
            national = {
                "passRate": entry["passRate"],
                "waitWeeks": entry["waitWeeks"],
                "abandoned": entry["abandoned"],
            }
            continue
        centres.append(entry)
        if slug:
            prev = by_slug.get(slug)
            if not prev or (
                (entry["passRate"] is not None and prev.get("passRate") is None)
                or (entry["waitWeeks"] is not None and prev.get("waitWeeks") is None)
            ):
                by_slug[slug] = {
                    "slug": slug,
                    "csoName": name,
                    "displayName": entry["displayName"],
                    "url": entry["url"],
                    "region": entry["region"],
                    "passRate": entry["passRate"],
                    "waitWeeks": entry["waitWeeks"],
                    "abandoned": entry["abandoned"],
                }

    route_slugs = {
        p.stem.replace("-routes", "")
        for p in ROOT.glob("*-routes.html")
        if p.parent == ROOT
    }
    missing_pages = sorted(route_slugs - set(by_slug))

    payload = {
        "period": PERIOD,
        "monthLabel": MONTH_LABEL,
        "lastUpdatedLabel": PERIOD_LABEL,
        "lastUpdatedDate": PERIOD_END_DATE,
        "source": {
            "publisher": "Central Statistics Office (CSO)",
            "series": "RSA driving test statistics (ROA)",
            "category": "Category B (Car or light van)",
            "citation": f"Source: CSO / RSA driving test statistics (ROA), Category B, {PERIOD_LABEL}.",
            "tables": {
                "passRate": "ROA30 Driving Test Pass Rate",
                "abandoned": "ROA30 Driving Tests Not Conducted / Abandoned",
                "waitWeeks": "ROA36 Estimated Time to Driving Test Invite at Month End",
            },
            "files": [
                f"_agent/data/cso/ROA30-pass-rates-{PERIOD}.csv",
                f"_agent/data/cso/ROA30-abandoned-{PERIOD}.csv",
                f"_agent/data/cso/ROA36-waiting-times-{PERIOD}.csv",
            ],
        },
        "national": national,
        "centres": centres,
        "bySlug": by_slug,
        "meta": {
            "unmappedCsoNames": unmapped,
            "driveflowSlugsWithoutCsoRow": missing_pages,
            "mappedSlugCount": len(by_slug),
        },
    }

    (ROOT / "data" / f"cso-driving-test-stats-{PERIOD}.json").write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    slim = {
        "period": payload["period"],
        "lastUpdatedLabel": payload["lastUpdatedLabel"],
        "lastUpdatedDate": payload["lastUpdatedDate"],
        "citation": payload["source"]["citation"],
        "national": national,
        "centres": by_slug,
    }
    (ROOT / "data" / "centre-stats.json").write_text(
        json.dumps(slim, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    print(f"mapped={len(by_slug)} unmapped={unmapped} missing={missing_pages}")


if __name__ == "__main__":
    main()
