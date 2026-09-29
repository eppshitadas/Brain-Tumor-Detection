const STEPS = [
  { title: "Upload", body: "You choose an MRI slice. It is validated for file type and size before anything else happens." },
  { title: "Preprocess", body: "The image is converted to RGB and resized to 128 x 128 pixels, matching what the model was trained on." },
  { title: "Classify", body: "A convolutional neural network extracts visual features and outputs a tumor probability from 0 to 1." },
  { title: "Explain", body: "The result is shown with its confidence score alongside the model's own test accuracy, for context." },
];

export default function HowItWorks() {
  return (
    <section className="section" id="how-it-works">
      <div className="container">
        <h2>How it works</h2>
        <p className="section-lede">
          A short pipeline connects the upload to a prediction. Each stage is deliberately simple
          enough to explain in a viva.
        </p>
        <ol className="steps-list">
          {STEPS.map((step, i) => (
            <li key={step.title} className="step-item">
              <span className="step-index">{i + 1}</span>
              <div>
                <h3>{step.title}</h3>
                <p>{step.body}</p>
              </div>
            </li>
          ))}
        </ol>
      </div>
    </section>
  );
}
