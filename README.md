# AI SEO Dashboard Monorepo

This repository contains the frontend and backend services for the AI-driven SEO dashboard. The project is structured as a monorepo with a React + Vite frontend and a FastAPI backend.

## Structure

- `frontend/` – Vite React application with Tailwind CSS and shadcn/ui.
- `backend/` – FastAPI application with SQLAlchemy, Celery, Redis, and Qdrant integrations.
- `.env.example` – Environment variables used by both services.
- `docker-compose.yml` – Local development dependencies (PostgreSQL, Redis, Qdrant, Prometheus, Loki).

Refer to the individual service READMEs for setup instructions.
