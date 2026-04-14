"""
White Track — AI Meeting Notes Summarizer
Flask Backend: File Upload + Transcription + AI Summarisation
"""

import os
import uuid
import json
import datetime
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from werkzeug.utils import secure_filename

from modules.transcriber import transcribe_audio
from modules.summariser import summarise_text
from modules.storage import save_record, get_all_records, create_user, authenticate_user

# ── App Setup ────────────────────────────────────────────────────────────────
app = Flask(__name__, static_folder="../frontend", static_url_path="")
CORS(app)  # Allow frontend to call backend during development

UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), "uploads")
ALLOWED_EXTENSIONS = {"mp3", "wav", "m4a", "ogg", "mp4", "webm", "txt", "pdf"}
MAX_FILE_MB = 50

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["MAX_CONTENT_LENGTH"] = MAX_FILE_MB * 1024 * 1024

os.makedirs(UPLOAD_FOLDER, exist_ok=True)


# ── Helpers ───────────────────────────────────────────────────────────────────
def allowed_file(filename: str) -> bool:
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def file_type(filename: str) -> str:
    ext = filename.rsplit(".", 1)[1].lower()
    return "audio" if ext in {"mp3", "wav", "m4a", "ogg", "mp4", "webm"} else "text"


# ── Routes ────────────────────────────────────────────────────────────────────

@app.route("/")
def index():
    """Serve the frontend."""
    return send_from_directory(app.static_folder, "index.html")


@app.route("/api/upload", methods=["POST"])
def upload():
    file = request.files.get("file")

    # 👇 ADD THIS LINE HERE
    user_id = request.form.get("user_id")

    # continue your logic
    """
    POST /api/upload
    Accepts a multipart form with field 'file'.
    Pipeline: validate → save → transcribe (if audio) → summarise → return JSON.
    """
    # 1. Validate file presence
    if "file" not in request.files:
        return jsonify({"error": "No file provided."}), 400

    file = request.files["file"]
    if file.filename == "":
        return jsonify({"error": "No file selected."}), 400

    if not allowed_file(file.filename):
        return jsonify({
            "error": f"Unsupported file type. Allowed: {', '.join(ALLOWED_EXTENSIONS)}"
        }), 415

    # 2. Save file securely
    original_name = secure_filename(file.filename)
    job_id = str(uuid.uuid4())
    saved_name = f"{job_id}_{original_name}"
    save_path = os.path.join(app.config["UPLOAD_FOLDER"], saved_name)
    file.save(save_path)

    file_size_kb = round(os.path.getsize(save_path) / 1024, 1)
    ftype = file_type(original_name)

    # 3. Transcribe (audio) or read (text)
    try:
        if ftype == "audio":
            transcript = transcribe_audio(save_path)
        else:
            transcript = _read_text_file(save_path, original_name)
    except Exception as e:
        return jsonify({"error": f"Transcription failed: {str(e)}"}), 500

    if not transcript or not transcript.strip():
        return jsonify({"error": "Could not extract any text from the file."}), 422

    # 4. Summarise
    try:
        result = summarise_text(transcript)
    except Exception as e:
        return jsonify({"error": f"Summarisation failed: {str(e)}"}), 500

    # 5. Persist record
    record = {
        "id": job_id,
        "filename": original_name,
        "size_kb": file_size_kb,
        "type": ftype,
        "date": datetime.datetime.utcnow().strftime("%d/%m/%Y"),
        "status": "Complete",
        "transcript": transcript,
        "summary": result.get("summary", ""),
        "key_points": result.get("key_points", []),
        "action_items": result.get("action_items", []),
        "decisions": result.get("decisions", []),
    }


    # 6. Return to frontend (omit full transcript to keep payload small)
    return jsonify({
        "id": job_id,
        "filename": original_name,
        "size_kb": file_size_kb,
        "date": record["date"],
        "status": "Complete",
        "summary": record["summary"],
        "key_points": record["key_points"],
        "action_items": record["action_items"],
        "decisions": record["decisions"],
    }), 200


@app.route("/api/history", methods=["GET"])
def history():
    """GET /api/history — returns all processed records (newest first)."""
    records = get_all_records()
    # Strip heavy transcript field before sending
    slim = [
        {k: v for k, v in r.items() if k != "transcript"}
        for r in reversed(records)
    ]
    return jsonify(slim), 200


@app.route("/api/history/<job_id>", methods=["GET"])
def history_detail(job_id):
    """GET /api/history/<id> — full detail for one record."""
    records = get_all_records()
    match = next((r for r in records if r["id"] == job_id), None)
    if not match:
        return jsonify({"error": "Record not found."}), 404
    return jsonify(match), 200


@app.route("/api/health", methods=["GET"])
def health():
    return jsonify({"status": "ok", "service": "White Track Backend"}), 200


# ── Internal helpers ──────────────────────────────────────────────────────────
def _read_text_file(path: str, original_name: str) -> str:
    ext = original_name.rsplit(".", 1)[1].lower()
    if ext == "txt":
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            return f.read()
    if ext == "pdf":
        try:
            import pdfplumber
            with pdfplumber.open(path) as pdf:
                return "\n".join(p.extract_text() or "" for p in pdf.pages)
        except ImportError:
            raise RuntimeError("pdfplumber not installed. Run: pip install pdfplumber")
    return ""


@app.route("/api/signup", methods=["POST"])
def signup():
    data = request.json
    username = data.get("username")
    password = data.get("password")

    if not username or not password:
        return jsonify({"error": "Username and password required"}), 400

    success = create_user(username, password)
    if success:
        return jsonify({"message": "User created"}), 201
    else:
        return jsonify({"error": "User already exists"}), 400

@app.route("/api/login", methods=["POST"])
def login():
    data = request.json
    username = data.get("username")
    password = data.get("password")

    user_id = authenticate_user(username, password)
    if user_id is not None:
        return jsonify({"message": "Login successful", "user_id": user_id, "username": username}), 200
    else:
        return jsonify({"error": "Invalid credentials"}), 401

# ── Entry point ───────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("Starting White Track backend on http://localhost:5000")
    app.run(debug=True, port=5000)