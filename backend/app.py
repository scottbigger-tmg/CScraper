from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import csv, os

app = Flask(__name__)
CORS(app)

UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), 'uploads')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
CSV_PATH = os.path.join(UPLOAD_FOLDER, 'scraped_jobs.csv')

@app.route('/upload', methods=['POST'])
def upload():
    file = request.files.get('file')
    if not file or not file.filename.endswith('.csv'):
        return jsonify({"error": "Invalid file"}), 400
    file.save(CSV_PATH)
    return jsonify({"message": "File uploaded"}), 200

@app.route('/jobs', methods=['GET'])
def jobs():
    if not os.path.exists(CSV_PATH):
        return jsonify([])

    with open(CSV_PATH, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)

        # Normalize fieldnames (strip, lowercase, remove BOM)
        raw_fieldnames = reader.fieldnames or []
        normalized_to_original = {}
        for fn in raw_fieldnames:
            norm = fn.strip().lower().replace('\ufeff', '')  # remove BOM if present
            normalized_to_original[norm] = fn  # map normalized -> original in file

        # Helper: pick first existing field from a list of candidate names
        def pick(row, candidates):
            for key in candidates:
                original = normalized_to_original.get(key)
                if original:
                    val = row.get(original)
                    if val is not None and val != "":
                        return val
            return ""

        # Common header variants to support
        company_keys  = ['company', 'employer', 'organization', 'org', 'companyname']
        title_keys    = ['title', 'jobtitle', 'position', 'role']
        location_keys = ['location', 'city', 'city/state', 'citystate', 'city, state']
        state_keys    = ['state', 'st', 'province', 'region']

        items = []
        for row in reader:
            items.append({
                'company':  pick(row, company_keys),
                'title':    pick(row, title_keys),
                'location': pick(row, location_keys),
                'state':    pick(row, state_keys),
            })

        return jsonify(items)

@app.route('/download', methods=['GET'])
def download():
    if os.path.exists(CSV_PATH):
        return send_file(CSV_PATH, as_attachment=True)
    return "No file", 404

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)

@app.route('/debug-headers', methods=['GET'])
def debug_headers():
    """Return the raw CSV headers and a couple of raw rows so we can see exact keys."""
    if not os.path.exists(CSV_PATH):
        return jsonify({"error": "no csv uploaded"}), 404

    with open(CSV_PATH, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames or []

        # Grab up to 2 raw rows to inspect keys/values
        sample_rows = []
        for i, row in enumerate(reader):
            sample_rows.append(row)
            if i >= 1:
                break

    return jsonify({
        "fieldnames": fieldnames,
        "sample_rows": sample_rows
    })
