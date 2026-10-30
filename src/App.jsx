import { useEffect, useState } from "react";
import {
  clearResetToken,
  fetchCurrentUser,
  readResetToken,
  signOut,
} from "./api/auth";
import { setUnauthorizedHandler } from "./api/client";
import AuthPage from "./components/AuthPage";
import Dashboard from "./components/Dashboard";
import AdminDashboard from "./components/AdminDashboard";
import ResetPassword from "./components/ResetPassword";
import "./App.css";

function App() {
  const [user, setUser] = useState(undefined); // undefined = still checking
  const [startupError, setStartupError] = useState("");
  const [resetToken, setResetToken] = useState(readResetToken);
  const [notice, setNotice] = useState("");

  // On load, ask the server whether we're already logged in (session cookie).
  useEffect(() => {
    let cancelled = false;

    fetchCurrentUser().then((result) => {
      if (cancelled) return;
      if (result.ok) {
        setUser(result.user);
      } else {
        setStartupError(result.error);
        setUser(null);
      }
    });

    return () => {
      cancelled = true;
    };
  }, []);

  // If the server says our login has expired, go back to the login page.
  useEffect(() => {
    setUnauthorizedHandler(() => {
      setNotice("Your session expired. Please log in again.");
      setUser(null);
    });
    return () => setUnauthorizedHandler(() => {});
  }, []);

  const handleLogout = async () => {
    await signOut();
    setNotice("");
    setUser(null);
  };

  const finishReset = (message) => {
    clearResetToken();
    setResetToken("");
    setNotice(message);
  };

  if (user === undefined) {
    return (
      <main className="auth-page">
        <p className="loading-text">Loading…</p>
      </main>
    );
  }

  if (resetToken) {
    return (
      <ResetPassword
        token={resetToken}
        onDone={() => finishReset("Password updated. Log in with your new password.")}
        onCancel={() => finishReset("")}
      />
    );
  }

  if (!user) {
    return <AuthPage notice={notice} startupError={startupError} onAuthenticated={setUser} />;
  }

  // `key` gives each account a fresh dashboard (and a fresh data load).
  if (user.role === "admin") {
  return <AdminDashboard user={user} onLogout={handleLogout} />;
}

return <Dashboard key={user.id} user={user} onLogout={handleLogout} />;
}

export default App;
