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

import sys, os, json, re, urllib.request, urllib.parse, requests

GEMINI_KEY   = os.environ.get("GEMINI_API_KEY", "")
PLACES_FILE  = "places.json"

# ── 1. Extract place name from Google Maps URL ──
def extract_name_from_url(url_or_name):
    m = re.search(r'/place/([^/]+)/', url_or_name)
    if m:
        return urllib.parse.unquote_plus(m.group(1)).replace('+', ' ')
    return url_or_name.strip()

# ── 2. Geocode via OpenStreetMap Nominatim ──
def geocode(name):
    query = f"{name}, Ho Chi Minh City, Vietnam"
    url   = "https://nominatim.openstreetmap.org/search?" + urllib.parse.urlencode({
        "q": query, "format": "json", "limit": 1
    })
    req = urllib.request.Request(url, headers={"User-Agent": "SaigonFoodMap/1.0"})
    try:
        with urllib.request.urlopen(req, timeout=8) as r:
            data = json.loads(r.read())
            if data:
                return float(data[0]["lat"]), float(data[0]["lon"])
    except Exception as e:
        print(f"  Geocoding failed: {e}")
    return 10.7769, 106.7009  # fallback: city centre

# ── 3. Gemini enrichment ──
def gemini_enrich(name, lat, lng):
    if not GEMINI_KEY:
        print("  ⚠️  No GEMINI_API_KEY set — skipping AI enrichment")
        return {}

    prompt = f"""You are a food and restaurant expert for Ho Chi Minh City (Saigon), Vietnam.
I am adding "{name}" to a personal food map of Saigon.

Use your knowledge of this restaurant or café to fill in the details below.
You MUST provide real, specific values — do NOT return null for cuisine, district, price, or must_try.
Only use null for rating or dishes if you truly have no knowledge of this specific venue.

Return ONLY a raw JSON object with no markdown fences, no explanation, nothing else before or after.
Use this exact structure:

{{
  "cuisine": "specific cuisine type e.g. Vietnamese Pho, Japanese Ramen, Specialty Coffee, Cocktail Bar",
  "district": "neighbourhood and city e.g. District 1, Ho Chi Minh City or Thao Dien, Thu Duc City",
  "rating": 4.5,
  "price": "$$",
  "dishes": "2-3 signature dishes or drinks this place is known for",
  "must_try": "Yes",
  "notes": "one useful fact e.g. Michelin star, famous for X, rooftop views. Empty string if nothing notable."
}}

Price guide (VND per person): $ = under 100k, $$ = 100-300k, $$$ = 300-700k, $$$$ = over 700k
must_try should be Yes if the place is well-regarded or popular, No if it is average or unknown.
The venue coordinates are lat={lat:.4f} lng={lng:.4f} which may help confirm the district."""

    # Try models in order — use latest stable names as of 2025/2026
    models = [
        "gemini-2.5-flash",
        "gemini-2.0-flash-lite",
        "gemini-1.5-flash-8b",
        "gemini-1.5-flash",
    ]

    for model in models:
        try:
            resp = requests.post(
                f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent",
                headers={"Content-Type": "application/json"},
                params={"key": GEMINI_KEY},
                json={"contents": [{"parts": [{"text": prompt}]}],
                      "generationConfig": {"temperature": 0.1, "maxOutputTokens": 512}},
                timeout=25
            )
            if resp.status_code != 200:
                print(f"  ⚠️  {model} returned HTTP {resp.status_code}: {resp.text[:200]}")
                continue
            resp.raise_for_status()
            candidates = resp.json().get("candidates", [])
            if not candidates:
                print(f"  ⚠️  {model} returned no candidates — may be blocked or quota hit")
                print(f"      Full response: {resp.text[:400]}")
                continue
            raw = candidates[0]["content"]["parts"][0]["text"]
            print(f"  Raw Gemini response ({model}):\n    {raw[:400]}")

            # Strip markdown fences if present
            clean = re.sub(r"```json|```", "", raw).strip()

            # Extract JSON object if there's surrounding text
            match = re.search(r'\{.*\}', clean, re.DOTALL)
            if match:
                clean = match.group(0)

            result = json.loads(clean)

            # If Gemini returned all nulls, something went wrong — try next model
            non_null = sum(1 for v in result.values() if v is not None and v != "")
            if non_null < 3:
                print(f"  ⚠️  Too many nulls from {model}, trying next model…")
                continue

            print(f"  ✓ Got good data from {model}")
            return result

        except json.JSONDecodeError as e:
            print(f"  ⚠️  JSON parse error from {model}: {e}")
            continue
        except Exception as e:
            print(f"  ⚠️  Error from {model}: {e}")
            continue

    print("  ⚠️  All models failed or returned nulls — saving with minimal data")
    return {}

