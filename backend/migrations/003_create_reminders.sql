CREATE TABLE IF NOT EXISTS reminders (
    id SERIAL PRIMARY KEY,
    user_id TEXT NOT NULL,
    medicine TEXT NOT NULL,
    reminder_time TIME NOT NULL,
    frequency TEXT DEFAULT 'daily',
    status TEXT DEFAULT 'active',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
