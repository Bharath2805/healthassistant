import { useEffect, useState } from "react";
import { useAuth } from "../context/useAuth";
import styles from "../styles/ReminderList.module.scss"; // ✅ SCSS module import

interface Reminder {
  id: number;
  medicine: string;
  reminder_time: string;
  frequency: string;
}

const ReminderList = () => {
  const { accessToken } = useAuth();
  const [reminders, setReminders] = useState<Reminder[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchReminders = async () => {
      try {
        const res = await fetch("http://localhost:8000/reminders", {
          headers: {
            Authorization: `Bearer ${accessToken}`,
          },
        });

        if (!res.ok) throw new Error("Failed to fetch reminders");
        const data = await res.json();
        setReminders(data); // ✅ Show ALL reminders
      } catch (error) {
        console.error("Error loading reminders:", error);
      } finally {
        setLoading(false);
      }
    };

    if (accessToken) {
      fetchReminders();
    } else {
      setLoading(false);
    }
  }, [accessToken]);

  return (
    <div className={styles.reminderBox}>
      <h2>Your Reminders</h2>
      {loading ? (
        <p className={styles.loading}>Loading...</p>
      ) : reminders.length === 0 ? (
        <p className={styles.empty}>You have no upcoming reminders.</p>
      ) : (
        reminders.map((reminder) => (
          <div key={reminder.id} className={styles.reminderItem}>
            <p>🧪 {reminder.medicine}</p>
            <p>⏰ {reminder.reminder_time}</p>
            <p>🗓️ {reminder.frequency}</p>
          </div>
        ))
      )}
    </div>
  );
};

export default ReminderList;
