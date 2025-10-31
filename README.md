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
