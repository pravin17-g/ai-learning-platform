import { useEffect, useState } from 'react';
import { useApp } from '../context/AppContext.jsx';
import { getCareerDetails } from '../services/api.js';
import { calculateGap, getStatus } from '../services/skillUtils.js';

export default function useCareerSkills(careerId) {
  const { ratings } = useApp();
  const [career, setCareer] = useState(null);
  const [baseSkills, setBaseSkills] = useState([]);
  const [loading, setLoading] = useState(Boolean(careerId));
  const [error, setError] = useState('');
  const [reloadKey, setReloadKey] = useState(0);

  useEffect(() => {
    if (!careerId) return undefined;

    let cancelled = false;
    setLoading(true);
    setError('');

    getCareerDetails(careerId)
      .then((data) => {
        if (cancelled) return;
        setCareer(data.career);
        setBaseSkills(data.skills);
        setLoading(false);
      })
      .catch((err) => {
        if (cancelled) return;
        setError(err.message || 'Something went wrong while loading skills.');
        setLoading(false);
      });

    return () => {
      cancelled = true;
    };
  }, [careerId, reloadKey]);

  // Add current level, gap, and status to every skill
  const skills = baseSkills.map((skill) => {
    const current = ratings[skill.id] ?? null; // null = not rated yet
    const gap = current === null ? null : calculateGap(skill.target, current);
    return {
      ...skill,
      current,
      gap,
      status: gap === null ? null : getStatus(gap),
    };
  });

  return {
    career,
    skills,
    loading,
    error,
    retry: () => setReloadKey((key) => key + 1),
  };
}