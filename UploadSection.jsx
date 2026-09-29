import { useCallback, useRef, useState } from "react";
import { predictImage, ApiError } from "../api.js";
import ResultCard from "./ResultCard.jsx";

const MAX_MB = 5;
const ACCEPTED = ["image/jpeg", "image/png", "image/bmp"];

export default function UploadSection({ modelInfo }) {
  const [file, setFile] = useState(null);
  const [previewUrl, setPreviewUrl] = useState(null);
  const [status, setStatus] = useState("idle"); // idle | loading | done | error
  const [result, setResult] = useState(null);
  const [error, setError] = useState("");
  const [dragActive, setDragActive] = useState(false);
  const inputRef = useRef(null);

  const acceptFile = useCallback((candidate) => {
    setError("");
    setResult(null);
    if (!candidate) return;
    if (!ACCEPTED.includes(candidate.type)) {
      setError("Please upload a JPG, PNG or BMP image.");
      return;
    }
    if (candidate.size > MAX_MB * 1024 * 1024) {
      setError(`That file is larger than ${MAX_MB} MB. Please upload a smaller image.`);
      return;
    }
    setFile(candidate);
    setPreviewUrl((old) => {
      if (old) URL.revokeObjectURL(old);
      return URL.createObjectURL(candidate);
    });
    setStatus("idle");
  }, []);

  function onInputChange(e) {
    acceptFile(e.target.files?.[0] ?? null);
  }

  function onDrop(e) {
    e.preventDefault();
    setDragActive(false);
    acceptFile(e.dataTransfer.files?.[0] ?? null);
  }

  async function runPrediction() {
    if (!file) return;
    setStatus("loading");
    setError("");
    try {
      const data = await predictImage(file);
      setResult(data);
      setStatus("done");
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Something went wrong. Please try again.");
      setStatus("error");
    }
  }

  function reset() {
    if (previewUrl) URL.revokeObjectURL(previewUrl);
    setFile(null);
    setPreviewUrl(null);
    setResult(null);
    setError("");
    setStatus("idle");
    if (inputRef.current) inputRef.current.value = "";
  }

  return (
    <section className="section upload-section" id="detect">
      <div className="container">
        <h2>Try it on an MRI image</h2>
        <p className="section-lede">
          The image stays in memory during the request and is discarded immediately after
          prediction &mdash; nothing is stored on the server.
        </p>

        {!result && (
          <div
            className={`dropzone ${dragActive ? "is-active" : ""}`}
            onDragOver={(e) => { e.preventDefault(); setDragActive(true); }}
            onDragLeave={() => setDragActive(false)}
            onDrop={onDrop}
          >
            <input
              ref={inputRef}
              id="mri-input"
              type="file"
              accept="image/jpeg,image/png,image/bmp"
              onChange={onInputChange}
              className="visually-hidden"
            />

            {!previewUrl ? (
              <label htmlFor="mri-input" className="dropzone-label">
                <svg width="40" height="40" viewBox="0 0 24 24" fill="none" aria-hidden="true">
                  <path d="M12 16V4m0 0 4 4m-4-4-4 4" stroke="#5FB3AA" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" />
                  <path d="M4 16v2a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2v-2" stroke="#5FB3AA" strokeWidth="1.8" strokeLinecap="round" />
                </svg>
                <span className="dropzone-title">Drag an MRI image here, or click to browse</span>
                <span className="dropzone-hint">JPG, PNG or BMP, up to {MAX_MB} MB</span>
              </label>
            ) : (
              <div className="preview-block">
                <img src={previewUrl} alt="Preview of the uploaded MRI scan" className="preview-img" />
                <div className="preview-actions">
                  <p className="file-name">{file.name}</p>
                  <div className="preview-buttons">
                    <button type="button" className="btn btn-quiet" onClick={() => inputRef.current?.click()}>
                      Choose a different image
                    </button>
                    <button
                      type="button"
                      className="btn btn-primary"
                      onClick={runPrediction}
                      disabled={status === "loading"}
                    >
                      {status === "loading" ? "Analyzing..." : "Run detection"}
                    </button>
                  </div>
                </div>
              </div>
            )}
          </div>
        )}

        {status === "loading" && (
          <div className="loading-row" role="status" aria-live="polite">
            <span className="spinner" aria-hidden="true" />
            Running the image through the model...
          </div>
        )}

        {error && (
          <p className="error-banner" role="alert">{error}</p>
        )}

        {result && (
          <ResultCard result={result} previewUrl={previewUrl} modelInfo={modelInfo} onReset={reset} />
        )}
      </div>
    </section>
  );
}
