
import React, { useState } from "react";
import "./App.css";

export default function App() {
  const [topic, setTopic] = useState("");
  const [numSlides, setNumSlides] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [downloadUrl, setDownloadUrl] = useState("");

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");
    setDownloadUrl("");
    if (!topic || !numSlides) {
      setError("Please enter both topic and number of slides.");
      return;
    }
    setLoading(true);
    try {
      const response = await fetch("/generate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ topic, num_slides: numSlides }),
      });
      if (!response.ok) {
        throw new Error("Failed to generate presentation.");
      }
      const data = await response.json();
      setDownloadUrl(`/download/${data.filename}`);
    } catch (err) {
      setError(err.message || "Something went wrong.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="ppt-bg dark-theme">
      <header className="ppt-hero dark-hero">
        <div className="ppt-logo">🦾</div>
        <h1>AgentSlides</h1>
        <div className="ppt-sub">Generate professional presentations instantly</div>
      </header>
      <main>
        <form className="ppt-form goated-glass dark-glass" onSubmit={handleSubmit}>
          <label>
            Topic
            <input
              type="text"
              value={topic}
              onChange={(e) => setTopic(e.target.value)}
              placeholder="Enter your topic..."
              required
            />
          </label>
          <label>
            Number of Slides
            <input
              type="number"
              min="1"
              max="30"
              value={numSlides}
              onChange={(e) => setNumSlides(e.target.value)}
              placeholder="e.g. 7"
              required
            />
          </label>
          {error && <div className="ppt-error">{error}</div>}
          <button className="goated-btn dark-btn" type="submit" disabled={loading}>
            {loading ? <span className="ppt-spinner" /> : "Generate PPT"}
          </button>
        </form>
        {downloadUrl && (
          <a className="ppt-download dark-download" href={downloadUrl} download>
            Download Presentation
          </a>
        )}
      </main>
      <footer className="ppt-footer dark-footer">
        &copy; {new Date().getFullYear()} AgentSlides &mdash; Powered by HuggingFaceLLM
      </footer>
    </div>
  );
}
// (Removed duplicate/erroneous JSX and export)
