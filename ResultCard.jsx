export default function ResultCard({ result, previewUrl, modelInfo, onReset }) {
  const isTumor = result.prediction === "Tumor Detected";
  const accuracy = modelInfo?.metrics?.accuracy;

  return (
    <div className={`result-card ${isTumor ? "is-tumor" : "is-clear"}`}>
      <img src={previewUrl} alt="Analyzed MRI scan" className="result-img" />
      <div className="result-body">
        <span className="result-badge">{result.prediction}</span>
        <div className="confidence-row">
          <div className="confidence-track" aria-hidden="true">
            <div className="confidence-fill" style={{ width: `${result.confidence}%` }} />
          </div>
          <span className="confidence-value">{result.confidence}% confidence</span>
        </div>

        <p className="result-explainer">
          {isTumor
            ? "The model found patterns in this scan similar to the tumor-labeled images it was trained on."
            : "The model did not find patterns in this scan matching the tumor-labeled images it was trained on."}
          {" "}This is a probability from a student CNN, not a clinical finding.
        </p>

        <dl className="result-meta">
          <div>
            <dt>Tumor probability</dt>
            <dd>{result.probabilities.tumor}%</dd>
          </div>
          <div>
            <dt>No-tumor probability</dt>
            <dd>{result.probabilities.no_tumor}%</dd>
          </div>
          {accuracy !== undefined && (
            <div>
              <dt>Model test accuracy</dt>
              <dd>{accuracy}%</dd>
            </div>
          )}
        </dl>

        <p className="disclaimer-inline">{result.disclaimer}</p>
        <button type="button" className="btn btn-primary" onClick={onReset}>
          Analyze another image
        </button>
      </div>
    </div>
  );
}
