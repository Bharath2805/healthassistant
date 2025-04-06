// src/components/FeatureCard.tsx
import { motion } from "framer-motion";
import { useNavigate } from "react-router-dom";
import { FaStethoscope, FaUserMd, FaXRay } from "react-icons/fa";

interface FeatureCardProps {
  title: string;
}

const iconMap: any = {
  "Check Symptoms": <FaStethoscope size={28} />,
  "Find Doctors": <FaUserMd size={28} />,
  "Analyze Images": <FaXRay size={28} />
};

const bgMap: any = {
  "Check Symptoms": "#e7efff",
  "Find Doctors": "#ffe9f3",
  "Analyze Images": "#f4f1ff"
};

const routeMap: any = {
  "Check Symptoms": "/chat",
  "Find Doctors": "/doctors",
  "Analyze Images": "/images"
};

const FeatureCard = ({ title }: FeatureCardProps) => {
  const navigate = useNavigate();

  return (
    <motion.div
      className="feature-card"
      onClick={() => navigate(routeMap[title])}
      whileHover={{ scale: 1.05 }}
      whileTap={{ scale: 0.98 }}
      style={{
        backgroundColor: bgMap[title],
        borderRadius: "16px",
        padding: "1.5rem",
        flex: "1 1 30%",
        boxShadow: "0 6px 20px rgba(0, 0, 0, 0.05)",
        cursor: "pointer"
      }}
    >
      <div style={{ marginBottom: "0.5rem" }}>{iconMap[title]}</div>
      <h3 style={{ fontSize: "1.1rem" }}>{title}</h3>
      <p style={{ color: "#6b7280", fontSize: "0.9rem" }}>
        Quickly access {title.toLowerCase()} tools and guidance.
      </p>
    </motion.div>
  );
};

export default FeatureCard;
