/** Format a number as Indian rupees, hiding ".00" for whole amounts. */
export function formatINR(value) {
  const decimals = Number.isInteger(value) ? 0 : 2;
  return new Intl.NumberFormat("en-IN", {
    style: "currency",
    currency: "INR",
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals,
  }).format(value);
}

/** Today's date in the user's local time as YYYY-MM-DD. */
export function todayISO() {
  const d = new Date();
  const month = String(d.getMonth() + 1).padStart(2, "0");
  const day = String(d.getDate()).padStart(2, "0");
  return `${d.getFullYear()}-${month}-${day}`;
}

/** "2026-10-28" -> "2026-10" */
export function monthKey(isoDate) {
  return isoDate.slice(0, 7);
}

export function currentMonthKey() {
  return monthKey(todayISO());
}

/** Move a "YYYY-MM" key forward or backward by a number of months. */
export function shiftMonth(key, delta) {
  const [year, month] = key.split("-").map(Number);
  const d = new Date(year, month - 1 + delta, 1);
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}`;
}

/** "2026-10" -> "October 2026" */
export function monthLabel(key) {
  const [year, month] = key.split("-").map(Number);
  return new Date(year, month - 1, 1).toLocaleDateString("en-IN", {
    month: "long",
    year: "numeric",
  });
}

/** "2026-10-28" -> "28 Oct" */
export function formatDate(isoDate) {
  const [year, month, day] = isoDate.split("-").map(Number);
  return new Date(year, month - 1, day).toLocaleDateString("en-IN", {
    day: "numeric",
    month: "short",
  });
}
