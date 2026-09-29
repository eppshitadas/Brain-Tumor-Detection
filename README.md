# Brain Tumor Detection System

A full-stack, educational brain-MRI tumor detection app: a React frontend
uploads an MRI slice, a Flask API runs it through a TensorFlow/Keras CNN, and
the result is shown with a confidence score.

> **Disclaimer.** This is a student / research project. Its predictions are
> **not a medical diagnosis** and must never be used to make health
> decisions. Always consult a qualified medical professional.

## Features

- Drag-and-drop MRI upload with client-side validation and image preview
- Flask REST API (`POST /predict`) that returns a prediction and confidence
- CNN trained from scratch on a public Kaggle brain-MRI dataset
- Model details and live evaluation metrics shown in the UI
- Clean error handling for bad files, oversized uploads, and a missing model
- Ready to deploy: Vercel (frontend) + a Docker host (backend)

## Architecture

```
Browser (React + Vite)
      │  fetch("<VITE_API_URL>/predict", multipart/form-data)
      ▼
Flask API  (backend/app.py)
      │  in-memory validation & preprocessing (backend/predict.py)
      ▼
Keras CNN  (model/brain_tumor_model.keras)
      │  sigmoid probability
      ▼
JSON response  { prediction, confidence, probabilities, disclaimer }
```

The frontend never talks to the model directly and the backend never writes
uploaded files to disk - everything happens in memory for one request.

## Project structure

```
brain-tumor-detection/
├── frontend/            React + Vite UI
│   └── src/
│       ├── api.js               fetch wrapper (reads VITE_API_URL)
│       ├── App.jsx
│       ├── components/          Navbar, Hero, UploadSection, ResultCard, ...
│       └── styles.css
├── backend/
│   ├── app.py                   Flask routes
│   ├── predict.py               model loading + preprocessing + inference
│   ├── test_api.py              unit tests
│   └── requirements.txt
├── training/
│   ├── train_model.py           builds, trains, evaluates, saves the CNN
│   └── requirements.txt
├── model/                       brain_tumor_model.keras + metrics.json (generated)
├── dataset/                     put the downloaded dataset here (see dataset/README.md)
├── deploy/huggingface/README.md backend hosting guide
├── Dockerfile                   for Hugging Face Spaces / Render / Railway
└── docs/VIVA_PREP.md            presentation script + 20 viva Q&A
```

## Technologies

| Layer      | Technology                              |
|------------|------------------------------------------|
| Frontend   | React 18, Vite 5, plain CSS               |
| Backend    | Flask 3, Flask-CORS, Gunicorn             |
| ML model   | TensorFlow / Keras 3 (Python 3.11+)       |
| Image prep | Pillow, NumPy                             |
| Evaluation | scikit-learn, Matplotlib                  |

Why this stack: Flask + a hand-rolled CNN keeps every line of the pipeline
readable and explainable in a viva, rather than depending on an opaque
pretrained model or a heavier framework a student would struggle to defend.

## 1. Get the dataset

See [`dataset/README.md`](dataset/README.md) - download a free Kaggle
brain-MRI dataset and place it under `dataset/`.

## 2. Train the model

```bash
cd training
python -m venv venv && source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
python train_model.py
```

This loads `dataset/`, splits it 70/15/15 (train/validation/test), trains a
4-block CNN with data augmentation and early stopping, evaluates it on the
held-out test set, and writes to `model/`:
- `brain_tumor_model.keras` - the trained model
- `metrics.json` - accuracy, precision, recall, F1, confusion matrix
- `training_curves.png`, `confusion_matrix.png` - evaluation plots

Useful flags: `python train_model.py --epochs 60 --batch-size 16`.

## 3. Run the backend

```bash
cd backend
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
python app.py
```

The API starts at `http://localhost:5000`. It loads the model from
`../model/brain_tumor_model.keras` automatically; if that file is missing,
the server still starts but `/predict` returns a clear `503` error until you
train the model.

Run the tests:
```bash
python -m unittest test_api -v
```

## 4. Run the frontend

```bash
cd frontend
npm install
npm run dev
```

Open `http://localhost:5173`. In development it reads the backend URL from
`frontend/.env.development` (`VITE_API_URL=http://localhost:5000`), already
included - no setup needed locally.

## API reference

### `POST /predict`
`multipart/form-data` with an image file in the field **`file`** (JPG, PNG or
BMP, max 5 MB).

