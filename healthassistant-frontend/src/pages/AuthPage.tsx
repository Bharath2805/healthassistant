// src/pages/AuthPage.tsx
import { useState, useEffect } from "react";
import { useNavigate, Link } from "react-router-dom";
import { useAuth } from "../context/useAuth";
import styles from "../styles/AuthPage.module.scss";
import PasswordInput from "../components/PasswordInput";

const AuthPage = () => {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [isSignup, setIsSignup] = useState(false);
  const { setTokens, isAuthenticated } = useAuth();
  const navigate = useNavigate();

  useEffect(() => {
    if (isAuthenticated) {
      navigate("/");
    }
  }, [isAuthenticated, navigate]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    const endpoint = isSignup ? "signup" : "login";

    try {
      const res = await fetch(`http://localhost:8000/auth/${endpoint}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, password }),
      });

      const data = await res.json();

      if (res.ok) {
        if (isSignup) {
          alert("Signup successful! Please verify your email.");
          setIsSignup(false);
        } else {
          setTokens(data.access_token, data.refresh_token);
          navigate("/");
        }
      } else {
        if (data.detail?.includes("already exists")) {
          alert("User already exists. Switching to login.");
          setIsSignup(false);
        } else if (data.detail?.includes("Invalid email or password")) {
          alert("Account not found. Switching to signup.");
          setIsSignup(true);
        } else {
          alert(data.detail || "Something went wrong.");
        }
      }
    } catch (err) {
      alert("Server error. Please try again.");
    }
  };

  const handleGoogleLogin = () => {
    window.location.href = "http://localhost:8000/auth/google-login";
  };

  return (
    <div className={styles.authPageWrapper}>
      <div className={styles.authPageCardContainer}>
        {/* Left - Illustration */}
        <div className={styles.illustration}>
          <img src="/doctor-login.png" alt="Doctor Illustration" />
        </div>

        {/* Right - Auth Form */}
        <div className={styles.card}>
          <h2>{isSignup ? "Create Account" : "Welcome Back"}</h2>

          <form onSubmit={handleSubmit}>
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="Email"
              required
            />

            <PasswordInput
              value={password}
              onChange={setPassword}
              placeholder="Password"
            />

            {!isSignup && (
              <div className={styles.forgotWrapper}>
                <Link to="/forgot-password" className={styles.forgotLink}>
                  Forgot Password?
                </Link>
              </div>
            )}

            <button type="submit" className={styles.submitBtn}>
              {isSignup ? "Sign Up" : "Login"}
            </button>
          </form>

          <div className={styles.or}>or</div>

          <button className={styles.googleBtn} onClick={handleGoogleLogin}>
            <img src="/download.png" alt="Google" className={styles.googleIcon} />
            Continue with Google
          </button>

          <p className={styles.toggleLink}>
            {isSignup ? "Already have an account?" : "New user?"}{" "}
            <span onClick={() => setIsSignup(!isSignup)}>
              {isSignup ? "Login" : "Sign Up"}
            </span>
          </p>
        </div>
      </div>
    </div>
  );
};

export default AuthPage;
