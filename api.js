// All communication with the Flask backend lives in this file.
// The address comes from the VITE_API_URL environment variable:
//   development: frontend/.env.development
//   production : set in the Vercel dashboard (never hard-coded here)
const API_URL = (import.meta.env.VITE_API_URL || "").replace(/\/+$/, "");
const TIMEOUT_MS = 90_000; // free hosts can take a while to wake up

export class ApiError extends Error {}

function requireApiUrl() {
  if (!API_URL) {
    throw new ApiError(
      "The API address is not configured. Set the VITE_API_URL environment variable and rebuild the frontend."
    );
  }
}

async function request(path, options = {}) {
  requireApiUrl();
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), TIMEOUT_MS);
  try {
    const response = await fetch(`${API_URL}${path}`, { ...options, signal: controller.signal });
    let body = null;
    try {
      body = await response.json();
    } catch {
      /* non-JSON response */
    }
    if (!response.ok) {
      throw new ApiError(body?.error || `The server returned an error (${response.status}).`);
    }
    return body;
  } catch (error) {
    if (error instanceof ApiError) throw error;
    if (error.name === "AbortError") {
      throw new ApiError("The server took too long to respond. Please try again in a minute.");
    }
    throw new ApiError("Cannot reach the server. Check your internet connection and that the backend is running.");
  } finally {
    clearTimeout(timer);
  }
}

export function predictImage(file) {
  const form = new FormData();
  form.append("file", file); // the backend expects the field name "file"
  return request("/predict", { method: "POST", body: form });
}

export function getModelInfo() {
  return request("/model-info");
}
