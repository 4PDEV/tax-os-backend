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

# TAX-OS Backend

Backend infrastructure for the Source-Referenced Business & Tax Research Platform.

## Purpose

This repository contains the deterministic backend foundation for:

- source registry
- versioned legal source storage
- legal object infrastructure
- effective-date handling
- citation infrastructure
- audit logging
- ingestion pipelines
- workflow orchestration

The platform is designed to operate:
- country by country
- tax regime by tax regime
- module by module

Initial jurisdiction:
- Rwanda

Initial focus:
- VAT
- PAYE/PIT
- Withholding Tax
- Corporate Tax
- Capital Gains
- Customs & Excise

---

## Core Principles

- deterministic-first
- source-referenced
- version-aware
- effective-date-aware
- auditable
- modular
- extensible
- cloud-portable

AI assists workflows but is NOT the source of truth.

---

## Initial Stack

- Python
- FastAPI
- PostgreSQL
- SQLAlchemy
- Alembic
- Docker
- pgAdmin

---

## Repository Structure

backend/
  app/
    api/
    audit/
    core/
    db/
    models/
    schemas/
    services/
    storage/

  migrations/
  scripts/
  tests/

---

## Governance

All implementation must follow:
- bounded task execution
- architecture governance
- deterministic principles
- version-controlled evolution

No uncontrolled AI-generated architecture changes are permitted.

---

## Current Phase

TASK-001
Source Registry & Versioned Source Storage Foundation
