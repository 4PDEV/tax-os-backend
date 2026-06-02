from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


from app.core.config import settings
from app.models.base.base import Base

from urllib.parse import quote_plus

# Import models for metadata discovery
from app.models import (  # noqa: F401
    AuditLog,
    Country,
    MonitoringAttempt,
    MonitoringCandidate,
    MonitoringCandidateStateTransition,
    MonitoringEvent,
    SourceAllowlistEntry,
    FetchRequest,
    FetchResult,
    ExtractedText,
    ExtractionRun,
    IngestionStateTransition,
    LegalObject,
    LegalObjectDuplicate,
    LegalObjectLineage,
    LegalObjectVersion,
    ParsedStructure,
    ParserRun,
    SourceDocument,
    SourceProcessingJob,
    SourceRetrievalLog,
    SourceVersion,
    TaxType,
)

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

encoded_password = quote_plus(settings.POSTGRES_PASSWORD)

DATABASE_URL = (
    f"postgresql://{settings.POSTGRES_USER}:"
    f"{encoded_password}@"
    f"{settings.POSTGRES_HOST}:"
    f"{settings.POSTGRES_PORT}/"
    f"{settings.POSTGRES_DB}"
)

#config.set_main_option("sqlalchemy.url", DATABASE_URL)
config.set_main_option("sqlalchemy.url", DATABASE_URL.replace("%", "%%"))

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")

    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
