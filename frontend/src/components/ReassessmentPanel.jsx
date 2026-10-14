import { useEffect, useState } from "react";

const LEVELS = [
  "0 – None (No prior experience)",
  "1 – Beginner (Basic concepts)",
  "2 – Basic (Can build simple tasks)",
  "3 – Intermediate (Working proficiency)",
  "4 – Advanced (Production ready)",
  "5 – Expert (Mastery & mentorship)",
];

export default function ReassessmentPanel({ skills, needsReassessment = [], onSubmit, busy }) {
  const [draft, setDraft] = useState({}); // only the skills the student changed

  useEffect(() => setDraft({}), [skills]); // reset when fresh data arrives

  const touched = Object.keys(draft).length;

  return (
    <div className="card" style={{ marginTop: "28px" }}>
      <div style={{ marginBottom: "16px" }}>
        <h3 style={{ fontSize: "1.15rem", fontWeight: 700, color: "var(--navy-900)" }}>
          🎯 Update Skill Proficiency
        </h3>
        <p className="muted small" style={{ marginTop: "4px" }}>
          Finished learning a skill or completed roadmap modules? Re-rate your level honestly. A skill counts as achieved only when your level meets or exceeds the target.
        </p>
      </div>

      {needsReassessment.length > 0 && (
        <div className="banner-warning" style={{ background: "#f0fdf4", borderColor: "#bbf7d0", borderLeftColor: "#16a34a", color: "#166534" }}>
          <div className="banner-warning-icon">🎉</div>
          <div className="banner-warning-body">
            <strong style={{ color: "#14532d" }}>Learning Activities Completed!</strong>
            You completed activities for: <strong>{needsReassessment.join(", ")}</strong>. Re-rate your proficiency below to confirm your new skill level and update your readiness score.
          </div>
        </div>
      )}

      <div className="reassess-grid">
        {skills.map((s) => {
          const isPendingReassess = needsReassessment.includes(s.name);
          const currentVal = draft[s.name] ?? s.current_level;
          const isChanged = draft[s.name] !== undefined;

          return (
            <div
              key={s.name}
              className={`reassess-item ${isPendingReassess ? "needs-attention" : ""}`}
            >
              <div style={{ minWidth: "200px", flex: 1 }}>
                <div style={{ display: "flex", alignItems: "center", gap: "8px", flexWrap: "wrap", marginBottom: "4px" }}>
                  <strong style={{ fontSize: "0.98rem", color: "var(--navy-900)" }}>{s.name}</strong>
                  <span className="badge" style={{ background: "#e0e7ff", color: "#3730a3", fontSize: "0.75rem" }}>
                    Target: Level {s.target_level}
                  </span>
                  {isPendingReassess && (
                    <span className="badge badge-improve" style={{ fontSize: "0.75rem" }}>
                      Ready to confirm
                    </span>
                  )}
                  {!s.assessed && (
                    <span className="badge badge-gap" style={{ fontSize: "0.75rem" }}>
                      Not assessed yet
                    </span>
                  )}
                  {isChanged && (
                    <span className="badge badge-achieved" style={{ fontSize: "0.75rem" }}>
                      Changed
                    </span>
                  )}
                </div>
                <div className="muted small">
                  Current Level: <strong>Level {s.current_level}</strong> · Gap: <strong>{s.gap} levels</strong>
                </div>
              </div>

              <div style={{ minWidth: "220px", display: "flex", alignItems: "center", gap: "10px" }}>
                <select
                  value={currentVal}
                  onChange={(e) => setDraft({ ...draft, [s.name]: Number(e.target.value) })}
                  style={{
                    padding: "8px 12px",
                    borderRadius: "8px",
                    border: isChanged ? "2px solid var(--blue-600)" : "1px solid #cbd5e1",
                    fontSize: "0.88rem",
                    fontFamily: "inherit",
                    background: isChanged ? "var(--blue-50)" : "#fff",
                    fontWeight: isChanged ? 600 : 400,
                    width: "100%",
                  }}
                >
                  {LEVELS.map((label, idx) => (
                    <option key={idx} value={idx}>
                      {label}
                    </option>
                  ))}
                </select>
              </div>
            </div>
          );
        })}
      </div>

      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginTop: "18px", flexWrap: "wrap", gap: "12px" }}>
        <span className="muted small">
          {touched > 0 ? (
            <span style={{ color: "var(--blue-600)", fontWeight: 600 }}>
              {touched} skill{touched > 1 ? "s" : ""} modified (unsaved)
            </span>
          ) : (
            "Select new levels above to update your proficiency profile"
          )}
        </span>

        <button
          className="btn btn-primary"
          disabled={busy || touched === 0}
          onClick={() => onSubmit(draft)}
          style={{ minWidth: "180px" }}
        >
          {busy ? (
            <>
              <span className="spinner" style={{ width: "16px", height: "16px", borderWidth: "2px" }} />
              Saving changes…
            </>
          ) : (
            `Save Updated Proficiency${touched > 0 ? ` (${touched})` : ""}`
          )}
        </button>
      </div>
    </div>
  );
}