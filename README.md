# cgdotcom

Archive and gallery viewer for [christinegedye.com](https://christinegedye.com).

Live at **https://davidgedye.github.io/cgdotcom/**

## What it does

Scrapes the Squarespace gallery pages on christinegedye.com and builds a sortable single-page archive of all works, with thumbnails loaded directly from the Squarespace CDN.

The archive covers 160 works across 10 year-based galleries (pre-2013 through 2024).

## Files

- **`scrape_gallery.py`** — scrapes a single Squarespace 7.0 gallery page and saves metadata to a JSON file
- **`build_gallery_html.py`** — reads all JSON files in `json/` and generates `index.html`
- **`json/`** — one JSON file per year, each containing title, description, dimensions (inches), pixel resolution, and CDN image URL for every work

## Usage

### Scrape a new gallery page

```bash
python3 scrape_gallery.py https://christinegedye.com/2024 ./christinegedye_2024
```

Then move the resulting `captions.json` to `json/2024.json` and run the build.

### Rebuild the gallery page

```bash
python3 build_gallery_html.py
```

Output is `index.html`. Requires `requests`, `beautifulsoup4`, and `Pillow`:

```bash
pip install requests beautifulsoup4 pillow
```

## Gallery viewer features

- Sortable columns: aspect ratio, year, title, status, dimensions (by area), caption, resolution (by pixel count)
- Default sort: year descending
- Click any thumbnail to open a full-size lightbox (press Escape or click outside to close)
- Mobile-friendly with horizontal scroll
