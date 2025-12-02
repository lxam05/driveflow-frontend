import requests
import json
from math import ceil

# ========= CONFIG =========
GOOGLE_API_KEY = "YOUR_DIRECTIONS_API_KEY_HERE"

# Example single route config – you’ll replace this with your real data
ROUTE_CONFIG = {
    "name": "Naas Route 1",
    "origin": {"lat": 53.2140693, "lng": -6.6700897},
    "destination": {"lat": 53.2139967, "lng": -6.6703431},
    "via_points": [
        {"lat": 53.2159796, "lng": -6.6713693},  # Turn 1
        {"lat": 53.2157624, "lng": -6.6744232},  # Turn 2
        {"lat": 53.2173070, "lng": -6.6743723},  # Turn 3
        {"lat": 53.2182451, "lng": -6.6753871},  # Turn 4
        {"lat": 53.2185923, "lng": -6.6746930},  # Turn 5
        {"lat": 53.2171360, "lng": -6.6711581},  # Turn 6
        {"lat": 53.2160823, "lng": -6.6710217},  # Turn 7
    ]
}

MAX_WAYPOINTS = 23  # origin + 23 + destination ≈ 25

# ========= POLYLINE DECODER =========
def decode_polyline(polyline_str):
    """Decodes a polyline that was encoded using the Google Maps method.
       Returns a list of (lat, lng) tuples."""
    index, lat, lng, coordinates = 0, 0, 0, []
    length = len(polyline_str)

    while index < length:
        shift, result = 0, 0
        while True:
            b = ord(polyline_str[index]) - 63
            index += 1
            result |= (b & 0x1f) << shift
            shift += 5
            if b < 0x20:
                break
        dlat = ~(result >> 1) if result & 1 else (result >> 1)
        lat += dlat

        shift, result = 0, 0
        while True:
            b = ord(polyline_str[index]) - 63
            index += 1
            result |= (b & 0x1f) << shift
            shift += 5
            if b < 0x20:
                break
        dlng = ~(result >> 1) if result & 1 else (result >> 1)
        lng += dlng

        coordinates.append((lat / 1e5, lng / 1e5))

    return coordinates

# ========= DIRECTIONS API CALL =========
def fetch_polyline_from_directions(route_config):
    origin = route_config["origin"]
    destination = route_config["destination"]
    via_points = route_config["via_points"]

    origin_str = f'{origin["lat"]},{origin["lng"]}'
    dest_str = f'{destination["lat"]},{destination["lng"]}'

    # via: tells Google we MUST go through these
    via_parts = [f'via:{p["lat"]},{p["lng"]}' for p in via_points]
    waypoints_param = "|".join(via_parts)

    params = {
        "origin": origin_str,
        "destination": dest_str,
        "mode": "driving",
        "key": GOOGLE_API_KEY
    }
    if waypoints_param:
        params["waypoints"] = waypoints_param

    resp = requests.get(
        "https://maps.googleapis.com/maps/api/directions/json",
        params=params
    )
    data = resp.json()

    if data.get("status") != "OK":
        raise RuntimeError(f"Directions API error: {data.get('status')} - {data}")

    # Use overview_polyline for the whole path
    polyline_str = data["routes"][0]["overview_polyline"]["points"]
    coords = decode_polyline(polyline_str)
    return coords

# ========= SEGMENT INTO GOOGLE MAPS URLS =========
def build_nav_links_from_coords(coords):
    total = len(coords)
    if total < 2:
        raise ValueError("Not enough coordinates to form a route.")

    print(f"Total polyline points: {total}")
    # Each segment: origin + up to 23 waypoints + destination
    segment_span = MAX_WAYPOINTS + 2
    segments = ceil(total / segment_span)

    links = []

    for i in range(segments):
        start = i * segment_span
        end = min(start + segment_span, total)
        chunk = coords[start:end]

        if len(chunk) < 2:
            break

        origin = f"{chunk[0][0]},{chunk[0][1]}"
        dest = f"{chunk[-1][0]},{chunk[-1][1]}"
        waypoints = "|".join(f"{lat},{lng}" for (lat, lng) in chunk[1:-1])

        url = (
            f"https://www.google.com/maps/dir/?api=1"
            f"&origin={origin}"
            f"&destination={dest}"
            f"&travelmode=driving"
        )
        if waypoints:
            url += f"&waypoints={waypoints}"

        links.append(url)

    return links

# ========= EXPORT JSON FOR VOICE TRIGGERS =========
def export_coords_json(coords, filename="route_points.json"):
    arr = [{"lat": lat, "lng": lng} for (lat, lng) in coords]
    with open(filename, "w") as f:
        json.dump(arr, f, indent=2)
    print(f"Saved {len(arr)} points to {filename}")

# ========= MAIN =========
if __name__ == "__main__":
    print(f"Fetching polyline for route: {ROUTE_CONFIG['name']}")
    coords = fetch_polyline_from_directions(ROUTE_CONFIG)

    # Save all points for future use (voice triggers, overlays etc.)
    export_coords_json(coords, filename="naas_route1_points.json")

    # Build Google Maps links
    links = build_nav_links_from_coords(coords)

    print("\n=== GOOGLE MAPS NAV LINKS ===\n")
    for i, link in enumerate(links, start=1):
        print(f"LEG {i}: {link}\n")
