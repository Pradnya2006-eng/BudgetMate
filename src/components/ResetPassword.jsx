import { useState } from "react";
import { setNewPassword } from "../api/auth";
import { MIN_PASSWORD_LENGTH } from "../utils/constants";
import PasswordInput from "./PasswordInput";

/** Shown after someone clicks the reset link in their email. */
export default function ResetPassword({ token, onDone, onCancel }) {
  const [password, setPassword] = useState("");
  const [confirm, setConfirm] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");

    if (password !== confirm) {
      setError("The two passwords don't match.");
      return;
    }

    setBusy(true);
    const result = await setNewPassword(token, password);
    setBusy(false);

    if (!result.ok) {
      setError(result.error);
      return;
    }
    onDone();
  };

  return (
    <main className="auth-page">
      <div className="auth-card">
        <div className="brand">
          <div className="brand-logo" aria-hidden="true">🔑</div>
          <h1>New password</h1>
        </div>

        <p className="auth-subtitle">Choose a new password for your BudgetMate account.</p>

        <form onSubmit={handleSubmit} noValidate>
          <div className="field">
            <label htmlFor="new-password">New password</label>
            <PasswordInput
              id="new-password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              autoComplete="new-password"
              placeholder={`At least ${MIN_PASSWORD_LENGTH} characters`}
            />
          </div>

          <div className="field">
            <label htmlFor="confirm-password">Confirm new password</label>
            <PasswordInput
              id="confirm-password"
              value={confirm}
              onChange={(e) => setConfirm(e.target.value)}
              autoComplete="new-password"
              placeholder="Type it again"
            />
          </div>

          {error && (
            <p className="alert alert--error" role="alert">
              {error}
            </p>
          )}

          <button type="submit" className="btn btn--primary btn--block" disabled={busy}>
            {busy ? "Saving…" : "Save new password"}
          </button>
        </form>

        <p className="auth-switch">
          <button type="button" className="link-button" onClick={onCancel}>
            Cancel
          </button>
        </p>
      </div>
    </main>
  );
}
