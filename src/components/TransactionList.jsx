import { formatDate, formatINR } from "../utils/format";

export default function TransactionList({ transactions, onDelete }) {
  const handleDelete = (transaction) => {
    const label = `${transaction.category} (${formatINR(transaction.amount)})`;
    if (window.confirm(`Delete this transaction?\n${label}`)) {
      onDelete(transaction.id);
    }
  };

  return (
    <section className="panel">
      <h2>Transactions</h2>

      {transactions.length === 0 ? (
        <p className="muted">No transactions this month.</p>
      ) : (
        <ul className="tx-list">
          {transactions.map((t) => (
            <li key={t.id} className="tx">
              <div className="tx-main">
                <strong>{t.category}</strong>
                <span className="tx-meta">
                  {formatDate(t.date)}
                  {t.description && ` · ${t.description}`}
                </span>
              </div>

              <div className="tx-side">
                <strong className={t.type === "income" ? "amount--income" : "amount--expense"}>
                  {t.type === "income" ? "+" : "−"}
                  {formatINR(t.amount)}
                </strong>
                <button
                  type="button"
                  className="btn btn--danger btn--small"
                  onClick={() => handleDelete(t)}
                  aria-label={`Delete ${t.category} transaction`}
                >
                  Delete
                </button>
              </div>
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}
