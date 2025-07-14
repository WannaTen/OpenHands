# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Development Commands

### Build and Setup
```bash
make build          # Full project build (installs dependencies, builds frontend)
make setup-config   # Setup config.toml with LLM API key and workspace directory
```

### Development Workflow
```bash
make run            # Start both backend and frontend servers
make start-backend  # Start backend server only (uvicorn on port 4000)
make start-frontend # Start frontend server only (Vite on port 4001)
make docker-dev     # Develop in Docker container
```

### Code Quality
```bash
make lint           # Run linters on both frontend and backend
make lint-backend   # Run Python linters (pre-commit hooks)
make lint-frontend  # Run frontend linters (ESLint)
make test           # Run test suites
make test-frontend  # Run frontend tests only
```

### Python Development
```bash
poetry run pytest ./tests/unit/test_*.py  # Run unit tests
poetry install --with dev,test,runtime    # Install dependencies
poetry run pre-commit run --all-files     # Run pre-commit hooks
```

### Frontend Development
```bash
cd frontend && npm run dev    # Start development server
cd frontend && npm run build  # Build production bundle
cd frontend && npm run test   # Run tests
```

## Architecture Overview

OpenHands is a modular AI-powered software development platform with the following key components:

### Core Architecture
- **Frontend**: React 19 + TypeScript + Vite application in `/frontend/`
- **Backend**: FastAPI Python server in `/openhands/server/`
- **Runtime**: Docker-based sandboxed execution environment in `/openhands/runtime/`
- **Agent Hub**: Pluggable AI agent implementations in `/openhands/agenthub/`

### Key Python Modules

#### `/openhands/agenthub/`
Contains different agent implementations:
- `codeact_agent/`: Primary coding agent with bash/Python execution
- `browsing_agent/`: Web browsing capabilities
- `visualbrowsing_agent/`: Visual web interaction
- All agents inherit from the base `Agent` class

#### `/openhands/runtime/`
Sandboxed execution environment:
- `docker_runtime.py`: Standard Docker container execution
- `kubernetes_runtime.py`: Kubernetes deployment support
- `local_runtime.py`: Local development runtime
- Plugin system for Jupyter, VSCode integration

#### `/openhands/server/`
FastAPI backend with routes:
- `conversation.py`: Chat and conversation management
- `files.py`: File operations and management
- `settings.py`: Configuration management
- WebSocket handling for real-time communication

#### `/openhands/events/`
Event-driven architecture:
- `action/`: User and agent actions (commands, file operations)
- `observation/`: Results and feedback from actions
- Event streaming and serialization for persistence

### Communication Flow
```
User → Frontend → WebSocket → Backend → Agent Controller → Agent → Runtime → Actions → Results
```

### Configuration
- `config.toml`: Main runtime configuration (LLM settings, workspace path)
- `pyproject.toml`: Python dependencies and project metadata
- `frontend/package.json`: Frontend dependencies and build scripts

### Development Patterns
- **Event-driven**: Actions and observations flow through the system
- **Sandboxed**: All code execution happens in isolated Docker containers
- **Modular**: Clear separation between agents, runtime, and server components
- **Real-time**: WebSocket communication for responsive UI

### Key Dependencies
- **Backend**: FastAPI, LiteLLM, Docker, Poetry
- **Frontend**: React 19, TypeScript, Vite, TailwindCSS, Monaco Editor
- **AI**: LiteLLM for multi-provider LLM support
- **Runtime**: Docker for sandboxed execution

### Testing
- Backend tests in `/tests/unit/` using pytest
- Frontend tests in `/frontend/__tests__/` using Jest/React Testing Library
- Evaluation framework in `/evaluation/` for benchmarking agents

### Extension Points
- Add new agents by implementing the `Agent` base class in `/openhands/agenthub/`
- Extend runtime capabilities in `/openhands/runtime/impl/`
- Add new evaluation benchmarks in `/evaluation/benchmarks/`
- MCP (Model Context Protocol) integration for external tools

## Important Notes

- **Python Version**: Requires Python 3.12+ (specified in pyproject.toml)
- **Node.js Version**: Requires Node.js 22+ (specified in frontend/package.json)
- **Docker**: Required for runtime sandboxing unless using local runtime
- **Configuration**: `config.toml` must be created before running (use `make setup-config`)
- **Workspace**: Default workspace directory is `./workspace/`
- **Logs**: Backend logs stored in `logs/` directory
- **LLM**: Supports multiple providers via LiteLLM (Claude Sonnet 4 recommended)

## Repository Structure

```
├── openhands/           # Core Python package
│   ├── agenthub/        # Agent implementations
│   ├── runtime/         # Sandboxed execution
│   ├── server/          # FastAPI backend
│   ├── events/          # Event system
│   └── ...
├── frontend/            # React frontend
├── evaluation/          # Benchmarking framework
├── microagents/         # Domain-specific prompts
├── third_party/         # External runtime integrations
└── tests/              # Test suites
```

Development workflow involves building with `make build`, configuring with `make setup-config`, and running with `make run` for full-stack development.
