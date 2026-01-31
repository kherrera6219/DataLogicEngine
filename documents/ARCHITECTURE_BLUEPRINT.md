# Architecture Blueprint

## 1. High-Level Overview
The DataLogicEngine is a hybrid desktop/web application designed for Universal Knowledge Graph (UKG) management and simulation. It employs a **Electron + Next.js** frontend and a **Python/Flask** backend.

### Core Deployment Modes
1. **Desktop Mode**: Electron wrapper launches a local Python server. Uses `file://` protocol or `app://` custom protocol for assets.
2. **Cloud Mode**: Standard Client-Server architecture where frontend connects to a remote API.

## 2. File Structure

### Root Directory
- **`app.py`**: Main Flask application factory and server configuration.
- **`main.py`**: Desktop entry point. Handles signal handling and local database management.
- **`models.py`**: Core SQLAlchemy database models (User, SimulationSession, KnowledgeGraphNode, etc.).
- **`extensions.py`**: Flask extensions initialization (db, login_manager, etc.).

### Backend (`/backend`)
The core logic resides here, organized by domain:
- **`api/`**: OpenAPI/Swagger specifications.
- **`auth/`**: Authentication logic (SSO, Replit Auth).
- **`config/`**: Configuration classes (Settings, API keys).
- **`knowledge_algorithms/`**: The "Brains" of the system. Contains KA-01 through KA-100+ implementation files for specific cognitive tasks.
- **`llm_gateway/`**: Interfaces with external LLM providers (OpenAI, Azure).
- **`mcp_server/`**: Model Context Protocol implementation for tool exposure.
- **`simulation/`**: Core simulation engine logic (10-layer architecture).
- **`truth_engine/`**: Validation and truth assurance logic.

### Frontend (`/frontend`)
- **`electron/`**: Electron main process code (`main.ts`).
- **`app/`**: Next.js App Router pages.
- **`components/`**: React components.
- **`out/`**: Static export output for Electron distribution.

### Documents (`/documents`)
Central repository for all technical documentation, architectural specs, and white papers.

### SDK (`/sdk`)
Python Client SDK for interacting with the UKG API programmatically.

## 3. Key Data Flows

### Simulation Flow
1. **Request**: User initiates simulation via Frontend `api/simulation/start`.
2. **Orchestration**: `simulation_engine.py` receives request.
3. **Execution**: `knowledge_algorithms` are invoked based on the configured workflow (`ka_registry.yaml`).
4. **Validation**: `truth_engine` validates steps.
5. **Storage**: Results stored in `SimulationSession` (SQLite/PostgreSQL).

### Application Startup (Desktop)
1. User launches `DataLogicEngine.exe`.
2. Electron starts `main.js`.
3. Electron spawns `main.py` as a child process.
4. `main.py` starts Flask server on `localhost:PORT`.
5. Electron loads `app://index.html`.
