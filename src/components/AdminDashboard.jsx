import { useEffect, useState } from "react";
import { request } from "../api/client";

function AdminDashboard({ user, onLogout }) {
  const [overview, setOverview] = useState(null);
  const [users, setUsers] = useState([]);
  const [transactions, setTransactions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const loadData = async () => {
    setLoading(true);
    setError("");

    const results = await Promise.all([
      request("GET", "/admin/overview"),
      request("GET", "/admin/users"),
      request("GET", "/admin/transactions"),
    ]);

    const failed = results.find((result) => !result.ok);

    if (failed) {
      setError(failed.error);
    } else {
      setOverview(results[0].data);
      setUsers(results[1].data.users);
      setTransactions(results[2].data.transactions);
    }

    setLoading(false);
  };

  useEffect(() => {
    loadData();
  }, []);

  const money = (amount) =>
    new Intl.NumberFormat("en-IN", {
      style: "currency",
      currency: "INR",
      maximumFractionDigits: 2,
    }).format(amount || 0);

  const cardStyle = {
    background: "white",
    padding: "22px",
    borderRadius: "14px",
    boxShadow: "0 3px 12px rgba(0,0,0,0.07)",
  };

  return (
    <main style={{
      maxWidth: "1200px",
      margin: "30px auto",
      padding: "20px",
      color: "#172554"
    }}>
      <header style={{
        display: "flex",
        justifyContent: "space-between",
        alignItems: "center",
        flexWrap: "wrap",
        gap: "15px"
      }}>
        <div>
          <h1>🛡️ BudgetMate Admin</h1>
          <p>Welcome, {user.name}</p>
        </div>

        <div>
          <button onClick={loadData}>Refresh</button>{" "}
          <button onClick={onLogout}>Log out</button>
        </div>
      </header>

      {loading && <p>Loading admin data...</p>}

      {error && (
        <p style={{ color: "red" }}>{error}</p>
      )}

      {!loading && !error && overview && (
        <>
          <h2>System Overview</h2>

          <section style={{
            display: "grid",
            gridTemplateColumns: "repeat(auto-fit, minmax(200px, 1fr))",
            gap: "18px"
          }}>
            <div style={cardStyle}>
              <h3>Total Users</h3>
              <h2>{overview.total_users}</h2>
            </div>

            <div style={cardStyle}>
              <h3>Total Transactions</h3>
              <h2>{overview.total_transactions}</h2>
            </div>

            <div style={cardStyle}>
              <h3>Total Income</h3>
              <h2 style={{ color: "green" }}>
                {money(overview.total_income)}
              </h2>
            </div>

            <div style={cardStyle}>
              <h3>Total Expenses</h3>
              <h2 style={{ color: "crimson" }}>
                {money(overview.total_expenses)}
              </h2>
            </div>
          </section>

          <section style={{ ...cardStyle, marginTop: "25px", overflowX: "auto" }}>
            <h2>Registered Users</h2>

            <table style={{ width: "100%", borderCollapse: "collapse" }}>
              <thead>
                <tr>
                  <th align="left">ID</th>
                  <th align="left">Name</th>
                  <th align="left">Email</th>
                  <th align="left">Role</th>
                  <th align="left">Joined</th>
                </tr>
              </thead>

              <tbody>
                {users.map((item) => (
                  <tr key={item.id}>
                    <td>{item.id}</td>
                    <td>{item.name}</td>
                    <td>{item.email}</td>
                    <td>{item.role}</td>
                    <td>{item.created_at}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </section>

          <section style={{ ...cardStyle, marginTop: "25px", overflowX: "auto" }}>
            <h2>All Transactions</h2>

            <table style={{ width: "100%", borderCollapse: "collapse" }}>
              <thead>
                <tr>
                  <th align="left">User</th>
                  <th align="left">Category</th>
                  <th align="left">Type</th>
                  <th align="left">Amount</th>
                  <th align="left">Date</th>
                </tr>
              </thead>

              <tbody>
                {transactions.map((item) => (
                  <tr key={item.id}>
                    <td>{item.user_name}</td>
                    <td>{item.category}</td>
                    <td>{item.type}</td>
                    <td>{money(item.amount)}</td>
                    <td>{item.date}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </section>
        </>
      )}
    </main>
  );
}

export default AdminDashboard;