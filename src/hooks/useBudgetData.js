import { useCallback, useEffect, useState } from "react";
import {
  fetchBudget,
  fetchTransactions,
  insertTransaction,
  removeTransaction,
  saveMonthlyBudget,
} from "../api/data";

/**
 * Loads and edits the signed-in user's transactions and monthly budget.
 * Every action returns { ok, error } so forms can show what went wrong.
 */
export function useBudgetData(userId) {
  const [transactions, setTransactions] = useState([]);
  const [monthlyBudget, setMonthlyBudget] = useState(0);
  const [status, setStatus] = useState("loading"); // loading | ready | error
  const [loadError, setLoadError] = useState("");
  const [attempt, setAttempt] = useState(0);

  useEffect(() => {
    let cancelled = false;

    async function load() {
      const [tx, budget] = await Promise.all([fetchTransactions(), fetchBudget()]);
      if (cancelled) return;

      if (!tx.ok || !budget.ok) {
        setLoadError(tx.error ?? budget.error);
        setStatus("error");
        return;
      }
      setTransactions(tx.data);
      setMonthlyBudget(budget.data);
      setStatus("ready");
    }

    load();
    return () => {
      cancelled = true;
    };
  }, [userId, attempt]);

  const retry = useCallback(() => {
    setStatus("loading");
    setAttempt((n) => n + 1);
  }, []);

  const addTransaction = useCallback(async (fields) => {
    const result = await insertTransaction(fields);
    if (result.ok) setTransactions((prev) => [result.data, ...prev]);
    return result;
  }, []);

  const deleteTransaction = useCallback(async (id) => {
    const result = await removeTransaction(id);
    if (result.ok) setTransactions((prev) => prev.filter((t) => t.id !== id));
    return result;
  }, []);

  const saveBudget = useCallback(async (amount) => {
    const result = await saveMonthlyBudget(amount);
    if (result.ok) setMonthlyBudget(amount);
    return result;
  }, []);

  return {
    transactions,
    monthlyBudget,
    status,
    loadError,
    retry,
    addTransaction,
    deleteTransaction,
    saveBudget,
  };
}
