export default function ErrorMessage({ message = 'Something went wrong.', onRetry }) {
  return (
    <div className="error-box" role="alert">
      <span>⚠️ {message}</span>
      {onRetry && (
        <button className="btn btn-outline" onClick={onRetry}>
          Try again
        </button>
      )}
    </div>
  );
}