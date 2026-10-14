import { useCallback, useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { useApp } from "../context/AppContext.jsx";
import { generateRoadmap, getRoadmap, updateActivity } from "../api/roadmap";
import ProgressBar from "../components/ProgressBar.jsx";
import LoadingIndicator from "../components/LoadingIndicator.jsx";
import ErrorBox from "../components/ErrorBox.jsx";

const STATUS_LABELS = {
  not_started: "Not Started",
  in_progress: "In Progress",
  completed: "Completed",
};

function getPriorityBadge(severity) {
  const s = String(severity || "").toLowerCase();
  if (s.includes("high")) {
    return <span className="badge badge-priority-high">High Priority</span>;
  }
  if (s.includes("med")) {
    return <span className="badge badge-priority-medium">Medium Priority</span>;
  }
  return <span className="badge badge-priority-low">Low Priority</span>;
}

export default function LearningRoadmap({ studentId, career }) {
  const { user, careerId } = useApp();
  const effectiveCareer = career || careerId || user?.career_id;
  const effectiveStudentId = studentId || user?.id;

  const [plan, setPlan] = useState(null);
  const [hoursPerDay, setHoursPerDay] = useState(1);
  const [daysPerWeek, setDaysPerWeek] = useState(7);
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  const [updatingId, setUpdatingId] = useState(null);
  const [error, setError] = useState(null);
  const [openWeek, setOpenWeek] = useState(1);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const saved = await getRoadmap(effectiveCareer);
      if (saved) {
        setPlan(saved);
        setHoursPerDay(saved.hours_per_day);
        setDaysPerWeek(saved.days_per_week);
      } else {
        setPlan(null);
      }
    } catch (e) {
      setError(e);
    } finally {
      setLoading(false);
    }
  }, [effectiveCareer]);

  useEffect(() => {
    load();
  }, [load]);

  const handleGenerate = async (force = false) => {
    setBusy(true);
    setError(null);
    try {
      const data = await generateRoadmap({
        student_id: effectiveStudentId,
        career: effectiveCareer,
        hours_per_day: Number(hoursPerDay),
        days_per_week: Number(daysPerWeek),
        force_regenerate: force,
      });
      setPlan(data);
      setOpenWeek(1);
    } catch (e) {
      setError(e);
    } finally {
      setBusy(false);
    }
  };

  const handleStatus = async (activity, status) => {
    setUpdatingId(activity.id);
    setError(null);
    try {
      const data = await updateActivity(
        activity.id,
        status,
        status === "in_progress" ? activity.hours_completed : undefined
      );
      if (data) setPlan(data);
    } catch (e) {
      setError(e);
    } finally {
      setUpdatingId(null);
    }
  };

  // Dedup warnings
  const warningsList = useMemo(() => {
    if (!plan?.warnings) return [];
    return Array.from(new Set(plan.warnings));
  }, [plan?.warnings]);

  const hasMissingAssessments =
    (plan?.missing_assessments && plan.missing_assessments.length > 0) ||
    warningsList.some((w) => w.toLowerCase().includes("not assessed"));

  const weeklyCommitment = (Number(hoursPerDay || 0) * Number(daysPerWeek || 0)).toFixed(1);

  if (loading) {
    return <LoadingIndicator message="Loading your learning roadmap…" />;
  }

  return (
    <div className="roadmap-page">
      {/* Header */}
      <div className="page-header">
        <div>
          <h1 style={{ display: "flex", alignItems: "center", gap: "10px", flexWrap: "wrap" }}>
            Learning Roadmap
            {(plan?.career || effectiveCareer) && (
              <span className="badge" style={{ background: "var(--blue-50)", color: "var(--blue-600)", border: "1px solid var(--blue-100)", fontSize: "0.85rem", padding: "4px 12px" }}>
                {plan?.career || effectiveCareer}
              </span>
            )}
          </h1>
          <p>
            AI-generated structured learning pathway tailored to your skill gaps and weekly study commitment.
          </p>
        </div>
      </div>

      {error && <ErrorBox error={error} onRetry={load} />}

      {/* Planning Controls Panel */}
      <div className="roadmap-controls-card">
        <div className="roadmap-controls-grid">
          <div className="control-field">
            <label htmlFor="input-hours-per-day">
              <span>Study Hours per Day</span>
            </label>
            <div className="control-input-wrapper">
              <input
                id="input-hours-per-day"
                type="number"
                min="0.5"
                max="12"
                step="0.5"
                value={hoursPerDay}
                disabled={busy}
                onChange={(e) => setHoursPerDay(e.target.value)}
              />
              <span className="control-field-suffix">hrs/day</span>
            </div>
          </div>

          <div className="control-field">
            <label htmlFor="input-days-per-week">
              <span>Days per Week</span>
            </label>
            <div className="control-input-wrapper">
              <input
                id="input-days-per-week"
                type="number"
                min="1"
                max="7"
                step="1"
                value={daysPerWeek}
                disabled={busy}
                onChange={(e) => setDaysPerWeek(e.target.value)}
              />
              <span className="control-field-suffix">days/wk</span>
            </div>
          </div>

          <div className="control-preview-badge">
            <span className="badge-title">Weekly Pace</span>
            <span className="badge-val">{weeklyCommitment} hrs/wk</span>
          </div>

          <div className="control-actions">
            <button
              className="btn btn-primary"
              disabled={busy || !hoursPerDay || !daysPerWeek}
              onClick={() => handleGenerate(false)}
              style={{ minHeight: "44px", minWidth: "160px" }}
            >
              {busy ? (
                <>
                  <span className="spinner" style={{ width: "16px", height: "16px", borderWidth: "2px" }} />
                  Generating…
                </>
              ) : plan ? (
                "Update Roadmap"
              ) : (
                "Generate Roadmap"
              )}
            </button>
          </div>
        </div>
      </div>

      {/* Empty State when no roadmap */}
      {!plan && (
        <div className="card empty-state">
          <div className="empty-icon">🗺️</div>
          <h2>No Learning Roadmap Yet</h2>
          <p>
            Set your target study hours and days per week above, then click <strong>Generate Roadmap</strong> to create your custom curriculum for {effectiveCareer || "your career goal"}.
          </p>
          <button
            className="btn btn-primary"
            disabled={busy}
            onClick={() => handleGenerate(false)}
          >
            {busy ? "Generating Roadmap…" : "Generate My Roadmap"}
          </button>
        </div>
      )}

      {/* Roadmap Content */}
      {plan && (
        <>
          {/* Warnings Banner */}
          {warningsList.length > 0 && (
            <div className="banner-warning">
              <div className="banner-warning-icon">⚠️</div>
              <div className="banner-warning-body">
                <strong>Roadmap Notice</strong>
                {warningsList.map((w, idx) => (
                  <div key={idx} style={{ marginTop: idx > 0 ? "4px" : "0" }}>
                    {w}
                  </div>
                ))}
                {hasMissingAssessments && (
                  <div className="banner-warning-actions">
                    <Link
                      to="/assessment"
                      className="btn btn-outline"
                      style={{ fontSize: "0.82rem", padding: "6px 14px", borderColor: "#f59e0b", color: "#92400e" }}
                    >
                      Complete Skill Assessment →
                    </Link>
                  </div>
                )}
              </div>
            </div>
          )}

          {/* Roadmap Summary Section */}
          {plan.activities.length > 0 && (
            <div className="card" style={{ marginBottom: "24px" }}>
              <div style={{ marginBottom: "16px" }}>
                <h3 style={{ fontSize: "1.08rem", fontWeight: 700, color: "var(--navy-900)" }}>
                  Curriculum Overview
                </h3>
                <p className="muted small">
                  Summary metrics for your personalized learning pathway
                </p>
              </div>

              <div className="stats-grid" style={{ marginBottom: "18px" }}>
                <div className="stat-card">
                  <span className="stat-label">Total Learning</span>
                  <span className="stat-value">{plan.summary.total_hours} <span style={{ fontSize: "1.1rem", fontWeight: 600 }}>hrs</span></span>
                  <span className="stat-sub">Across {plan.activities.length} learning modules</span>
                </div>

                <div className="stat-card">
                  <span className="stat-label">Weekly Pace</span>
                  <span className="stat-value">{plan.summary.weekly_hours} <span style={{ fontSize: "1.1rem", fontWeight: 600 }}>hrs/wk</span></span>
                  <span className="stat-sub">{plan.hours_per_day}h/day × {plan.days_per_week} days</span>
                </div>

                <div className="stat-card">
                  <span className="stat-label">Est. Timeline</span>
                  <span className="stat-value">
                    {plan.summary.estimated_weeks_min === plan.summary.estimated_weeks_max
                      ? `${plan.summary.estimated_weeks_min}`
                      : `${plan.summary.estimated_weeks_min}–${plan.summary.estimated_weeks_max}`}{" "}
                    <span style={{ fontSize: "1.1rem", fontWeight: 600 }}>weeks</span>
                  </span>
                  <span className="stat-sub">At your configured study pace</span>
                </div>

                <div className="stat-card tone-completed">
                  <span className="stat-label">Completion</span>
                  <span className="stat-value">{plan.summary.progress_percent}%</span>
                  <span className="stat-sub">
                    {plan.progress?.completed || 0} of {plan.activities.length} completed
                  </span>
                </div>
              </div>

              <ProgressBar
                value={plan.summary.progress_percent}
                label="Overall Roadmap Progress"
                showPercent={true}
                tone={plan.summary.progress_percent === 100 ? "green" : "blue"}
              />

              {plan.summary.estimate_note && (
                <p className="form-hint" style={{ marginTop: "10px", fontSize: "0.82rem" }}>
                  ℹ {plan.summary.estimate_note}
                </p>
              )}
            </div>
          )}

          {/* Learning Activities Section */}
          <div className="section-header">
            <h2 className="section-title">
              Learning Activities
              <span className="badge" style={{ background: "var(--navy-800)", color: "#fff", fontSize: "0.8rem" }}>
                {plan.activities.length}
              </span>
            </h2>
            <span className="muted small">Recommended sequential order</span>
          </div>

          {plan.activities.length === 0 ? (
            <div className="card" style={{ textAlign: "center", padding: "36px 20px" }}>
              <p style={{ fontWeight: 600, color: "var(--green)", fontSize: "1.05rem" }}>
                🎯 All target skill levels achieved!
              </p>
              <p className="muted small" style={{ marginTop: "6px" }}>
                You have no remaining skill gaps for {plan.career}.
              </p>
            </div>
          ) : (
            <div className="stack" style={{ gap: "16px" }}>
              {plan.activities.map((a) => {
                const isCompleted = a.status === "completed";
                const isInProgress = a.status === "in_progress";
                const isUpdating = updatingId === a.id;

                return (
                  <article
                    key={a.id}
                    className={`activity-card ${isCompleted ? "is-completed" : ""} ${isInProgress ? "is-inprogress" : ""}`}
                  >
                    {/* Step indicator */}
                    <div className="activity-step">
                      {isCompleted ? "✓" : a.sequence}
                    </div>

                    <div className="activity-card-body">
                      {/* Top Header */}
                      <div className="activity-card-header">
                        <div style={{ display: "flex", alignItems: "center", gap: "10px", flexWrap: "wrap" }}>
                          <h3 className="activity-title">
                            {a.sequence}. {a.skill_name}
                          </h3>
                          {getPriorityBadge(a.severity)}
                        </div>

                        <span
                          className={`badge badge-activity-${a.status.replace("_", "")}`}
                          style={{ fontSize: "0.8rem", padding: "4px 12px" }}
                        >
                          {STATUS_LABELS[a.status] || a.status}
                        </span>
                      </div>

                      {/* Meta information row */}
                      <div className="activity-meta-row">
                        <div className="activity-meta-item">
                          <span>📈</span>
                          <span>
                            Level <strong>{a.current_level}</strong> → <strong>{a.target_level}</strong> (gap: {a.gap})
                          </span>
                        </div>
                        <div className="activity-meta-item">
                          <span>⏱</span>
                          <span>
                            <strong>{a.estimated_hours}h</strong> estimated
                            {a.hours_completed > 0 && a.status !== "completed" && (
                              <span style={{ color: "var(--blue-600)" }}> ({a.hours_completed}h logged)</span>
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

                      {/* Reason / Start with */}
                      {a.reason && (
                        <div style={{ fontSize: "0.86rem", color: "#475569" }}>
                          💡 <em>{a.reason}</em>
                        </div>
                      )}

                      {/* Learning Objectives */}
                      {a.learning_objectives && a.learning_objectives.length > 0 && (
                        <div className="activity-objectives">
                          <div className="activity-objectives-title">Learning Objectives</div>
                          <ul>
                            {a.learning_objectives.map((obj, i) => (
                              <li key={i}>{obj}</li>
                            ))}
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
                                  disabled={isUpdating}
                                  onClick={() => handleStatus(a, val)}
                                >
                                  {isActive && val === "completed" && "✓ "}
                                  {label}
                                </button>
                              );
                            })}
                          </div>
                          {isUpdating && (
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

          {/* Weekly Schedule Section */}
          {plan.weekly_schedule && plan.weekly_schedule.length > 0 && (
            <div className="schedule-container">
              <div className="section-header">
                <h2 className="section-title">
                  Weekly Study Schedule
                </h2>
                <span className="muted small">Recommended distribution across weeks</span>
              </div>

              {/* Week Selector Tabs */}
              <div className="tabs">
                {plan.weekly_schedule.map((w) => (
                  <button
                    key={w.week}
                    className={`tab ${openWeek === w.week ? "active" : ""}`}
                    onClick={() => setOpenWeek(w.week)}
                  >
                    Week {w.week} ({w.total_hours}h)
                  </button>
                ))}
              </div>

              {/* Selected Week Card */}
              {plan.weekly_schedule
                .filter((w) => w.week === openWeek)
                .map((w) => (
                  <div className="schedule-card" key={w.week}>
                    <div className="schedule-header">
                      <div>
                        <h3 style={{ fontSize: "1.05rem", fontWeight: 700, color: "var(--navy-900)" }}>
                          Week {w.week} Study Plan · {w.total_hours} Hours
                        </h3>
                        <p className="muted small" style={{ marginTop: "2px" }}>
                          Focus Skills: {w.focus.join(", ")}
                        </p>
                      </div>
                      <div className="chip-row">
                        {w.focus.map((f, i) => (
                          <span key={i} className="chip" style={{ background: "var(--blue-50)", color: "var(--blue-600)", fontWeight: 600 }}>
                            {f}
                          </span>
                        ))}
                      </div>
                    </div>

                    <div className="schedule-days-grid">
                      {w.days.map((d) => (
                        <div className="schedule-day-box" key={d.day}>
                          <div className="schedule-day-name">
                            <span>{d.day}</span>
                            <span style={{ color: "var(--blue-600)", fontWeight: 700 }}>{d.hours}h</span>
                          </div>
                          <div className="schedule-sessions-list">
                            {d.sessions.map((s, idx) => (
                              <div className="schedule-session-item" key={idx}>
                                <span>{s.skill}</span>
                                <strong>{s.hours}h</strong>
                              </div>
                            ))}
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                ))}
            </div>
          )}
        </>
      )}
    </div>
  );
}