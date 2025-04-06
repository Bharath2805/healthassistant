// src/pages/ForgotPassword.tsx
import { useState } from "react";
import { useNavigate } from "react-router-dom";
import styles from "../styles/AuthPage.module.scss";

const ForgotPassword = () => {
  const [email, setEmail] = useState("");
  const [status, setStatus] = useState("");
  const [error, setError] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const navigate = useNavigate();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    setStatus("");
    setError("");

    try {
      const res = await fetch("http://localhost:8000/auth/forgot-password", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email }),
      });

      const data = await res.json();

      if (res.ok) {
        setStatus("📩 A reset link has been sent to your email.");
      } else {
        if (data.detail === "Email not found") {
          setError("Email not found. Redirecting to Sign Up...");
          setTimeout(() => navigate("/auth", { state: { isSignup: true } }), 2000);
        } else {
          setError(data.detail || "Failed to send reset link.");
        }
      }
    } catch {
      setError("Server error. Please try again.");
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className={styles.authPage}>
      <div className={styles.card}>
        <h2>Forgot Password</h2>
        <form onSubmit={handleSubmit}>
          <input
            type="email"
            placeholder="Enter your registered email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
          />
          <button type="submit" disabled={isLoading}>
            {isLoading ? "Sending..." : "Send Reset Link"}
          </button>
        </form>
        {status && <p className={styles.successMessage}>{status}</p>}
        {error && <p className={styles.errorMessage}>{error}</p>}
        <p className={styles.toggleLink}>
          <span onClick={() => navigate("/auth")}>Back to Login</span>
        </p>
      </div>
    </div>
  );
};

export default ForgotPassword;
