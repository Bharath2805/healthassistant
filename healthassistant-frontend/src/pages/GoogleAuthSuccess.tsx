import { useEffect } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";

const GoogleAuthSuccess = () => {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();

  useEffect(() => {
    const accessToken = searchParams.get("access_token");
    const refreshToken = searchParams.get("refresh_token");

    console.log("Access Token:", accessToken);
    console.log("Refresh Token:", refreshToken);

    if (accessToken && refreshToken) {
      localStorage.setItem("access_token", accessToken);
      localStorage.setItem("refresh_token", refreshToken);
      navigate("/"); // Go to Home
    } else {
      navigate("/auth"); // Fallback
    }
  }, [navigate, searchParams]);

  return <div>Logging you in with Google...</div>;
};

export default GoogleAuthSuccess;