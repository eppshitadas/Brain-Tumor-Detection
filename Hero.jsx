function ScanIllustration() {
  const grid = [40, 80, 120, 160, 200, 240, 280];
  return (
    <svg className="scan-art" viewBox="0 0 320 320" role="img" aria-label="Illustration of a brain MRI slice being scanned">
      <rect width="320" height="320" rx="12" fill="#0E2530" />
      <g stroke="#1F3D4C" strokeWidth="1">
        {grid.map((n) => (
          <g key={n}>
            <line x1={n} y1="0" x2={n} y2="320" />
            <line x1="0" y1={n} x2="320" y2={n} />
          </g>
        ))}
      </g>
      <ellipse cx="160" cy="160" rx="112" ry="126" fill="#1B3B4B" stroke="#5FB3AA" strokeWidth="2" />
      <g fill="none" stroke="#33606F" strokeWidth="3" strokeLinecap="round">
        <path d="M78 130c14-10 22-4 30-16M84 190c16 6 24-2 32-12M110 84c10 8 20 4 28-6M212 84c-10 8-20 4-28-6M242 130c-14-10-22-4-30-16M236 190c-16 6-24-2-32-12M112 244c12-8 22-4 32 4M208 244c-12-8-22-4-32 4" />
      </g>
      <path d="M160 46v268" stroke="#0E2530" strokeWidth="3" />
      <path d="M137 148c8-26 20-26 23-4 3-22 15-22 23 4-2 38-12 50-23 52-11-2-21-14-23-52z" fill="#0E2530" />
      <g stroke="#7FE0D2" strokeWidth="2">
        <path d="M10 22V10h12M298 10h12v12M310 298v12h-12M22 310H10v-12" fill="none" />
      </g>
      <text x="22" y="304" fill="#8FB5BF" fontSize="11" fontFamily="Public Sans, system-ui, sans-serif">Axial slice, 128 x 128 px input</text>
      <rect className="scan-line" x="0" y="0" width="320" height="3" fill="#7FE0D2" opacity="0.85" />
    </svg>
  );
}

export default function Hero() {
  return (
    <section className="hero" id="top">
      <div className="container hero-grid">
        <div className="hero-copy">
          <h1>Brain Tumor Detection System</h1>
          <p className="lede">
            Upload a brain MRI slice and a convolutional neural network estimates whether it
            resembles the tumor scans it was trained on. Built as a college project with React,
            Flask and TensorFlow.
          </p>
          <div className="hero-actions">
            <a className="btn btn-primary" href="#detect">Upload MRI</a>
            <a className="btn btn-quiet" href="#how-it-works">See how it works</a>
          </div>
          <p className="fine-print">
            Educational project. Results are not a medical diagnosis and must not be used for
            health decisions.
          </p>
        </div>
        <ScanIllustration />
      </div>
    </section>
  );
}
