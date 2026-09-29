const STACK = [
  ["Frontend", "React + Vite"],
  ["Backend", "Flask REST API"],
  ["Model", "TensorFlow / Keras CNN"],
  ["Hosting", "Vercel + Render or Hugging Face Spaces"],
];

export default function TechStack() {
  return (
    <section className="section" id="stack">
      <div className="container">
        <h2>Technology stack</h2>
        <div className="stack-grid">
          {STACK.map(([label, value]) => (
            <div key={label} className="stack-item">
              <span className="stack-label">{label}</span>
              <span className="stack-value">{value}</span>
            </div>
          ))}
        </div>
        <p className="disclaimer-block">
          This is an educational, research-style project. It is not a certified medical device
          and its predictions must never be used to diagnose or rule out a medical condition.
        </p>
      </div>
    </section>
  );
}
