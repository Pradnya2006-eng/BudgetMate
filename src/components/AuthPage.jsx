import { useState } from "react";
import { requestPasswordReset, signIn, signUp } from "../api/auth";
import { MIN_PASSWORD_LENGTH } from "../utils/constants";
import PasswordInput from "./PasswordInput";

const COPY = {
  login: {
    title: "Welcome Back!",
    subtitle: "Log in to manage your expenses",
    submit: "Log in",
  },
    admin: {
    title: "Admin Login",
    subtitle: "Sign in to manage BudgetMate",
    submit: "Log in as admin",
  },
  register: {
    title: "Create Account",
    subtitle: "Start managing your money today",
    submit: "Create account",
  },
  forgot: {
    title: "Forgot your password?",
    subtitle: "Enter your email and we'll send you a link to choose a new one",
    submit: "Send reset link",
  },
};

/**
 * `notice` is a message to show on arrival (e.g. "Password updated"),
 * `startupError` is set if the server couldn't be reached at load time, and
 * `onAuthenticated` receives the user after a successful log in or sign up.
 */
export default function AuthPage({ notice: initialNotice = "", startupError = "", onAuthenticated }) {
  const [mode, setMode] = useState("login");
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState(startupError);
  const [notice, setNotice] = useState(initialNotice);
  const [busy, setBusy] = useState(false);

  const copy = COPY[mode];

  const switchMode = (next, message = "") => {
    setMode(next);
    setPassword("");
    setError("");
    setNotice(message);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");
    setNotice("");
    setBusy(true);

    let result;
    if (mode === "register") {
      result = await signUp({ name, email, password });
    } else if (mode === "forgot") {
      result = await requestPasswordReset(email);
      if (result.ok) {
        setNotice(
          `If an account exists for ${email.trim()}, a password reset link is on its way. It can take a minute and may land in spam.`
        );
      }
    } else {
      result = await signIn({ email, password });
    }

    if (!result.ok) {
      setBusy(false);
      setError(result.error);
      return;
    }
    if (mode === "admin" && result.user.role !== "admin") {
  setBusy(false);
  setError("This account does not have administrator access.");
  return;
}

    // Log in and sign up hand back the user; App then shows the dashboard.
    if (mode !== "forgot") onAuthenticated(result.user);
    else setBusy(false);
  };

  return (
    <main className="auth-page">
      <div className="auth-card">
        <div className="brand">
          <div className="brand-logo" aria-hidden="true">💰</div>
          <h1>BudgetMate</h1>
          <p className="tagline">🌱 Track. 🐷 Budget. 🪙 Save.</p>
        </div>

        <h2>{copy.title}</h2>
        <p className="auth-subtitle">{copy.subtitle}</p>

        <form onSubmit={handleSubmit} noValidate>
          {mode === "register" && (
            <div className="field">
              <label htmlFor="name">Full name</label>
              <input
                id="name"
                className="input"
                type="text"
                value={name}
                onChange={(e) => setName(e.target.value)}
                autoComplete="name"
                placeholder="Enter your name"
              />
            </div>
          )}

          <div className="field">
            <label htmlFor="email">Email</label>
            <input
              id="email"
              className="input"
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              autoComplete="email"
              placeholder="you@example.com"
            />
          </div>

          {mode !== "forgot" && (
            <div className="field">
              <label htmlFor="password">Password</label>
              <PasswordInput
                id="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                autoComplete={mode === "register" ? "new-password" : "current-password"}
                placeholder={
                  mode === "register"
                    ? `At least ${MIN_PASSWORD_LENGTH} characters`
                    : "Enter your password"
                }
              />
              {mode === "login" && (
                <div className="field-aside">
                  <button
                    type="button"
                    className="link-button"
                    onClick={() => switchMode("forgot")}
                  >
                    Forgot password?
                  </button>
                </div>
              )}
            </div>
          )}

          {notice && (
            <p className="alert alert--info" role="status">
              {notice}
            </p>
          )}
          {error && (
            <p className="alert alert--error" role="alert">
              {error}
            </p>
          )}

          <button type="submit" className="btn btn--primary btn--block" disabled={busy}>
            {busy ? "Please wait…" : copy.submit}
          </button>
        </form>

        <p className="auth-switch">
          {mode === "login" ? (
            <>
              Don't have an account?
              <button type="button" className="link-button" onClick={() => switchMode("register")}>
                Register
              </button>
            </>
          ) : (
            <>
              {mode === "register" ? "Already have an account?" : "Remembered it?"}
              <button type="button" className="link-button" onClick={() => switchMode("login")}>
                Log in
              </button>
            </>
          )}
        </p>
        <button
  type="button"
  className="link-button"
  onClick={() => switchMode("admin")}
>
  Admin Login
</button>
      </div>
    </main>
  );
}
