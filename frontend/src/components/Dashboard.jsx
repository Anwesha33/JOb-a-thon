import { useEffect, useState } from "react";
import { api } from "../api.js";

function fmtDate(s) {
  if (!s) return "";
  const d = new Date(s.replace(" ", "T") + "Z");
  return d.toLocaleDateString(undefined, {
    day: "numeric",
    month: "short",
    year: "numeric",
  });
}

export default function Dashboard({ refreshKey }) {
  const [data, setData] = useState(null);
  const [error, setError] = useState("");

  async function load() {
    try {
      setData(await api.listApplications());
    } catch (err) {
      setError(err.message);
    }
  }

  useEffect(() => {
    load();
  }, [refreshKey]);

  async function changeStatus(id, status) {
    // Optimistic update, then reconcile.
    setData((d) => ({
      ...d,
      applications: d.applications.map((a) =>
        a.id === id ? { ...a, status } : a
      ),
    }));
    try {
      await api.updateApplicationStatus(id, status);
      await load();
    } catch (err) {
      setError(err.message);
    }
  }

  if (error) return <div className="banner error">{error}</div>;
  if (!data) return <section className="card">Loading applications…</section>;

  const { applications, summary, statuses } = data;

  return (
    <section className="card">
      <div className="list-header">
        <h2>Applications</h2>
        <div className="summary-chips">
          <span className="chip total">Total {summary.total}</span>
          {statuses.map((s) => (
            <span className={`chip status-${s}`} key={s}>
              {s} {summary[s]}
            </span>
          ))}
        </div>
      </div>

      {applications.length === 0 ? (
        <p className="hint">
          Nothing applied to yet. Find openings, select them, and hit “Apply to
          selected” — they'll show up here.
        </p>
      ) : (
        <table className="apps-table">
          <thead>
            <tr>
              <th>Company</th>
              <th>Role</th>
              <th>Applied</th>
              <th>Status</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            {applications.map((a) => (
              <tr key={a.id}>
                <td>{a.company}</td>
                <td className="role-cell">{a.title}</td>
                <td className="nowrap">{fmtDate(a.applied_at)}</td>
                <td>
                  <select
                    className={`status-select status-${a.status}`}
                    value={statuses.includes(a.status) ? a.status : "applied"}
                    onChange={(e) => changeStatus(a.id, e.target.value)}
                  >
                    {statuses.map((s) => (
                      <option value={s} key={s}>
                        {s}
                      </option>
                    ))}
                  </select>
                </td>
                <td>
                  <a href={a.url} target="_blank" rel="noreferrer" className="view-link">
                    View
                  </a>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </section>
  );
}
