#!/usr/bin/env python3
"""
Squarespace 7.0 gallery scraper — parses data-image/data-title/data-description
attributes from the mainContent HTML returned by ?format=json

Usage: python3 scrape_gallery.py <page_url> [output_dir]
"""

import json
import re
import sys
import time
import urllib.parse
from pathlib import Path

import requests
from bs4 import BeautifulSoup

HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; gallery-archiver/1.0)"}


def fetch_gallery(page_url: str, session: requests.Session):
    parsed = urllib.parse.urlparse(page_url)
    json_url = urllib.parse.urlunparse(parsed._replace(query="format=json"))
    resp = session.get(json_url, headers=HEADERS, timeout=15)
    resp.raise_for_status()
    data = resp.json()

    html = data.get("mainContent", "")
    soup = BeautifulSoup(html, "html.parser")

    images = []
    for a in soup.find_all("a", attrs={"data-title": True}):
        img = a.find("img", attrs={"data-image": True})
        if not img:
            continue
        desc_html = a.get("data-description", "")
        desc_text = BeautifulSoup(desc_html, "html.parser").get_text(strip=True)
        images.append({
            "url": img.get("data-image", "").strip(),
            "title": a.get("data-title", "").strip(),
            "description": desc_text,
        })
    return images


def resolve_url(url: str, session: requests.Session) -> tuple:
    """
    If the URL contains 'lo-res', attempt the hi-res equivalent by replacing
    'lo-res' with 'hi-res'. Returns (resolved_url, used_hires: bool).
    Falls back to the original lo-res URL if the hi-res one doesn't exist.
    """
    if "lo-res" not in url:
        return url, False

    hires_url = url.replace("lo-res", "hi-res")
    try:
        r = session.head(hires_url, headers=HEADERS, timeout=10, allow_redirects=True)
        if r.status_code == 200:
            return hires_url, True
    except Exception:
        pass

    print(f"  (hi-res not found, using lo-res)")
    return url, False


def sanitize(s: str) -> str:
    return re.sub(r"[^\w\- ]", "", s).strip().replace(" ", "_")


def download(url: str, dest: Path, session: requests.Session) -> bool:
    try:
        r = session.get(url, headers=HEADERS, timeout=30, stream=True)
        r.raise_for_status()
        with open(dest, "wb") as f:
            for chunk in r.iter_content(8192):
                f.write(chunk)
        return True
    except Exception as e:
        print(f"  ERROR: {e}")
        return False


def scrape(page_url: str, output_dir: str = "gallery_output"):
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    session = requests.Session()

    print(f"Fetching {page_url} ...")
    images = fetch_gallery(page_url, session)
    print(f"Found {len(images)} images\n")

    manifest = []

    for i, img in enumerate(images, 1):
        resolved_url, used_hires = resolve_url(img["url"], session)

        ext = Path(urllib.parse.urlparse(resolved_url).path).suffix or ".jpg"
        slug = sanitize(img["title"])[:60]
        filename = f"{i:02d}_{slug}{ext}" if slug else f"{i:02d}{ext}"
        dest = out / filename

        print(f"[{i}/{len(images)}] {img['title']}")
        if img["description"]:
            print(f"  {img['description']}")
        if used_hires:
            print(f"  (hi-res)")

        download(resolved_url, dest, session)

        manifest.append({
            "index": i,
            "filename": filename,
            "url": resolved_url,
            "title": img["title"],
            "description": img["description"],
        })

        time.sleep(0.3)

    (out / "captions.json").write_text(json.dumps(manifest, indent=2))

    hires_count = sum(1 for m in manifest if "hi-res" in m["url"])
    lores_count = sum(1 for m in manifest if "lo-res" in m["url"])
    neither_count = len(manifest) - hires_count - lores_count
    print(f"\n--- Resolution summary ---")
    if hires_count:
        print(f"  Hi-res fetched:    {hires_count}")
    if lores_count:
        print(f"  Lo-res fallback:   {lores_count}")
    if neither_count:
        print(f"  No res tag:        {neither_count}")
    print(f"\nSaved to {out.resolve()}")
    print(f"Manifest: {out / 'captions.json'}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 scrape_gallery.py <page_url> [output_dir]")
        sys.exit(1)
    scrape(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else "gallery_output")
