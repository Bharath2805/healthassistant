import { useAuth } from "../context/useAuth";
// Remove SCSS import for now
// import "./LogoutButton.scss";

const LogoutButton = () => {
  const { logout } = useAuth();

  const handleLogout = () => {
    console.log("Logout button clicked");
    logout();
  };

  return (
    <button
      style={{
        background: "none",
        border: "none",
        color: "white",
        fontSize: "16px",
        padding: 0,
        cursor: "pointer",
        textDecoration: "none",
      }}
      onMouseEnter={(e) => (e.currentTarget.style.textDecoration = "underline")}
      onMouseLeave={(e) => (e.currentTarget.style.textDecoration = "none")}
      onClick={handleLogout}
    >
      Logout
    </button>
  );
};

export default LogoutButton;