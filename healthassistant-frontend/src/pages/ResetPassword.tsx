import { useState, useEffect } from "react";
import { useSearchParams, useNavigate } from "react-router-dom";
import styles from "../styles/AuthPage.module.scss";
import PasswordInput from "../components/PasswordInput";

const ResetPassword = () => {
  const [searchParams] = useSearchParams();
  const token = searchParams.get("token");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [status, setStatus] = useState("");
  const [error, setError] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const navigate = useNavigate();

  useEffect(() => {
    if (!token) {
      setError("Invalid or missing token. Please request a new password reset link.");
    }
  }, [token]);

  const validatePassword = () => {
    if (password.length < 8) {
      setError("Password must be at least 8 characters long.");
      return false;
    }
    if (password !== confirmPassword) {
      setError("Passwords do not match.");
      return false;
    }
    return true;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!validatePassword()) return;

    setIsLoading(true);
    setStatus("");
    setError("");

    try {
      const res = await fetch("http://localhost:8000/auth/reset-password", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ token, new_password: password }),
      });

      const data = await res.json();

      if (res.ok) {
        setStatus("✅ Password reset successfully! Redirecting to login...");
        setTimeout(() => navigate("/auth"), 2000);
      } else {
        setError(data.detail || "Reset failed. The link may be expired.");
      }
    } catch {
      setError("Server error. Please try again later.");
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className={styles.authPage}>
      <div className={styles.card}>
        <h2>Reset Password</h2>
        {!token ? (
          <p className={styles.errorMessage}>Invalid or missing token.</p>
        ) : (
          <form onSubmit={handleSubmit}>
            <PasswordInput
              value={password}
              onChange={setPassword}
              placeholder="New Password"
            />
            <PasswordInput
              value={confirmPassword}
              onChange={setConfirmPassword}
              placeholder="Confirm New Password"
            />
            <button type="submit" disabled={isLoading}>
              {isLoading ? "Resetting..." : "Reset Password"}
            </button>
          </form>
        )}
        {status && <p className={styles.successMessage}>{status}</p>}
        {error && <p className={styles.errorMessage}>{error}</p>}
        <p className={styles.toggleLink}>
          <span onClick={() => navigate("/auth")}>Back to Login</span>
        </p>
      </div>
    </div>
  );
};

export default ResetPassword;
