import json
from pathlib import Path
from .scraper_core import scrape_from_config, write_csv, upload_csv

UPLOAD_URL = "https://career-scraper-backend.onrender.com/upload"
CONFIG_PATH = Path(__file__).parent / "company_config.json"

def main():
    if CONFIG_PATH.exists():
        config = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    else:
        config = []
    rows = scrape_from_config(config)
    out_path = Path("scraped_jobs.csv")
    write_csv(rows, out_path)
    print(f"[OK] Wrote {out_path} with {len(rows)} rows. Uploading to dashboard...")
    try:
        resp = upload_csv(out_path, UPLOAD_URL)
        print("[OK] Upload response:", resp)
    except Exception as e:
        print("[ERROR] Upload failed:", e)

if __name__ == "__main__":
    main()
