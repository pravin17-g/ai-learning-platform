import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { useApp } from '../context/AppContext.jsx';
import { getCareers } from '../services/api.js';
import LoadingIndicator from '../components/LoadingIndicator.jsx';
import ErrorMessage from '../components/ErrorMessage.jsx';

export default function CareerGoals() {
  const { careerId, selectCareer, assessed } = useApp();
  const [careers, setCareers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [reloadKey, setReloadKey] = useState(0);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    setError('');

    getCareers()
      .then((data) => {
        if (cancelled) return;
        setCareers(data);
        setLoading(false);
      })
      .catch((err) => {
        if (cancelled) return;
        setError(err.message || 'Could not load careers.');
        setLoading(false);
      });

    return () => {
      cancelled = true;
    };
  }, [reloadKey]);

  if (loading) return <LoadingIndicator message="Loading career paths..." />;
  if (error) return <ErrorMessage message={error} onRetry={() => setReloadKey((k) => k + 1)} />;

  return (
    <div>
      <div className="page-header">
        <div>
          <h1>Career Goals</h1>
          <p>Choose the career you want to prepare for. You can change it at any time.</p>
        </div>
      </div>

      <div className="career-grid">
        {careers.map((career) => {
          const isSelected = career.id === careerId;
          const extra = career.skillCount - career.topSkills.length;

          return (
            <div key={career.id} className={`career-card ${isSelected ? 'selected' : ''}`}>
              <div className="career-icon">{career.icon}</div>
              <h2>{career.name}</h2>
              <p className="muted">{career.description}</p>

              <div>
                <p className="small muted" style={{ marginBottom: 6 }}>
                  {career.skillCount} required skills, including:
                </p>
                <div className="chip-row">
                  {career.topSkills.map((name) => (
                    <span key={name} className="chip">{name}</span>
                  ))}
                  {extra > 0 && <span className="chip">+{extra} more</span>}
                </div>
              </div>

              {isSelected ? (
                <button className="btn btn-outline" disabled>✓ Your current goal</button>
              ) : (
                <button className="btn btn-primary" onClick={() => selectCareer(career.id)}>
                  Select this career
                </button>
              )}
            </div>
          );
        })}
      </div>

      {careerId && (
        <div className="card" style={{ marginTop: 22 }}>
          <h2 className="card-title">Next step</h2>
          <p className="muted">
            {assessed[careerId]
              ? 'You have already assessed this career. You can view your results or update your ratings.'
              : 'Rate your current skills for this career so we can find your skill gaps.'}
          </p>
          <div className="btn-row">
            <Link to="/assessment" className="btn btn-primary">
              {assessed[careerId] ? 'Reassess my skills' : 'Start skill assessment'}
            </Link>
            {assessed[careerId] && (
              <Link to="/gap-analysis" className="btn btn-outline">View skill-gap analysis</Link>
            )}
          </div>
        </div>
      )}
    </div>
  );
}