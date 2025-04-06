// src/components/ReminderCard.tsx
import styles from "../styles/Reminders.module.scss";

interface Props {
  reminder: any;
  onDelete: (id: number) => void;
}

const ReminderCard = ({ reminder, onDelete }: Props) => {
  return (
    <div className={styles.card}>
      <h3>{reminder.medicine}</h3>
      <p>⏰ {reminder.reminder_time}</p>
      <p>📅 {reminder.frequency}</p>
      <button onClick={() => onDelete(reminder.id)}>Delete</button>
    </div>
  );
};

export default ReminderCard;
