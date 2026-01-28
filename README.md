# Mathenique 🧮

**Mathenique** is a modern, gamified mathematics learning platform designed to make mastering math concepts engaging and competitive. Built with a robust React frontend and a high-performance FastAPI backend, it features interactive lessons, real-time quizzes, and a global leaderboard system.


## 🚀 Features

- **Interactive Lessons**: Step-by-step visual learning for topics like Graph Theory, Number Theory, and Logic.
- **Game Modes**:
  - **Classic Mode**: Practice at your own pace.
  - **Time Rush**: Race against the clock to solve problems.
- **Progression System**: Track your stats (Accuracy, Wins, Games Played).
- **Global Leaderboard**: Compete with other users worldwide for the top rank.
- **Authentication**: Secure user accounts with JWT-based authentication.
- **Responsive Design**: fully responsive UI built with Tailwind CSS and Shadcn/UI.

## 🛠️ Tech Stack

### Frontend
- **Framework**: React (Vite)
- **Language**: TypeScript
- **Styling**: Tailwind CSS
- **Components**: Shadcn/UI (@radix-ui)
- **Icons**: Lucide React
- **HTTP Client**: Axios

### Backend
- **Framework**: FastAPI (Python)
- **Database ORM**: SQLAlchemy / SQLModel
- **Authentication**: PyJWT, Passlib (Bcrypt)
- **Database**: 
  - SQLite (Local Development)
  - PostgreSQL (Production)

## 📦 Installation & Setup

### Prerequisites
- Node.js (v18+)
- Python (v3.9+)

### 1. Clone the Repository
```bash
git clone https://github.com/yourusername/mathenique.git
cd mathenique
```

### 2. Frontend Setup
Navigate to the root directory and install dependencies:
```bash
npm install
```

Start the development server:
```bash
npm run dev
```
The application will run at `http://localhost:8080`.

### 3. Backend Setup
Ideally, run the backend in a virtual environment.

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
.\venv\Scripts\activate
# Mac/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

Start the FastAPI server:
```bash
uvicorn backend.main:app --reload
```
The API will be available at `http://localhost:8000`.

## 🗃️ Database Initialization
When you first run the application locally, it will automatically create a `mathenique.db` SQLite database. To seed the initial questions, simply run the backend server—the initialization logic checks for existing data on startup.

## 🚢 Deployment (Render)
This project is configured for deployment on [Render](https://render.com).
- **Build Command**: `npm install && npm run build`
- **Publish Directory**: `dist`
- **Rewrite Rule**: Rewrite all paths to `/index.html` (SPA support).
- **Backend**: Python Web Service running `uvicorn backend.main:app --host 0.0.0.0 --port $PORT`.

## 📄 License
This project is open source and available under the [MIT License](LICENSE).
