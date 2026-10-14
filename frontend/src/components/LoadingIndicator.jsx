export default function LoadingIndicator({ message = 'Loading...' }) {
  return (
    <div className="loading" role="status">
      <div className="spinner" />
      <p>{message}</p>
    </div>
  );
}