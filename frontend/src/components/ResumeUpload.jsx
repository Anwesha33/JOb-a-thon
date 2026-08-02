import { useState } from "react";
import { api } from "../api.js";

export default function ResumeUpload({ profile, onProfile }) {
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  async function handleFile(e) {
    const file = e.target.files?.[0];
    if (!file) return;
    setBusy(true);
    setError("");
    try {
      const p = await api.uploadResume(file);
      onProfile(p);
    } catch (err) {
      setError(err.message);
    } finally {
      setBusy(false);
    }
  }

  return (
    <section className="card">
      <h2>1 · Your resume</h2>
      <label className="file-drop">
        <input
          type="file"
          accept=".pdf,.docx,.txt,.md"
          onChange={handleFile}
          disabled={busy}
        />
        {busy ? "Reading resume…" : "Choose a PDF / DOCX / TXT resume"}
      </label>
      {error && <p className="error">{error}</p>}
      {profile && (
        <div className="profile-summary">
          <strong>{profile.name || "Resume loaded"}</strong>
          {profile.headline && <span> · {profile.headline}</span>}
          {profile.skills?.length > 0 && (
            <div className="chips">
              {profile.skills.slice(0, 12).map((s) => (
                <span className="chip" key={s}>
                  {s}
                </span>
              ))}
            </div>
          )}
        </div>
      )}
    </section>
  );
}
