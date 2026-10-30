import { MIN_PASSWORD_LENGTH } from "../utils/constants";
import { request } from "./client";

const EMAIL_PATTERN = /^\S+@\S+\.\S+$/;

const normalizeEmail = (email) => email.trim().toLowerCase();

function checkPassword(password) {
  if (password.length < MIN_PASSWORD_LENGTH) {
    return `Password must be at least ${MIN_PASSWORD_LENGTH} characters.`;
  }
  return null;
}

/** The person who is logged in (from the session cookie), or null. */
export async function fetchCurrentUser() {
  const result = await request("GET", "/auth/me");
  if (result.ok) return { ok: true, user: result.data.user };
  // 401 just means "not logged in". Anything else is a real problem.
  return result.status === 401 ? { ok: true, user: null } : result;
}

export async function signUp({ name, email, password }) {
  const cleanName = name.trim();
  const cleanEmail = normalizeEmail(email);

  if (!cleanName || !cleanEmail || !password) {
    return { ok: false, error: "Please fill in all fields." };
  }
  if (!EMAIL_PATTERN.test(cleanEmail)) {
    return { ok: false, error: "Please enter a valid email address." };
  }
  const passwordProblem = checkPassword(password);
  if (passwordProblem) return { ok: false, error: passwordProblem };

  const result = await request("POST", "/auth/register", {
    name: cleanName,
    email: cleanEmail,
    password,
  });
  return result.ok ? { ok: true, user: result.data.user } : result;
}

export async function signIn({ email, password }) {
  const cleanEmail = normalizeEmail(email);
  if (!cleanEmail || !password) {
    return { ok: false, error: "Please enter your email and password." };
  }

  const result = await request("POST", "/auth/login", { email: cleanEmail, password });
  return result.ok ? { ok: true, user: result.data.user } : result;
}

export async function signOut() {
  await request("POST", "/auth/logout", {});
}

/** Asks the server to email a reset link. Succeeds whether or not the address has an account. */
export async function requestPasswordReset(email) {
  const cleanEmail = normalizeEmail(email);
  if (!EMAIL_PATTERN.test(cleanEmail)) {
    return { ok: false, error: "Please enter a valid email address." };
  }
  return request("POST", "/auth/forgot", { email: cleanEmail });
}

/** Used on the reset screen, after the person arrives from the email link. */
export async function setNewPassword(token, password) {
  const passwordProblem = checkPassword(password);
  if (passwordProblem) return { ok: false, error: passwordProblem };
  return request("POST", "/auth/reset", { token, password });
}

/** The reset link looks like  http://localhost:5173/?reset_token=...  */
export function readResetToken() {
  return new URLSearchParams(window.location.search).get("reset_token") ?? "";
}

export function clearResetToken() {
  const url = new URL(window.location.href);
  if (url.searchParams.has("reset_token")) {
    url.searchParams.delete("reset_token");
    window.history.replaceState(null, "", url.pathname + url.search + url.hash);
  }
}
