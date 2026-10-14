import { useCallback, useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { useApp } from "../context/AppContext";
import { getDashboard } from "../api/progress";
import { GapChart, ProficiencyChart, ProgressChart } from "../components/Charts";
import ErrorBox from "../components/ErrorBox";
import ProgressBar from "../components/ProgressBar";
import LoadingIndicator from "../components/LoadingIndicator";
import EmptyState from "../components/EmptyState";

export default function Dashboard() {
  const { user } = useApp();
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState(null);

  const load = useCallback(async (isRefresh = false) => {
    if (isRefresh) {
      setRefreshing(true);
    } else {
      setLoading(true);
    }
    setError(null);
    try {
      const res = await getDashboard();
      setData(res);
    } catch (e) {
      setError(e);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, []);

  useEffect(() => {
    load(false);
  }, [load]);

  if (loading) {
    return <LoadingIndicator message="Loading your dashboard…" />;
  }

  if (error && !data) {
    return <ErrorBox error={error} onRetry={() => load(false)} />;
  }

  if (!data) return null;

  const studentName = data.student?.name || user?.name || "Student";

  // If no career has been selected yet
  if (!data.career) {
    return (
      <div className="dashboard-page">
        <div className="page-header">
          <div>
            <h1>Welcome, {studentName}</h1>
            <p>Select a career goal to personalize your skills assessment, roadmap, and learning dashboard.</p>
          </div>
          <button
            className="btn btn-outline"
            onClick={() => load(true)}
            disabled={refreshing}
          >
            {refreshing ? "Refreshing…" : "↻ Refresh"}
          </button>
        </div>

        <EmptyState
          icon="🎯"
          title="No Career Goal Selected"
          text={data.message || "Please choose a career track to view your personalized dashboard and skill benchmarks."}
          actionLabel="Choose Career Goal →"
          to="/career"
        />
      </div>
    );
  }

  const progress = data.roadmap?.progress;
  const hasRoadmap = !!progress;

  return (
    <div className="dashboard-page">
      {/* Welcome Header */}
      <div className="page-header">
        <div>
          <h1 style={{ display: "flex", alignItems: "center", gap: "10px", flexWrap: "wrap" }}>
            Welcome, {studentName}
            {data.career && (
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
                {data.career}
              </span>
            )}
          </h1>
          <p>
            Your personalized skill readiness, curriculum progress, and recommended next activities.
          </p>
        </div>

        <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
          <button
            className="btn btn-outline"
            onClick={() => load(true)}
            disabled={refreshing}
            style={{ minWidth: "115px" }}
          >
            {refreshing ? (
              <>
                <span className="spinner" style={{ width: "14px", height: "14px", borderWidth: "2px" }} />
                Refreshing…
              </>
            ) : (
              <>
                <span>↻</span> Refresh
              </>
            )}
          </button>
        </div>
      </div>

      <ErrorBox error={error} />

      {/* Assessment Recommendation Banner */}
      {!data.has_assessments && (
        <div className="banner-warning" style={{ marginBottom: "22px" }}>
          <div className="banner-warning-icon">⚠️</div>
          <div className="banner-warning-body">
            <strong>Skill Assessment Recommended</strong>
            <div>
              {data.message || "Complete your skill assessment to accurately evaluate your current proficiencies and identify your true skill gaps."}
            </div>
            <div className="banner-warning-actions">
              <Link
                to="/assessment"
                className="btn btn-outline"
                style={{ fontSize: "0.82rem", padding: "6px 14px", borderColor: "#f59e0b", color: "#92400e" }}
              >
                Take Skill Assessment →
              </Link>
            </div>
          </div>
        </div>
      )}

      {/* Completed Learning Activity Notice (Needs Reassessment) */}
      {data.needs_reassessment && data.needs_reassessment.length > 0 && (
        <div
          className="banner-warning"
          style={{
            background: "#f0fdf4",
            borderColor: "#bbf7d0",
            borderLeftColor: "#16a34a",
            color: "#166534",
            marginBottom: "22px",
          }}
        >
          <div className="banner-warning-icon">🎉</div>
          <div className="banner-warning-body">
            <strong style={{ color: "#14532d" }}>Learning Activities Completed!</strong>
            <div>
              You finished learning activities for: <strong>{data.needs_reassessment.join(", ")}</strong>. Confirm your updated proficiency level to verify your achievement in your readiness score.
            </div>
            <div className="banner-warning-actions">
              <Link
                to="/progress"
                className="btn btn-outline"
                style={{ fontSize: "0.82rem", padding: "6px 14px", borderColor: "#16a34a", color: "#15803d" }}
              >
                Confirm in Progress Tracker →
              </Link>
            </div>
          </div>
        </div>
      )}

      {/* Compact Statistics Row (4 Cards) */}
      <div className="stats-grid" style={{ marginBottom: "24px" }}>
        <div className="stat-card">
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
            <span className="stat-label">Skill Readiness</span>
            <span style={{ fontSize: "1.1rem" }}>🎯</span>
          </div>
          <span className="stat-value">{data.readiness_score}%</span>
          <span className="stat-sub">
            {data.achieved_skills.length} of {data.skills.length} skills achieved
          </span>
        </div>

        <div className="stat-card">
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
            <span className="stat-label">Total Activities</span>
            <span style={{ fontSize: "1.1rem" }}>📚</span>
          </div>
          <span className="stat-value">{hasRoadmap ? progress.total : "—"}</span>
          <span className="stat-sub">
            {hasRoadmap ? "Across active roadmap" : "Roadmap not generated"}
          </span>
        </div>

        <div className="stat-card tone-completed">
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
            <span className="stat-label">Completed</span>
            <span style={{ fontSize: "1.1rem" }}>✅</span>
          </div>
          <span className="stat-value">{hasRoadmap ? progress.completed : "—"}</span>
          <span className="stat-sub">
            {hasRoadmap ? `${progress.percent}% of curriculum done` : "Awaiting start"}
          </span>
        </div>

        <div className="stat-card tone-remaining">
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
            <span className="stat-label">Remaining</span>
            <span style={{ fontSize: "1.1rem" }}>⏳</span>
          </div>
          <span className="stat-value">{hasRoadmap ? progress.remaining : "—"}</span>
          <span className="stat-sub">
            {hasRoadmap ? `${progress.in_progress} in progress` : "Create roadmap to begin"}
          </span>
        </div>
      </div>

      {/* 2-Column Section: Skill Readiness & Learning Progress */}
      <div className="grid-equal" style={{ marginBottom: "24px" }}>
        {/* Left Column: Skill Assessment & Readiness */}
        <div className="card" style={{ display: "flex", flexDirection: "column", justifyContent: "space-between" }}>
          <div>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: "16px", gap: "10px" }}>
              <div>
                <h3 style={{ fontSize: "1.08rem", fontWeight: 700, color: "var(--navy-900)" }}>
                  Skill Readiness
                </h3>
                <p className="muted small">Competency breakdown for {data.career}</p>
              </div>
              <span
                className="badge"
                style={{
                  background: data.readiness_score >= 80 ? "var(--green-bg)" : "var(--blue-50)",
                  color: data.readiness_score >= 80 ? "var(--green)" : "var(--blue-600)",
                  fontSize: "0.8rem",
                  padding: "4px 10px",
                }}
              >
                {data.readiness_score}% Readiness
              </span>
            </div>

            <ProgressBar
              value={data.readiness_score}
              label="Overall Readiness Score"
              showPercent={true}
              tone={data.readiness_score >= 80 ? "green" : "blue"}
            />

            {/* Achieved Skills Group */}
            <div style={{ marginTop: "18px" }}>
              <strong style={{ fontSize: "0.85rem", color: "var(--navy-800)", textTransform: "uppercase", letterSpacing: "0.03em" }}>
                Achieved Skills ({data.achieved_skills.length})
              </strong>
              {data.achieved_skills.length > 0 ? (
                <div className="skill-badges-wrap">
                  {data.achieved_skills.map((s) => (
                    <span key={s} className="skill-chip achieved">
                      ✓ {s}
                    </span>
                  ))}
                </div>
              ) : (
                <p className="muted small" style={{ marginTop: "6px" }}>
                  None achieved yet. Complete modules to reach benchmark levels.
                </p>
              )}
            </div>

            {/* Skills Needing Improvement Group */}
            <div style={{ marginTop: "16px" }}>
              <strong style={{ fontSize: "0.85rem", color: "var(--navy-800)", textTransform: "uppercase", letterSpacing: "0.03em" }}>
                Needs Improvement ({data.improvement_skills.length})
              </strong>
              {data.improvement_skills.length > 0 ? (
                <div className="skill-badges-wrap">
                  {data.improvement_skills.map((s) => (
                    <span key={s} className="skill-chip improve">
                      ▲ {s}
                    </span>
                  ))}
                </div>
              ) : (
                <p className="muted small" style={{ marginTop: "6px" }}>
                  All target levels have been met!
                </p>
              )}
            </div>
          </div>

          <div
            style={{
              marginTop: "20px",
              paddingTop: "12px",
              borderTop: "1px solid #f1f5f9",
              display: "flex",
              justifyContent: "space-between",
              alignItems: "center",
              flexWrap: "wrap",
              gap: "8px",
            }}
          >
            <span className="muted small">
              {data.has_assessments ? "Assessment results active" : "Assessment pending"}
            </span>
            <Link
              to="/assessment"
              className="btn btn-outline"
              style={{ fontSize: "0.82rem", padding: "6px 12px" }}
            >
              Skill Assessment Details →
            </Link>
          </div>
        </div>

        {/* Right Column: Learning Progress */}
        <div className="card" style={{ display: "flex", flexDirection: "column", justifyContent: "space-between" }}>
          <div>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: "16px", gap: "10px" }}>
              <div>
                <h3 style={{ fontSize: "1.08rem", fontWeight: 700, color: "var(--navy-900)" }}>
                  Learning Progress
                </h3>
                <p className="muted small">
                  {hasRoadmap
                    ? `${progress.completed} of ${progress.total} activities completed`
                    : "No active roadmap found"}
                </p>
              </div>
              {hasRoadmap && (
                <span
                  className="badge"
                  style={{
                    background: progress.percent === 100 ? "var(--green-bg)" : "var(--blue-50)",
                    color: progress.percent === 100 ? "var(--green)" : "var(--blue-600)",
                    fontSize: "0.8rem",
                    padding: "4px 10px",
                  }}
                >
                  {progress.percent}% Completed
                </span>
              )}
            </div>

            {hasRoadmap ? (
              <ProgressChart progress={progress} />
            ) : (
              <div className="empty-state" style={{ padding: "32px 16px" }}>
                <div className="empty-icon" style={{ fontSize: "2.2rem" }}>🗺️</div>
                <h4 style={{ margin: "0 0 6px" }}>No Learning Roadmap Yet</h4>
                <p className="muted small" style={{ margin: "0 auto 16px", maxWidth: "340px" }}>
                  Generate your custom learning roadmap to start tracking your module completions and milestones.
                </p>
                <Link to="/roadmap" className="btn btn-primary" style={{ fontSize: "0.88rem" }}>
                  Generate Learning Roadmap →
                </Link>
              </div>
            )}
          </div>

          {hasRoadmap && (
            <div
              style={{
                marginTop: "20px",
                paddingTop: "12px",
                borderTop: "1px solid #f1f5f9",
                display: "flex",
                justifyContent: "space-between",
                alignItems: "center",
                flexWrap: "wrap",
                gap: "8px",
              }}
            >
              <span className="muted small">
                {progress.remaining} activities remaining
              </span>
              <Link
                to="/progress"
                className="btn btn-outline"
                style={{ fontSize: "0.82rem", padding: "6px 12px" }}
              >
                Open Progress Tracker →
              </Link>
            </div>
          )}
        </div>
      </div>

      {/* Recommended Next Activities Section */}
      <div className="card" style={{ marginBottom: "24px" }}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "16px", flexWrap: "wrap", gap: "10px" }}>
          <div>
            <h3 style={{ fontSize: "1.08rem", fontWeight: 700, color: "var(--navy-900)" }}>
              Recommended Next Activities
            </h3>
            <p className="muted small">
              Prioritized learning steps to address your highest-impact skill gaps
            </p>
          </div>
          <Link
            to="/roadmap"
            className="btn btn-outline"
            style={{ fontSize: "0.82rem", padding: "6px 12px" }}
          >
            View All in Roadmap →
          </Link>
        </div>

        {data.recommended_activities && data.recommended_activities.length > 0 ? (
          <div className="rec-list">
            {data.recommended_activities.map((a) => (
              <div key={a.id} className="rec-item">
                <div className="rec-item-info">
                  <div className="rec-item-seq">{a.sequence}</div>
                  <div>
                    <div className="rec-item-title">{a.skill_name}</div>
                    <span className="muted small">⏱ {a.estimated_hours}h estimated</span>
                  </div>
                </div>

                <div className="rec-item-meta">
                  <span className={`badge badge-activity-${a.status.replace("_", "")}`}>
                    {a.status === "not_started"
                      ? "Not Started"
                      : a.status === "in_progress"
                      ? "In Progress"
                      : "Completed"}
                  </span>

                  {a.resource && (
                    <a
                      href={a.resource.url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="activity-resource-link"
                      style={{ fontSize: "0.82rem", padding: "5px 12px" }}
                    >
                      <span>📚</span>
                      <span>{a.resource.title}</span>
                      <span style={{ fontSize: "0.72rem" }}>↗</span>
                    </a>
                  )}
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div style={{ textAlign: "center", padding: "28px 16px", color: "var(--muted)" }}>
            <p style={{ fontSize: "0.92rem", margin: 0 }}>
              {hasRoadmap
                ? "No open activities! Update your proficiency or generate a new roadmap to view recommendations."
                : "Generate a roadmap to receive tailored activity recommendations."}
            </p>
            {hasRoadmap ? (
              <Link to="/progress" className="btn btn-outline" style={{ marginTop: "12px", fontSize: "0.84rem" }}>
                Go to Progress Tracker
              </Link>
            ) : (
              <Link to="/roadmap" className="btn btn-primary" style={{ marginTop: "12px", fontSize: "0.84rem" }}>
                Generate Learning Roadmap
              </Link>
            )}
          </div>
        )}
      </div>

      {/* Visualizations: Proficiency Comparison & Skill Gaps */}
      {data.skills && data.skills.length > 0 && (
        <div className="grid-equal">
          <div className="card">
            <div style={{ marginBottom: "14px" }}>
              <h3 style={{ fontSize: "1.05rem", fontWeight: 700, color: "var(--navy-900)" }}>
                Current vs. Target Proficiency
              </h3>
              <p className="muted small">
                Evaluated proficiency level compared to role benchmark
              </p>
            </div>
            <ProficiencyChart skills={data.skills} />
          </div>

          <div className="card">
            <div style={{ marginBottom: "14px" }}>
              <h3 style={{ fontSize: "1.05rem", fontWeight: 700, color: "var(--navy-900)" }}>
                Skill Gap Analysis
              </h3>
              <p className="muted small">
                Remaining level deficit per skill required for full career readiness
              </p>
            </div>
            <GapChart skills={data.skills} />
          </div>
        </div>
      )}
    </div>
  );
}