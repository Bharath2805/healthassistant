# 🩺 Health Assistant AI Web App

A modern, full-stack AI-powered Health Assistant that provides intelligent symptom analysis, medical image diagnosis, doctor recommendations, reminders, and secure user authentication.

Built with **FastAPI** (Python) on the backend and **React + Vite + TypeScript** on the frontend. The app uses **OpenAI GPT-4**, **Google Vision API**, and integrates with Google OAuth, SendGrid, and Twilio.

---

## ✨ Features

- 💬 Chat-based health assistant (OpenAI powered)
- 🖼️ Medical image analysis using Google Vision
- 📍 Doctor recommendation based on condition and location
- 🧠 Context-aware assistant with session history
- 📅 Reminder system (email/SMS)
- 🔐 Authentication (email/password, Google login, verification, reset)
- 📄 PDF summary report for diagnoses
- 🧪 Built-in support for medical image quality checks and specialty extraction
- 🌐 Fully responsive UI with glowing dark theme

---

## 🛠️ Tech Stack

| Frontend              | Backend                | AI & APIs                      | Other                    |
|-----------------------|------------------------|--------------------------------|--------------------------|
| React + Vite + TS     | FastAPI (Python)       | OpenAI GPT-4                   | Supabase (PostgreSQL)    |
| CSS Modules + SCSS    | SQLAlchemy, Alembic    | Google Cloud Vision API        | SendGrid (Email)         |
| Axios, React Router   | Celery, Redis          | Google Places API (Doctors)    | Twilio (SMS)             |
| Framer Motion         | Pydantic, JWT Auth     | Custom AI prompts + formatters | PDF Generation (ReportLab)|

---

## 🚀 Getting Started

### 🔧 Backend Setup (FastAPI)

```bash
cd backend
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows
pip install -r requirements.txt
