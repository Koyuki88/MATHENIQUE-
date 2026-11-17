# Mathenique 🧮

**Mathenique** is a full-stack, gamified mathematics learning platform built with **React + TypeScript** and **FastAPI**. Learners progress through structured **Algebra**, **Geometry**, and **Trigonometry** lessons, battle in timed **Arena** modes, unlock achievements, and compete on a live global leaderboard backed by PostgreSQL or SQLite.

---

## ✨ Features

- **Adventure Mode (6 Progressive Lessons)**
  - Structured **Training** and **Mastery** stages across **Algebra**, **Geometry**, and **Trigonometry** with 3-life gameplay and 1–3 star completion ratings.
- **Arena Modes (4 Competitive Modes)**
  - **Focused:** 10-question topic-specific practice unlocked as you complete topics in Adventure.
  - **Mayhem:** Cross-topic mixed battle unlocked after finishing all 6 lessons.
  - **Challenge:** 10-second per-question sprint tracking personal high scores and streaks.
  - **Apocalypse:** 60-second rapid-fire endurance run.
- **Live Global Leaderboard**
  - Updates scores, streaks, and accuracy in real time as Arena questions are answered, with paginated **Global Rankings**, **Top 10**, personal rank summary, and live auto-refresh.
- **Progress & Achievements**
  - Detailed accuracy, topic mastery, and high-score analytics plus **12 unlockable achievements** (*Novice Steps*, *Firebringer*, *Sharpshooter*, *Star Gazer*, *Master of the Streak*, *The Math Gladiator*, *Mathenique's 'The' Challenger*, *Survivor of the Apocalypse*, *The Wizard of Mathenique*, *Shoot for the Stars*, *A Mathenique Odyssey*, and *The Chosen*).
- **Interactive Sound System**
  - Zero-asset Web Audio API synthesizer producing tactile UI taps, streak-scaled correct-answer chimes, low-time warning ticks, and victory/defeat fanfares—with a navbar mute button and volume/preview controls in **Settings**.
- **Readable Math Notation**
  - Clean superscript exponent formatting (`2x² - x - 3`, `sin²x + cos²x`, `(x + 3)²`) via safe JSX rendering.

---

## 🛡️ Security & Architecture

- **Server-Authoritative Gameplay:** Question answer keys (`correct_index`) are never sent to the client before submission. Game sessions, answer verification, lives, timeouts, star awards, stats, and leaderboard scores are computed and atomically finalized on the server.
- **Authentication & Hashing:** Passwords use SHA-256 pre-hashing with **Argon2** (`argon2-cffi`); sessions use **PyJWT** (`HS256`) access tokens validated against active database users.
- **Abuse & Transport Protection:** Sliding-window per-IP and per-account rate limiting, Pydantic input validation, environment-driven CORS & `TrustedHostMiddleware`, HTTP security headers (`X-Content-Type-Options`, `X-Frame-Options`, `Referrer-Policy`, `Permissions-Policy`, `Cache-Control`, and HSTS in production), and automatic OpenAPI/Swagger hiding when `ENVIRONMENT=production`.

---

## 🛠️ Tech Stack

### Frontend (`Mathenique-main/src`)
- **Framework:** React 18, TypeScript, Vite
- **Styling & UI:** Tailwind CSS, Shadcn/UI (`@radix-ui/*`), Lucide React, Sonner
- **Data & Routing:** Axios, React Router v6, TanStack Query
- **Audio:** Native Web Audio API (`src/lib/sound.ts`)

### Backend (`Mathenique-main/backend`)
- **API Framework:** FastAPI, Starlette, Pydantic v2, Uvicorn
- **Database & ORM:** SQLAlchemy 2.0 (`SQLite` for local dev, `PostgreSQL` via `psycopg2-binary` in production)
- **Auth:** PyJWT, Argon2 (`argon2-cffi`), python-dotenv

---

## 📁 Project Structure

```text
MATHENIQUE-/
├── README.md
└── Mathenique-main/
    ├── .env.example
    ├── index.html
    ├── package.json
    ├── requirements.txt
    ├── check_db_script.py
    ├── backend/
    │   ├── auth.py             # Argon2 password hashing & PyJWT bearer verification
    │   ├── database.py         # SQLAlchemy engine (SQLite / PostgreSQL)
    │   ├── main.py             # FastAPI app, lifespan seeding, security middleware, API routes
    │   ├── models.py           # User, Progress, LessonProgress, Question, GameSession, Leaderboard
    │   ├── questions_seed.py   # Initial Algebra, Geometry, and Trigonometry question bank
    │   ├── schemas.py          # Pydantic request/response schemas & validation
    │   └── security.py         # Sliding-window rate limiter & proxy IP resolution
    └── src/
        ├── api/axios.ts        # Axios client & Authorization header interceptor
        ├── components/         # UI components, Navigation, QuestionCard, MathText, Timer, Sonner
        ├── contexts/           # AuthContext, GameContext, SoundContext
        ├── data/lessons.ts     # Adventure lesson metadata
        ├── lib/sound.ts        # Web Audio API sound synthesizer
        └── pages/              # Index, Auth, Lessons, Play, Progress, Leaderboard, Settings
```

---

## 🚀 Local Setup & Running

### Prerequisites
- **Node.js** v18+
- **Python** v3.10+

### 1. Clone & Enter App Directory
```bash
git clone https://github.com/Koyuki88/MATHENIQUE-.git
cd MATHENIQUE-/Mathenique-main
```

### 2. Configure Environment Variables
Copy `.env.example` to `.env` inside `Mathenique-main/` (adjust values as needed):
```bash
cp .env.example .env
```
For local development, `VITE_API_URL=http://127.0.0.1:8000` works out of the box. In production, always set a strong random `SECRET_KEY`.

### 3. Backend Setup
```bash
# Create and activate a virtual environment
python -m venv venv
# Windows PowerShell: .\venv\Scripts\Activate.ps1
# macOS/Linux:        source venv/bin/activate

# Install Python dependencies
pip install -r requirements.txt

# Start FastAPI server (auto-creates tables and seeds questions on startup)
uvicorn backend.main:app --reload
```
Backend API runs at `http://127.0.0.1:8000` (interactive docs at `/docs` in development).

### 4. Frontend Setup
In a second terminal inside `Mathenique-main/`:
```bash
npm install
npm run dev
```
Frontend runs at `http://localhost:8080`.

---

## 🔌 API Overview

| Method & Path | Auth | Description |
| :--- | :---: | :--- |
| `POST /register` | No | Create account (validates unique email & username, min 8-char password) |
| `POST /login` | No | Authenticate via OAuth2 form and issue JWT access token |
| `GET /me` | Yes | Fetch current authenticated user profile |
| `GET /stats` | Yes | Get user gameplay statistics & high scores |
| `GET /lessons/progress` | Yes | Get completed Adventure lessons and star ratings |
| `POST /game/start` | Yes | Start a server-tracked Lesson or Arena session (returns questions without answers) |
| `POST /game/{session_id}/answer` | Yes | Evaluate answer server-side, update score/lives/leaderboard |
| `POST /game/{session_id}/timeout` | Yes | Handle Challenge/Apocalypse timer expiration |
| `POST /game/{session_id}/finish` | Yes | Idempotently finalize session, award stars, and record game outcome |
| `GET /leaderboard/global` | Yes | Paginated global leaderboard (`skip`, `limit`) |
| `GET /leaderboard/top-10` | Yes | Top 10 ranked players |
| `GET /leaderboard/my-rank` | Yes | Current user's rank, score, and total player count |
| `GET /leaderboard/user/{user_name}` | Yes | Exact case-insensitive player leaderboard lookup |

---

## 🚢 Deployment (Render)

Set **Root Directory** to `Mathenique-main` for both Render services:

### Backend (Python Web Service)
- **Build Command:** `pip install -r requirements.txt`
- **Start Command:** `uvicorn backend.main:app --host 0.0.0.0 --port $PORT`
- **Environment Variables:**
  - `ENVIRONMENT=production`
  - `SECRET_KEY` *(32+ random characters, e.g. `python -c "import secrets; print(secrets.token_urlsafe(48))"`)*
  - `DATABASE_URL` *(Render PostgreSQL Internal Database URL)*
  - `TRUST_PROXY_HEADERS=true`
  - `ALLOWED_ORIGINS` *(comma-separated frontend URL(s), no trailing slash)*
  - `ALLOWED_HOSTS` *(backend hostname, e.g. `your-backend.onrender.com`)*

### Frontend (Static Site)
- **Build Command:** `npm install && npm run build`
- **Publish Directory:** `dist`
- **Rewrite Rule:** `/*` → `/index.html` (SPA routing)
- **Environment Variable:** `VITE_API_URL=https://your-backend.onrender.com`

---

## 📄 License

This project is open source under the **MIT License**.
