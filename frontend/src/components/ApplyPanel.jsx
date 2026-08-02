const LABELS = {
  pending: "Starting…",
  filling: "Auto-filling the form…",
  awaiting_user: "Ready — finish in the browser window",
  done: "Done",
  error: "Couldn't apply",
};

export default function ApplyPanel({ jobs }) {
  const entries = Object.values(jobs);
  if (entries.length === 0) return null;

  return (
    <section className="card">
      <h2>4 · Applications in progress</h2>
      <ul className="jobs">
        {entries.map((j) => (
          <li key={j.oppId} className={`job job-${j.status}`}>
            <div className="job-title">
              {j.title} <span className="company">· {j.company}</span>
            </div>
            <div className="job-status">
              <span className={`dot dot-${j.status}`} />
              {LABELS[j.status] || j.status}
            </div>
            {j.message && <p className="job-msg">{j.message}</p>}
          </li>
        ))}
      </ul>
    </section>
  );
}
