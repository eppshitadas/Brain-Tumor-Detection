import { useState } from "react";

const LINKS = [
  ["#detect", "Detect"],
  ["#how-it-works", "How it works"],
  ["#model", "Model"],
  ["#stack", "Tech stack"],
];

export default function Navbar() {
  const [open, setOpen] = useState(false);
  return (
    <header className="navbar">
      <div className="container navbar-inner">
        <a className="brand" href="#top" aria-label="Brain Tumor Detection System, home">
          <svg width="28" height="28" viewBox="0 0 64 64" aria-hidden="true">
            <rect width="64" height="64" rx="14" fill="#0E2530" />
            <ellipse cx="32" cy="32" rx="19" ry="22" fill="#1B3B4B" stroke="#5FB3AA" strokeWidth="3" />
            <path d="M32 12v40" stroke="#0E2530" strokeWidth="3" />
          </svg>
          <span>Brain Tumor Detection</span>
        </a>
        <nav className={`nav-links ${open ? "is-open" : ""}`} aria-label="Main">
          {LINKS.map(([href, label]) => (
            <a key={href} href={href} onClick={() => setOpen(false)}>{label}</a>
          ))}
        </nav>
        <button
          className="menu-btn"
          aria-expanded={open}
          aria-label="Toggle navigation menu"
          onClick={() => setOpen((v) => !v)}
        >
          {open ? "Close" : "Menu"}
        </button>
      </div>
    </header>
  );
}
