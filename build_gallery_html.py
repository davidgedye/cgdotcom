#!/usr/bin/env python3
"""
build_gallery_html.py

Reads all christinegedye_YEAR/ directories in the current folder,
combines their captions.json metadata with the downloaded image files,
and writes gallery.html — a sortable single-page archive.

Usage: python3 build_gallery_html.py
Output: gallery.html (open in a browser; image paths are relative)
"""

import json
import re
from pathlib import Path

def parse_status(title: str, description: str):
    """Return (clean_title, status_string)."""
    if "- SOLD" in title or title.endswith("SOLD"):
        return re.sub(r"\s*-\s*SOLD\s*$", "", title).strip(), "SOLD"
    if "SOLD" in description:
        return title, "SOLD"
    if "Private Commission" in description:
        return title, "Commission"
    if "Available" in description:
        return title, "Available"
    return title, ""


def load_rows():
    rows = []
    for manifest in sorted(Path("json").glob("*.json"), reverse=True):
        year = manifest.stem
        data = json.loads(manifest.read_text())
        for item in data:
            title, status = parse_status(item["title"], item["description"])
            w = item.get("width", "")
            h = item.get("height", "")
            px_w = item.get("px_width") or 0
            px_h = item.get("px_height") or 0
            rows.append({
                "year": year,
                "title": title,
                "status": status,
                "width": w,
                "height": h,
                "area": (w * h) if (w != "" and h != "") else 0,
                "description": item["description"],
                "resolution": f"{px_w} × {px_h}" if px_w else "",
                "px_area": px_w * px_h,
                "img": item["url"],
            })
    return rows


def build_row_html(r: dict) -> str:
    status_class = "sold" if r["status"] == "SOLD" else ""
    dims = (
        f"{r['width']:.4g} × {r['height']:.4g} in"
        if r["width"] != ""
        else ""
    )
    return (
        f"    <tr>\n"
        f"      <td><img src=\"{r['img']}\" alt=\"{r['title']}\" "
        f"style=\"height:100px;width:auto;display:block;cursor:zoom-in;\" "
        f"onclick=\"openLightbox(this.src)\"></td>\n"
        f"      <td data-sort=\"{r['px_area']}\">{r['resolution']}</td>\n"
        f"      <td data-sort=\"{r['year']}\">{r['year']}</td>\n"
        f"      <td>{r['title']}</td>\n"
        f"      <td class=\"{status_class}\">{r['status']}</td>\n"
        f"      <td data-sort=\"{r['area']}\">{dims}</td>\n"
        f"      <td>{r['description']}</td>\n"
        f"    </tr>"
    )


def build_html(rows: list) -> str:
    html_rows = "\n".join(build_row_html(r) for r in rows)

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Christine Gedye — Gallery Archive</title>
<style>
  body {{ font-family: sans-serif; font-size: 16px; background: #f9f9f9; color: #222; margin: 0; padding: 24px; }}
  h1 {{ font-size: 1.6em; margin-bottom: 20px; }}
  .table-wrap {{ overflow-x: auto; -webkit-overflow-scrolling: touch; }}
  table {{ border-collapse: collapse; width: 100%; min-width: 700px; background: #fff; }}
  td {{ word-break: break-word; }}
  th {{
    text-align: left; padding: 10px 14px; background: #222; color: #fff;
    font-weight: normal; font-size: 15px; position: sticky; top: 0;
    cursor: default; user-select: none;
  }}
  th.sortable {{ cursor: pointer; }}
  th.sortable:hover {{ background: #444; }}
  th.asc::after  {{ content: ' ▲'; font-size: 11px; }}
  th.desc::after {{ content: ' ▼'; font-size: 11px; }}
  td {{ padding: 6px 14px; border-bottom: 1px solid #eee; vertical-align: middle; font-size: 22px; }}
  tr:hover td {{ background: #f5f5f5; }}
  td:first-child {{ padding: 4px; }}
  td:nth-child(2) {{ color: #666; font-size: 21px; }}
  td:nth-child(7) {{ color: #555; max-width: 320px; font-size: 22px; }}
  .sold {{ color: #999; font-style: italic; }}

  #lightbox {{
    display: none; position: fixed; inset: 0;
    background: rgba(0,0,0,0.85); z-index: 1000;
    align-items: center; justify-content: center;
  }}
  #lightbox.open {{ display: flex; }}
  #lightbox img {{ max-width: 90vw; max-height: 90vh; box-shadow: 0 0 40px rgba(0,0,0,0.8); }}
  #lightbox-close {{
    position: fixed; top: 20px; right: 28px;
    font-size: 36px; color: #fff; cursor: pointer;
    line-height: 1; user-select: none;
  }}
  #lightbox-close:hover {{ color: #ccc; }}
</style>
</head>
<body>
<div id="lightbox" onclick="closeLightbox()">
  <span id="lightbox-close" onclick="closeLightbox()">&#x2715;</span>
  <img id="lightbox-img" src="" alt="" onclick="event.stopPropagation()">
</div>
<h1>Christine Gedye — Gallery Archive ({len(rows)} works)</h1>
<div class="table-wrap">
<table id="gallery">
  <thead>
    <tr>
      <th>Image</th>
      <th class="sortable" data-col="1" data-type="num">Res.</th>
      <th class="sortable" data-col="2" data-type="num">Year</th>
      <th class="sortable" data-col="3" data-type="str">Title</th>
      <th class="sortable" data-col="4" data-type="str">Status</th>
      <th class="sortable" data-col="5" data-type="num">Dim.</th>
      <th class="sortable" data-col="6" data-type="str">Caption</th>
    </tr>
  </thead>
  <tbody>
{html_rows}
  </tbody>
</table>
</div>
<script>
  const tbody = document.querySelector('#gallery tbody');
  let sortCol = -1, sortDir = -1; // default: year descending

  function getVal(row, col, type) {{
    const cell = row.cells[col];
    if (type === 'num') return parseFloat(cell.dataset.sort ?? cell.textContent) || 0;
    return cell.textContent.trim().toLowerCase();
  }}

  function sortTable(col, type) {{
    if (col === sortCol) {{ sortDir *= -1; }}
    else {{ sortCol = col; sortDir = (type === 'num') ? -1 : 1; }}

    const rows = Array.from(tbody.rows);
    rows.sort((a, b) => {{
      const va = getVal(a, col, type), vb = getVal(b, col, type);
      return va < vb ? -sortDir : va > vb ? sortDir : 0;
    }});
    rows.forEach(r => tbody.appendChild(r));

    document.querySelectorAll('th').forEach(th => th.classList.remove('asc', 'desc'));
    document.querySelectorAll('th')[col].classList.add(sortDir === 1 ? 'asc' : 'desc');
  }}

  document.querySelectorAll('th.sortable').forEach(th => {{
    th.addEventListener('click', () => sortTable(+th.dataset.col, th.dataset.type));
  }});

  // Apply default sort (year descending)
  sortTable(2, 'num');

  function openLightbox(src) {{
    document.getElementById('lightbox-img').src = src;
    document.getElementById('lightbox').classList.add('open');
  }}
  function closeLightbox() {{
    document.getElementById('lightbox').classList.remove('open');
    document.getElementById('lightbox-img').src = '';
  }}
  document.addEventListener('keydown', e => {{ if (e.key === 'Escape') closeLightbox(); }});
</script>
</body>
</html>"""


def main():
    rows = load_rows()
    if not rows:
        print("No christinegedye_* directories found.")
        return
    html = build_html(rows)
    Path("index.html").write_text(html)
    print(f"Written index.html ({len(rows)} rows)")


if __name__ == "__main__":
    main()
