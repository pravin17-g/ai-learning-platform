
import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useApp } from "../context/AppContext.jsx";
import { http, ApiError } from "../api/http.js";

const EMAIL_PATTERN = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

export default function Login() {
  const { login } = useApp();
  const navigate = useNavigate();

  const [form, setForm] = useState({
    email: "",
    password: "",
  });

  const [errors, setErrors] = useState({});
  const [message, setMessage] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleChange = (event) => {
    setForm((previous) => ({
      ...previous,
      [event.target.name]: event.target.value,
    }));
  };

  const validate = () => {
    const found = {};

    if (!EMAIL_PATTERN.test(form.email.trim())) {
      found.email = "Please enter a valid email address.";
    }

    if (!form.password) {
      found.password = "Please enter your password.";
    }

    return found;
  };

  const handleSubmit = async (event) => {
    event.preventDefault();
    setMessage("");

    const found = validate();
    setErrors(found);

    if (Object.keys(found).length > 0) return;

    setIsSubmitting(true);

    try {
      // Authenticate with the real FastAPI backend.
      const response = await http("/login", {
        method: "POST",
        body: {
          email: form.email.trim().toLowerCase(),
          password: form.password,
        },
      });

      if (!response?.access_token) {
        throw new Error(
          "The server did not return an access token. Please check the login API response."
        );
      }

      // This key must match TOKEN_KEY in src/api/http.js.
      localStorage.setItem("token", response.access_token);

      // Update local application context as well.
      try {
        const profile = await http("/profile");
        login(profile);
      } catch (contextError) {
        login(form.email.trim().toLowerCase());
      }

      navigate("/dashboard", { replace: true });
    } catch (error) {
      // Remove an old, stale token if backend login is rejected.
      if (error instanceof ApiError && error.status === 401) {
        localStorage.removeItem("token");
      }

      setMessage(
        error instanceof ApiError
          ? error.message
          : error.message || "Login failed. Please try again."
      );
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleDemoLogin = async () => {
    setMessage("");
    setIsSubmitting(true);

    try {
      const response = await http("/demo-login", {
        method: "POST",
      });

      if (!response?.access_token) {
        throw new Error(
          "The server did not return an access token for the demo account."
        );
      }

      localStorage.setItem("token", response.access_token);

      try {
        const profile = await http("/profile");
        login(profile);
      } catch (contextError) {
        login({ name: "Pravin", email: "pravin@example.com", career_id: "full-stack" });
      }

      navigate("/dashboard", { replace: true });
    } catch (error) {
      setMessage(
        error instanceof ApiError
          ? error.message
          : error.message || "Demo login failed. Please try again."
      );
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="auth-page">
      <div className="auth-card">
        <div className="auth-logo">🎓</div>

        <h1>Welcome back</h1>

        <p className="auth-subtitle">
          Log in to continue your personalized learning journey.
        </p>

        {message && (
          <div className="alert alert-error" role="alert">
            {message}
          </div>
        )}

        <form onSubmit={handleSubmit} noValidate>
          <div className="form-group">
            <label htmlFor="email">Email</label>

            <input
              id="email"
              name="email"
              type="email"
              autoComplete="email"
              value={form.email}
              onChange={handleChange}
              placeholder="you@example.com"
              disabled={isSubmitting}
            />

            {errors.email && (
              <div className="field-error">{errors.email}</div>
            )}
          </div>

          <div className="form-group">
            <label htmlFor="password">Password</label>

            <input
              id="password"
              name="password"
              type="password"
              autoComplete="current-password"
              value={form.password}
              onChange={handleChange}
              placeholder="Enter your password"
              disabled={isSubmitting}
            />

            {errors.password && (
              <div className="field-error">{errors.password}</div>
            )}
          </div>

          <button
            type="submit"
            className="btn btn-primary btn-block"
            disabled={isSubmitting}
          >
            {isSubmitting ? "Logging in..." : "Log in"}
          </button>
        </form>

        <div className="auth-divider">or</div>

        <button
          type="button"
          className="btn btn-outline btn-block"
          onClick={handleDemoLogin}
          disabled={isSubmitting}
        >
          Try demo account (Pravin, Full Stack Developer)
        </button>

        <p
          className="form-hint"
          style={{ textAlign: "center", marginTop: 14 }}
        >
          Use a registered backend account to access protected features.
        </p>

        <p className="auth-footer">
          New here? <Link to="/register">Create an account</Link>
        </p>
      </div>
    </div>
  );
}
