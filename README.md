<div align="center">
  <h1>ThinkSpire</h1>
  <p><strong>AI-Powered Problem Solving Assistant</strong></p>
  <p>An intelligent learning platform that adapts to your skill level, helps debug code, and guides you through problem-solving using interactive AI conversations.</p>
  <br>
  <p>
    <img src="https://img.shields.io/badge/Frontend-Next.js%2014-black?style=flat-square&logo=next.js" />
    <img src="https://img.shields.io/badge/Backend-FastAPI-009688?style=flat-square&logo=fastapi" />
    <img src="https://img.shields.io/badge/Database-MongoDB-47A248?style=flat-square&logo=mongodb" />
    <img src="https://img.shields.io/badge/Cache-Redis-DC382D?style=flat-square&logo=redis" />
    <img src="https://img.shields.io/badge/AI-Groq%20API-F55036?style=flat-square" />
    <img src="https://img.shields.io/badge/Auth-JWT-000000?style=flat-square&logo=jsonwebtokens" />
    <img src="https://img.shields.io/badge/License-MIT-yellow?style=flat-square" />
  </p>
</div>

---

## Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [Features](#features)
  - [Adaptive Learning Engine](#adaptive-learning-engine)
  - [AI Multi-Provider System](#ai-multi-provider-system)
  - [Authentication & Security](#authentication--security)
  - [Rate Limiting & Protection](#rate-limiting--protection)
  - [Session Management](#session-management)
  - [User Interface](#user-interface)
- [Tech Stack](#tech-stack)
- [Project Structure](#project-structure)
- [Getting Started](#getting-started)
- [Environment Variables](#environment-variables)
- [API Reference](#api-reference)
- [Deployment](#deployment)
- [Security](#security)
- [Roadmap](#roadmap)

---

## Overview

Think Inspire is a full-stack web application that combines AI language models with adaptive learning strategies to create an intelligent problem-solving assistant. Unlike traditional chatbots, it tailors its teaching approach based on user behavior, tracks progress across sessions, and provides a secure, scalable platform for continuous learning.

### Problem Statement

Existing problem-solving platforms often fall into two categories:
- **Traditional forums** — Slow, unstructured, no personalization
- **Generic AI chatbots** — Stateless, no adaptive learning, no user management

Think Inspire bridges this gap by offering an **adaptive, stateful, AI-powered assistant** that:
- Adjusts its teaching strategy based on user skill level
- Maintains conversation history across sessions
- Provides secure user management with modern authentication
- Supports multiple AI providers for high availability

### Use Cases

- **Bug Debugging** — Paste error messages, get guided solutions
- **Concept Learning** — Ask "what is X?" to get structured explanations
- **Practice Problems** — Generate exercises at your skill level
- **Code Reviews** — Get feedback on your code
- **Interview Preparation** — Practice with adaptive difficulty

---

## Architecture

```
┌─────────────────┐      ┌─────────────────┐      ┌─────────────────┐
│                 │      │                 │      │                 │
│   Vercel CDN    │ ──►  │   FastAPI API   │ ──►  │  MongoDB Atlas  │
│   (Next.js)     │      │   (uvicorn)     │      │  (Users/Logs)   │
│                 │ ◄──  │                 │ ◄──  │                 │
└─────────────────┘      └───────┬─────────┘      └─────────────────┘
                                 │
                    ┌────────────┼────────────┐
                    │                         │
                    ▼                         ▼
           ┌────────────┐              ┌──────────┐
           │   Redis    │              │   LLM    │
           │  Cloud     │              │   API    │
           │ (Session)  │              │          │
           +-----------+               │(Fallback)│
           │ Blacklist  │              └──────────┘
           │ RateLimit  │
           └────────────┘
```

### Data Flow

1. **User** accesses the frontend via Vercel
2. **Frontend** sends requests to the FastAPI backend with JWT auth
3. **Backend** validates tokens via Redis blacklist
4. **Backend** loads session data from Redis/Memory
5. **Request** is sent to AI provider (Groq → Gemini → Ollama)
6. **Response** is returned and stored in session + MongoDB
7. **Rate limiting** applied to auth endpoints for security

---

## Features

### Adaptive Learning Engine

The core of Think Inspire is its **adaptive learning system** that adjusts teaching strategies based on user behavior.

**Teaching Modes:**

| Mode | Description | When Used |
|------|-------------|-----------|
| **EXPLAINER** | Direct explanations with examples | New users, quick questions |
| **TUTOR** | Socratic method — guides through questions | Users needing conceptual help |
| **PRACTICE** | Generates practice problems | Users who understand but need application |
| **DISCOVERY** | Guided exploration with puzzles | Advanced users seeking deeper understanding |

**Adaptive Logic:**
- **Tracks:** Message count, correct streaks, struggle patterns
- **Reacts:** Drops difficulty when user struggles, increases when mastering
- **Analyzes:** Repeat questions, similar problems, response time

**Example Flow:**
```
New User (Level 0) ──► EXPLAINER mode ──► Direct answers
         │
         ▼ (After 3+ messages)
Learning (Level 1) ──► TUTOR mode ──► Guiding questions
         │
         ▼ (After 5 correct answers)
Practicing (Level 2) ──► PRACTICE mode ──► Problems to solve
         │
         ▼ (Mastering)
Advanced (Level 3) ──► DISCOVERY mode ──► Explore concepts
```



### Authentication & Security

JWT-based authentication with modern security practices:

| Feature | Implementation | Benefit |
|---------|---------------|---------|
| **Access Tokens** | 15-minute expiration | Limits damage if stolen |
| **Refresh Tokens** | 7-day rotation | Persistent sessions |
| **Token Blacklist** | Redis with TTL | Immediate logout |
| **Password Validation** | 8+ chars, upper, number, special | Strong passwords |
| **Storage** | Argon2 hashing | Resistant to cracking |

### Rate Limiting & Protection

| Endpoint | Limit | Window | Lockout |
|----------|-------|--------|---------|
| `/login` | 5 attempts | 60 seconds | 5 min after 3 failures |
| `/signup` | 5 attempts | 60 seconds | — |

**Features:**
- Redis-backed distributed rate limiting
- In-memory fallback for fault tolerance
- Retry-After headers for client feedback
- Automatic lockout on brute force detection

### Session Management

| Component | Storage | Purpose |
|-----------|---------|---------|
| **Session Data** | Redis Cloud | Conversation history, learning level |
| **Fallback** | In-memory dict | Continues working when Redis is down |
| **TTL** | 7 days | Automatic cleanup |
| **Interaction Logs** | MongoDB | Analytics, progress tracking |


---


## Project Structure

```
think-inspire/
│
├── app/                              # Next.js Frontend
│   ├── chat/
│   │   └── page.tsx                  # Main chat interface
│   ├── login/
│   │   └── page.tsx                  # Login/Signup page
│   ├── page.tsx                      # Landing page
│   ├── layout.tsx                    # Root layout
│   ├── globals.css                   # Global styles
│   └── .env.local                    # Frontend environment
│
├── backend/                          # FastAPI Backend
│   ├── main.py                       # Entry point + CORS config
│   ├── requirements.txt              # Python dependencies
│   ├── Procfile                      # Render deployment config
│   │
│   ├── agent/
│   │   └── agent.py                  # Core learning agent logic
│   │
│   ├── api/v1/routers/
│   │   ├── auth.py                   # Login, signup, logout, refresh
│   │   └── chat.py                   # Chat, modes, progress endpoints
│   │
│   ├── database/
│   │   ├── mongodb.py                # MongoDB connection + logging
│   │   └── users.py                  # User CRUD operations
│   │
│   ├── services/
│   │   ├── ai_service.py             # Multi-provider AI orchestration
│   │   ├── auth_service.py           # JWT, password, blacklist
│   │   ├── error_handling.py         # Fallback responses, validation
│   │   └── rate_limiter.py           # Redis-backed rate limiting
│   │
│   ├── sessions/
│   │   └── redis_session.py          # Redis session with memory fallback
│   │
│   └── tests/
│       ├── test_agent.py             # Unit tests (15)
│       └── test_api.py               # Integration tests (14)
│
├── .gitignore
├── README.md
└── LICENSE
```

---

## Getting Started

### Prerequisites

| Dependency | Minimum Version | Installation |
|------------|----------------|--------------|
| Python | 3.10+ | [python.org](https://python.org) |
| Node.js | 18+ | [nodejs.org](https://nodejs.org) |


### 1. Clone the Repository

```bash
git clone https://github.com/your-username/think-inspire.git
cd think-inspire
```

### 2. Backend Setup

```bash
cd backend

# Create virtual environment (recommended)
python -m venv venv
source venv/bin/activate  # On Windows: .\venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your credentials (see below)

# Run the server
uvicorn main:app --reload --port 8000
```

### 3. Frontend Setup

```bash
cd app

# Install dependencies
npm install

# Configure environment
echo "NEXT_PUBLIC_API_URL=http://localhost:8000" > .env.local

# Run development server
npm run dev
```

### 4. Verify

- **Backend:** Open `http://localhost:8000/docs` (Swagger UI)
- **Frontend:** Open `http://localhost:3000`
- **Health Check:** `http://localhost:8000/health`

---

## Environment Variables

### Backend — `backend/.env`

```env
# ── Redis Cloud ─────────────────────────────────────

REDIS_URL=redis://default:your_password@your_host:your_port

# ── MongoDB Atlas ──────────────────────────────────

MONGO_URI=mongodb+srv://username:password@cluster.mongodb.net/
MONGO_DB=thinkinspire

# ── AI Provider ────────────────────────────────────

GROQ_API_KEY=gsk_your_groq_api_key


# ── Authentication ─────────────────────────────────
# Generate with: python -c "import secrets; print(secrets.token_urlsafe(32))"
JWT_SECRET=your_random_secret_key

# ── CORS ──────────────────────────────────────────
# Frontend URL for CORS policy
FRONTEND_URL=http://localhost:3000
```

### Frontend — `app/.env.local`

```env
# Backend API URL (local or deployed)
NEXT_PUBLIC_API_URL=http://localhost:8000
```

---

## Security

### Authentication Flow

```
1. Login ──► Server validates credentials ──► Returns access + refresh tokens
2. API call ──► Include access token in Authorization header
3. Token expires (15 min) ──► Use refresh token to get new access token
4. Logout ──► Token added to Redis blacklist (auto-expires)
5. Server restart ──► Blacklist persists in Redis
```

---

<div align="center">
  <p>Built with ❤️ for problem solvers</p>
  <p>
    <a href="https://github.com/priyanshijain1/think-inspire/issues">Report Bug</a> ·
    <a href="https://github.com/priyanshijain1/think-inspire/issues">Request Feature</a>
  </p>
</div>
