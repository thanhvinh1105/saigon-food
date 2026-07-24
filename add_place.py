"""
add_place.py  –  AI-powered place prefiller
==============================================
Usage:
  python add_place.py "https://www.google.com/maps/place/..."
  python add_place.py "Anan Saigon"

Requires:
  pip install requests

Set environment variable:
  GEMINI_API_KEY=your_key_here
"""

import sys, os, json, re, urllib.request, urllib.parse, time, requests

GEMINI_KEY = os.environ.get("GEMINI_API_KEY", "")
PLACES_FILE = "places.json"

# ── 1. Extract place name from Google Maps URL or use as-is ──
def extract_name_from_url(url_or_name):
    m = re.search(r'/place/([^/]+)/', url_or_name)
    if m:
        return urllib.parse.unquote_plus(m.group(1)).replace('+', ' ')
    return url_or_name.strip()

# ── 2. Geocode via OpenStreetMap Nominatim (free, no key) ──
def geocode(name, country="Vietnam"):
    query = f"{name}, Ho Chi Minh City, {country}"
    url = "https://nominatim.openstreetmap.org/search?" + urllib.parse.urlencode({
        "q": query, "format": "json", "limit": 1
    })
    req = urllib.request.Request(url, headers={"User-Agent": "SaigonFoodMap/1.0 (personal project)"})
    try:
        with urllib.request.urlopen(req, timeout=8) as r:
            data = json.loads(r.read())
            if data:
                return float(data[0]["lat"]), float(data[0]["lon"])
    except Exception as e:
        print(f"  Geocoding failed: {e}")
    # Fallback: city centre
    return 10.7769, 106.7009

# ── 3. AI enrichment via Gemini Flash (free tier) ──
def gemini_enrich(name, lat, lng):
    if not GEMINI_KEY:
        print("  ⚠️  No GEMINI_API_KEY set — skipping AI enrichment")
        return {}

    prompt = f"""You are a food guide assistant for Ho Chi Minh City (Saigon), Vietnam.
A user wants to add "{name}" to their personal food map.
The venue is at approximately lat {lat:.4f}, lng {lng:.4f}.

Return ONLY a valid JSON object (no markdown, no explanation) with these exact keys:
{{
  "cuisine": "Short cuisine type, e.g. Vietnamese Pho, Japanese Ramen, Cocktail Bar, Specialty Coffee",
  "district": "District and city, e.g. District 1, Ho Chi Minh City or Thao Dien, Thu Duc City",
  "rating": 4.5,
  "price": "$$",
  "dishes": "2-3 signature dishes or drinks, comma separated",
  "must_try": "Yes or No based on whether this is a highly recommended spot",
  "notes": "Any useful note — Michelin star, famous for X, unusual feature. Empty string if nothing notable."
}}

If you don't know a field with confidence, use null. Price scale: $ under 100k VND/person, $$ 100-300k, $$$ 300-700k, $$$$ above 700k."""

    try:
        resp = requests.post(
            "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent",
            headers={"Content-Type": "application/json"},
            params={"key": GEMINI_KEY},
            json={"contents": [{"parts": [{"text": prompt}]}]},
            timeout=20
        )
        resp.raise_for_status()
        text = resp.json()["candidates"][0]["content"]["parts"][0]["text"]
        # Strip markdown fences if present
        text = re.sub(r"```json|```", "", text).strip()
        return json.loads(text)
    except Exception as e:
        print(f"  ⚠️  Gemini call failed: {e}")
        return {}

# ── 4. Main ──
def main():
    if len(sys.argv) < 2:
        print("Usage: python add_place.py '<Google Maps URL or place name>'")
        sys.exit(1)

    raw_input = " ".join(sys.argv[1:])
    url = raw_input if raw_input.startswith("http") else ""
    name = extract_name_from_url(raw_input)

    print(f"\n📍 Adding: {name}")

    # Geocode
    print("  Geocoding…")
    lat, lng = geocode(name)
    print(f"  → {lat:.5f}, {lng:.5f}")

    # AI enrich
    print("  Asking Gemini for details…")
    ai = gemini_enrich(name, lat, lng)
    print(f"  → {ai}")

    # Build place object
    place = {
        "name": name,
        "url": url or f"https://www.google.com/maps/search/{urllib.parse.quote(name)}",
        "cuisine": ai.get("cuisine"),
        "district": ai.get("district"),
        "rating": ai.get("rating"),
        "price": ai.get("price"),
        "dishes": ai.get("dishes"),
        "must_try": ai.get("must_try"),
        "notes": ai.get("notes", ""),
        "source": "Added via script",
        "lat": round(lat, 6),
        "lng": round(lng, 6),
    }

    # Load existing places
    if os.path.exists(PLACES_FILE):
        with open(PLACES_FILE, encoding="utf-8") as f:
            places = json.load(f)
    else:
        places = []

    # Check for duplicate
    existing_names = [p["name"].lower() for p in places]
    if name.lower() in existing_names:
        print(f"\n  ⚠️  '{name}' already exists in places.json — skipping.")
        sys.exit(0)

    places.append(place)

    with open(PLACES_FILE, "w", encoding="utf-8") as f:
        json.dump(places, f, ensure_ascii=False, indent=2)

    print(f"\n✅ Added '{name}' to {PLACES_FILE} ({len(places)} total places)")

if __name__ == "__main__":
    main()
