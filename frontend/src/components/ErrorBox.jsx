export default function ErrorBox({ error, onRetry }) {
  if (!error) return null;
  return (
    <div role="alert" className="card" style={{ borderLeft: "4px solid crimson" }}>
      <p style={{ color: "crimson", margin: 0 }}>{error.message}</p>
      {error.status === 401 && (
        <p><a href="/login">Go to login</a></p> /* ADAPT: your login route */
      )}
      {onRetry && error.status !== 401 && (
        <button className="btn" onClick={onRetry}>Try again</button>
      )}
    </div>
  );
}