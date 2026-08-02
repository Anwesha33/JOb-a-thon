import { useEffect, useState } from "react";
import { api } from "./api.js";
import ResumeUpload from "./components/ResumeUpload.jsx";
import SearchForm from "./components/SearchForm.jsx";
import OpportunityList from "./components/OpportunityList.jsx";

export default function App() {
  const [profile, setProfile] = useState(null);
  const [opportunities, setOpportunities] = useState([]);
  const [selected, setSelected] = useState(new Set());
  const [budget, setBudget] = useState(null);
  const [searching, setSearching] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    api.budget().then(setBudget).catch(() => {});
    api.listOpportunities().then(setOpportunities).catch(() => {});
  }, []);

  async function handleSearch(payload) {
    if (!profile) {
      setError("Upload a resume first.");
      return;
    }
    setSearching(true);
    setError("");
    try {
      const res = await api.search({ ...payload, profile_id: profile.id });
      setOpportunities(res.opportunities);
      setBudget(res.budget);
      setSelected(new Set());
      if (res.count === 0) {
        setError("No fresh openings found. Try a broader role or location.");
      }
    } catch (err) {
      setError(err.message);
    } finally {
      setSearching(false);
    }
  }

  function toggle(id) {
    setSelected((prev) => {
      const next = new Set(prev);
      next.has(id) ? next.delete(id) : next.add(id);
      return next;
    });
  }

  function toggleAll(checked) {
    setSelected(checked ? new Set(opportunities.map((o) => o.id)) : new Set());
  }

  return (
    <div className="app">
      <header className="topbar">
        <h1>JOb-a-thon</h1>
        <p>Find recent openings from your resume, then apply to the ones you pick.</p>
        {budget && (
          <div className="budget">
            Today's company budget: {budget.companies_used}/{budget.limit} used ·{" "}
            {budget.remaining} left
          </div>
        )}
      </header>

      {error && <div className="banner error">{error}</div>}

      <ResumeUpload profile={profile} onProfile={setProfile} />
      <SearchForm disabled={!profile} busy={searching} onSearch={handleSearch} />
      <OpportunityList
        opportunities={opportunities}
        selected={selected}
        onToggle={toggle}
        onToggleAll={toggleAll}
      >
        <span className="selected-count">{selected.size} selected</span>
      </OpportunityList>
    </div>
  );
}
