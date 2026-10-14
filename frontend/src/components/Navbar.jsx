import { useState } from 'react';
import { NavLink } from 'react-router-dom';
import { useApp } from '../context/AppContext.jsx';

const links = [
  { to: '/dashboard', label: 'Dashboard', icon: '🏠' },
  { to: '/profile', label: 'Student Profile', icon: '👤' },
  { to: '/career', label: 'Career Goals', icon: '🎯' },
  { to: '/assessment', label: 'Skill Assessment', icon: '📝' },
  { to: '/gap-analysis', label: 'Skill-Gap Analysis', icon: '📊' },
  { to: '/roadmap', label: 'Learning Roadmap', icon: '🗺️' },
  { to: '/progress', label: 'Progress Tracker', icon: '✅' },
];

export default function Navbar() {
  const [open, setOpen] = useState(false);
  const { user, logout } = useApp();

  const initials = user?.name
    ? user.name.split(' ').map((part) => part[0]).slice(0, 2).join('').toUpperCase()
    : '?';

  return (
    <>
      {/* Top bar, visible on phones only */}
      <header className="mobile-topbar">
        <button className="menu-btn" onClick={() => setOpen(!open)} aria-label="Open or close menu">
          ☰
        </button>
        <span className="mobile-title">Skill-Gap Platform</span>
      </header>

      {open && <div className="sidebar-overlay" onClick={() => setOpen(false)} />}

      <aside className={`sidebar ${open ? 'sidebar-open' : ''}`}>
        <div className="sidebar-brand">
          <span className="brand-logo">🎓</span>
          <div>
            <strong>Skill-Gap Platform</strong>
            <small>AI Personalized Learning</small>
          </div>
        </div>

        <nav className="sidebar-nav">
          {links.map((link) => (
            <NavLink
              key={link.to}
              to={link.to}
              onClick={() => setOpen(false)}
              className={({ isActive }) => (isActive ? 'nav-link active' : 'nav-link')}
            >
              <span className="nav-icon">{link.icon}</span>
              {link.label}
            </NavLink>
          ))}
        </nav>

        <div className="sidebar-footer">
          <div className="user-box">
            <div className="avatar">{initials}</div>
            <div className="user-info">
              <strong>{user?.name}</strong>
              <small>{user?.email}</small>
            </div>
          </div>
          <button className="btn btn-ghost btn-block" onClick={logout}>
            Log out
          </button>
        </div>
      </aside>
    </>
  );
}