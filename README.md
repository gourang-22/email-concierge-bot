# Email Concierge Bot 📧

An intelligent, full-stack application designed to provide email accountability, task management, and productivity tracking. This assistant syncs your emails, extracts tasks, and sends you notifications to keep you on top of your inbox.

## 🌟 Features

- **Email Synchronization:** Connects to your email provider to securely fetch and analyze your inbox.
- **Task Extraction & Management:** Automatically identifies action items from your emails and converts them into manageable tasks.
- **AI-Powered Insights:** Utilizes AI to summarize threads and extract context for your tasks.
- **Notifications & Cron Jobs:** Integrates with Telegram and other services to provide scheduled reminders and alerts.
- **Modern Dashboard:** A clean, responsive React frontend for viewing tasks and tracking accountability.

## 🛠 Tech Stack

### Backend
- **Python (FastAPI):** High-performance backend API.
- **Database:** Relational database for storing user data, tasks, and oauth states.
- **Scheduler:** Background cron jobs and sync services.
- **AI Services:** For natural language processing and email intelligence.

### Frontend
- **React (Vite):** Fast, modern UI development.
- **Tailwind / Vanilla CSS:** Dynamic and premium design styling.
- **State Management:** Secure authentication and application state management.

## 🚀 Getting Started

### Prerequisites
- Python 3.10+
- Node.js & npm

### Backend Setup
1. Navigate to the `backend` directory:
   ```bash
   cd backend
   ```
2. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows use: venv\Scripts\activate
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Set up your environment variables by copying `.env.example` to `.env`.
5. Run the development server:
   ```bash
   uvicorn app.main:app --reload
   ```

### Frontend Setup
1. Navigate to the `frontend` directory:
   ```bash
   cd frontend
   ```
2. Install dependencies:
   ```bash
   npm install
   ```
3. Start the development server:
   ```bash
   npm run dev
   ```

## 📜 License

This project is licensed under the [MIT License](LICENSE).
