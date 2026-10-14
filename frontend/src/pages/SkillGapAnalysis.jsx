import { Link } from 'react-router-dom';
import { useApp } from '../context/AppContext.jsx';
import useCareerSkills from '../hooks/useCareerSkills.js';
import LoadingIndicator from '../components/LoadingIndicator.jsx';
import ErrorMessage from '../components/ErrorMessage.jsx';
import EmptyState from '../components/EmptyState.jsx';
import ProgressBar from '../components/ProgressBar.jsx';
import { LEVEL_NAMES, calculateReadiness, statusBadgeClass } from '../services/skillUtils.js';

export default function SkillGapAnalysis() {
  const { careerId, assessed } = useApp();
  const { career, skills, loading, error, retry } = useCareerSkills(careerId);

  if (!careerId) {
    return (
      <EmptyState icon="🎯" title="Choose a career goal first"
        text="Pick a career so we can compare your skills with what it requires."
        actionLabel="Choose a career" to="/career" />
    );
  }
  if (loading) return <LoadingIndicator message="Analyzing your skills..." />;
  if (error) return <ErrorMessage message={error} onRetry={retry} />;
  if (!assessed[careerId]) {
    return (
      <EmptyState icon="📝" title="Complete your skill assessment first"
        text={`Rate your current skills for ${career.name} to see your skill gaps.`}
        actionLabel="Start assessment" to="/assessment" />
    );
  }

  const readiness = calculateReadiness(skills);
  const achieved = skills.filter((s) => s.status === 'Achieved').length;
  const improving = skills.filter((s) => s.status === 'Needs Improvement').length;
  const gaps = skills.filter((s) => s.status === 'Skill Gap').length;

  return (
    <div>
      <div className="page-header">
        <div>
          <h1>Skill-Gap Analysis</h1>
          <p>Your current skills compared with the requirements for <strong>{career.name}</strong>.</p>
        </div>
        <Link to="/roadmap" className="btn btn-primary">View learning roadmap</Link>
      </div>

      <div className="stats-grid">
        <div className="stat-card">
          <span className="stat-label">Skill-Readiness</span>
          <span className="stat-value">{readiness}%</span>
          <ProgressBar value={readiness} showPercent={false} />
        </div>
        <div className="stat-card">
          <span className="stat-label">Achieved</span>
          <span className="stat-value">{achieved}</span>
          <span className="stat-sub">target reached</span>
        </div>
        <div className="stat-card">
          <span className="stat-label">Needs Improvement</span>
          <span className="stat-value">{improving}</span>
          <span className="stat-sub">1 level below target</span>
        </div>
        <div className="stat-card">
          <span className="stat-label">Skill Gap</span>
          <span className="stat-value">{gaps}</span>
          <span className="stat-sub">2+ levels below target</span>
        </div>
      </div>

      <div className="card">
        <h2 className="card-title">Skill-by-skill results</h2>
        <div className="table-wrap">
          <table className="data-table">
            <thead>
              <tr>
                <th>Skill</th>
                <th>Current</th>
                <th>Target</th>
                <th>Gap</th>
                <th>Status</th>
              </tr>
            </thead>
            <tbody>
              {skills.map((skill) => (
                <tr key={skill.id}>
                  <td>
                    <strong>{skill.name}</strong>
                    <div className="muted small">{skill.priority} priority</div>
                  </td>
                  <td>
                    {skill.current} <span className="muted small">({LEVEL_NAMES[skill.current]})</span>
                  </td>
                  <td>
                    {skill.target} <span className="muted small">({LEVEL_NAMES[skill.target]})</span>
                  </td>
                  <td className="gap-value">{skill.gap > 0 ? `-${skill.gap}` : '0'}</td>
                  <td>
                    <span className={`badge ${statusBadgeClass(skill.status)}`}>{skill.status}</span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        <div className="rule-box">
          <strong>How status is decided:</strong> gap = target − current. Gap 0 is <em>Achieved</em>, gap 1 is{' '}
          <em>Needs Improvement</em>, and gap 2 or more is a <em>Skill Gap</em>. Readiness gives more weight to
          High-priority skills.
        </div>
      </div>
    </div>
  );
}