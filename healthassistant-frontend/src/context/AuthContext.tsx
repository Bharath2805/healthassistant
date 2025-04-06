import { createContext, useContext, useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";

interface AuthContextType {
  isAuthenticated: boolean | null;
  accessToken: string | null;
  refreshToken: string | null;
  setTokens: (access: string, refresh: string) => void;
  logout: () => void;
}

export const AuthContext = createContext<AuthContextType | undefined>(undefined); // ✅ EXPORT THIS

export const AuthProvider = ({ children }: { children: React.ReactNode }) => {
  const [accessToken, setAccessToken] = useState<string | null>(localStorage.getItem("access_token"));
  const [refreshToken, setRefreshToken] = useState<string | null>(localStorage.getItem("refresh_token"));
  const [isAuthenticated, setIsAuthenticated] = useState<boolean | null>(null);
  const navigate = useNavigate();

  const logout = () => {
    localStorage.removeItem("access_token");
    localStorage.removeItem("refresh_token");
    setAccessToken(null);
    setRefreshToken(null);
    setIsAuthenticated(false);
    navigate("/auth");
  };

  const setTokens = (access: string, refresh: string) => {
    localStorage.setItem("access_token", access);
    localStorage.setItem("refresh_token", refresh);
    setAccessToken(access);
    setRefreshToken(refresh);
    setIsAuthenticated(true);
  };

  useEffect(() => {
    const checkToken = () => {
      const token = localStorage.getItem("access_token");
      if (!token) {
        setIsAuthenticated(false);
        return;
      }

      try {
        const payload = JSON.parse(atob(token.split(".")[1]));
        const expiry = payload.exp * 1000;
        const now = Date.now();

        if (now > expiry) {
          logout();
        } else {
          setIsAuthenticated(true);
          const timeout = setTimeout(() => {
            logout();
          }, expiry - now);
          return () => clearTimeout(timeout);
        }
      } catch (err) {
        logout();
      }
    };

    checkToken();
  }, []);

  return (
    <AuthContext.Provider
      value={{
        isAuthenticated,
        accessToken,
        refreshToken,
        setTokens,
        logout,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};
