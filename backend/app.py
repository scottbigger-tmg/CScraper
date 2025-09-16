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

    # Read all lines as text so we can handle fully-quoted lines
    with open(CSV_PATH, 'r', encoding='utf-8', newline='') as f:
        # Strip CR/LF but keep content; ignore empty/whitespace-only lines
        lines = [ln.rstrip('\r\n') for ln in f.readlines()]
    if not lines:
        return jsonify([])

    def is_fully_quoted(s: str) -> bool:
        s = s.strip()
        return len(s) >= 2 and s.startswith('"') and s.endswith('"')

    # Consider only non-empty lines for detection
    nonempty = [ln for ln in lines if ln.strip() != '']

    # CASE A: Fully-quoted lines where commas are inside the quotes (your sample)
    if nonempty and all(is_fully_quoted(ln) for ln in nonempty):
        # Unwrap quotes and split
        header_raw = nonempty[0].strip()[1:-1]  # strip outer quotes
        header = [h.strip().lower().replace('\ufeff', '') for h in header_raw.split(',')]

        data_rows = []
        for ln in nonempty[1:]:
            row_raw = ln.strip()[1:-1]  # strip outer quotes
            parts = [p.strip() for p in row_raw.split(',')]
            data_rows.append(dict(zip(header, parts)))
    else:
        # ... keep the rest of your existing code here (the Sniffer/DictReader path) ...
        with open(CSV_PATH, 'r', encoding='utf-8', newline='') as f:
            sample = f.read(4096)
            f.seek(0)
            try:
                sniffer = csv.Sniffer()
                dialect = sniffer.sniff(sample, delimiters=[',', ';', '\t', '|'])
                has_header = sniffer.has_header(sample)
            except Exception:
                class _Dialect(csv.Dialect):
                    delimiter = ','
                    quotechar = '"'
                    escapechar = None
                    doublequote = True
                    skipinitialspace = False
                    lineterminator = '\n'
                    quoting = csv.QUOTE_MINIMAL
                dialect = _Dialect()
                has_header = True

            f.seek(0)
            if has_header:
                reader = csv.DictReader(f, dialect=dialect)
                fieldnames = reader.fieldnames or []

                # Normalize fieldnames (handle single combined header like "a,b,c")
                if len(fieldnames) == 1 and ',' in fieldnames[0]:
                    f.seek(0)
                    first_line = f.readline()
                    header = [h.strip().lower().replace('\ufeff', '') for h in first_line.split(',')]
                    remainder = f.read().splitlines()
                    reader = csv.DictReader(remainder, fieldnames=header, dialect=dialect)
                    data_rows = list(reader)
                else:
                    data_rows = list(reader)
            else:
                # No header: map by index
                f.seek(0)
                row_reader = csv.reader(f, dialect=dialect)
                items = []
                for row in row_reader:
                    def get_i(i): return row[i].strip() if i < len(row) else ''
                    items.append({
                        'company': get_i(0),
                        'title': get_i(1),
                        'location': get_i(2),
                        'state': get_i(3),
                    })
                return jsonify(items)

    # Normalize keys and map to the four fields we expose
    def norm_key(k: str) -> str:
        return (k or '').strip().lower().replace('\ufeff', '')

    def pick(row: dict, candidates):
        norm_map = {norm_key(k): k for k in row.keys()}
        for key in candidates:
            orig = norm_map.get(key)
            if orig:
                val = row.get(orig, '')
                if val is not None and val != '':
                    return str(val).strip()
        return ''

    company_keys  = ['company', 'employer', 'organization', 'org', 'companyname']
    title_keys    = ['title', 'jobtitle', 'position', 'role']
    location_keys = ['location', 'city', 'city/state', 'citystate', 'city, state']
    state_keys    = ['state', 'st', 'province', 'region']

    items = []
    for r in data_rows:
        items.append({
            'company':  pick(r, company_keys),
            'title':    pick(r, title_keys),
            'location': pick(r, location_keys),
            'state':    pick(r, state_keys),
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

@app.route('/debug-raw', methods=['GET'])
def debug_raw():
    """Return the first few raw lines and byte markers to diagnose delimiter/BOM issues."""
    if not os.path.exists(CSV_PATH):
        return jsonify({"error": "no csv uploaded"}), 404

    # Read both bytes and text to inspect BOM & raw lines
    try:
        with open(CSV_PATH, 'rb') as fb:
            raw_bytes = fb.read(200)  # first 200 bytes
    except Exception as e:
        return jsonify({"error": f"read-bytes failed: {e}"}), 500

    try:
        with open(CSV_PATH, 'r', encoding='utf-8', newline='') as ft:
            lines = []
            for _ in range(5):  # first 5 lines
                line = ft.readline()
                if not line:
                    break
                lines.append(line.rstrip('\n'))
    except Exception as e:
        return jsonify({"error": f"read-text failed: {e}"}), 500

    # Hex preview of first up-to-80 bytes
    hex_preview = raw_bytes[:80].hex()

    return jsonify({
        "hex_preview_first_80_bytes": hex_preview,
        "raw_text_first_lines": lines
    })
