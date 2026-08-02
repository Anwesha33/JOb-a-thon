import { useState } from "react";

// Role, location, and (optional) specific companies are all entered here, so
// the tool stays generic — nothing about the search is hardcoded.
export default function SearchForm({ disabled, onSearch, busy }) {
  const [role, setRole] = useState("");
  const [location, setLocation] = useState("");
  const [country, setCountry] = useState("in");
  const [companies, setCompanies] = useState("");
  const [limit, setLimit] = useState(100);

  function submit(e) {
    e.preventDefault();
    onSearch({
      role: role.trim() || null,
      location: location.trim() || null,
      country: country.trim() || null,
      limit: Number(limit) || 100,
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
        Only openings posted in the last 30 days are shown, and at most 10 new
        companies are searched per day.
      </p>
    </section>
  );
}
