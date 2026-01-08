# Universal Knowledge Graph (UKG) System

> Enterprise-grade AI-powered knowledge management platform with a Next.js Frontend and Flask/MCP Backend.

[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Next.js](https://img.shields.io/badge/Next.js-14-black)](https://nextjs.org/)
[![Python](https://img.shields.io/badge/python-3.11%2B-blue)](https://www.python.org/downloads/)
[![Flask](https://img.shields.io/badge/flask-3.x-green)](https://flask.palletsprojects.com/)

---

## Overview

The **Universal Knowledge Graph (UKG)** is a dual-stack enterprise application designed for sophisticated knowledge synthesis and AI agent orchestration.

- **Frontend**: Modern **Next.js 14** application (TypeScript, Tailwind CSS) providing a rich, responsive user interface.
- **Backend**: robust **Flask** API acting as the Knowledge Engine, MCP Server, and LLM Gateway.

### Core Capabilities

- **17-Axis Framework**: Multi-dimensional knowledge organization.
- **Traceability**: Full execution tracing for every AI reasoning step.
- **MCP Integration**: Native Model Context Protocol server exposing 100+ Knowledge Algorithms.
- **LLM Gateway**: Middleware to enhance any LLM with UKG data and reasoning.

---

## Quick Start

### Prerequisites

- Node.js 18+
- Python 3.11+
- PostgreSQL 15+ (Local or Cloud)
- Redis (Optional, for rate limiting)

### 1. Backend Setup (Flask)

Runs the knowledge engine and API on `http://localhost:5000`.

```bash
# Terminal 1: Backend
cd DataLogicEngine
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

pip install -r requirements.txt

# Initial Setup
cp .env.template .env      # Configure DATABASE_URL in .env
flask db upgrade           # Run migrations
python backend/seed_data.py

python main.py
```

### 2. Frontend Setup (Next.js)

Runs the UI on `http://localhost:3000` and proxies API requests to backend.

```bash
# Terminal 2: Frontend
cd frontend
npm install
npm run dev
```

Visit **[http://localhost:3000](http://localhost:3000)** to launch the application.

---

## Architecture

The system uses a split architecture for maximum scalability and developer experience.

```mermaid
graph LR
    User[Web Browser] -->|Port 3000| Next[Next.js Frontend]
    Next -->|/api proxy| Flask[Flask Backend]
    Flask -->|SQL| DB[(PostgreSQL)]
    Flask -->|MCP| LLM[LLM Gateway]
```

### Frontend (`/frontend`)

- **Framework**: Next.js 14 (App Router)
- **Language**: TypeScript
- **Styling**: Tailwind CSS + Shadcn UI
- **Features**:
  - `dashboard/`: Real-time system monitoring.
  - `chat/`: Recursive reasoning interface.
  - `runs/`: Execution trace explorer.

### Backend (`/backend`, `/core`)

- **Framework**: Flask
- **Protocol**: HTTP + MCP (Model Context Protocol)
- **Key Modules**:
  - `core/mcp`: Registers 114 Knowledge Algorithms as tools.
  - `backend/tracing`: Distributed tracing for reasoning steps.
  - `backend/llm_gateway`: Universal adapter for OpenAI/Anthropic/Azure.

---

## API Documentation

The backend exposes a comprehensive REST API at `http://localhost:5000/api/v1`.

| Service     | Endpoint Prefix   | Description                        |
| :---------- | :---------------- | :--------------------------------- |
| **Trace**   | `/api/v1/trace`   | Store and retrieve execution logs. |
| **Gateway** | `/api/v1/gateway` | Chat with UKG-enhanced LLMs.       |
| **MCP**     | `/api/v1/mcp`     | Model Context Protocol endpoints.  |
| **System**  | `/health`         | System health check.               |

Interactive Swagger UI is available at `http://localhost:5000/api/docs`.

---

## Testing

```bash
# Backend Tests
pytest tests/

# Frontend Tests (Lint/Build check)
cd frontend
npm run lint
npm run build
```

---

## License

MIT
