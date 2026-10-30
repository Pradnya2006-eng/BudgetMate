import { request } from "./client";

/** Every transaction for the logged-in person, newest first. */
export async function fetchTransactions() {
  const result = await request("GET", "/transactions");
  return result.ok ? { ok: true, data: result.data.transactions } : result;
}

export async function fetchBudget() {
  const result = await request("GET", "/budget");
  return result.ok ? { ok: true, data: Number(result.data.monthly_budget) } : result;
}

export async function insertTransaction({ type, amount, category, description, date }) {
  const result = await request("POST", "/transactions", {
    type,
    amount,
    category,
    description,
    date,
  });
  return result.ok ? { ok: true, data: result.data.transaction } : result;
}

export async function removeTransaction(id) {
  return request("DELETE", `/transactions/${id}`);
}

export async function saveMonthlyBudget(amount) {
  return request("PUT", "/budget", { monthly_budget: amount });
}
