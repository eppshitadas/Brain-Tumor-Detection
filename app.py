"""
app.py - Flask REST API for the Brain Tumor Detection System.

Endpoints
  GET  /            service info
  GET  /health      liveness check
  GET  /model-info  model details and evaluation metrics
  POST /predict     multipart/form-data with an image in the field "file"
"""
import logging
import os

from flask import Flask, jsonify, request
from flask_cors import CORS

from predict import (
    InvalidImageError,
    ModelNotFoundError,
    ModelService,
    PredictionError,
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("brain-tumor-api")

ALLOWED_EXTENSIONS = {"jpg", "jpeg", "png", "bmp"}
MAX_UPLOAD_MB = int(os.getenv("MAX_UPLOAD_MB", "5"))

# Comma-separated list of allowed frontend origins, e.g.
#   CORS_ORIGINS=https://my-app.vercel.app,http://localhost:5173
DEFAULT_ORIGINS = "http://localhost:5173,http://127.0.0.1:5173"
ORIGINS = [o.strip() for o in os.getenv("CORS_ORIGINS", DEFAULT_ORIGINS).split(",") if o.strip()]


def create_app() -> Flask:
    app = Flask(__name__)
    app.config["MAX_CONTENT_LENGTH"] = MAX_UPLOAD_MB * 1024 * 1024
    CORS(app, resources={r"/*": {"origins": ORIGINS}}, methods=["GET", "POST", "OPTIONS"])

    service = ModelService()
    app.extensions["model_service"] = service
    try:
        service.load()  # warm start; the API still runs if the model is missing
    except ModelNotFoundError as exc:
        log.warning("Model not loaded at startup: %s", exc)

    @app.after_request
    def add_security_headers(response):
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["Cache-Control"] = "no-store"
        return response

    @app.get("/")
    def index():
        return jsonify(
            service="Brain Tumor Detection API",
            status="ok",
            endpoints=["GET /health", "GET /model-info", "POST /predict"],
        )

    @app.get("/health")
    def health():
        return jsonify(status="ok", model_loaded=service.is_loaded)

    @app.get("/model-info")
    def model_info():
        return jsonify(service.info())

    @app.post("/predict")
    def predict():
        if "file" not in request.files:
            return jsonify(error="No file uploaded. Send the image in a form-data field named 'file'."), 400
        upload = request.files["file"]
        if not upload.filename:
            return jsonify(error="No file selected."), 400

        extension = upload.filename.rsplit(".", 1)[-1].lower() if "." in upload.filename else ""
        if extension not in ALLOWED_EXTENSIONS:
            return jsonify(error="Unsupported file type. Please upload a JPG, PNG or BMP image."), 415

        # The upload is processed in memory only. It is never written to disk, so
        # no user-supplied filename ever touches the file system.
        data = upload.read()
        if not data:
            return jsonify(error="The uploaded file is empty."), 400

        try:
            return jsonify(service.predict(data))
        except InvalidImageError as exc:
            return jsonify(error=str(exc)), 400
        except ModelNotFoundError as exc:
            return jsonify(error=str(exc)), 503
        except PredictionError as exc:
            return jsonify(error=str(exc)), 500

    @app.errorhandler(413)
    def too_large(_):
        return jsonify(error=f"File too large. The maximum size is {MAX_UPLOAD_MB} MB."), 413

    @app.errorhandler(404)
    def not_found(_):
        return jsonify(error="Endpoint not found."), 404

    @app.errorhandler(405)
    def method_not_allowed(_):
        return jsonify(error="Method not allowed."), 405

    @app.errorhandler(Exception)
    def unexpected(exc):
        log.exception("Unhandled error: %s", exc)
        return jsonify(error="Internal server error."), 500

    return app


app = create_app()

if __name__ == "__main__":
    # Local development server. In production the app is served by gunicorn.
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", "5000")), debug=False)
