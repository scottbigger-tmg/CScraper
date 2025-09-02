# Requirements Folder

Use these files to install dependencies:

## Backend (Flask API + Scraper)
- Path: `backend/requirements.txt` (also duplicated at `requirements/backend.txt`)
- Install: `pip install -r backend/requirements.txt`

## Automation (Daily Runner)
- Path: `automation/requirements.txt` (also duplicated at `requirements/automation.txt`)
- Install: `pip install -r automation/requirements.txt`

### Notes
- We avoid heavy native deps (like `lxml`) to keep Render builds fast.
- `gunicorn` is included for production servers.
