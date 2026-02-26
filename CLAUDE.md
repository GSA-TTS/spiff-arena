# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

SpiffArena is a BPMN workflow execution platform. It is a monorepo (git subtree-based) with a Python/Flask backend and a React/TypeScript frontend, built around the [SpiffWorkflow](https://github.com/sartography/SpiffWorkflow) BPMN engine.

## Common Commands

### Running All Tests + Linting

```bash
cd [git_root] && ./bin/run_pyl
```

This runs: frontend lint:fix, pre-commit hooks (ruff check/format), backend mypy, and backend pytest (parallel, random order, SQLite).

### Running a Single Backend Test

```bash
cd spiffworkflow-backend && poet [test_name]
# Example:
cd spiffworkflow-backend && poet test_process_instance_list_filter
```

Or a single test file:

```bash
cd spiffworkflow-backend && uv run pytest tests/spiffworkflow_backend/integration/test_process_model_milestones.py
```

Or with pytest -k:

```bash
cd spiffworkflow-backend && uv run pytest -k test_process_instance_list_filter
```

### Backend Tests in Parallel

```bash
cd spiffworkflow-backend && ./bin/tests-par
```

Requires SQLite test DB. Set up with: `SPIFFWORKFLOW_BACKEND_DATABASE_TYPE=sqlite ./bin/recreate_db clean`

### Frontend Commands

```bash
cd spiffworkflow-frontend
npm install          # install dependencies
npm start            # dev server on port 7001
npm run build        # production build
npm test             # vitest with coverage
npm run typecheck    # tsc --noEmit
npm run lint:fix     # eslint --fix
npm run check        # typecheck + lint:fix + test
```

### Backend Setup

```bash
cd spiffworkflow-backend
uv sync
./bin/recreate_db clean
./bin/run_server_locally           # starts on port 7000
./bin/run_server_locally keycloak  # use keycloak instead of built-in openid
```

## Tooling Constraints

- **Python**: Use `uv` (not pip or poetry). Backend requires 3.10+; root workspace requires 3.11 or 3.12 (not 3.13).
- **JavaScript**: Use `npm` (not yarn or pnpm).
- **Linting**: Backend uses `ruff` for linting/formatting and `mypy` (strict mode) for type checking. Frontend uses `eslint` and `prettier`.
- **Testing**: Backend uses `pytest` with SQLite for tests. Frontend uses `vitest` with jsdom.

## Architecture

### Monorepo Structure

- `spiffworkflow-backend/` — Python/Flask API server (Connexion + SQLAlchemy + Alembic)
- `spiffworkflow-frontend/` — React/TypeScript SPA (Vite + MUI + Carbon + bpmn-js)
- `spiff-arena-common/` — Shared Python library (workspace dependency)
- `connector-proxy-demo/` — Demo connector proxy service
- `connector-proxies/` — Additional connector proxy implementations

### Backend Architecture

**Entry point**: `create_app()` in `spiffworkflow_backend/__init__.py` creates a Connexion FlaskApp.

**API layer**: Routes defined in `api.yml` (OpenAPI 3.0.2) and implemented in `routes/` controllers. Connexion maps `operationId` to controller functions.

**Key directories under `spiffworkflow_backend/`**:
- `routes/` — API controllers (process_instances, process_models, tasks, messages, authentication, etc.)
- `models/` — SQLAlchemy models. Central models: `ProcessInstanceModel`, `TaskModel`, `HumanTaskModel`, `ProcessModelModel`, `UserModel`, `MessageInstanceModel`
- `services/` — Business logic. Key services: `process_instance_processor.py` (main workflow execution engine), `workflow_execution_service.py` (task execution), `process_model_service.py` (model CRUD + filesystem)
- `config/` — Environment-based config (`default.py`, `local_development.py`, `unit_testing.py`). Settings loaded via `config_from_env()` with `SPIFFWORKFLOW_BACKEND_` prefix.
- `background_processing/` — Celery-based async task processing
- `data_migrations/` — Data migration scripts (separate from Alembic schema migrations)
- `migrations/` — Alembic schema migrations (via Flask-Migrate)

**SpiffWorkflow integration**: `process_instance_processor.py` loads/runs serialized BPMN workflows. `bpmn_process_service.py` handles serialization with custom converters. Script tasks use RestrictedPython.

**Test structure**: `tests/spiffworkflow_backend/{integration,unit,scripts}/` with BPMN test fixtures in `tests/data/`. Tests use `with_db_and_bpmn_file_cleanup` and `with_super_admin_user` fixtures from `conftest.py`.

### Frontend Architecture

**Entry point**: `index.tsx` → `App.tsx` (BrowserRouter + QueryClientProvider + CASL AbilityContext).

**Key directories under `spiffworkflow-frontend/src/`**:
- `views/` — Page-level components (HomePage, TaskShow, ProcessModelShow, etc.)
- `components/` — Reusable UI components (ReactDiagramEditor, ProcessInstanceListTable, CustomForm, etc.)
- `services/` — API communication (`HttpService.ts` using fetch with JWT auth), user service, date/formatting utilities
- `hooks/` — Custom React hooks (useProcessInstances, usePermissionService, etc.)
- `contexts/` — React contexts (APIErrorContext, CASL ability)
- `rjsf/` — React JSON Schema Form customizations

**BPMN editor**: `packages/bpmn-js-spiffworkflow-react/` wraps bpmn-js with SpiffWorkflow-specific extensions, script/markdown/JSON schema editors, and diagram navigation.

**State management**: TanStack React Query v5 for server state; React contexts for app state; CASL for permissions.
