import { ACTIVITY_STATUSES, statusSlug } from '../services/skillUtils.js';

export default function RoadmapCard({ item, status, onStatusChange, compact = false }) {
  return (
    <article className={`roadmap-card ${status === 'Completed' ? 'is-completed' : ''}`}>
      <div className="step-number">{item.step}</div>

      <div className="roadmap-body">
        <div className="roadmap-head">
          <h3>{item.name}</h3>
          <span className={`badge badge-activity-${statusSlug(status)}`}>{status}</span>
        </div>

        {!compact && (
          <p className="roadmap-objective">
            <strong>Learning objective:</strong> {item.objective}
          </p>
        )}

        <div className="roadmap-meta">
          <span>⏱ {item.estimatedHours} hours</span>
          <span>📈 Level {item.current} → {item.target}</span>
          {!compact && item.prerequisite && <span>🔗 Learn first: {item.prerequisite}</span>}
          <a href={item.resource.url} target="_blank" rel="noopener noreferrer">
            📚 {item.resource.title}
          </a>
        </div>

        {onStatusChange && (
          <div className="segmented" role="group" aria-label={`Status of ${item.name}`}>
            {ACTIVITY_STATUSES.map((option) => (
              <button
                key={option}
                type="button"
                className={`segment seg-${statusSlug(option)} ${status === option ? 'active' : ''}`}
                onClick={() => onStatusChange(item.id, option)}
              >
                {option}
              </button>
            ))}
          </div>
        )}
      </div>
    </article>
  );
}