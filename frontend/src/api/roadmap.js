
import { ApiError, http } from "./http";

// Get the student's roadmap
export async function getRoadmap(career) {
  try {
    const params = career ? { career } : {};
    return await http("/roadmap/me", { params });
  } catch (error) {
    if (error instanceof ApiError && (error.status === 404 || error.status === 400)) {
      return null;
    }
    throw error;
  }
}

// Generate a learning roadmap
export async function generateRoadmap(data) {
  return http("/roadmap/generate", {
    method: "POST",
    body: data,
  });
}

// Update a roadmap activity
export async function updateActivity(activityId, statusOrData, hoursCompleted) {
  const path = "/roadmap/activities/" + encodeURIComponent(activityId);
  const body =
    typeof statusOrData === "object" && statusOrData !== null
      ? statusOrData
      : {
          status: statusOrData,
          ...(hoursCompleted !== undefined ? { hours_completed: hoursCompleted } : {}),
        };

  return http(path, {
    method: "PATCH",
    body,
  });
}
