import { useEffect, useState } from "react";
import styles from "../styles/EmergencyCard.module.scss";

interface EmergencyData {
  country: string;
  emergency: {
    ambulance: string;
    fire: string;
    police: string;
  };
}

function EmergencyCard() {
  const [data, setData] = useState<EmergencyData | null>(null);
  const [error, setError] = useState(false);

  useEffect(() => {
    const fetchEmergency = async () => {
      try {
        const res = await fetch("http://localhost:8000/health/emergency-info");
        if (!res.ok) throw new Error("Failed to fetch emergency info");
        const result = await res.json();
        setData(result);
      } catch (err) {
        console.error(err);
        setError(true);
      }
    };

    fetchEmergency();
  }, []);

  return (
    <div className={styles.card}>
      <h3>🚨 Emergency Info {data?.country && `for ${data.country}`}</h3>
      {error ? (
        <p className={styles.error}>Unable to fetch emergency info.</p>
      ) : !data ? (
        <p className={styles.loading}>Loading...</p>
      ) : (
        <ul>
          <li>🚑 <strong>Ambulance:</strong> {data.emergency.ambulance}</li>
          <li>🚒 <strong>Fire:</strong> {data.emergency.fire}</li>
          <li>👮 <strong>Police:</strong> {data.emergency.police}</li>
        </ul>
      )}
    </div>
  );
}

export default EmergencyCard;
