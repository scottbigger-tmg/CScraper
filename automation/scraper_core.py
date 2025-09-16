import csv, time, sys
from pathlib import Path
from typing import List, Dict
import requests

from .scraper_adapters import scrape_greenhouse, scrape_lever, scrape_generic_page

def scrape_from_config(config: List[Dict]) -> List[Dict]:
    all_rows = []
    for entry in config:
        company = entry.get("company","")
        typ = entry.get("type","").lower()
        url = entry.get("url","")
        try:
            if typ == "greenhouse":
                rows = scrape_greenhouse(url)
            elif typ == "lever":
                rows = scrape_lever(url)
            elif typ == "generic":
                rows = scrape_generic_page(url, entry.get("title_selector",""), entry.get("location_selector",""))
            else:
                print(f"[WARN] Unsupported type '{typ}' for company {company}. Skipping.", file=sys.stderr)
                rows = []
            for r in rows:
                r["company"] = company
            all_rows.extend(rows)
            time.sleep(1.2)
        except Exception as e:
            print(f"[ERROR] Failed scraping {company} ({typ}) {url}: {e}", file=sys.stderr)
            continue
    return all_rows

def write_csv(rows: List[Dict], out_path: Path):
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["company","title","location","state","source_url"])
        w.writeheader()
        for r in rows:
            w.writerow({
                "company": r.get("company",""),
                "title": r.get("title",""),
                "location": r.get("location",""),
                "state": r.get("state",""),
                "source_url": r.get("source_url",""),
            })

def upload_csv(csv_path: Path, upload_url: str):
    with csv_path.open("rb") as fh:
        resp = requests.post(upload_url, files={"file": fh})
        resp.raise_for_status()
    return resp.text
