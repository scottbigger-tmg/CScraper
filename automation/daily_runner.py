
# daily_runner.py - auto run job scraper and upload to cloud
import requests
import subprocess
import time

# Step 1: Run the scraper and create the CSV
subprocess.run(["python", "career_scraper.py"])

# Step 2: Upload to cloud dashboard
url = 'https://your-flask-api.onrender.com/upload'  # replace with deployed API URL

try:
    with open("scraped_jobs.csv", 'rb') as file:
        r = requests.post(url, files={"file": file})
        print("Upload result:", r.status_code, r.text)
except Exception as e:
    print("Error uploading CSV:", e)

# Schedule this using crontab or GitHub Actions
