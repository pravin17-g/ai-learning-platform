// Small helper functions used by the pages.
// Rule-based and simple. This is NOT machine learning.

export const LEVEL_NAMES = {
  1: 'Beginner',
  2: 'Basic',
  3: 'Intermediate',
  4: 'Advanced',
  5: 'Expert',
};

export const PRIORITY_WEIGHT = { High: 3, Medium: 2, Low: 1 };

export const ACTIVITY_STATUSES = ['Not Started', 'In Progress', 'Completed'];

// gap = target - current (never below 0)
export function calculateGap(target, current) {
  return Math.max(target - current, 0);
}

// gap 0 -> Achieved, gap 1 -> Needs Improvement, gap 2+ -> Skill Gap
export function getStatus(gap) {
  if (gap === 0) return 'Achieved';
  if (gap === 1) return 'Needs Improvement';
  return 'Skill Gap';
}

// CSS class for the status badge
export function statusBadgeClass(status) {
  if (status === 'Achieved') return 'badge-achieved';
  if (status === 'Needs Improvement') return 'badge-improve';
  return 'badge-gap';
}

// "In Progress" -> "inprogress" (used for CSS class names)
export function statusSlug(status) {
  return status.toLowerCase().replace(/\s+/g, '');
}

// Readiness % = sum(min(current/target, 1) x weight) / sum(weight) x 100
export function calculateReadiness(skills) {
  let earned = 0;
  let totalWeight = 0;
  skills.forEach((skill) => {
    const weight = PRIORITY_WEIGHT[skill.priority];
    const current = skill.current ?? 0;
    earned += Math.min(current / skill.target, 1) * weight;
    totalWeight += weight;
  });
  return totalWeight === 0 ? 0 : Math.round((earned / totalWeight) * 100);
}

// Roadmap = skills with a gap, in the suggested learning order.
// estimatedHours = gap x hoursPerLevel
export function buildRoadmap(skills) {
  return skills
    .filter((skill) => skill.gap > 0)
    .sort((a, b) => a.order - b.order)
    .map((skill, index) => ({
      ...skill,
      step: index + 1,
      estimatedHours: skill.gap * skill.hoursPerLevel,
    }));
}

// Status of one activity (defaults to Not Started)
export function getActivityStatus(activityStatus, skillId) {
  return activityStatus[skillId] || 'Not Started';
}

// Totals used by the dashboard, roadmap, and progress tracker
export function summarizeProgress(roadmap, activityStatus) {
  const statusOf = (item) => getActivityStatus(activityStatus, item.id);
  const completed = roadmap.filter((item) => statusOf(item) === 'Completed');
  const inProgress = roadmap.filter((item) => statusOf(item) === 'In Progress');
  const notStarted = roadmap.filter((item) => statusOf(item) === 'Not Started');

  const totalHours = roadmap.reduce((sum, item) => sum + item.estimatedHours, 0);
  const completedHours = completed.reduce((sum, item) => sum + item.estimatedHours, 0);

  return {
    total: roadmap.length,
    completed: completed.length,
    inProgress: inProgress.length,
    notStarted: notStarted.length,
    totalHours,
    completedHours,
    completionPct: roadmap.length ? Math.round((completed.length / roadmap.length) * 100) : 100,
    hoursPct: totalHours ? Math.round((completedHours / totalHours) * 100) : 100,
  };
}