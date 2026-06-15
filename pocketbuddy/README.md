# 🎯 PocketBuddy 2.0 — AI-Powered Student Life Coach

A production-grade full-stack AI platform that continuously analyzes a student's financial behavior, emotional wellbeing, lifestyle habits, academic workload, and spending patterns to generate personalized routines, wellness plans, financial guidance, burnout prevention alerts, and life-management insights.

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Frontend (React + TS)                     │
│  Dashboard │ Financial │ Wellness │ Chat │ Routine │ Reports │
└─────────────────────────┬───────────────────────────────────┘
                          │ REST API
┌─────────────────────────▼───────────────────────────────────┐
│                    Backend (FastAPI)                          │
│  Auth │ Financial API │ Wellness API │ Chat │ Reports │ AI   │
└──┬──────────┬───────────────────────────────┬───────────────┘
   │          │                               │
   ▼          ▼                               ▼
┌──────┐  ┌───────┐              ┌────────────────────────────┐
│Postgres│  │ Redis │              │   AI Multi-Agent System     │
│  DB   │  │ Cache │              │                            │
└───────┘  └───────┘              │  ┌──────────────────────┐  │
                                  │  │ Financial Agent       │  │
                                  │  │ Wellness Agent        │  │
                                  │  │ Burnout Agent         │  │
                                  │  │ Routine Agent         │  │
                                  │  │ Emotional Agent       │  │
                                  │  │ Life Coach Agent      │  │
                                  │  └──────────────────────┘  │
                                  │         │                   │
                                  │    Gemini / OpenAI API      │
                                  └────────────────────────────┘
```

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | React 18, TypeScript, Tailwind CSS, Recharts, Zustand |
| Backend | FastAPI, Python 3.11, SQLAlchemy 2.0 (async) |
| Database | PostgreSQL 15 |
| Cache | Redis 7 |
| AI | Google Gemini API, OpenAI GPT-4o-mini (fallback) |
| Auth | JWT + Google OAuth |
| Deploy | Docker Compose |

## AI Agents

1. **Financial Wellness Agent** — Spending analysis, categorization, budget adherence, financial scoring
2. **Wellness Agent** — Sleep, stress, mood, nutrition, activity pattern analysis
3. **Burnout Detection Agent** — Multi-factor burnout risk assessment with early warnings
4. **Routine Planning Agent** — Personalized daily/weekly/exam routines based on constraints
5. **Emotional Support Agent** — Empathetic conversations, coping strategies, reflection prompts
6. **Student Life Coach Agent** — Synthesizes all agents into weekly action plans

## Quick Start

### Prerequisites
- Docker & Docker Compose
- Gemini API key (get free at https://aistudio.google.com)

### 1. Clone and configure
```bash
cd pocketbuddy
cp .env.example .env
# Edit .env and add your GEMINI_API_KEY
```

### 2. Start with Docker
```bash
docker-compose up --build
```

### 3. Access
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000/api/docs
- Health check: http://localhost:8000/health

### Development (without Docker)

**Backend:**
```bash
cd backend
python -m venv venv
venv\Scripts\activate  # Windows
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

**Frontend:**
```bash
cd frontend
npm install
npm run dev
```

## Features

### Financial Dashboard
- Manual expense/income logging
- Natural language expense logging ("Spent ₹250 on lunch")
- Bank statement PDF upload with AI extraction
- Category-wise spending breakdown
- Budget tracking and alerts
- Financial wellness score (0-100)

### Wellness Tracker
- Daily check-in (mood, stress, sleep, meals, water, study, exercise)
- AI emotional state classification
- Wellness score breakdown (radar chart)
- 30-day trend analysis
- Burnout risk monitoring

### AI Chat (Conversational Interface)
- Multi-agent routing based on message intent
- Conversational expense logging
- Conversational wellness updates
- Financial advice
- Emotional support
- Routine suggestions

### Routine Planner
- AI-generated personalized routines
- Daily / Weekly / Exam / Budget-friendly modes
- Considers: budget, living situation, schedule, sleep goals, food preferences
- Timeline visualization

### Weekly Reports
- Combined financial + wellness + burnout analysis
- Prioritized action plans
- PDF export
- Historical comparison

### Predictive Analytics
- Month-end spending forecast
- Burnout risk trend prediction
- Savings projection

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | /api/v1/auth/register | Register new user |
| POST | /api/v1/auth/login | Login |
| PUT | /api/v1/auth/profile | Update profile |
| POST | /api/v1/financial/expenses | Add expense |
| GET | /api/v1/financial/summary | Financial summary |
| POST | /api/v1/financial/expenses/conversational | NLP expense |
| POST | /api/v1/financial/statements/upload | Upload bank statement |
| POST | /api/v1/wellness/checkin | Daily check-in |
| GET | /api/v1/wellness/score | Wellness scores |
| GET | /api/v1/wellness/trends | Trend data |
| POST | /api/v1/chat/message | AI chat |
| POST | /api/v1/ai/routine/generate | Generate routine |
| GET | /api/v1/ai/burnout/status | Burnout assessment |
| GET | /api/v1/ai/predictions | Predictive analytics |
| POST | /api/v1/reports/weekly/generate | Generate weekly report |

## Project Structure

```
pocketbuddy/
├── backend/
│   ├── app/
│   │   ├── agents/          # AI multi-agent system
│   │   ├── api/v1/          # API endpoints
│   │   ├── core/            # Config, DB, security, Redis
│   │   ├── middleware/       # Logging, rate limiting
│   │   ├── models/          # SQLAlchemy models
│   │   ├── schemas/         # Pydantic schemas
│   │   ├── services/        # Business logic
│   │   └── main.py          # FastAPI app
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── components/      # Reusable UI components
│   │   ├── lib/             # API client, utilities
│   │   ├── pages/           # Page components
│   │   ├── store/           # Zustand state management
│   │   ├── App.tsx          # Router setup
│   │   └── main.tsx         # Entry point
│   ├── Dockerfile
│   └── package.json
├── docker-compose.yml
└── README.md
```

## License

MIT
