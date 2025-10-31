# AI SEO + CRM Platform

This repository contains two isolated applications that share infrastructure but operate with different security scopes.

## Services

- `crm_api/`: FastAPI service serving sales users (`SALES`, `SALES_MANAGER`, `OWNER`).
- `ops_api/`: FastAPI service for SEO/DevOps operators (`SEO_ENGINEER`, `DEVOPS`, `OWNER`).
- `crm/`: React single-page app for sales workflows deployed at `https://crm.example.com`.
- `ops-console/`: React single-page app for operational tooling deployed at `https://ops.example.com`.

Each service exposes its own OpenAPI schema and enforces short-lived JWT access with role-based authorization.

## Local Development

```bash
poetry install --directory crm_api
poetry run --directory crm_api uvicorn app.main:app --reload

poetry install --directory ops_api
poetry run --directory ops_api uvicorn app.main:app --reload

npm install --prefix crm
npm run dev --prefix crm

npm install --prefix ops-console
npm run dev --prefix ops-console
```

Run automated tests with:

```bash
poetry run --directory crm_api pytest
poetry run --directory ops_api pytest
npm test --prefix crm
npm test --prefix ops-console
```

Run the orchestrator worker locally once Redis or RabbitMQ is available:

```bash
poetry run --directory ops_api celery -A ops_api.celery_app worker -l info
```

### Adding a new orchestrator task

1. Define a payload schema in `ops_api/app/schemas/orchestrator.py` so FastAPI can validate incoming requests.
2. Map the task name to a queue in `ops_api/orchestrator/celery_app.py` if it should run outside the default queue.
3. Implement the Celery function inside `ops_api/orchestrator/tasks/` using the `OrchestratorTask` base. The base automatically handles idempotency keys, retries, and status recording.
4. Expose the task through `ops_api/app/api/routes/orchestrator.py` by adding the schema to `PAYLOAD_SCHEMAS`.
5. Update the ops console (e.g. `ops-console/src/lib/api.ts`) if the UI needs to dispatch the new task.
6. Add or adjust pytest coverage under `ops_api/tests/` to assert queueing behavior.
