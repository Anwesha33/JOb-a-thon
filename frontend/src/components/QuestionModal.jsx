import { useState } from "react";

// Shown when an application asked something the tool couldn't answer from the
// resume. The answer is stored for a week, so it's asked only once.
export default function QuestionModal({ item, onSave, onSkip }) {
  const [answer, setAnswer] = useState("");
  const [saving, setSaving] = useState(false);

  if (!item) return null;

  async function save() {
    if (!answer.trim()) return;
    setSaving(true);
    try {
      await onSave(item, answer.trim());
    } finally {
      setSaving(false);
    }
  }

  return (
    <div className="modal-backdrop">
      <div className="modal">
        <h3>We need your input</h3>
        <p className="modal-context">
          {item.company} · {item.title}
        </p>
        <p className="modal-q">{item.question}</p>
        <textarea
          rows={3}
          value={answer}
          onChange={(e) => setAnswer(e.target.value)}
          placeholder="Your answer (remembered for 7 days)"
          autoFocus
        />
        <div className="modal-actions">
          <button className="ghost" onClick={onSkip} disabled={saving}>
            Skip
          </button>
          <button onClick={save} disabled={saving || !answer.trim()}>
            {saving ? "Saving…" : "Save & remember"}
          </button>
        </div>
      </div>
    </div>
  );
}
