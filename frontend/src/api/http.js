import axios from "axios";

export const TOKEN_KEY = "token";

export class ApiError extends Error {
  constructor(message, status = 0, response = null) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.response = response;
  }
}

export const apiClient = axios.create({
  baseURL: "http://127.0.0.1:8000",
  timeout: 10000,
});

function buildMessage(error) {
  const status = error.response?.status ?? 0;
  const data = error.response?.data;

  if (Array.isArray(data?.detail)) {
    return data.detail.map((item) => item.msg).join("; ");
  }

  if (typeof data?.detail === "string") {
    return data.detail;
  }

  if (data?.errors?.length) {
    return data.errors.map((item) => item.message).join(" ");
  }

  if (status === 401) {
    return "Login required. Please log in again.";
  }

  if (status === 403) {
    return "You do not have permission to perform this action.";
  }

  if (status === 404) {
    return "Requested API endpoint was not found.";
  }

  if (status >= 500) {
    return "Backend server error. Check the backend terminal.";
  }

  if (!error.response) {
    return "Cannot connect to the backend. Check whether http://127.0.0.1:8000/docs opens.";
  }

  return `Request failed (${status}).`;
}

export async function http(path, options = {}) {
  const {
    method = "GET",
    body,
    params,
    headers = {},
  } = options;

  const token = localStorage.getItem(TOKEN_KEY);

  try {
    const response = await apiClient.request({
      url: path,
      method,
      data: body,
      params,
      headers: {
        ...headers,
        ...(token
          ? { Authorization: `Bearer ${token}` }
          : {}),
      },
    });

    return response.data;
  } catch (error) {
    const status = error.response?.status ?? 0;
    const isAuthCall =
      path.includes("/login") ||
      path.includes("/register") ||
      path.includes("/demo-login");

    if (status === 401 && !isAuthCall) {
      localStorage.removeItem(TOKEN_KEY);
      localStorage.removeItem("skillgap-platform-phase2-state");

      if (window.location.pathname !== "/login") {
        window.location.href = "/login";
      }
    }

    throw new ApiError(
      buildMessage(error),
      status,
      error.response ?? null
    );
  }
}

http.get = (path, options = {}) =>
  http(path, { ...options, method: "GET" });

http.post = (path, body, options = {}) =>
  http(path, { ...options, method: "POST", body });

http.put = (path, body, options = {}) =>
  http(path, { ...options, method: "PUT", body });

http.patch = (path, body, options = {}) =>
  http(path, { ...options, method: "PATCH", body });

http.delete = (path, options = {}) =>
  http(path, { ...options, method: "DELETE" });

export default http;