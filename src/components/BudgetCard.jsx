import { useState } from "react";
import { formatINR } from "../utils/format";

export default function BudgetCard({ budget, spent, onSave }) {
  const [input, setInput] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  const hasBudget = budget > 0;
  const percent = hasBudget ? (spent / budget) * 100 : 0;
  const remaining = budget - spent;
  const status = percent > 100 ? "over" : percent >= 80 ? "near" : "ok";

  const handleSubmit = async (e) => {
    e.preventDefault();
    const value = Number(input);

    if (input.trim() === "" || !Number.isFinite(value) || value < 0) {
      setError("Enter a budget of 0 or more.");
      return;
    }
    if (value > 9_999_999_999) {
      setError("That budget looks too large.");
      return;
    }

    setError("");
    setBusy(true);
    const result = await onSave(Math.round(value * 100) / 100);
    setBusy(false);

    if (!result.ok) {
      setError(`Couldn't save the budget. ${result.error}`);
      return;
    }
    setInput("");
  };

  return (
    <section className="panel">
      <h2>Monthly budget</h2>

      {hasBudget ? (
        <>
          <div className="budget-figures">
            <span>
              <strong>{formatINR(spent)}</strong> spent of {formatINR(budget)}
            </span>
          </div>

          <div
            className={`progress progress--${status}`}
            role="progressbar"
            aria-label="Budget used"
            aria-valuemin={0}
            aria-valuemax={100}
            aria-valuenow={Math.min(100, Math.round(percent))}
          >
            <div className="progress-fill" style={{ width: `${Math.min(100, percent)}%` }} />
          </div>

          <p className={`budget-status budget-status--${status}`}>
            {status === "over"
              ? `⚠️ Over budget by ${formatINR(Math.abs(remaining))}`
              : status === "near"
                ? `Careful: ${formatINR(remaining)} left (${Math.round(percent)}% used)`
                : `${formatINR(remaining)} left (${Math.round(percent)}% used)`}
          </p>
        </>
      ) : (
        <p className="muted">Set a monthly budget to see how much you have left to spend.</p>
      )}

      <form className="inline-form" onSubmit={handleSubmit} noValidate>
        <label htmlFor="budget" className="visually-hidden">
          Monthly budget in rupees
        </label>
        <input
          id="budget"
          className="input"
          type="number"
          inputMode="decimal"
          min="0"
          step="1"
          placeholder={hasBudget ? "Change budget (₹)" : "Monthly budget (₹)"}
          value={input}
          onChange={(e) => setInput(e.target.value)}
        />
        <button type="submit" className="btn btn--primary" disabled={busy}>
          {busy ? "Saving…" : hasBudget ? "Update" : "Set budget"}
        </button>
      </form>

      {error && (
        <p className="alert alert--error" role="alert">
          {error}
        </p>
      )}
    </section>
  );
}
