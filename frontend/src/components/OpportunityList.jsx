function daysAgo(dateStr) {
  if (!dateStr) return null;
  const posted = new Date(dateStr);
  const diff = Math.floor((Date.now() - posted.getTime()) / 86400000);
  if (diff <= 0) return "today";
  if (diff === 1) return "1 day ago";
  return `${diff} days ago`;
}

function salary(o) {
  if (!o.salary_min && !o.salary_max) return null;
  const fmt = (n) => (n ? Math.round(n).toLocaleString() : "?");
  return `${fmt(o.salary_min)}–${fmt(o.salary_max)}`;
}

export default function OpportunityList({
  opportunities,
  selected,
  onToggle,
  onToggleAll,
  children,
}) {
  if (opportunities.length === 0) return null;

  const allSelected = opportunities.every((o) => selected.has(o.id));

  return (
    <section className="card">
      <div className="list-header">
        <h2>3 · Pick where to apply</h2>
        <div className="list-actions">
          <label className="select-all">
            <input
              type="checkbox"
              checked={allSelected}
              onChange={(e) => onToggleAll(e.target.checked)}
            />
            Select all ({opportunities.length})
          </label>
          {children}
        </div>
      </div>

      <ul className="opps">
        {opportunities.map((o) => {
          const age = daysAgo(o.posted_date);
          const pay = salary(o);
          return (
            <li key={o.id} className={selected.has(o.id) ? "opp selected" : "opp"}>
              <input
                type="checkbox"
                checked={selected.has(o.id)}
                onChange={() => onToggle(o.id)}
              />
              <div className="opp-body">
                <div className="opp-title">
                  <a href={o.url} target="_blank" rel="noreferrer">
                    {o.title}
                  </a>
                  <span className="company">{o.company}</span>
                </div>
                <div className="opp-meta">
                  {o.location && <span>{o.location}</span>}
                  {age && <span className="posted">Posted {age}</span>}
                  {pay && <span>{pay}</span>}
                  {o.status && o.status !== "new" && (
                    <span className={`status status-${o.status}`}>{o.status}</span>
                  )}
                </div>
                {o.description && <p className="opp-desc">{o.description}</p>}
              </div>
            </li>
          );
        })}
      </ul>
    </section>
  );
}
