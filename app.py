from flask import Flask, request, jsonify
from detector import llm_classifier, stylometric_score
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from datetime import datetime
import uuid
import json
import os

app = Flask(__name__)
limiter = Limiter(
    get_remote_address,
    app=app,
    default_limits=[],
    storage_uri="memory://"
)

LOG_FILE = "audit_log.json"
CONTENT_STORE = {}



def log_entry(entry):
    """
    Append a structured entry to the audit log.
    """

    if os.path.exists(LOG_FILE):
        with open(LOG_FILE, "r") as f:
            try:
                logs = json.load(f)
            except json.JSONDecodeError:
                logs = []
    else:
        logs = []

    logs.append(entry)

    with open(LOG_FILE, "w") as f:
        json.dump(logs, f, indent=2)


@app.route("/submit", methods=["POST"])
@limiter.limit("10 per minute;100 per day")
def submit():
    data = request.get_json()

    if not data:
        return jsonify({
            "error": "Missing JSON body."
        }), 400

    text = data.get("text")
    creator_id = data.get("creator_id")

    if not text or not creator_id:
        return jsonify({
            "error": "Both 'text' and 'creator_id' are required."
        }), 400

    llm_score = llm_classifier(text)
    style_score = stylometric_score(text)

    confidence = round(
        (0.6 * llm_score) +
        (0.4 * style_score),
        2
    )
    content_id = str(uuid.uuid4())

    if confidence >= 0.70:
        attribution = "likely_ai"
    elif confidence >= 0.40:
        attribution = "uncertain"
    else:
        attribution = "likely_human"


    log_data = {
        "content_id": content_id,
        "creator_id": creator_id,
        "timestamp": datetime.utcnow().isoformat(),
        "attribution": attribution,
        "confidence": confidence,
        "llm_score": llm_score,
        "stylometric_score": style_score,
        "status": "classified"
    }

    log_entry(log_data)
    CONTENT_STORE[content_id] = {
            "creator_id": creator_id,
            "attribution": attribution,
            "confidence": confidence,
            "llm_score": llm_score,
            "stylometric_score": style_score,
            "status": "classified"
        }

    return jsonify({
        "content_id": content_id,
        "attribution": attribution,
        "confidence": confidence,
        "label": generate_label(confidence),
        "llm_score": llm_score,
        "stylometric_score": style_score
    })


@app.route("/log", methods=["GET"])
def get_log():

    if os.path.exists(LOG_FILE):
        with open(LOG_FILE, "r") as f:
            try:
                logs = json.load(f)
            except json.JSONDecodeError:
                logs = []
    else:
        logs = []

    return jsonify({
        "entries": logs
    })


@app.route("/")
def home():
    return jsonify({
        "message": "Provenance Guard API is running."
    })

@app.route("/appeal", methods=["POST"])
def appeal():

    data = request.get_json()

    content_id = data.get("content_id")
    reasoning = data.get("creator_reasoning")

    if content_id not in CONTENT_STORE:
        return jsonify({
            "error": "Content not found."
        }), 404

    CONTENT_STORE[content_id]["status"] = "under_review"

    appeal_entry = {
        "content_id": content_id,
        "timestamp": datetime.utcnow().isoformat(),
        "status": "under_review",
        "appeal_reasoning": reasoning
    }

    log_entry(appeal_entry)

    return jsonify({
        "message": "Appeal received.",
        "status": "under_review"
    })

def generate_label(confidence):

    if confidence >= 0.70:
        return (
            "This content shows strong indicators of AI-generated writing. "
            "Our system has high confidence in this assessment based on multiple detection signals. "
            "Creators may appeal this decision if they disagree."
        )

    elif confidence >= 0.40:
        return (
            "This content contains mixed signals. "
            "Our system is not confident enough to classify the content as AI-generated or human-written. "
            "Additional review may be necessary. Creators may appeal this result if they disagree."
        )

    return (
        "This content appears to be human-written. "
        "Our system found strong indicators of human authorship across multiple detection signals. "
        "Creators may appeal this decision if they disagree."
    )

if __name__ == "__main__":
    app.run(debug=True)