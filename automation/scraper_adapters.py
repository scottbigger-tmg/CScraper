import requests, re, time
from bs4 import BeautifulSoup
from urllib.parse import urljoin

HEADERS = {
    "User-Agent": "CareerScraperBot/1.0 (+contact: ops@example.com)"
}

def _get(url, timeout=15):
    resp = requests.get(url, headers=HEADERS, timeout=timeout)
    resp.raise_for_status()
    return resp

def scrape_greenhouse(board_url):
    jobs = []
    r = _get(board_url)
    soup = BeautifulSoup(r.text, "html.parser")
    for opening in soup.select(".opening a, a[href*='/jobs/']"):
        title = opening.get_text(strip=True)
        job_url = urljoin(board_url, opening.get("href"))
        li = opening.find_parent("div") or opening.find_parent("li")
        loc_text = ""
        if li:
            loc_node = li.find(class_=re.compile("location", re.I))
            if loc_node:
                loc_text = loc_node.get_text(strip=True)
        jobs.append({
            "title": title,
            "location": loc_text,
            "state": guess_state(loc_text),
            "source_url": job_url,
        })
    return jobs

def scrape_lever(board_url):
    jobs = []
    r = _get(board_url)
    soup = BeautifulSoup(r.text, "html.parser")
    for post in soup.select("div.posting, .posting, a.posting-title"):
        title_node = post.select_one(".posting-title h5, h5, .title")
        if not title_node and hasattr(post, "get"):
            title_node = post
        title = title_node.get_text(strip=True) if title_node else ""
        loc_node = post.select_one(".posting-categories .location, .sort-by-location, .location")
        loc_text = loc_node.get_text(strip=True) if loc_node else ""
        a = post.find("a", href=True) if hasattr(post, "find") else None
        job_url = urljoin(board_url, a["href"]) if a else board_url
        jobs.append({
            "title": title,
            "location": loc_text,
            "state": guess_state(loc_text),
            "source_url": job_url,
        })
    return jobs

def scrape_generic_page(page_url, title_selector, location_selector):
    jobs = []
    r = _get(page_url)
    soup = BeautifulSoup(r.text, "html.parser")
    titles = soup.select(title_selector) if title_selector else []
    for t in titles:
        title = t.get_text(strip=True)
        loc_node, loc_text = None, ""
        if location_selector:
            all_locs = soup.select(location_selector)
            idx = list(t.parent.children).index(t) if t.parent else -1
            if 0 <= idx < len(all_locs):
                loc_text = all_locs[idx].get_text(strip=True)
        jobs.append({
            "title": title,
            "location": loc_text,
            "state": guess_state(loc_text),
            "source_url": page_url,
        })
    return jobs

US_STATE_ABBR = {
    'AL','AK','AZ','AR','CA','CO','CT','DE','FL','GA','HI','ID','IL','IN','IA','KS','KY','LA','ME','MD','MA','MI',
    'MN','MS','MO','MT','NE','NV','NH','NJ','NM','NY','NC','ND','OH','OK','OR','PA','RI','SC','SD','TN','TX','UT',
    'VT','VA','WA','WV','WI','WY','DC'
}

def guess_state(loc_text):
    if not loc_text:
        return ""
    m = re.search(r",\s*([A-Z]{2})(?:\b|[^A-Za-z])", loc_text)
    if m and m.group(1) in US_STATE_ABBR:
        return m.group(1)
    m = re.search(r"\s-\s([A-Z]{2})\b", loc_text)
    if m and m.group(1) in US_STATE_ABBR:
        return m.group(1)
    return ""
