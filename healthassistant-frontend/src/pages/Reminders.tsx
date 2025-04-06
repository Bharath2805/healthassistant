// src/pages/Reminders.tsx
import { useEffect, useState } from "react";
import AddReminderForm from "../components/AddReminderForm";
import ReminderCard from "../components/ReminderCard";
import styles from "../styles/Reminders.module.scss";

const Reminders = () => {
  const [reminders, setReminders] = useState([]);
  const [loading, setLoading] = useState(true);

  const fetchReminders = async () => {
    const token = localStorage.getItem("access_token");
    const res = await fetch("http://localhost:8000/reminders", {
      headers: {
        Authorization: `Bearer ${token}`,
      },
    });
    const data = await res.json();
    setReminders(data || []);
    setLoading(false);
  };

  const handleAddReminder = async (newReminder: any) => {
    // Optimistically append the new reminder (optional)
    setReminders((prev) => [newReminder, ...prev]);
  };

  const deleteReminder = async (id: number) => {
    const token = localStorage.getItem("access_token");
    const res = await fetch(`http://localhost:8000/reminders/${id}`, {
      method: "DELETE",
      headers: {
        Authorization: `Bearer ${token}`,
      },
    });
    if (res.ok) {
      setReminders(reminders.filter((r) => r.id !== id));
    }
  };

  useEffect(() => {
    fetchReminders();
  }, []);

  return (
    <div className={styles.wrapper}>
      <h2>🗓️ Set Medicine Reminders</h2>
      <AddReminderForm
        onAdd={(newReminder) => {
          handleAddReminder(newReminder);
        }}
      />

      {loading ? (
        <p>Loading...</p>
      ) : reminders.length === 0 ? (
        <p>No reminders set. Start by adding one above.</p>
      ) : (
        reminders.map((reminder) => (
          <ReminderCard
            key={reminder.id}
            reminder={reminder}
            onDelete={deleteReminder}
          />
        ))
      )}
    </div>
  );
};

export default Reminders;
