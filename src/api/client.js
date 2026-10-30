/**
 * Talks to the Flask backend. Every function in src/api returns
 * { ok: true, data } or { ok: false, error, status } so screens can show
 * what went wrong instead of crashing.
 *
 * Requests go to "/api/...". In development Vite forwards them to Flask
 * (see vite.config.js); in production Flask serves the app itself.
 */

let onUnauthorized = () => {};

/** App registers this so an expired login sends the person back to the login page. */
export function setUnauthorizedHandler(handler) {
  onUnauthorized = handler;
}

export async function request(method, path, body) {
  let response;
  try {
    response = await fetch(`/api${path}`, {
      method,
      headers: body === undefined ? undefined : { "Content-Type": "application/json" },
      body: body === undefined ? undefined : JSON.stringify(body),
      credentials: "same-origin",
    });
  } catch {
    return {
      ok: false,
      status: 0,
      error: "Can't reach the server. Check your connection and that the backend is running.",
    };
  }

  let data = null;
  try {
    data = await response.json();
  } catch {
    // Not JSON, e.g. an error page from a proxy.
  }

  if (!response.ok) {
    // Logging in or out failing with 401 is expected, so only react to it elsewhere.
    if (response.status === 401 && !path.startsWith("/auth/")) onUnauthorized();

    const fallback =
      response.status >= 500
        ? "The server isn't responding properly. Is the Flask backend running?"
        : "Something went wrong. Please try again.";
    return { ok: false, status: response.status, error: data?.error ?? fallback };
  }

  return { ok: true, data };
}
