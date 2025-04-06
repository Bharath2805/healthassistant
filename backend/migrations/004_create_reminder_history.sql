CREATE TABLE IF NOT EXISTS reminder_history (
    id SERIAL PRIMARY KEY,
    user_id TEXT NOT NULL,
    reminder_id INT NOT NULL REFERENCES reminders(id) ON DELETE CASCADE,
    sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    delivery_status TEXT DEFAULT 'pending'
);
