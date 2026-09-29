export default function ModelInfo({ info }) {
  const metrics = info?.metrics;
  return (
    <section className="section model-section" id="model">
      <div className="container">
        <h2>Model details</h2>
        {!info && (
          <p className="section-lede">Model information will appear here once the backend is reachable.</p>
        )}
        {info && (
          <div className="model-grid">
            <div className="model-card">
              <h3>Architecture</h3>
              <p>{info.architecture}</p>
              <p className="model-sub">Input size: {info.input_size?.join(" x ")}</p>
            </div>
            {metrics ? (
              <>
                <div className="model-card">
                  <h3>Test accuracy</h3>
                  <p className="model-number">{metrics.accuracy}%</p>
                  <p className="model-sub">On {metrics.test_images} held-out images</p>
                </div>
                <div className="model-card">
                  <h3>Precision / Recall</h3>
                  <p className="model-number">{metrics.precision}% / {metrics.recall}%</p>
                  <p className="model-sub">F1 score: {metrics.f1_score}%</p>
                </div>
                <div className="model-card">
                  <h3>Training set</h3>
                  <p className="model-number">{metrics.train_images}</p>
                  <p className="model-sub">images across {metrics.epochs_trained} epochs</p>
                </div>
              </>
            ) : (
              <div className="model-card">
                <h3>Evaluation metrics</h3>
                <p>Not available yet &mdash; train the model to populate this section.</p>
              </div>
            )}
          </div>
        )}
      </div>
    </section>
  );
}
