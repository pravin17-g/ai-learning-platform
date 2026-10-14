import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useApp } from '../context/AppContext.jsx';
import useCareerSkills from '../hooks/useCareerSkills.js';
import SkillCard from '../components/SkillCard.jsx';
import ProgressBar from '../components/ProgressBar.jsx';
import LoadingIndicator from '../components/LoadingIndicator.jsx';
import ErrorMessage from '../components/ErrorMessage.jsx';
import EmptyState from '../components/EmptyState.jsx';
import { LEVEL_NAMES } from '../services/skillUtils.js';

export default function SkillAssessment() {
  const navigate = useNavigate();
  const { careerId, assessed, saveAssessment } = useApp();
  const { career, skills, loading, error, retry } = useCareerSkills(careerId);
  const [draft, setDraft] = useState({}); // ratings changed on this page

  if (!careerId) {
    return (
      <EmptyState
        icon="🎯"
        title="Choose a career goal first"
        text="We need to know your career goal so we can show the right skills to assess."
        actionLabel="Choose a career"
        to="/career"
      />
    );
  }
  if (loading) return <LoadingIndicator message="Loading skills to assess..." />;
  if (error) return <ErrorMessage message={error} onRetry={retry} />;

  const isReassessment = Boolean(assessed[careerId]);

  // The value shown = new choice on this page, otherwise the saved rating
  const valueOf = (skill) => draft[skill.id] ?? skill.current;
  const ratedCount = skills.filter((skill) => valueOf(skill) !== null).length;
  const allRated = ratedCount === skills.length;
  const percent = Math.round((ratedCount / skills.length) * 100);

  const handleChange = (skillId, level) => {
    setDraft((prev) => ({ ...prev, [skillId]: level }));
  };

  const handleSave = () => {
    const finalRatings = {};
    skills.forEach((skill) => {
      finalRatings[skill.id] = valueOf(skill);
    });
    saveAssessment(careerId, finalRatings);
    navigate('/gap-analysis');
  };

  return (
    <div>
      <div className="page-header">
        <div>
          <h1>{isReassessment ? 'Skill Reassessment' : 'Skill Assessment'}</h1>
          <p>
            Rate your current level for each <strong>{career.name}</strong> skill. Be honest, because
            accurate ratings give you a better roadmap.
          </p>
        </div>
      </div>

      {isReassessment && (
        <div className="alert alert-info">
          You have already assessed this career. Update any ratings that have improved, then save to
          refresh your skill gaps and roadmap.
        </div>
      )}

      <div className="legend-card">
        {[1, 2, 3, 4, 5].map((level) => (
          <div key={level} className="legend-item">
            <strong>{level}</strong> {LEVEL_NAMES[level]}
          </div>
        ))}
      </div>

      <div className="skill-list">
        {skills.map((skill) => (
          <SkillCard key={skill.id} skill={skill} value={valueOf(skill)} onChange={handleChange} />
        ))}
      </div>

      <div className="sticky-bar">
        <ProgressBar value={percent} label={`Rated ${ratedCount} of ${skills.length} skills`} />
        <button className="btn btn-primary" onClick={handleSave} disabled={!allRated}>
          {isReassessment ? 'Save reassessment' : 'Save assessment'}
        </button>
      </div>
    </div>
  );
}