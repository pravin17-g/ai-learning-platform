import { useCallback, useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { getDashboard, getMyProgress, reassess } from "../api/progress";
import { updateActivity } from "../api/roadmap";
import { ProgressChart } from "../components/Charts";
import ErrorBox from "../components/ErrorBox";
import ReassessmentPanel from "../components/ReassessmentPanel";
import ProgressBar from "../components/ProgressBar";
import LoadingIndicator from "../components/LoadingIndicator";

const STATUS_LABELS = {
  not_started: "Not Started",
  in_progress: "In Progress",
  completed: "Completed",
};

export default function ProgressTracker() {
  const [plan, setPlan] = useState(null); // null = no roadmap yet
  const [dash, setDash] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [notice, setNotice] = useState("");
  const [savingId, setSavingId] = useState(null);
  const [reassessBusy, setReassessBusy] = useState(false);
  const [statusFilter, setStatusFilter] = useState("all");

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const [d, p] = await Promise.all([getDashboard(), getMyProgress()]);
      setDash(d);
      setPlan(p);
    } catch (e) {
      setError(e);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  const handleStatus = async (activity, status) => {
    setSavingId(activity.id);
    setError(null);
    setNotice("");
    try {
      const updated = await updateActivity(
        activity.id,
        status,
        status === "in_progress" ? activity.hours_completed : undefined
      );
      setPlan(updated);
      setDash(await getDashboard()); // keeps "needs reassessment" and recommendations current
    } catch (e) {
      setError(e);
      if (e.status === 409) load(); // roadmap was replaced elsewhere: show the current one
    } finally {
      setSavingId(null);
    }
  };

  const handleReassess = async (levels) => {
    setReassessBusy(true);
    setError(null);
    setNotice("");
    try {
      const result = await reassess(levels);
      setDash(result);
      setNotice(
        result.roadmap_regenerated
          ? "Proficiency saved successfully. Your roadmap and next recommendations were updated."
          : "Proficiency saved successfully. Your roadmap remains up to date."
      );
      setPlan(await getMyProgress());
    } catch (e) {
      setError(e);
    } finally {
      setReassessBusy(false);
    }
  };

  const p = plan?.progress || {
    total: 0,
    completed: 0,
    in_progress: 0,
    not_started: 0,
    remaining: 0,
    percent: 0,
  };

  const filteredActivities = useMemo(() => {
    if (!plan?.activities) return [];
    if (statusFilter === "all") return plan.activities;
    return plan.activities.filter((a) => a.status === statusFilter);
  }, [plan?.activities, statusFilter]);

  if (loading) {
    return <LoadingIndicator message="Loading your learning progress…" />;
  }

  if (error && !dash && !plan) {
    return <ErrorBox error={error} onRetry={load} />;
  }

  return (
    <div className="progress-page">
      {/* Page Header */}
      <div className="page-header">
        <div>
          <h1 style={{ display: "flex", alignItems: "center", gap: "10px", flexWrap: "wrap" }}>
            Progress Tracker
            {(plan?.career || dash?.career) && (
              <span
                className="badge"
                style={{
                  background: "var(--blue-50)",
                  color: "var(--blue-600)",
                  border: "1px solid var(--blue-100)",
                  fontSize: "0.85rem",
                  padding: "4px 12px",
                }}
              >
                {plan?.career || dash?.career}
              </span>
            )}
          </h1>
          <p>
            Track completion across your learning activities, visualize milestone progress, and update skill proficiencies.
          </p>
        </div>
      </div>

      <ErrorBox error={error} />

      {notice && (
        <div
          className="card"
          style={{
            background: "#f0fdf4",
            borderColor: "#bbf7d0",
            borderLeft: "4px solid #16a34a",
            color: "#166534",
            padding: "14px 18px",
            marginBottom: "20px",
            display: "flex",
            alignItems: "center",
            gap: "10px",
          }}
        >
          <span>✓</span>
          <span style={{ fontWeight: 500 }}>{notice}</span>
        </div>
      )}

      {/* Empty State when no roadmap */}
      {!plan && (
        <div className="card empty-state">
          <div className="empty-icon">🗺️</div>
          <h2>No Active Roadmap Found</h2>
          <p>
            You haven't generated a learning roadmap yet. Create a roadmap to start tracking your activities, study pace, and milestone completions.
          </p>
          <Link to="/roadmap" className="btn btn-primary">
            Go to Learning Roadmap →
          </Link>
        </div>
      )}

      {plan && (
        <>
          {/* Progress Summary Cards (6 metrics) */}
          <div className="stats-grid-6">
            <div className="stat-card">
              <span className="stat-label">Total Activities</span>
              <span className="stat-value">{p.total}</span>
              <span className="stat-sub">Planned steps</span>
            </div>

            <div className="stat-card tone-completed">
              <span className="stat-label">Completed</span>
              <span className="stat-value">{p.completed}</span>
              <span className="stat-sub">{p.percent}% finished</span>
            </div>

            <div className="stat-card tone-inprogress">
              <span className="stat-label">In Progress</span>
              <span className="stat-value">{p.in_progress}</span>
              <span className="stat-sub">Currently learning</span>
            </div>

            <div className="stat-card tone-notstarted">
              <span className="stat-label">Not Started</span>
              <span className="stat-value">{p.not_started}</span>
              <span className="stat-sub">Awaiting start</span>
            </div>

            <div className="stat-card tone-remaining">
              <span className="stat-label">Remaining</span>
              <span className="stat-value">{p.remaining}</span>
              <span className="stat-sub">Left to complete</span>
            </div>

            <div className="stat-card tone-completed">
              <span className="stat-label">Completion Rate</span>
              <span className="stat-value">{p.percent}%</span>
              <span className="stat-sub">{p.completed} of {p.total} done</span>
            </div>
          </div>

          {/* Learning Progress Chart Card */}
          <div className="card" style={{ marginBottom: "24px" }}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", flexWrap: "wrap", gap: "10px", marginBottom: "16px" }}>
              <div>
                <h3 style={{ fontSize: "1.08rem", fontWeight: 700, color: "var(--navy-900)" }}>
                  Learning Progress
                </h3>
                <p className="muted small">
                  Activity completion distribution for {plan.career}
                </p>
              </div>
              <div style={{ minWidth: "180px", maxWidth: "260px", flex: 1 }}>
                <ProgressBar
                  value={p.percent}
                  label="Roadmap Completion"
                  showPercent={true}
                  tone={p.percent === 100 ? "green" : "blue"}
                />
              </div>
            </div>

            <ProgressChart progress={p} />
          </div>

          {/* Activities Section */}
          <div className="section-header">
            <div>
              <h2 className="section-title">
                Roadmap Activities
                <span className="badge" style={{ background: "var(--navy-800)", color: "#fff", fontSize: "0.8rem" }}>
                  {filteredActivities.length}
                </span>
              </h2>
            </div>

            {/* Filter Bar */}
            <div className="filter-bar">
              <button
                type="button"
                className={`filter-pill ${statusFilter === "all" ? "active" : ""}`}
                onClick={() => setStatusFilter("all")}
              >
                All ({p.total})
              </button>
              <button
                type="button"
                className={`filter-pill ${statusFilter === "in_progress" ? "active" : ""}`}
                onClick={() => setStatusFilter("in_progress")}
              >
                In Progress ({p.in_progress})
              </button>
              <button
                type="button"
                className={`filter-pill ${statusFilter === "completed" ? "active" : ""}`}
                onClick={() => setStatusFilter("completed")}
              >
                Completed ({p.completed})
              </button>
              <button
                type="button"
                className={`filter-pill ${statusFilter === "not_started" ? "active" : ""}`}
                onClick={() => setStatusFilter("not_started")}
              >
                Not Started ({p.not_started})
              </button>
            </div>
          </div>

          {/* Activity Cards List */}
          {filteredActivities.length === 0 ? (
            <div className="card" style={{ textAlign: "center", padding: "32px 16px" }}>
              <p className="muted">
                {plan.activities.length === 0
                  ? "No activities found in this roadmap."
                  : `No activities matching the "${STATUS_LABELS[statusFilter] || statusFilter}" filter.`}
              </p>
            </div>
          ) : (
            <div className="stack" style={{ gap: "14px" }}>
              {filteredActivities.map((a) => {
                const isCompleted = a.status === "completed";
                const isInProgress = a.status === "in_progress";
                const isSaving = savingId === a.id;

                return (
                  <article
                    key={a.id}
                    className={`activity-card ${isCompleted ? "is-completed" : ""} ${isInProgress ? "is-inprogress" : ""}`}
                  >
                    {/* Sequence Badge */}
                    <div className="activity-step">
                      {isCompleted ? "✓" : a.sequence}
                    </div>

                    <div className="activity-card-body">
                      {/* Header */}
                      <div className="activity-card-header">
                        <h3 className="activity-title">
                          {a.sequence}. {a.skill_name}
                        </h3>
                        <span
                          className={`badge badge-activity-${a.status.replace("_", "")}`}
                          style={{ fontSize: "0.8rem", padding: "4px 12px" }}
                        >
                          {STATUS_LABELS[a.status] || a.status}
                        </span>
                      </div>

                      {/* Meta Information */}
                      <div className="activity-meta-row">
                        <div className="activity-meta-item">
                          <span>📈</span>
                          <span>
                            Level <strong>{a.current_level}</strong> → <strong>{a.target_level}</strong>
                          </span>
                        </div>
                        <div className="activity-meta-item">
                          <span>⏱</span>
                          <span>
                            <strong>{a.estimated_hours}h</strong> estimated
                            {a.status === "in_progress" && a.hours_completed > 0 && (
                              <span style={{ color: "var(--blue-600)" }}> ({a.hours_completed}h completed)</span>
                            )}
                          </span>
                        </div>
                        {a.prerequisites && a.prerequisites.length > 0 && (
                          <div className="activity-meta-item" style={{ color: "#b45309" }}>
                            <span>🔗</span>
                            <span>Prereqs: <strong>{a.prerequisites.join(", ")}</strong></span>
                          </div>
                        )}
                      </div>

                      {/* Objectives summary if available */}
                      {a.learning_objectives && a.learning_objectives.length > 0 && (
                        <div className="activity-objectives">
                          <div className="activity-objectives-title">Learning Objectives</div>
                          <ul>
                            {a.learning_objectives.slice(0, 3).map((obj, i) => (
                              <li key={i}>{obj}</li>
                            ))}
                            {a.learning_objectives.length > 3 && (
                              <li style={{ color: "var(--muted)", listStyleType: "none" }}>
                                + {a.learning_objectives.length - 3} more objectives
                              </li>
                            )}
                          </ul>
                        </div>
                      )}

                      {/* Footer: Resource link and status toggle */}
                      <div className="activity-footer">
                        {a.resource && (
                          <a
                            href={a.resource.url}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="activity-resource-link"
                          >
                            <span>📚</span>
                            <span>{a.resource.title}</span>
                            <span style={{ fontSize: "0.75rem" }}>↗</span>
                          </a>
                        )}

                        <div className="activity-status-controls">
                          <span className="muted small" style={{ marginRight: "4px" }}>Status:</span>
                          <div className="segmented" role="group" aria-label={`Status for ${a.skill_name}`}>
                            {Object.entries(STATUS_LABELS).map(([val, label]) => {
                              const isActive = a.status === val;
                              return (
                                <button
                                  key={val}
                                  type="button"
                                  className={`segment seg-${val.replace("_", "")} ${isActive ? "active" : ""}`}
                                  disabled={isSaving}
                                  onClick={() => handleStatus(a, val)}
                                >
                                  {isActive && val === "completed" && "✓ "}
                                  {label}
                                </button>
                              );
                            })}
                          </div>
                          {isSaving && (
                            <span className="spinner" style={{ width: "16px", height: "16px", borderWidth: "2px" }} />
                          )}
                        </div>
                      </div>
                    </div>
                  </article>
                );
              })}
            </div>
          )}
        </>
      )}

      {/* Reassessment Panel */}
      {dash && dash.skills && dash.skills.length > 0 && (
        <ReassessmentPanel
          skills={dash.skills}
          needsReassessment={dash.needs_reassessment}
          onSubmit={handleReassess}
          busy={reassessBusy}
        />
      )}
    </div>
  );
}