import { useEffect, useRef, useState } from "react";
import { api } from "./api.js";
import ResumeUpload from "./components/ResumeUpload.jsx";
import SearchForm from "./components/SearchForm.jsx";
import OpportunityList from "./components/OpportunityList.jsx";
import ApplyPanel from "./components/ApplyPanel.jsx";
import ApplyFromLink from "./components/ApplyFromLink.jsx";
import QuestionModal from "./components/QuestionModal.jsx";
import Dashboard from "./components/Dashboard.jsx";

const TERMINAL = new Set(["done", "error"]);

export default function App() {
  const [profile, setProfile] = useState(null);
  const [opportunities, setOpportunities] = useState([]);
  const [selected, setSelected] = useState(new Set());
  const [budget, setBudget] = useState(null);
  const [searching, setSearching] = useState(false);
  const [error, setError] = useState("");

  const [jobs, setJobs] = useState({}); // oppId -> job
  const [questionQueue, setQuestionQueue] = useState([]); // {oppId, company, title, question}
  const seenQuestions = useRef(new Set()); // `${oppId}::${question}` already queued

  const [view, setView] = useState("search"); // "search" | "dashboard"
  const [dashKey, setDashKey] = useState(0); // bump to refresh the dashboard

  useEffect(() => {
    api.budget().then(setBudget).catch(() => {});
    api.listOpportunities().then(setOpportunities).catch(() => {});
  }, []);

  // Poll any non-terminal apply jobs.
  useEffect(() => {
    const active = Object.values(jobs).filter((j) => !TERMINAL.has(j.status));
    if (active.length === 0) return;
    const timer = setInterval(async () => {
      for (const j of active) {
        try {
          const s = await api.applyStatus(j.jobId);
          setJobs((prev) => ({
            ...prev,
            [j.oppId]: { ...prev[j.oppId], status: s.status, message: s.message },
          }));
          for (const q of s.pending_questions || []) {
            const key = `${j.oppId}::${q}`;
            if (!seenQuestions.current.has(key)) {
              seenQuestions.current.add(key);
              setQuestionQueue((prev) => [
                ...prev,
                { oppId: j.oppId, company: j.company, title: j.title, question: q },
              ]);
            }
          }
        } catch (_) {
          /* keep polling */
        }
      }
    }, 2500);
    return () => clearInterval(timer);
  }, [jobs]);

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
        setError(
          res.budget?.remaining === 0
            ? `Today's company budget is used up (${res.budget.limit}/${res.budget.limit}). ` +
              "New companies unlock tomorrow — or raise DAILY_COMPANY_LIMIT in .env."
            : "No fresh openings found. Try a broader role or location."
        );
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

  async function applySelected() {
    if (!profile || selected.size === 0) return;
    setError("");
    const chosen = opportunities.filter((o) => selected.has(o.id));
    for (const o of chosen) {
      if (jobs[o.id]) continue; // already applying
      try {
        const res = await api.startApply({
          opportunity_id: o.id,
          profile_id: profile.id,
        });
        setJobs((prev) => ({
          ...prev,
          [o.id]: {
            oppId: o.id,
            jobId: res.job_id,
            company: o.company,
            title: o.title,
            status: res.status,
            message: "",
          },
        }));
      } catch (err) {
        setError(`Couldn't start apply for ${o.company}: ${err.message}`);
      }
    }
    setDashKey((k) => k + 1); // newly-applied jobs appear on the dashboard
  }

  async function applyFromLink(url) {
    if (!profile) {
      setError("Upload a resume first.");
      return;
    }
    setError("");
    let host = "job link";
    try {
      host = new URL(url).hostname.replace(/^www\./, "");
    } catch (_) {
      /* keep default */
    }
    try {
      const res = await api.applyLink(url, profile.id);
      const key = `link:${res.job_id}`;
      setJobs((prev) => ({
        ...prev,
        [key]: {
          oppId: key,
          jobId: res.job_id,
          company: host,
          title: "Job from link",
          status: res.status,
          message: "",
        },
      }));
    } catch (err) {
      setError(`Couldn't apply from that link: ${err.message}`);
    }
  }

  async function saveAnswer(item, answer) {
    await api.answerQuestion(item.question, answer);
    setQuestionQueue((prev) => prev.filter((q) => q !== item));
  }

  function skipAnswer(item) {
    setQuestionQueue((prev) => prev.filter((q) => q !== item));
  }

  return (
    <div className="app">
      <header className="topbar">
        <h1>JOb-a-thon</h1>
        <p>Find recent openings from your resume, then apply to the ones you pick.</p>
        {budget && view === "search" && (
          <div className="budget">
            Today's company budget: {budget.companies_used}/{budget.limit} used ·{" "}
            {budget.remaining} left
          </div>
        )}
        <nav className="tabs">
          <button
            className={view === "search" ? "tab active" : "tab"}
            onClick={() => setView("search")}
          >
            Find &amp; apply
          </button>
          <button
            className={view === "dashboard" ? "tab active" : "tab"}
            onClick={() => {
              setView("dashboard");
              setDashKey((k) => k + 1);
            }}
          >
            Dashboard
          </button>
        </nav>
      </header>

      {error && <div className="banner error">{error}</div>}

      {view === "search" ? (
        <>
          <ResumeUpload profile={profile} onProfile={setProfile} />
          <SearchForm
            disabled={!profile}
            busy={searching}
            onSearch={handleSearch}
            detectedExperience={profile?.experience_years}
          />
          <OpportunityList
            opportunities={opportunities}
            selected={selected}
            onToggle={toggle}
            onToggleAll={toggleAll}
          >
            <span className="selected-count">{selected.size} selected</span>
            <button onClick={applySelected} disabled={selected.size === 0}>
              Apply to selected ({selected.size})
            </button>
          </OpportunityList>

          <ApplyFromLink disabled={!profile} onApply={applyFromLink} />

          <ApplyPanel jobs={jobs} />

          <QuestionModal
            item={questionQueue[0]}
            onSave={saveAnswer}
            onSkip={() => skipAnswer(questionQueue[0])}
          />
        </>
      ) : (
        <Dashboard refreshKey={dashKey} />
      )}
    </div>
  );
}
