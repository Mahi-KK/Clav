from flask import Blueprint, current_app, jsonify, render_template, request

from .heatmap import FINGER_OF, LAYOUT, analyze

bp = Blueprint("clav", __name__)


@bp.get("/")
def index():
    return render_template(
        "index.html",
        layout=LAYOUT,
        finger_of=FINGER_OF,
        version=current_app.config["APP_VERSION"],
    )


@bp.post("/api/analyze")
def api_analyze():
    payload = request.get_json(silent=True)
    if not isinstance(payload, dict) or not isinstance(payload.get("text"), str):
        return jsonify(error='Send JSON like {"text": "your text"}.'), 400
    return jsonify(analyze(payload["text"]))


@bp.get("/health")
def health():
    return jsonify(status="ok", version=current_app.config["APP_VERSION"])


@bp.app_errorhandler(404)
def not_found(_error):
    return jsonify(error="Not found."), 404


@bp.app_errorhandler(405)
def method_not_allowed(_error):
    return jsonify(error="Method not allowed."), 405


@bp.app_errorhandler(413)
def too_large(_error):
    return jsonify(error="Text is too long. The limit is 100 KB."), 413
