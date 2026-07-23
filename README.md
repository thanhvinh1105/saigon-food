# 🗺️ Saigon Food Map

A personal interactive food map of Ho Chi Minh City, hosted free on GitHub Pages.

**Live map:** `https://YOUR-USERNAME.github.io/YOUR-REPO-NAME`

---

## ✨ Features

- 193 places plotted across Saigon
- Filter by cuisine category and price range
- ⭐ "Must Try" highlights
- Click any pin for details + Google Maps link
- Add new places with one GitHub Issue — AI fills in the details automatically

---

## 🚀 Setup (one time)

### 1. Enable GitHub Pages
Go to **Settings → Pages**, set source to `Deploy from a branch` → `main` → `/ (root)`.

### 2. Add your Gemini API key
- Get a free key at [aistudio.google.com](https://aistudio.google.com) (no credit card needed)
- Go to **Settings → Secrets and variables → Actions**
- Add a secret named `GEMINI_API_KEY` with your key

### 3. You're done!
Your map is live at `https://YOUR-USERNAME.github.io/YOUR-REPO-NAME`

---

## ➕ Adding a new place

**Method A – GitHub Issue (automated, AI-powered):**
1. Click [New Issue](../../issues/new/choose) → "Add a place"
2. Paste a Google Maps link in the body
3. Wait ~60 seconds → the place appears on the map automatically

**Method B – Edit directly:**
Open `places.json` and add an entry:
```json
{
  "name": "Place Name",
  "url": "https://maps.google.com/...",
  "cuisine": "Vietnamese Pho",
  "district": "District 3, Ho Chi Minh City",
  "rating": 4.7,
  "price": "$$",
  "dishes": "Pho bo, Pho ga",
  "must_try": "Yes",
  "notes": "",
  "source": "Manual",
  "lat": 10.7799,
  "lng": 106.6890
}
```

**Method C – Run the script locally:**
```bash
pip install requests
export GEMINI_API_KEY=your_key_here
python add_place.py "https://www.google.com/maps/place/..."
```

---

## 🗂️ File structure

```
├── index.html          # The map website (single file, no build needed)
├── places.json         # All place data
├── add_place.py        # CLI script to add a place with AI prefill
├── .github/
│   ├── workflows/
│   │   └── add-place.yml       # GitHub Action
│   └── ISSUE_TEMPLATE/
│       └── add-place.md        # Issue template
└── README.md
```

---

## 🆓 Everything used is free

| Tool | What it does | Cost |
|------|-------------|------|
| GitHub Pages | Hosts the website | Free |
| GitHub Actions | Runs the add-place script | Free (public repos) |
| Leaflet.js + OpenStreetMap | Map tiles and pins | Free, no key needed |
| Gemini Flash API | AI prefills place details | Free tier: 1,500 req/day, no card |
| OpenStreetMap Nominatim | Geocoding (address → coordinates) | Free |
