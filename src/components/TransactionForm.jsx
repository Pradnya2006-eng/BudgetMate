import { useState } from "react";
import { CATEGORIES_BY_TYPE } from "../utils/constants";
import { todayISO } from "../utils/format";

const MAX_AMOUNT = 1_000_000_000;

export default function TransactionForm({ onAdd }) {
  const [today] = useState(todayISO);
  const [type, setType] = useState("expense");
  const [amount, setAmount] = useState("");
  const [category, setCategory] = useState("");
  const [date, setDate] = useState(today);
  const [description, setDescription] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  const handleTypeChange = (next) => {
    setType(next);
    setCategory("");
  };

  const handleSubmit = async (e) => {
    e.preventDefault();

    const value = Math.round(Number(amount) * 100) / 100;

    if (!Number.isFinite(value) || value <= 0) {
      setError("Enter an amount greater than 0.");
      return;
    }
    if (value > MAX_AMOUNT) {
      setError("That amount looks too large.");
      return;
    }
    if (!category) {
      setError("Please choose a category.");
      return;
    }
    if (!date || date > today) {
      setError("Please choose a valid date (not in the future).");
      return;
    }

    setError("");
    setBusy(true);
    const result = await onAdd({
      type,
      amount: value,
      category,
      description: description.trim(),
      date,
    });
    setBusy(false);

    if (!result.ok) {
      setError(`Couldn't save it. ${result.error}`);
      return;
    }

    setAmount("");
    setCategory("");
    setDescription("");
    setError("");
  };

  return (
    <section className="panel">
      <h2>Add transaction</h2>

      <form className="stack" onSubmit={handleSubmit} noValidate>
        <fieldset className="segmented">
          <legend className="visually-hidden">Transaction type</legend>
          {["expense", "income"].map((option) => (
            <label key={option} className={type === option ? "is-active" : ""}>
              <input
                type="radio"
                name="type"
                value={option}
                checked={type === option}
                onChange={() => handleTypeChange(option)}
              />
              {option === "expense" ? "Expense" : "Income"}
            </label>
          ))}
        </fieldset>

        <div className="field">
          <label htmlFor="amount">Amount (₹)</label>
          <input
            id="amount"
            className="input"
            type="number"
            inputMode="decimal"
            min="0.01"
            step="0.01"
            placeholder="0"
            value={amount}
            onChange={(e) => setAmount(e.target.value)}
          />
        </div>

        <div className="field">
          <label htmlFor="category">Category</label>
          <select
            id="category"
            className="input"
            value={category}
            onChange={(e) => setCategory(e.target.value)}
          >
            <option value="">Select a category</option>
            {CATEGORIES_BY_TYPE[type].map((name) => (
              <option key={name} value={name}>
                {name}
              </option>
            ))}
          </select>
        </div>

        <div className="field">
          <label htmlFor="date">Date</label>
          <input
            id="date"
            className="input"
            type="date"
            max={today}
            value={date}
            onChange={(e) => setDate(e.target.value)}
          />
        </div>

        <div className="field">
          <label htmlFor="description">Note (optional)</label>
          <input
            id="description"
            className="input"
            type="text"
            maxLength={80}
            placeholder="e.g. Lunch with friends"
            value={description}
            onChange={(e) => setDescription(e.target.value)}
          />
        </div>

        {error && (
          <p className="alert alert--error" role="alert">
            {error}
          </p>
        )}

        <button type="submit" className="btn btn--primary btn--block" disabled={busy}>
          {busy ? "Saving…" : `Add ${type}`}
        </button>
      </form>
    </section>
  );
}
