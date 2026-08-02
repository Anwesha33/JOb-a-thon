import { useState } from "react";

// Role, location, and (optional) specific companies are all entered here, so
// the tool stays generic — nothing about the search is hardcoded.
export default function SearchForm({ disabled, onSearch, busy, detectedExperience }) {
  const [role, setRole] = useState("");
  const [location, setLocation] = useState("");
  const [country, setCountry] = useState("in");
  const [companies, setCompanies] = useState("");
  const [limit, setLimit] = useState(100);
  const [experience, setExperience] = useState("");

  function submit(e) {
    e.preventDefault();
    const exp = experience.trim();
    onSearch({
      role: role.trim() || null,
      location: location.trim() || null,
      country: country.trim() || null,
      limit: Number(limit) || 100,
      experience_years: exp === "" ? null : Number(exp),
      companies: companies
        .split(",")
        .map((c) => c.trim())
        .filter(Boolean),
    });
  }

  return (
    <section className="card">
      <h2>2 · Find openings</h2>
      <form onSubmit={submit} className="search-form">
        <label>
          Role / profile
          <input
            value={role}
            onChange={(e) => setRole(e.target.value)}
            placeholder="e.g. Backend Engineer (blank uses your resume)"
          />
        </label>
        <label>
          Location
          <input
            value={location}
            onChange={(e) => setLocation(e.target.value)}
            placeholder="e.g. Bengaluru or Remote"
          />
        </label>
        <label>
          Country
          <input
            value={country}
            onChange={(e) => setCountry(e.target.value)}
            placeholder="in"
          />
        </label>
        <label>
          Specific companies (optional, comma-separated)
          <input
            value={companies}
            onChange={(e) => setCompanies(e.target.value)}
            placeholder="e.g. Razorpay, Zomato — leave blank for any"
          />
        </label>
        <label>
          Years of experience
          <input
            type="number"
            min="0"
            max="50"
            step="0.5"
            value={experience}
            onChange={(e) => setExperience(e.target.value)}
            placeholder={
              detectedExperience != null
                ? `blank uses resume (~${detectedExperience} yrs)`
                : "blank uses your resume"
            }
          />
        </label>
        <label>
          Target count
          <input
            type="number"
            min="1"
            max="100"
            value={limit}
            onChange={(e) => setLimit(e.target.value)}
          />
        </label>
        <button type="submit" disabled={disabled || busy}>
          {busy ? "Searching…" : "Search openings"}
        </button>
      </form>
      <p className="hint">
        Only openings posted in the last 30 days are shown. Experience filters
        out openings that are clearly the wrong seniority.
      </p>
    </section>
  );
}
