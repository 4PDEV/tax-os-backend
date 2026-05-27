# tax-os-backend

Backend implementation repository for TAX-OS.

## Purpose

This repository contains the backend API, database models, migrations, services, storage abstraction, audit logic, and deterministic source registry infrastructure.

## Initial Stack

- Python
- FastAPI
- SQLAlchemy 2.x
- Alembic
- PostgreSQL
- Pytest

## Governance

Implementation must follow the architecture repository:

- tax-os-architecture
- bounded tasks only
- deterministic-first
- source-referenced
- version-aware
- audit-first
