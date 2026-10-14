import { ApiError, http } from "./http";

// Returns null when the student has no roadmap yet.
export async function getMyProgress(career) {
  try {
    const params = career ? { career } : {};
    return await http("/progress/me", { params });
  } catch (e) {
    if (e instanceof ApiError && (e.status === 404 || e.status === 400)) return null;
    throw e;
  }
}

export const getDashboard = (career) =>
  http("/dashboard/me", career ? { params: { career } } : {});

export const reassess = (levels, career) =>
  http("/assessments/reassess", { method: "POST", body: { levels, career } });