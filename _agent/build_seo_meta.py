#!/usr/bin/env python3
"""Generate seo-centre-meta.json for DriveFlow centre pages."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = Path(__file__).resolve().parent / "seo-centre-meta.json"

# County / region clustering for nearby links
GROUPS: dict[str, list[str]] = {
    "Dublin": [
        "tallaght",
        "mulhuddart",
        "finglas",
        "raheny",
        "killester",
        "dun-laoghaire",
        "naas",
        "wicklow",
    ],
    "Cork": [
        "wilton",
        "ballincollig",
        "mallow",
        "mitchelstown",
        "skibbereen",
        "woodview",
    ],
    "Galway": [
        "westside",
        "clybaun",
        "carnmore",
        "loughrea",
        "tuam",
        "clifden",
    ],
    "Limerick_Clare": [
        "limerick-castlemungret",
        "newcastle-west",
        "newcastle-west-longcourt-house-hotel",
        "shannon",
        "ennis",
        "kilrush",
        "maldron-hotel",
    ],
    "Kerry": ["tralee", "killarney"],
    "Waterford_Tipperary": [
        "waterford",
        "dungarvan",
        "clonmel",
        "nenagh",
        "thurles",
        "tipperary",
    ],
    "Wexford_Carlow_Kilkenny": [
        "wexford",
        "gorey",
        "carlow",
        "carlow-talbot-hotel",
        "kilkenny-oloughlin-gaels",
        "kilkenny-government-buildings",
        "portlaoise",
    ],
    "Midlands": [
        "athlone",
        "mullingar",
        "tullamore",
        "longford",
        "birr-county-arms-hotel",
        "roscommon",
    ],
    "NorthEast": [
        "drogheda",
        "dundalk",
        "navan",
        "cavan",
        "monaghan",
        "maple-house",
    ],
    "NorthWest": [
        "sligo",
        "letterkenny",
        "donegal",
        "buncrana",
        "ballina",
        "castlebar",
        "carrick-on-shannon",
    ],
}

# slug -> (displayName, county, region_key)
CENTRES: dict[str, tuple[str, str, str]] = {
    "athlone": ("Athlone", "Westmeath", "Midlands"),
    "ballina": ("Ballina", "Mayo", "NorthWest"),
    "ballincollig": ("Ballincollig", "Cork", "Cork"),
    "birr-county-arms-hotel": ("Birr – County Arms Hotel", "Offaly", "Midlands"),
    "buncrana": ("Buncrana", "Donegal", "NorthWest"),
    "carlow": ("Carlow", "Carlow", "Wexford_Carlow_Kilkenny"),
    "carlow-talbot-hotel": ("Carlow – Talbot Hotel", "Carlow", "Wexford_Carlow_Kilkenny"),
    "carnmore": ("Carnmore", "Galway", "Galway"),
    "carrick-on-shannon": ("Carrick-on-Shannon", "Leitrim", "NorthWest"),
    "castlebar": ("Castlebar", "Mayo", "NorthWest"),
    "cavan": ("Cavan", "Cavan", "NorthEast"),
    "clifden": ("Clifden", "Galway", "Galway"),
    "clonmel": ("Clonmel", "Tipperary", "Waterford_Tipperary"),
    "clybaun": ("Clybaun Galway", "Galway", "Galway"),
    "donegal": ("Donegal", "Donegal", "NorthWest"),
    "drogheda": ("Drogheda", "Louth", "NorthEast"),
    "dun-laoghaire": ("Dún Laoghaire", "Dublin", "Dublin"),
    "dundalk": ("Dundalk", "Louth", "NorthEast"),
    "dungarvan": ("Dungarvan", "Waterford", "Waterford_Tipperary"),
    "ennis": ("Ennis", "Clare", "Limerick_Clare"),
    "finglas": ("Finglas", "Dublin", "Dublin"),
    "gorey": ("Gorey", "Wexford", "Wexford_Carlow_Kilkenny"),
    "kilkenny-government-buildings": (
        "Kilkenny – Government Buildings",
        "Kilkenny",
        "Wexford_Carlow_Kilkenny",
    ),
    "kilkenny-oloughlin-gaels": (
        "Kilkenny – O'Loughlin Gaels",
        "Kilkenny",
        "Wexford_Carlow_Kilkenny",
    ),
    "killarney": ("Killarney", "Kerry", "Kerry"),
    "killester": ("Killester", "Dublin", "Dublin"),
    "kilrush": ("Kilrush", "Clare", "Limerick_Clare"),
    "letterkenny": ("Letterkenny", "Donegal", "NorthWest"),
    "limerick-castlemungret": ("Limerick – Castlemungret", "Limerick", "Limerick_Clare"),
    "longford": ("Longford", "Longford", "Midlands"),
    "loughrea": ("Loughrea", "Galway", "Galway"),
    "maldron-hotel": ("Maldron Hotel Limerick", "Limerick", "Limerick_Clare"),
    "mallow": ("Mallow", "Cork", "Cork"),
    "maple-house": ("Maple House", "Meath", "NorthEast"),
    "mitchelstown": ("Mitchelstown", "Cork", "Cork"),
    "monaghan": ("Monaghan", "Monaghan", "NorthEast"),
    "mulhuddart": ("Mulhuddart", "Dublin", "Dublin"),
    "mullingar": ("Mullingar", "Westmeath", "Midlands"),
    "naas": ("Naas", "Kildare", "Dublin"),
    "navan": ("Navan", "Meath", "NorthEast"),
    "nenagh": ("Nenagh", "Tipperary", "Waterford_Tipperary"),
    "newcastle-west": ("Newcastle West", "Limerick", "Limerick_Clare"),
    "newcastle-west-longcourt-house-hotel": (
        "Newcastle West – Longcourt House Hotel",
        "Limerick",
        "Limerick_Clare",
    ),
    "portlaoise": ("Portlaoise", "Laois", "Wexford_Carlow_Kilkenny"),
    "raheny": ("Raheny", "Dublin", "Dublin"),
    "roscommon": ("Roscommon", "Roscommon", "Midlands"),
    "shannon": ("Shannon", "Clare", "Limerick_Clare"),
    "skibbereen": ("Skibbereen", "Cork", "Cork"),
    "sligo": ("Sligo", "Sligo", "NorthWest"),
    "tallaght": ("Tallaght", "Dublin", "Dublin"),
    "thurles": ("Thurles", "Tipperary", "Waterford_Tipperary"),
    "tipperary": ("Tipperary", "Tipperary", "Waterford_Tipperary"),
    "tralee": ("Tralee", "Kerry", "Kerry"),
    "tuam": ("Tuam", "Galway", "Galway"),
    "tullamore": ("Tullamore", "Offaly", "Midlands"),
    "waterford": ("Waterford", "Waterford", "Waterford_Tipperary"),
    "westside": ("Westside Galway", "Galway", "Galway"),
    "wexford": ("Wexford", "Wexford", "Wexford_Carlow_Kilkenny"),
    "wicklow": ("Wicklow", "Wicklow", "Dublin"),
    "wilton": ("Wilton", "Cork", "Cork"),
    "woodview": ("Woodview", "Cork", "Cork"),
}

CUSTOM_META = {
    "killester": {
        "title": "Killester Driving Test Routes (2026) – Maps, Tips & Common Fail Areas | DriveFlow",
        "description": (
            "Practice real Killester driving test routes with Google Maps, examiner tips, "
            "fail hotspots, roundabout guidance, and local junction walkthroughs used by Dublin learners in 2026."
        ),
    },
    "raheny": {
        "title": "Raheny Driving Test Routes (2026) – Maps, Tips & Common Fail Areas | DriveFlow",
        "description": (
            "Practice real Raheny driving test routes with Google Maps, local fail hotspots, "
            "examiner tips, and junction walkthroughs used by Dublin learners in 2026."
        ),
    },
    "mulhuddart": {
        "title": "Mulhuddart Driving Test Routes (2026) + Tips to Pass First Time | DriveFlow",
        "description": (
            "Mulhuddart driving test routes (2026): real RSA-style practice routes, key roads, "
            "pass tips and common mistakes to help you pass your Mulhuddart driving test first time."
        ),
    },
    "gorey": {
        "title": "Gorey Wexford Driving Test Routes – Local Guide | DriveFlow",
        "description": (
            "Real local guide to Gorey Wexford driving test routes. Learn which roads, "
            "roundabouts and junctions examiners use — and what causes people to fail at this centre."
        ),
    },
    "kilkenny-oloughlin-gaels": {
        "title": "Kilkenny (O'Loughlin Gaels) Driving Test Routes | DriveFlow",
        "description": (
            "Practice Kilkenny (O'Loughlin Gaels) driving test routes using real Google Maps directions. "
            "Dublin Road, Ring Road, Hebron area — learn junctions and common mistakes before your exam."
        ),
    },
}

# Title/description templates rotated for uniqueness without stuffing
TITLE_TEMPLATES = [
    "{name} Driving Test Centre Routes (Ireland) | DriveFlow",
    "{name} Driving Test Routes – Google Maps Practice | DriveFlow",
    "Practice {name} Driving Test Routes | DriveFlow Ireland",
    "{name} RSA Test Centre Routes & Local Tips | DriveFlow",
    "{name} Driving Test Routes in County {county} | DriveFlow",
]

DESC_TEMPLATES = [
    (
        "Prepare for the {name} driving test centre in County {county}. "
        "Study local road patterns, junctions and Google Maps practice routes before test day."
    ),
    (
        "Get familiar with {name} RSA driving test routes in {county}. "
        "Review common examiner areas, roundabouts and manoeuvres used by Irish learners."
    ),
    (
        "{name} driving test routes for County {county} learners. "
        "Practise realistic Google Maps navigation covering junctions, estates and speed-limit changes."
    ),
    (
        "Learn how {name} driving test routes typically run around County {county}. "
        "Build confidence with local tips and structured route practice on DriveFlow."
    ),
    (
        "County {county} learners: practise {name} driving test centre routes with Google Maps. "
        "Focus on trickier junctions and the areas examiners reuse most often."
    ),
]


def nearby_for(slug: str, region: str, limit: int = 5) -> list[str]:
    peers = [s for s in GROUPS.get(region, []) if s != slug and s in CENTRES]
    return peers[:limit]


def main() -> None:
    centres = []
    for i, (slug, (name, county, region)) in enumerate(sorted(CENTRES.items())):
        custom = CUSTOM_META.get(slug)
        if custom:
            title = custom["title"]
            description = custom["description"]
        else:
            title = TITLE_TEMPLATES[i % len(TITLE_TEMPLATES)].format(name=name, county=county)
            description = DESC_TEMPLATES[i % len(DESC_TEMPLATES)].format(name=name, county=county)
        centres.append(
            {
                "slug": slug,
                "displayName": name,
                "county": county,
                "region": region,
                "nearby": nearby_for(slug, region),
                "title": title,
                "description": description,
                "canonical": f"https://www.driveflow.ie/{slug}-routes.html",
                "h1": f"{name} Driving Test Routes",
            }
        )

    payload = {
        "siteOrigin": "https://www.driveflow.ie",
        "organizationId": "https://www.driveflow.ie/#organization",
        "websiteId": "https://www.driveflow.ie/#website",
        "ogImage": "https://www.driveflow.ie/backgroundForWeb.jpg",
        "centres": centres,
    }
    OUT.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Wrote {len(centres)} centres to {OUT}")


if __name__ == "__main__":
    main()
