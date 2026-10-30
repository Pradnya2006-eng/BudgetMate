import { formatINR } from "../utils/format";

export default function SummaryCards({ income, expenses, balance, allTimeBalance }) {
  return (
    <section className="cards" aria-label="Monthly summary">
      <article className="card">
        <h3>Income</h3>
        <p className="card-value card-value--income">{formatINR(income)}</p>
      </article>

      <article className="card">
        <h3>Expenses</h3>
        <p className="card-value card-value--expense">{formatINR(expenses)}</p>
      </article>

      <article className="card">
        <h3>Balance</h3>
        <p className={`card-value ${balance < 0 ? "card-value--expense" : ""}`}>
          {formatINR(balance)}
        </p>
        <p className="card-note">All time: {formatINR(allTimeBalance)}</p>
      </article>
    </section>
  );
}
