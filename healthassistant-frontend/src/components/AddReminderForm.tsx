import { useState } from "react";
import styles from "../styles/Reminders.module.scss";

interface Props {
  onAdd: (newReminder: any) => void;
}

const AddReminderForm = ({ onAdd }: Props) => {
  const [medicine, setMedicine] = useState("");
  const [reminderTime, setReminderTime] = useState("");
  const [frequency, setFrequency] = useState("daily");
  const [error, setError] = useState("");

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");

    if (!medicine || !reminderTime) {
      setError("Please fill all fields");
      return;
    }

    const token = localStorage.getItem("access_token");
    const res = await fetch("http://localhost:8000/reminders", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${token}`,
      },
      body: JSON.stringify({
        medicine,
        reminder_time: reminderTime,
        frequency,
      }),
    });

    const data = await res.json();

    if (res.ok) {
      const newReminder = {
        id: data.reminder_id,
        medicine,
        reminder_time: reminderTime,
        frequency,
      };
      onAdd(newReminder); // Pass to parent immediately

      // Clear form fields
      setMedicine("");
      setReminderTime("");
      setFrequency("daily");
    } else {
      setError(data.detail || "Failed to add reminder.");
    }
  };

  return (
    <form className={styles.form} onSubmit={handleSubmit}>
      <input
        type="text"
        placeholder="Medicine name"
        value={medicine}
        onChange={(e) => setMedicine(e.target.value)}
        required
      />
      <input
        type="time"
        value={reminderTime}
        onChange={(e) => setReminderTime(e.target.value)}
        required
      />
      <select
        value={frequency}
        onChange={(e) => setFrequency(e.target.value)}
      >
        <option value="daily">Daily</option>
        <option value="weekly">Weekly</option>
        <option value="monthly">Monthly</option>
      </select>
      <button type="submit">Add Reminder</button>
      {error && <p className={styles.error}>{error}</p>}
    </form>
  );
};

export default AddReminderForm;
