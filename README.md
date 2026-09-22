# Missouri Field Guide

An interactive, offline-ready field guide for the outdoors in Missouri. Covers flora, fauna, fungi, trees, fish, animal tracking, and a danger/caution section — all in a single self-contained HTML file with embedded photos.

## Features

- **Single-file web app** — `index.html` works offline with no internet connection required; all images are base64-encoded inline
- **Tabbed interface** — Flora, Fauna, Fungi, Trees, Fish, Tracking, Danger
- **123 species entries** — each with photos, descriptions, and field-identification facts
- **Printable PDF** — compact 66-page print layout via `scripts/build_pdf.py`
- **Missouri-specific** — plants, animals, and fungi native to or commonly found in Missouri

## Contents

| Tab | Entries |
|-----|---------|
| Flora (Edible & Dangerous Plants) | Wildflowers, berries, roots |
| Fauna (Wildlife & Animals) | Mammals, reptiles, birds, amphibians |
| Fungi (Edible & Dangerous Mushrooms) | Morels, chanterelles, deadly species |
| Trees | Oaks, hickories, maples, and distinctive trees |
| Fish | Missouri sport fish |
| Tracking | Animal tracks and sign |
| Danger Zone | Venomous snakes, toxic plants, poisonous fungi |

## Files

```
index.html              — Main field guide (open in any browser)
output/
  Missouri_Field_Guide.pdf  — Compact print-ready PDF (66 pages)
data/
  items_full.json       — Source data for all 123 entries
scripts/
  build_pdf.py          — Generate the PDF from items_full.json
  restructure_html.py   — Extract Fish tab; alphabetize entries
  rich_content.py       — Rich text content for Flora & Fungi entries
  rich_content_fauna.py — Rich text content for Fauna entries
  rich_content_trees_tracking.py — Rich text content for Trees & Tracking
```

## Usage

**View the field guide:**
Just open `index.html` in any modern web browser. No server required.

**Rebuild the PDF:**
```bash
pip install reportlab beautifulsoup4
python scripts/build_pdf.py
```

## Notes

- Photos are sourced from iNaturalist (CC-licensed) and embedded as base64 data URIs
- The danger section images are pending — to be added when photo fetching is available
- Honey Locust and Kentucky Coffeetree tree/fruit photos are also pending
