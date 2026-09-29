import { useEffect, useState } from "react";
import { getModelInfo } from "./api.js";
import Navbar from "./components/Navbar.jsx";
import Hero from "./components/Hero.jsx";
import UploadSection from "./components/UploadSection.jsx";
import HowItWorks from "./components/HowItWorks.jsx";
import ModelInfo from "./components/ModelInfo.jsx";
import TechStack from "./components/TechStack.jsx";
import Footer from "./components/Footer.jsx";

export default function App() {
  const [modelInfo, setModelInfo] = useState(null);

  useEffect(() => {
    getModelInfo()
      .then(setModelInfo)
      .catch(() => setModelInfo(null)); // the page still works without this
  }, []);

  return (
    <>
      <a className="skip-link" href="#detect">Skip to the upload tool</a>
      <Navbar />
      <main>
        <Hero />
        <UploadSection modelInfo={modelInfo} />
        <HowItWorks />
        <ModelInfo info={modelInfo} />
        <TechStack />
      </main>
      <Footer />
    </>
  );
}
