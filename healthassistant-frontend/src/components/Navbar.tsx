import { Link } from "react-router-dom";
import LogoutButton from "./LogoutButton"; // Import the LogoutButton
import "../styles/Navbar.scss";

const Navbar = () => {
  return (
    <nav className="navbar">
      <h1>HealthAssistant</h1>
      <ul>
        <li><Link to="/chat">Chat</Link></li>
        <li><Link to="/symptoms">Symptom Checker</Link></li>
        <li><Link to="/doctors">Doctors</Link></li>
        <li><Link to="/reminders">Reminders</Link></li>
        <li>
          <LogoutButton /> {/* Replace Link with LogoutButton */}
        </li>
      </ul>
    </nav>
  );
};

export default Navbar;