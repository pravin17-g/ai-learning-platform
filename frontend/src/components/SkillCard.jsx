import { LEVEL_NAMES } from '../services/skillUtils.js';

export default function SkillCard({ skill, value, onChange }) {
  return (
    <div className={`skill-card ${value ? 'rated' : ''}`}>
      <div className="skill-card-head">
        <div>
          <h3>{skill.name}</h3>
          <p className="muted small">{skill.objective}</p>
        </div>
        <span className={`badge badge-priority-${skill.priority.toLowerCase()}`}>
          {skill.priority} priority
        </span>
      </div>

      <div className="skill-card-meta">
        <span>
          Target level: <strong>{skill.target} ({LEVEL_NAMES[skill.target]})</strong>
        </span>
        {skill.prerequisite && (
          <span>
            Learn first: <strong>{skill.prerequisite}</strong>
          </span>
        )}
      </div>

      <div className="level-buttons" role="group" aria-label={`Rate your ${skill.name} skill`}>
        {[1, 2, 3, 4, 5].map((level) => (
          <button
            key={level}
            type="button"
            className={`level-btn ${value === level ? 'selected' : ''}`}
            onClick={() => onChange(skill.id, level)}
            aria-pressed={value === level}
          >
            <span className="level-number">{level}</span>
            <span className="level-name">{LEVEL_NAMES[level]}</span>
          </button>
        ))}
      </div>
    </div>
  );
}