# ── 4. Sensible fallback for missing fields ──
def guess_from_name(name):
    """Make educated guesses from the place name when Gemini fails."""
    n = name.lower()
    cuisine = None
    if any(w in n for w in ['ramen','pho','bun','com','viet','banh']):
        cuisine = 'Vietnamese'
    elif any(w in n for w in ['sushi','yakiniku','omakase','izakaya','japanese']):
        cuisine = 'Japanese'
    elif any(w in n for w in ['bbq','korean','grill']):
        cuisine = 'BBQ & Korean'
    elif any(w in n for w in ['cafe','coffee','matcha','tea']):
        cuisine = 'Café / Coffee'
    elif any(w in n for w in ['bar','cocktail','lounge']):
        cuisine = 'Cocktail Bar'
    elif any(w in n for w in ['pizza','pasta','italian']):
        cuisine = 'Italian'
    elif any(w in n for w in ['burger','smash','diner']):
        cuisine = 'Burgers'
    return {
        "cuisine": cuisine or "Restaurant / Café",
        "district": "Ho Chi Minh City",
        "rating": None,
        "price": "$$",
        "dishes": None,
        "must_try": "No",
        "notes": "Details not available — please update manually."
    }

# ── 5. Main ──
def main():
    if len(sys.argv) < 2:
        print("Usage: python add_place.py '<Google Maps URL or place name>'")
        sys.exit(1)

    raw_input = " ".join(sys.argv[1:])
    url  = raw_input if raw_input.startswith("http") else ""
    name = extract_name_from_url(raw_input)

    print(f"\n📍 Adding: {name}")

    # Geocode
    print("  Geocoding…")
    lat, lng = geocode(name)
    print(f"  → {lat:.5f}, {lng:.5f}")

    # AI enrich
    print("  Asking Gemini for details…")
    ai = gemini_enrich(name, lat, lng)

    # Fill in any missing fields with guesses
    if not ai or sum(1 for v in ai.values() if v) < 3:
        print("  Using name-based fallback for missing fields…")
        fallback = guess_from_name(name)
        for key, val in fallback.items():
            if not ai.get(key):
                ai[key] = val

    # Build place object
    place = {
        "name":     name,
        "url":      url or f"https://www.google.com/maps/search/{urllib.parse.quote(name)}",
        "cuisine":  ai.get("cuisine"),
        "district": ai.get("district"),
        "rating":   ai.get("rating"),
        "price":    ai.get("price"),
        "dishes":   ai.get("dishes"),
        "must_try": ai.get("must_try"),
        "notes":    ai.get("notes", ""),
        "source":   "Added via script",
        "lat":      round(lat, 6),
        "lng":      round(lng, 6),
    }

    print(f"\n  Final data:")
    for k, v in place.items():
        if k not in ('url','lat','lng','source'):
            print(f"    {k}: {v}")

    # Load existing places
    if os.path.exists(PLACES_FILE):
        with open(PLACES_FILE, encoding="utf-8") as f:
            places = json.load(f)
    else:
        places = []

    # Check for duplicate
    if any(p["name"].lower() == name.lower() for p in places):
        print(f"\n  ⚠️  '{name}' already exists in places.json — skipping.")
        sys.exit(0)

    places.append(place)

    with open(PLACES_FILE, "w", encoding="utf-8") as f:
        json.dump(places, f, ensure_ascii=False, indent=2)

    print(f"\n✅ Added '{name}' to {PLACES_FILE} ({len(places)} total places)")

if __name__ == "__main__":
    main()
