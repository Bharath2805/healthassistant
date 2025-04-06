import styles from "../styles/DoctorCard.module.scss";
import { motion } from "framer-motion";

interface DoctorCardProps {
  doctor: {
    name: string;
    specialty: string;
    address: string;
    phone?: string | null;
    website?: string | null;
  };
}

const DoctorCard = ({ doctor }: DoctorCardProps) => {
  return (
    <motion.div
      className={styles.card}
      whileHover={{ scale: 1.05 }}
      transition={{ type: "spring", stiffness: 300 }}
    >
      <h3 className={styles.name}>{doctor.name}</h3>
      <p><strong>Specialty:</strong> {doctor.specialty}</p>
      <p><strong>Address:</strong> {doctor.address}</p>
      {doctor.phone && <p><strong>Phone:</strong> {doctor.phone}</p>}
      {doctor.website && (
        <a href={doctor.website} target="_blank" rel="noopener noreferrer">
          Visit Website
        </a>
      )}
    </motion.div>
  );
};

export default DoctorCard;
