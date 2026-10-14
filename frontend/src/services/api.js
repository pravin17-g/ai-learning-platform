import axios from 'axios';
import { careers, skillCatalog, careerRequirements } from './sampleData.js';

// Axios client is READY but NOT USED yet (the backend does not exist in Phase 2).
// In Phase 3 we will use it, for example: apiClient.get('/careers')
export const apiClient = axios.create({
  baseURL: 'http://localhost:8000',
  timeout: 10000,
});

// Pretends to be a network request: waits a moment, then returns data.
// If the function throws an error, the promise is rejected (like a failed request).
function simulateRequest(getData, delay = 450) {
  return new Promise((resolve, reject) => {
    setTimeout(() => {
      try {
        resolve(getData());
      } catch (error) {
        reject(error);
      }
    }, delay);
  });
}

// List of careers (with skill count and a few skill names for the cards)
export function getCareers() {
  return simulateRequest(() =>
    careers.map((career) => ({
      ...career,
      skillCount: careerRequirements[career.id].length,
      topSkills: careerRequirements[career.id]
        .slice(0, 5)
        .map((req) => req.label || skillCatalog[req.skillId].name),
    }))
  );
}

// One career with its required skills (targets, priorities, hours, resources)
export function getCareerDetails(careerId) {
  return simulateRequest(() => {
    const career = careers.find((c) => c.id === careerId);
    const requirements = careerRequirements[careerId];
    if (!career || !requirements) {
      throw new Error('This career could not be found.');
    }

    const skills = requirements.map((req) => {
      const skill = skillCatalog[req.skillId];
      return {
        id: req.skillId,
        name: req.label || skill.name,
        target: req.target,
        priority: req.priority,
        prerequisite: req.prerequisite,
        order: req.order,
        hoursPerLevel: skill.hoursPerLevel,
        objective: skill.objective,
        resource: skill.resource,
      };
    });

    return { career, skills };
  });
}