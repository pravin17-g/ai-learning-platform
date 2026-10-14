import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useApp } from '../context/AppContext.jsx';
import { http, ApiError } from '../api/http.js';

const EMAIL_PATTERN = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

export default function Register() {
  const { register } = useApp();
  const navigate = useNavigate();
  const [form, setForm] = useState({ name: '', email: '', password: '', confirm: '' });
  const [errors, setErrors] = useState({});
  const [message, setMessage] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleChange = (event) => {
    setForm({ ...form, [event.target.name]: event.target.value });
  };

  const validate = () => {
    const found = {};
    if (form.name.trim().length < 2) found.name = 'Please enter your full name (at least 2 characters).';
    if (!EMAIL_PATTERN.test(form.email.trim())) found.email = 'Please enter a valid email address.';
    if (form.password.length < 8) {
      found.password = 'Password must be at least 8 characters.';
    } else if (!/[a-zA-Z]/.test(form.password) || !/[0-9]/.test(form.password)) {
      found.password = 'Password must contain at least one letter and one number.';
    } else if (form.password.length > 72) {
      found.password = 'Password is too long (maximum 72 characters).';
    }
    if (form.confirm !== form.password) found.confirm = 'Passwords do not match.';
    return found;
  };

  const handleSubmit = async (event) => {
    event.preventDefault();
    setMessage('');
    const found = validate();
    setErrors(found);
    if (Object.keys(found).length > 0) return;

    setIsSubmitting(true);
    try {
      // 1. Create account on backend
      const registeredUser = await http.post('/register', {
        name: form.name.trim(),
        email: form.email.trim().toLowerCase(),
        password: form.password,
      });

      // 2. Log in to obtain JWT access token
      const loginRes = await http.post('/login', {
        email: form.email.trim().toLowerCase(),
        password: form.password,
      });

      if (!loginRes?.access_token) {
        throw new Error('Registration succeeded, but failed to retrieve an access token.');
      }

      // 3. Persist JWT token
      localStorage.setItem('token', loginRes.access_token);

      // 4. Update AppContext state
      register(registeredUser);

      // 5. Navigate to dashboard
      navigate('/dashboard', { replace: true });
    } catch (error) {
      setMessage(
        error instanceof ApiError
          ? error.message
          : error.message || 'Registration failed. Please try again.'
      );
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="auth-page">
      <div className="auth-card">
        <div className="auth-logo">🚀</div>
        <h1>Create your account</h1>
        <p className="auth-subtitle">Start finding your skill gaps and building your learning roadmap.</p>

        {message && (
          <div className="alert alert-error" role="alert">
            {message}
          </div>
        )}

        <form onSubmit={handleSubmit} noValidate>
          <div className="form-group">
            <label htmlFor="name">Full name</label>
            <input
              id="name"
              name="name"
              value={form.name}
              onChange={handleChange}
              placeholder="Your name"
              disabled={isSubmitting}
            />
            {errors.name && <div className="field-error">{errors.name}</div>}
          </div>

          <div className="form-group">
            <label htmlFor="email">Email</label>
            <input
              id="email"
              name="email"
              type="email"
              value={form.email}
              onChange={handleChange}
              placeholder="you@example.com"
              disabled={isSubmitting}
            />
            {errors.email && <div className="field-error">{errors.email}</div>}
          </div>

          <div className="form-group">
            <label htmlFor="password">Password</label>
            <input
              id="password"
              name="password"
              type="password"
              value={form.password}
              onChange={handleChange}
              placeholder="At least 8 characters (letters and numbers)"
              disabled={isSubmitting}
            />
            {errors.password && <div className="field-error">{errors.password}</div>}
          </div>

          <div className="form-group">
            <label htmlFor="confirm">Confirm password</label>
            <input
              id="confirm"
              name="confirm"
              type="password"
              value={form.confirm}
              onChange={handleChange}
              placeholder="Type the password again"
              disabled={isSubmitting}
            />
            {errors.confirm && <div className="field-error">{errors.confirm}</div>}
          </div>

          <button type="submit" className="btn btn-primary btn-block" disabled={isSubmitting}>
            {isSubmitting ? 'Creating account...' : 'Create account'}
          </button>
        </form>

        <p className="auth-footer">
          Already have an account? <Link to="/login">Log in</Link>
        </p>
      </div>
    </div>
  );
}