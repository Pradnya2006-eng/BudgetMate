import { useMemo, useState } from "react";
import { useBudgetData } from "../hooks/useBudgetData";
import { currentMonthKey, monthKey, monthLabel, shiftMonth } from "../utils/format";
import BudgetCard from "./BudgetCard";
import CategoryReport from "./CategoryReport";
import SummaryCards from "./SummaryCards";
import TransactionForm from "./TransactionForm";
import TransactionList from "./TransactionList";

export default function Dashboard({ user, onLogout }) {
  const {
    transactions,
    monthlyBudget,
    status,
    loadError,
    retry,
    addTransaction,
    deleteTransaction,
    saveBudget,
  } = useBudgetData(user.id);

  const [thisMonth] = useState(currentMonthKey);
  const [month, setMonth] = useState(thisMonth);
  const [deleteError, setDeleteError] = useState("");

  const stats = useMemo(() => {
    // Newest date first; same-day entries keep the order they were loaded in.
    const inMonth = transactions
      .filter((t) => monthKey(t.date) === month)
      .sort((a, b) => b.date.localeCompare(a.date));

    let income = 0;
    let expenses = 0;
    const byCategory = {};

    for (const t of inMonth) {
      if (t.type === "income") {
        income += t.amount;
      } else {
        expenses += t.amount;
        byCategory[t.category] = (byCategory[t.category] ?? 0) + t.amount;
      }
    }

    const allTimeBalance = transactions.reduce(
      (sum, t) => sum + (t.type === "income" ? t.amount : -t.amount),
      0
    );

    return {
      inMonth,
      income,
      expenses,
      allTimeBalance,
      categoryTotals: Object.entries(byCategory).sort((a, b) => b[1] - a[1]),
    };
  }, [transactions, month]);

  const handleAdd = async (fields) => {
    const result = await addTransaction(fields);
    // Jump to the month the entry belongs to so it's visible right away.
    if (result.ok) setMonth(monthKey(fields.date));
    return result;
  };

  const handleDelete = async (id) => {
    const result = await deleteTransaction(id);
    setDeleteError(result.ok ? "" : result.error);
  };

  return (
    <div className="dashboard">
      <header className="topbar">
        <div>
          <h1>💰 BudgetMate</h1>
          <p className="muted">Hi, {user.name.split(" ")[0]} 👋</p>
        </div>
        <button type="button" className="btn btn--ghost" onClick={onLogout}>
          Log out
        </button>
      </header>

      {status === "loading" && <p className="state-box">Loading your data…</p>}

      {status === "error" && (
        <div className="state-box state-box--error" role="alert">
          <p>Couldn't load your data. {loadError}</p>
          <button type="button" className="btn btn--primary" onClick={retry}>
            Try again
          </button>
        </div>
      )}

      {status === "ready" && (
        <>
          <nav className="month-nav" aria-label="Choose month">
            <button
              type="button"
              className="btn btn--ghost btn--icon"
              onClick={() => setMonth((m) => shiftMonth(m, -1))}
              aria-label="Previous month"
            >
              ‹
            </button>
            <span className="month-label" aria-live="polite">
              {monthLabel(month)}
            </span>
            <button
              type="button"
              className="btn btn--ghost btn--icon"
              onClick={() => setMonth((m) => shiftMonth(m, 1))}
              disabled={month >= thisMonth}
              aria-label="Next month"
            >
              ›
            </button>
          </nav>

          <SummaryCards
            income={stats.income}
            expenses={stats.expenses}
            balance={stats.income - stats.expenses}
            allTimeBalance={stats.allTimeBalance}
          />

          {deleteError && (
            <p className="alert alert--error page-alert" role="alert">
              Couldn't delete that transaction. {deleteError}
            </p>
          )}

          <div className="dashboard-grid">
            <div className="dashboard-col">
              <BudgetCard budget={monthlyBudget} spent={stats.expenses} onSave={saveBudget} />
              <TransactionForm onAdd={handleAdd} />
            </div>

            <div className="dashboard-col">
              <CategoryReport totals={stats.categoryTotals} totalExpenses={stats.expenses} />
              <TransactionList transactions={stats.inMonth} onDelete={handleDelete} />
            </div>
          </div>
        </>
      )}
    </div>
  );
}
