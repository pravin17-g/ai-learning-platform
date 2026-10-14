export default function ProgressBar({ value, label, showPercent = true, tone = 'blue' }) {
  const percent = Math.min(Math.max(Number(value) || 0, 0), 100);

  return (
    <div className="progress-wrap">
      {(label || showPercent) && (
        <div className="progress-label">
          <span>{label}</span>
          {showPercent && <span>{percent}%</span>}
        </div>
      )}
      <div
        className="progress"
        role="progressbar"
        aria-valuenow={percent}
        aria-valuemin={0}
        aria-valuemax={100}
      >
        <div className={`progress-fill ${tone === 'green' ? 'tone-green' : ''}`} style={{ width: `${percent}%` }} />
      </div>
    </div>
  );
}