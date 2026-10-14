import { useState } from 'react';
import { useApp } from '../context/AppContext.jsx';

const EDUCATION_LEVELS = [
  'High School',
  'Diploma',
  'Undergraduate - Year 1',
  'Undergraduate - Year 2',
  'Undergraduate - Year 3',
  'Undergraduate - Year 4',
  'Postgraduate',
  'Working Professional',
];

export default function StudentProfile() {
  const { user, updateUser } = useApp();
  const [form, setForm] = useState({
    name: user.name,
    education: user.education || '',
    studyHoursPerWeek: String(user.studyHoursPerWeek ?? 10),
  });
  const [errors, setErrors] = useState({});
  const [saved, setSaved] = useState(false);

  const handleChange = (event) => {
    setSaved(false);
    setForm({ ...form, [event.target.name]: event.target.value });
  };

  const handleSubmit = (event) => {
    event.preventDefault();
    const found = {};
    const hours = Number(form.studyHoursPerWeek);

    if (form.name.trim().length < 2) found.name = 'Please enter your full name.';
    if (!form.education) found.education = 'Please choose your education level.';
    if (!Number.isFinite(hours) || hours < 1 || hours > 60) {
      found.studyHoursPerWeek = 'Enter a number of hours between 1 and 60.';
    }

    setErrors(found);
    if (Object.keys(found).length > 0) return;

    updateUser({
      name: form.name.trim(),
      education: form.education,
      studyHoursPerWeek: hours,
    });
    setSaved(true);
  };

  return (
    <div>
      <div className="page-header">
        <div>
          <h1>Student Profile</h1>
          <p>Your study time helps us estimate how long your learning roadmap will take.</p>
        </div>
      </div>

      <div className="card" style={{ maxWidth: 620 }}>
        {saved && <div className="alert alert-success">✅ Profile saved successfully.</div>}

        <form onSubmit={handleSubmit} noValidate>
          <div className="form-group">
            <label htmlFor="name">Full name</label>
            <input id="name" name="name" value={form.name} onChange={handleChange} />
            {errors.name && <div className="field-error">{errors.name}</div>}
          </div>

          <div className="form-group">
            <label htmlFor="email">Email</label>
            <input id="email" value={user.email} disabled />
            <div className="form-hint">Your email cannot be changed.</div>
          </div>

          <div className="form-group">
            <label htmlFor="education">Education level</label>
            <select id="education" name="education" value={form.education} onChange={handleChange}>
              <option value="">Select your education level</option>
              {EDUCATION_LEVELS.map((level) => (
                <option key={level} value={level}>{level}</option>
              ))}
            </select>
            {errors.education && <div className="field-error">{errors.education}</div>}
          </div>

          <div className="form-group">
            <label htmlFor="studyHoursPerWeek">Study hours available per week</label>
            <input
              id="studyHoursPerWeek"
              name="studyHoursPerWeek"
              type="number"
              min="1"
              max="60"
              value={form.studyHoursPerWeek}
              onChange={handleChange}
            />
            {errors.studyHoursPerWeek && <div className="field-error">{errors.studyHoursPerWeek}</div>}
          </div>

          <button type="submit" className="btn btn-primary">Save profile</button>
        </form>
      </div>
    </div>
  );
}