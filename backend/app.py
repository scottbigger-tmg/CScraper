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
        return jsonify(list(reader))

@app.route('/download', methods=['GET'])
def download():
    if os.path.exists(CSV_PATH):
        return send_file(CSV_PATH, as_attachment=True)
    return "No file", 404

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
