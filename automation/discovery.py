# automation/discovery.py
import os, re, json, time
from typing import List, Dict
import requests

# === CONFIG ===
BING_ENDPOINT = "https://api.bing.microsoft.com/v7.0/search"
BING_KEY = os.getenv("BING_API_KEY")  # set in Render Cron Job environment

# Recognize common ATS domains
ATS_PATTERNS = [
    (re.compile(r"https?://boards\.greenhouse\.io/([^/?#]+)"), "greenhouse"),
    (re.compile(r"https?://jobs\.lever\.co/([^/?#]+)"), "lever"),
]

def _bing_search(query: str, count: int = 20, market: str = "en-US") -> List[Dict]:
    if not BING_KEY:
        raise RuntimeError("BING_API_KEY environment variable not set")
    headers = {"Ocp-Apim-Subscription-Key": BING_KEY}
    params = {"q": query, "mkt": market, "count": count, "responseFilter": "Webpages"}
    r = requests.get(BING_ENDPOINT, headers=headers, params=params, timeout=20)
    r.raise_for_status()
    data = r.json()
    items = data.get("webPages", {}).get("value", []) if isinstance(data, dict) else []
    # Normalize: title, url, snippet
    return [{"name": i.get("name",""), "url": i.get("url",""), "snippet": i.get("snippet","")} for i in items]

def _classify_url(url: str) -> Dict:
    # Try ATS first
    for rx, typ in ATS_PATTERNS:
        m = rx.match(url)
        if m:
            slug = m.group(1)
            return {"type": typ, "url": url, "slug": slug}
    # Generic careers pages
    if re.search(r"/careers|/jobs|/join-?us|/work-?with-?us", url, re.I):
        return {"type": "generic", "url": url}
    return {"type": "unknown", "url": url}

def discover_companies(keywords: List[str], states: List[str] = None, max_per_query: int = 20) -> List[Dict]:
    """
    Returns a list of scraper config entries: {company, type, url, ...}
    Heuristic: run queries, classify URLs, collapse duplicates.
    """
    states = states or []
    seen = set()
    out: List[Dict] = []
    queries = []

    # Build queries
    base_patterns = [
        "{kw} careers",
        "{kw} hiring",
        "{kw} jobs",
        "{kw} event staffing jobs",
        "{kw} venue jobs",
        "{kw} hospitality jobs",
    ]
    for kw in keywords:
        if states:
            for st in states:
                for pat in base_patterns:
                    queries.append(pat.format(kw=f"{kw} {st}"))
        else:
            for pat in base_patterns:
                queries.append(pat.format(kw=kw))

    # Execute
    for q in queries:
        try:
            results = _bing_search(q, count=max_per_query)
        except Exception as e:
            print("[DISCOVERY] Search failed for query:", q, e)
            continue

        for item in results:
            url = item["url"]
            cls = _classify_url(url)
            ukey = (cls["type"], cls["url"])
            if cls["type"] == "unknown":
                continue  # skip noise
            if ukey in seen:
                continue
            seen.add(ukey)

            # Create a generic company label from hostname/slug
            company_label = None
            if cls["type"] in ("greenhouse", "lever"):
                company_label = f"{cls['slug'].replace('-', ' ').title()} ({cls['type'].title()})"
            else:
                # Extract hostname for label
                m = re.match(r"https?://([^/]+)/", url + "/")
                host = m.group(1) if m else url
                company_label = f"{host} (Generic)"

            entry = {"company": company_label, "type": cls["type"], "url": cls["url"]}
            out.append(entry)

        time.sleep(0.8)  # be polite to the API

    # Deduplicate by (type, url)
    dedup = []
    seen2 = set()
    for e in out:
        k = (e["type"], e["url"])
        if k in seen2:
            continue
        seen2.add(k)
        dedup.append(e)
    return dedup

def write_company_config(entries: List[Dict], path: str):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(entries, f, indent=2)
