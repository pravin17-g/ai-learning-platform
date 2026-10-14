import { Link } from 'react-router-dom';

export default function EmptyState({ icon = '📌', title, text, actionLabel, to }) {
  return (
    <div className="card empty-state">
      <div className="empty-icon">{icon}</div>
      <h2>{title}</h2>
      <p>{text}</p>
      {to && (
        <Link to={to} className="btn btn-primary">
          {actionLabel}
        </Link>
      )}
    </div>
  );
}