import { createContext, useContext, useEffect, useState } from 'react';
import {
  sampleStudent,
  sampleCareerId,
  sampleRatings,
  sampleAssessed,
  sampleActivityStatus,
} from '../services/sampleData.js';

// TEMPORARY: the browser's localStorage keeps data after a page refresh.
// In Phase 3/4 this will be replaced by the backend and SQLite database.
const STORAGE_KEY = 'skillgap-platform-phase2-state';

const emptyState = {
  isLoggedIn: false,
  user: null,
  careerId: null,
  ratings: {},        // { skillId: 1-5 }
  assessed: {},       // { careerId: true }
  activityStatus: {}, // { skillId: 'Not Started' | 'In Progress' | 'Completed' }
};

function loadSavedState() {
  try {
    const saved = localStorage.getItem(STORAGE_KEY);
    const token = localStorage.getItem('token');
    if (saved) {
      const parsed = JSON.parse(saved);
      return {
        ...emptyState,
        ...parsed,
        isLoggedIn: Boolean(token && parsed.isLoggedIn),
      };
    }
  } catch {
    // If anything goes wrong, just start fresh
  }
  return emptyState;
}

const AppContext = createContext(null);

export function AppProvider({ children }) {
  const [state, setState] = useState(loadSavedState);

  // Save to localStorage every time the state changes
  useEffect(() => {
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(state));
    } catch {
      // Ignore storage errors
    }
  }, [state]);

  // Login handler supporting backend profile payload or email
  const login = (userData) => {
    if (typeof userData === 'string') {
      setState((prev) => ({
        ...prev,
        isLoggedIn: true,
        user: prev.user && prev.user.email.toLowerCase() === userData.toLowerCase()
          ? prev.user
          : { name: userData.split('@')[0], email: userData, education: '', studyHoursPerWeek: 10 },
      }));
      return { ok: true };
    }

    if (userData && typeof userData === 'object') {
      setState((prev) => ({
        ...prev,
        isLoggedIn: true,
        user: {
          name: userData.name || prev.user?.name || '',
          email: userData.email || prev.user?.email || '',
          education: userData.education ?? prev.user?.education ?? '',
          studyHoursPerWeek: userData.study_hours_per_week ?? userData.studyHoursPerWeek ?? prev.user?.studyHoursPerWeek ?? 10,
        },
        careerId: userData.career_id || userData.career?.id || prev.careerId,
      }));
      return { ok: true };
    }

    setState((prev) => ({ ...prev, isLoggedIn: true }));
    return { ok: true };
  };

  // Loads the sample student so you can see a fully working dashboard
  const loginAsDemo = () => {
    setState({
      isLoggedIn: true,
      user: { ...sampleStudent },
      careerId: sampleCareerId,
      ratings: { ...sampleRatings },
      assessed: { ...sampleAssessed },
      activityStatus: { ...sampleActivityStatus },
    });
  };

  // New student starts with profile and session
  const register = (userData) => {
    setState({
      ...emptyState,
      isLoggedIn: true,
      user: {
        name: userData?.name || '',
        email: userData?.email || '',
        education: userData?.education || '',
        studyHoursPerWeek: userData?.study_hours_per_week ?? userData?.studyHoursPerWeek ?? 10,
      },
      careerId: userData?.career_id || null,
    });
  };

  const logout = () => {
    localStorage.removeItem('token');
    localStorage.removeItem(STORAGE_KEY);
    setState(emptyState);
  };

  const updateUser = (changes) =>
    setState((prev) => ({ ...prev, user: { ...prev.user, ...changes } }));

  const selectCareer = (careerId) => setState((prev) => ({ ...prev, careerId }));

  // Saves all ratings for a career and marks it as assessed
  const saveAssessment = (careerId, newRatings) =>
    setState((prev) => ({
      ...prev,
      ratings: { ...prev.ratings, ...newRatings },
      assessed: { ...prev.assessed, [careerId]: true },
    }));

  const setActivityStatus = (skillId, status) =>
    setState((prev) => ({
      ...prev,
      activityStatus: { ...prev.activityStatus, [skillId]: status },
    }));

  const value = {
    ...state,
    login,
    loginAsDemo,
    register,
    logout,
    updateUser,
    selectCareer,
    saveAssessment,
    setActivityStatus,
  };

  return <AppContext.Provider value={value}>{children}</AppContext.Provider>;
}

export function useApp() {
  const context = useContext(AppContext);
  if (!context) throw new Error('useApp must be used inside AppProvider');
  return context;
}