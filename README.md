# AI Path Finder — Personalized Learning Path Recommender

> **AI-powered learning platform** that builds personalized roadmaps, identifies skill gaps, and adapts to your feedback in real time.

---

## 🚀 Quick Start

### Prerequisites
- Python 3.10+
- Node.js 18+

### 1. Start Backend
```bash
cd backend
pip install fastapi uvicorn sqlalchemy pydantic pydantic-settings aiosqlite python-dotenv httpx python-multipart
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```
API runs at **http://localhost:8000** · Swagger docs at **http://localhost:8000/docs**

### 2. Start Frontend
```bash
cd frontend
npm install
npm run dev
```
App runs at **http://localhost:5173**

---

## 🎯 Demo Mode

Click **"Try Demo (Alex Chen)"** on the welcome screen to load a pre-seeded learner with:
- **Goal:** Backend Java Developer
- **Progress:** 28.5% complete
- **Skills:** Core Java (3.5/5), SQL (3/5), OOP (3.5/5)
- **Roadmap:** 4 phases, 12 items, 3 completed

---

## ✨ Key Features

| Feature | Description |
|---------|-------------|
| **Profile Analysis** | NLP extraction of goals, skills, timeline from natural language |
| **Skill Gap Analysis** | Priority-ranked gaps with radar chart visualization |
| **Smart Roadmap** | Phase-based roadmap with prerequisites, milestones, project tasks |
| **AI Mentor** | Context-aware chat grounded in your actual learning data |
| **Adaptive Learning** | Feedback (too easy / too hard / skip) triggers roadmap changes |
| **Assessments** | AI-generated quizzes that update your skill proficiency |
| **Next Best Action** | Always-on recommendation with confidence score |
| **Progress Dashboard** | Real-time stats: streak, hours learned, milestones, skill chart |

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────┐
│                Frontend (React + Vite)       │
│  Dashboard | Roadmap | AI Chat | Assessments │
└──────────────────┬──────────────────────────┘
                   │ REST API
┌──────────────────▼──────────────────────────┐
│             Backend (FastAPI)                │
│                                             │
│  ┌─────────────┐  ┌────────────────────┐   │
│  │ AI Engine   │  │ Recommendation     │   │
│  │ - Provider  │  │ Engine (scoring)   │   │
│  │ - Gemini    │  │                    │   │
│  │ - Fallback  │  │ Adaptation Engine  │   │
│  └─────────────┘  └────────────────────┘   │
│                                             │
│  ┌─────────────────────────────────────┐   │
│  │ SQLite / SQLAlchemy async ORM       │   │
│  └─────────────────────────────────────┘   │
└─────────────────────────────────────────────┘
```

## 📡 API Endpoints

| Endpoint | Description |
|----------|-------------|
| `GET /api/learners/demo` | Load demo learner |
| `GET /api/dashboard/{id}` | Full dashboard data |
| `GET /api/roadmaps/{id}` | Learning roadmap |
| `PUT /api/roadmaps/items/{id}/status` | Update item progress |
| `GET /api/skill-gaps/{id}` | Skill gap analysis |
| `POST /api/assistant/chat` | AI mentor chat |
| `POST /api/feedback` | Submit adaptive feedback |
| `POST /api/assessments/generate` | Generate skill quiz |
| `POST /api/assessments/{id}/submit` | Submit assessment |
| `GET /api/health` | Health check |

## 🤖 AI Strategy

- **With Gemini key:** Full AI personalization — NLP goal extraction, context-aware chat, adaptive quiz generation
- **Without key:** Deterministic fallback — rule-based responses grounded in learner data, pre-seeded questions, scoring algorithm

The app is **fully functional without an API key**.

---

## 🌱 Add Gemini AI

1. Get a free key at [Google AI Studio](https://aistudio.google.com/)
2. Create `backend/.env`:
   ```
   AI_API_KEY=your_key_here
   AI_PROVIDER=gemini
   ```
3. Restart the backend

---

## 📊 Recommendation Algorithm

Each roadmap item is scored on 8 factors:

| Factor | Weight |
|--------|--------|
| Goal alignment | 25% |
| Skill gap criticality | 20% |
| Prerequisites met | 15% |
| Difficulty match | 10% |
| Learning style | 10% |
| Time availability | 10% |
| Progress momentum | 5% |
| Feedback signals | 5% |
