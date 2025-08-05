
# career_scraper.py - Scrapes job titles, cities, and states from public career pages
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import csv


def scrape_career_page(company_name, base_url, job_list_path, job_title_selector, location_selector, state=None):
    try:
        response = requests.get(urljoin(base_url, job_list_path), timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')

        job_titles = [job.get_text(strip=True) for job in soup.select(job_title_selector)]
        locations = [loc.get_text(strip=True) for loc in soup.select(location_selector)]

        jobs = list(zip(job_titles, locations))
        return [{
            "company": company_name,
            "title": j[0],
            "location": j[1],
            "state": state if state else ""
        } for j in jobs]

    except Exception as e:
        print(f"Error scraping {company_name}: {e}")
        return []


def export_to_csv(job_data, filename='scraped_jobs.csv'):
    with open(filename, 'w', newline='', encoding='utf-8') as file:
        writer = csv.DictWriter(file, fieldnames=["company", "title", "location", "state"])
        writer.writeheader()
        writer.writerows(job_data)


if __name__ == '__main__':
    company_configs = [
        {
            "company": "ABC Events",
            "base_url": "https://www.abcevents.com",
            "job_list_path": "/careers",
            "job_title_selector": ".job-title",
            "location_selector": ".job-location",
            "state": "Michigan"
        },
        {
            "company": "XYZ Hospitality",
            "base_url": "https://www.xyzhospitality.com",
            "job_list_path": "/jobs",
            "job_title_selector": "h2.title",
            "location_selector": "p.location",
            "state": "Indiana"
        }
    ]

    all_jobs = []
    for config in company_configs:
        jobs = scrape_career_page(
            config['company'],
            config['base_url'],
            config['job_list_path'],
            config['job_title_selector'],
            config['location_selector'],
            config.get('state')
        )
        all_jobs.extend(jobs)

    export_to_csv(all_jobs)
    print(f"Exported {len(all_jobs)} job listings to scraped_jobs.csv")
