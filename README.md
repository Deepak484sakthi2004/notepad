# NoteSpace

A full-stack note-taking and flashcard application with AI-powered study features.

## Tech Stack

- **Backend**: Python + Flask + SQLAlchemy + Flask-JWT-Extended
- **Database**: PostgreSQL + Redis
- **AI**: OpenAI GPT-4o
- **Frontend**: React (Vite) + TailwindCSS + TipTap
- **Auth**: JWT (access token in memory + refresh token in httpOnly cookie)

## Quick Start (Docker)

```bash
# Clone and enter the directory
cd notespace

# Copy env file and fill in your keys
cp backend/.env.example backend/.env

# Start all services
docker-compose up --build
```

Frontend: http://localhost:5173
Backend API: http://localhost:5000/api/health

## Local Development

### Backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # fill in values
python run.py
```

### Frontend

```bash
cd frontend
npm install
cp .env.example .env
npm run dev
```

## Environment Variables

### Backend (`backend/.env`)

| Variable | Description |
|----------|-------------|
| `SECRET_KEY` | Flask secret key |
| `JWT_SECRET_KEY` | JWT signing key |
| `DATABASE_URL` | PostgreSQL connection string |
| `REDIS_URL` | Redis connection string |
| `OPENAI_API_KEY` | OpenAI API key |
| `MAIL_*` | SMTP settings for password reset |

### Frontend (`frontend/.env`)

| Variable | Default |
|----------|---------|
| `VITE_API_BASE_URL` | `http://localhost:5000` |

## API Overview

| Group | Endpoints |
|-------|-----------|
| Auth | `/api/auth/*` |
| Workspaces | `/api/workspaces/*` |
| Pages | `/api/workspaces/:id/pages`, `/api/pages/:id/*` |
| Tags | `/api/workspaces/:id/tags`, `/api/tags/:id` |
| Search | `/api/search?q=` |
| Flashcards | `/api/flashcards/*` |
| AI | `/api/ai/ask` |

## Features

- **Rich note editor** with TipTap: headings, lists, tasks, code blocks, tables, images
- **Slash `/` command** menu for block insertion
- **Auto-save** with 1s debounce and visual indicator
- **AI flashcard generation** from note content (GPT-4o)
- **SM-2 spaced repetition** for optimal review scheduling
- **Study sessions** with card flip animation and keyboard shortcuts
- **Charts** for review history and accuracy over time
- **Full-text search** across all pages
- **Tags** for page organisation
- **Trash** with soft delete and restore
- **Export** pages as Markdown, plain text, or PDF
