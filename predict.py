"""
predict.py - model loading, image validation, preprocessing and prediction.

The preprocessing function `preprocess_image` MUST stay identical to the one in
training/train_model.py. If you change IMG_SIZE or the resize method in one
place, change it in the other and retrain the model.
"""
import io
import json
import logging
import os
import threading
import urllib.request
from pathlib import Path

os.environ.setdefault("TF_CPP_MIN_LOG_LEVEL", "2")  # quieter TensorFlow logs

import numpy as np
from PIL import Image, UnidentifiedImageError

log = logging.getLogger("brain-tumor-api")

# --------------------------------------------------------------------------
# Configuration (can be overridden with environment variables)
# --------------------------------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent
MODEL_PATH = Path(os.getenv("MODEL_PATH", BASE_DIR.parent / "model" / "brain_tumor_model.keras"))
METRICS_PATH = Path(os.getenv("METRICS_PATH", MODEL_PATH.parent / "metrics.json"))
MODEL_URL = os.getenv("MODEL_URL", "").strip()  # optional: download model if missing
METRICS_URL = os.getenv("METRICS_URL", "").strip()

IMG_SIZE = 128                       # must match training
ALLOWED_FORMATS = {"JPEG", "PNG", "BMP"}
MIN_SIDE = 32                        # reject tiny images
Image.MAX_IMAGE_PIXELS = 25_000_000  # protects against decompression bombs

DISCLAIMER = (
    "Educational project only. This prediction is not a medical diagnosis. "
    "Consult a qualified medical professional for any health concern."
)


class ModelNotFoundError(Exception):
    """The trained model file does not exist / could not be loaded."""


class InvalidImageError(Exception):
    """The uploaded file is not a valid, supported image."""


class PredictionError(Exception):
    """Something went wrong while running the model."""


def preprocess_image(data: bytes) -> np.ndarray:
    """Validate raw bytes and turn them into a (1, 128, 128, 3) float32 array
    with pixel values in 0-255 (the model rescales to 0-1 internally)."""
    try:
        with Image.open(io.BytesIO(data)) as probe:
            if probe.format not in ALLOWED_FORMATS:
                raise InvalidImageError("Unsupported image format. Please upload a JPG, PNG or BMP image.")
            probe.verify()  # detects truncated / corrupted files
        with Image.open(io.BytesIO(data)) as img:  # verify() invalidates the object, so re-open
            if min(img.size) < MIN_SIDE:
                raise InvalidImageError("Image is too small. Please upload a larger MRI image.")
            img = img.convert("RGB")
            img = img.resize((IMG_SIZE, IMG_SIZE), Image.Resampling.BILINEAR)
            arr = np.asarray(img, dtype=np.float32)
    except InvalidImageError:
        raise
    except (UnidentifiedImageError, OSError, ValueError, Image.DecompressionBombError, SyntaxError):
        raise InvalidImageError("The file is not a valid image or is corrupted.")
    return np.expand_dims(arr, axis=0)


def _download(url: str, destination: Path) -> None:
    if not url.lower().startswith("https://"):
        raise ModelNotFoundError("MODEL_URL must start with https://")
    destination.parent.mkdir(parents=True, exist_ok=True)
    tmp = destination.with_suffix(destination.suffix + ".part")
    log.info("Downloading %s ...", destination.name)
    with urllib.request.urlopen(url, timeout=120) as response, open(tmp, "wb") as out:
        while chunk := response.read(1024 * 1024):
            out.write(chunk)
    os.replace(tmp, destination)


class ModelService:
    """Loads the Keras model once and reuses it for every request."""

    def __init__(self) -> None:
        self._model = None
        self._lock = threading.Lock()

    @property
    def is_loaded(self) -> bool:
        return self._model is not None

    def load(self):
        with self._lock:
            if self._model is not None:
                return self._model
            try:
                if not MODEL_PATH.exists() and MODEL_URL:
                    _download(MODEL_URL, MODEL_PATH)
                if not METRICS_PATH.exists() and METRICS_URL:
                    _download(METRICS_URL, METRICS_PATH)
            except Exception as exc:  # network problems etc.
                log.error("Model download failed: %s", exc)
                raise ModelNotFoundError("The model could not be downloaded.")
            if not MODEL_PATH.exists():
                raise ModelNotFoundError(
                    "Model file not found. Train the model first (see README) or set MODEL_URL."
                )
            try:
                from tensorflow import keras  # imported here so the API starts fast
                self._model = keras.models.load_model(MODEL_PATH, compile=False)
            except Exception as exc:
                log.error("Model loading failed: %s", exc)
                raise ModelNotFoundError("The model file exists but could not be loaded.")
            log.info("Model loaded.")
            return self._model

    def predict(self, data: bytes) -> dict:
        batch = preprocess_image(data)  # validate first, so bad files never need the model
        model = self.load()
        try:
            with self._lock:
                p_tumor = float(model(batch, training=False).numpy().reshape(-1)[0])
        except Exception as exc:
            log.error("Prediction failed: %s", exc)
            raise PredictionError("The model failed to process this image.")

        p_tumor = min(max(p_tumor, 0.0), 1.0)
        is_tumor = p_tumor >= 0.5
        confidence = (p_tumor if is_tumor else 1.0 - p_tumor) * 100
        return {
            "prediction": "Tumor Detected" if is_tumor else "No Tumor Detected",
            "confidence": round(confidence, 2),
            "probabilities": {
                "tumor": round(p_tumor * 100, 2),
                "no_tumor": round((1.0 - p_tumor) * 100, 2),
            },
            "disclaimer": DISCLAIMER,
        }

    def info(self) -> dict:
        metrics = None
        if METRICS_PATH.exists():
            try:
                metrics = json.loads(METRICS_PATH.read_text(encoding="utf-8"))
            except (OSError, ValueError):
                metrics = None
        return {
            "model_loaded": self.is_loaded,
            "model_file_present": MODEL_PATH.exists(),
            "architecture": "Custom CNN (4 convolution blocks)",
            "input_size": [IMG_SIZE, IMG_SIZE, 3],
            "metrics": metrics,
        }