```bash
curl -F "file=@scan.jpg" http://localhost:5000/predict
```

Response `200`:
```json
{
  "prediction": "Tumor Detected",
  "confidence": 92.4,
  "probabilities": { "tumor": 92.4, "no_tumor": 7.6 },
  "disclaimer": "Educational project only. This prediction is not a medical diagnosis. Consult a qualified medical professional for any health concern."
}
```

Error responses: `400` invalid/missing file, `413` file too large,
`415` unsupported type, `503` model not trained/loaded, `500` prediction
failure. Every error is `{"error": "human-readable message"}`.

### `GET /model-info`
Returns the architecture, input size, and the `metrics.json` produced by
training (or `null` metrics if not trained yet).

### `GET /health`
`{"status": "ok", "model_loaded": true}` - used for uptime checks.

## Deployment

### Frontend -> Vercel
1. Push this repo to GitHub (see below).
2. In Vercel: **New Project** -> import the repo -> set **Root Directory**
   to `frontend`.
3. Add an environment variable: `VITE_API_URL` = your deployed backend URL
   (no trailing slash), e.g. `https://your-space.hf.space`.
4. Deploy. Vercel builds with `npm run build` automatically (Vite is
   auto-detected). The frontend never hardcodes `localhost` - it always
   reads `VITE_API_URL` at build time.

### Backend -> a Docker host
A plain serverless function host (Vercel/Netlify functions) cannot fit
TensorFlow's size limits, so the backend needs a container host with a
persistent Python process. See
[`deploy/huggingface/README.md`](deploy/huggingface/README.md) for exact
steps on Hugging Face Spaces (free, Docker-based). The same `Dockerfile`
also works unmodified on Render or Railway if you prefer those.

After the backend is live, set `CORS_ORIGINS` on the backend host to your
Vercel URL, and `VITE_API_URL` on Vercel to the backend URL, then redeploy
the frontend so the new env variable is baked into the build.

## GitHub setup

```bash
git init
git add .
git commit -m "Initial commit: Brain Tumor Detection System"
git branch -M main
git remote add origin https://github.com/<your-username>/brain-tumor-detection.git
git push -u origin main
```

The `.gitignore` already excludes `node_modules/`, Python virtual
environments, the dataset, and the trained model/metrics files, so the
repository stays small. If you *do* want the trained model in the repo and
it's under 100 MB, remove the `model/*.keras` line from `.gitignore` first.

## How the ML pipeline works (plain language)

```
MRI Image → Preprocessing → CNN → Feature Extraction → Classification → Prediction + Confidence → Web Interface
```

- **CNN (Convolutional Neural Network):** a neural network built from layers
  that slide small filters across an image to detect patterns like edges and
  shapes, then combine them into higher-level features - well suited to
  images because it reuses the same filter everywhere instead of learning a
  separate weight per pixel.
- **Preprocessing:** every image is converted to RGB and resized to a fixed
  128x128 so the model always receives input of the same shape.
- **Training vs. validation:** the model learns from the training split; the
  validation split (not used for learning) checks progress after each epoch
  and drives early stopping, so the model doesn't just memorize the training
  images.
- **Accuracy:** the percentage of test images the model classified correctly.
- **Confidence/probability:** the model outputs a single number between 0
  and 1 (via a sigmoid); values near 1 mean "looks like tumor", near 0 mean
  "looks like no tumor", and the distance from 0.5 becomes the confidence
  percentage shown in the UI.
- **Limitations:** trained on a small public dataset, so it will not
  generalize to every scanner, imaging protocol, or tumor type, and gives no
  location, size, or tumor-type information - a real diagnostic tool needs
  far more data, clinical validation, and regulatory approval.

## Future improvements

- Train on a larger, more diverse, multi-institution dataset
- Multi-class classification (tumor type, not just presence)
- Explainable AI (e.g. Grad-CAM heatmaps showing which pixels drove the prediction)
- Transfer learning from a medical-imaging pretrained backbone
- Stronger validation protocol (k-fold cross-validation, external test set)
- User accounts and a history of past uploads (with explicit consent and no PHI)

## Viva preparation

See [`docs/VIVA_PREP.md`](docs/VIVA_PREP.md) for a 2-3 minute presentation
script and 20 likely technical questions with concise answers.

## Screenshots

_Add screenshots of the home page, upload flow, and result card here before
submitting._

## License

MIT - see [LICENSE](LICENSE).
