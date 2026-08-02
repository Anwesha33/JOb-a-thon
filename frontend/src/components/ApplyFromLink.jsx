import { useState } from "react";

// Paste a LinkedIn (or direct) job URL. The engine opens it, follows a
// LinkedIn "Apply" button through to the company portal, and auto-fills there.
export default function ApplyFromLink({ disabled, onApply }) {
  const [url, setUrl] = useState("");

  function submit(e) {
    e.preventDefault();
    const u = url.trim();
    if (!u) return;
    onApply(u);
    setUrl("");
  }

  return (
    <section className="card">
      <h2>Apply from a job link</h2>
      <form onSubmit={submit} className="link-form">
        <input
          value={url}
          onChange={(e) => setUrl(e.target.value)}
          placeholder="Paste a LinkedIn job URL or a direct application link"
        />
        <button type="submit" disabled={disabled || !url.trim()}>
          Open &amp; apply
        </button>
      </form>
      <p className="hint">
        A browser opens the link. For a LinkedIn post it follows the “Apply”
        button to the company site and fills the form; for LinkedIn “Easy Apply”
        (login-walled) it opens the page for you to finish.
      </p>
    </section>
  );
}
