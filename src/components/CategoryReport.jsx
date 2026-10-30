import { formatINR } from "../utils/format";

/** `totals` is an array of [category, amount] pairs, largest first. */
export default function CategoryReport({ totals, totalExpenses }) {
  return (
    <section className="panel">
      <h2>📊 Spending by category</h2>

      {totals.length === 0 ? (
        <p className="muted">No expenses this month yet. Add one to see your breakdown.</p>
      ) : (
        <ul className="report">
          {totals.map(([category, total]) => {
            const percent = totalExpenses > 0 ? (total / totalExpenses) * 100 : 0;
            return (
              <li key={category}>
                <div className="report-row">
                  <strong>{category}</strong>
                  <span>
                    {formatINR(total)} · {percent.toFixed(0)}%
                  </span>
                </div>
                <div className="bar" aria-hidden="true">
                  <div className="bar-fill" style={{ width: `${percent}%` }} />
                </div>
              </li>
            );
          })}
        </ul>
      )}
    </section>
  );
}
