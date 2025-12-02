# Transparent AI Interview Coach

> "每个英语学习者都值得一个透明的 AI 教练"

A multi-agent English interview coaching system built with Claude Agent SDK. This project demonstrates transparent AI decision-making through real-time observation of agent activities.

## Features

- **Multi-Agent System**: Three specialized agents working together
  - 🎤 **Interviewer Agent**: Conducts professional English interviews
  - 📊 **Scorer Agent**: Evaluates answers across 4 dimensions (Grammar, Content, Fluency, Vocabulary)
  - 💡 **Feedback Agent**: Provides actionable improvement suggestions in Chinese

- **Transparent AI**: Real-time observation panel showing:
  - Agent handoff events
  - Thinking process visualization
  - Tool call tracking
  - Token consumption and latency metrics

- **Interview Simulation**: Practice English interviews with:
  - Realistic interview questions
  - Multi-dimensional scoring (1-10 scale)
  - Detailed feedback with examples
  - Practice suggestions

## Project Structure

```
interview-coach/
├── backend/                 # Python FastAPI backend
│   ├── agents/             # Agent definitions and prompts
│   │   ├── interviewer.py  # Interviewer Agent
│   │   ├── scorer.py       # Scorer Agent
│   │   └── feedback.py     # Feedback Agent
│   ├── tools/              # MCP tools
│   │   ├── scoring.py      # Scoring evaluation tools
│   │   └── questions.py    # Question bank
│   ├── api/                # API routes and WebSocket
│   │   ├── routes.py       # REST endpoints
│   │   ├── websocket.py    # Real-time tracing
│   │   └── models.py       # Pydantic models
│   ├── main.py             # FastAPI application
│   └── interview_runner.py # Claude Agent SDK integration
│
└── frontend/               # React + TypeScript frontend
    ├── src/
    │   ├── components/     # React components
    │   │   ├── InterviewPanel.tsx
    │   │   ├── ObservationPanel.tsx
    │   │   └── ScoreCard.tsx
    │   ├── hooks/          # Custom hooks
    │   │   └── useWebSocket.ts
    │   └── utils/          # Utilities
    │       └── api.ts
    └── ...config files
```

## Quick Start

### Prerequisites

- Python 3.10+
- Node.js 18+
- Claude Agent SDK (claude-agent-sdk)

### Backend Setup

```bash
cd interview-coach/backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -e .

# Copy environment file
cp .env.example .env

# Run the server
python main.py
```

The API will be available at `http://localhost:8000`

### Frontend Setup

```bash
cd interview-coach/frontend

# Install dependencies
npm install

# Run development server
npm run dev
```

The frontend will be available at `http://localhost:3000`

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/interview/start` | POST | Start a new interview session |
| `/api/interview/answer` | POST | Submit an answer for evaluation |
| `/api/interview/session/{id}` | GET | Get session state |
| `/api/interview/trace/{id}` | GET | Get trace events |
| `/api/interview/ws/{id}` | WebSocket | Real-time trace streaming |

## Agent Architecture

```
┌────────────────────────────────────────────────────────────────┐
│                     User Interface                              │
│  ┌──────────────────────┐    ┌───────────────────────────────┐ │
│  │   Interview Panel    │    │    Observation Panel          │ │
│  │   - Q&A Display      │    │    - Agent Events             │ │
│  │   - Score Cards      │    │    - Handoff Flow             │ │
│  │   - Feedback         │    │    - Metrics                  │ │
│  └──────────────────────┘    └───────────────────────────────┘ │
└────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌────────────────────────────────────────────────────────────────┐
│                    Agent Orchestration                          │
│                                                                  │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐      │
│  │ Interviewer  │───▶│   Scorer     │───▶│  Feedback    │      │
│  │    Agent     │    │    Agent     │    │    Agent     │      │
│  │              │    │              │    │              │      │
│  │ - Ask Qs     │    │ - Evaluate   │    │ - Synthesize │      │
│  │ - Follow-up  │    │ - Score      │    │ - Suggest    │      │
│  └──────────────┘    └──────────────┘    └──────────────┘      │
│          │                  │                  │                │
│          └──────────────────┴──────────────────┘                │
│                           │                                      │
│                    Trace Events → WebSocket                      │
└────────────────────────────────────────────────────────────────┘
```

## Scoring Dimensions

| Dimension | Weight | Description |
|-----------|--------|-------------|
| Grammar | 25% | Tense consistency, sentence structure, article usage |
| Content | 30% | Relevance, logical structure, specific examples |
| Fluency | 25% | Natural flow, filler words, pacing |
| Vocabulary | 20% | Word diversity, accuracy, professional terms |

## Demo Mode

The demo mode is optimized for a 2-3 minute presentation:
- 2 interview rounds
- Pre-selected questions from the question bank
- Real-time observation panel updates
- Comprehensive feedback generation

## Technology Stack

- **Backend**: Python, FastAPI, Claude Agent SDK
- **Frontend**: React, TypeScript, TailwindCSS, Vite
- **Communication**: REST API + WebSocket for real-time updates
- **LLM**: Claude (via Claude Agent SDK)

## Contributing

This project was created for the Volcengine Winter Conference Demo. Contributions are welcome!

## License

MIT License - See LICENSE file for details.

---

Built with ❤️ by OneOneTalk × AgentKit
