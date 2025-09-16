import os, json
from pathlib import Path
from .scraper_core import scrape_from_config, write_csv, upload_csv
from .discovery import discover_companies, write_company_config

UPLOAD_URL = "https://career-scraper-backend.onrender.com/upload"

# Keyword input file (optional). If absent, we fall back to hardcoded defaults.
KEYWORDS_PATH = Path(__file__).parent / "keywords.json"
COMPANY_CONFIG_PATH = Path(__file__).parent / "company_config.json"

DEFAULT_KEYWORDS = {
    "keywords": ["catering", "event center", "arena", "stadium", "hospitality", "convention center"],
    "states": ["MI", "IN"]  # tweak as needed, or leave empty to search broadly
}

def main():
    # 1) Load keywords
    if KEYWORDS_PATH.exists():
        kw_cfg = json.loads(KEYWORDS_PATH.read_text(encoding="utf-8"))
    else:
        kw_cfg = DEFAULT_KEYWORDS

    keywords = kw_cfg.get("keywords", [])
    states = kw_cfg.get("states", [])

    # 2) Discover targets via search API
    discovered = discover_companies(keywords, states, max_per_query=20)

    # 3) Write to company_config.json (so you can inspect)
    write_company_config(discovered, str(COMPANY_CONFIG_PATH))
    print(f"[DISCOVERY] Wrote {len(discovered)} targets to {COMPANY_CONFIG_PATH}")

    # 4) Scrape using discovered config
    rows = scrape_from_config(discovered)
    out_path = Path("scraped_jobs.csv")
    write_csv(rows, out_path)
    print(f"[SCRAPER] Wrote {out_path} with {len(rows)} rows. Uploading to dashboard...")

    # 5) Upload to backend
    try:
        resp = upload_csv(out_path, UPLOAD_URL)
        print("[UPLOAD] Upload response:", resp)
    except Exception as e:
        print("[UPLOAD] Failed:", e)

if __name__ == "__main__":
    main()
