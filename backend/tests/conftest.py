import os
from pathlib import Path
from urllib.parse import quote_plus, urlparse

import pytest
from alembic import command
from alembic.config import Config
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event, text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import sessionmaker

ROOT_DIR = Path(__file__).resolve().parents[2]
ALEMBIC_INI_PATH = ROOT_DIR / "alembic.ini"
MIGRATIONS_PATH = ROOT_DIR / "backend" / "migrations"

def _build_db_url(host: str, port: str, user: str, password: str, db_name: str) -> str:
    encoded_password = quote_plus(password)
    return f"postgresql://{user}:{encoded_password}@{host}:{port}/{db_name}"


def _requires_explicit_test_database_url() -> bool:
    value = os.getenv("REQUIRE_TEST_DATABASE_URL", "1").strip().lower()
    return value not in {"0", "false", "no"}


def _is_safe_test_database_url(database_url: str) -> bool:
    parsed = urlparse(database_url)
    db_name = parsed.path.lstrip("/").lower()
    return bool(db_name) and ("test" in db_name or db_name.endswith("_ci"))


def _test_db_config() -> dict[str, str]:
    host = os.getenv("TEST_POSTGRES_HOST", "localhost")
    port = os.getenv("TEST_POSTGRES_PORT", "5432")
    db_name = os.getenv("TEST_POSTGRES_DB", "taxos_test")
    user = os.getenv("TEST_POSTGRES_USER", "postgres")
    password = os.getenv("TEST_POSTGRES_PASSWORD", "postgres")

    explicit_database_url = os.getenv("TEST_DATABASE_URL")
    if _requires_explicit_test_database_url() and not explicit_database_url:
        database_url = ""
    else:
        database_url = explicit_database_url or _build_db_url(
            host=host,
            port=port,
            user=user,
            password=password,
            db_name=db_name,
        )

    return {
        "host": host,
        "port": port,
        "db_name": db_name,
        "user": user,
        "password": password,
        "database_url": database_url,
    }


def _integration_skip_reason() -> str | None:
    cfg = _test_db_config()
    database_url = cfg["database_url"]
    if not database_url:
        return (
            "Skipping integration DB tests: TEST_DATABASE_URL is required for destructive "
            "migration/isolation tests. Set TEST_DATABASE_URL to a dedicated test database."
        )

    if not _is_safe_test_database_url(database_url):
        return (
            "Skipping integration DB tests: TEST_DATABASE_URL does not look like a dedicated "
            "test database (name must include 'test' or end with '_ci')."
        )

    engine = create_engine(database_url, connect_args={"connect_timeout": 3})
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
    except SQLAlchemyError as exc:
        return (
            "Skipping integration DB tests: TEST_DATABASE_URL is not reachable "
            f"({exc})."
        )
    finally:
        engine.dispose()
    return None


def pytest_collection_modifyitems(config, items):
    skip_reason = _integration_skip_reason()
    if not skip_reason:
        return
    marker = pytest.mark.skip(reason=skip_reason)
    for item in items:
        if "integration" in item.keywords:
            item.add_marker(marker)


@pytest.fixture(scope="session")
def _configure_test_database_env():
    cfg = _test_db_config()
    os.environ["POSTGRES_HOST"] = cfg["host"]
    os.environ["POSTGRES_PORT"] = cfg["port"]
    os.environ["POSTGRES_DB"] = cfg["db_name"]
    os.environ["POSTGRES_USER"] = cfg["user"]
    os.environ["POSTGRES_PASSWORD"] = cfg["password"]


@pytest.fixture(scope="session")
def migrated_test_database(_configure_test_database_env):
    skip_reason = _integration_skip_reason()
    if skip_reason:
        pytest.skip(skip_reason)

    cfg = _test_db_config()
    test_database_name = cfg["db_name"]
    admin_engine = create_engine(
        _build_db_url(
            host=cfg["host"],
            port=cfg["port"],
            user=cfg["user"],
            password=cfg["password"],
            db_name="postgres",
        ),
        isolation_level="AUTOCOMMIT",
        connect_args={"connect_timeout": 3},
    )
    with admin_engine.connect() as conn:
        exists = conn.execute(
            text("SELECT 1 FROM pg_database WHERE datname = :db_name"),
            {"db_name": test_database_name},
        ).scalar()
        if not exists:
            conn.execute(text(f'CREATE DATABASE "{test_database_name}"'))
    admin_engine.dispose()

    alembic_cfg = Config(str(ALEMBIC_INI_PATH))
    alembic_cfg.set_main_option("script_location", str(MIGRATIONS_PATH))
    command.downgrade(alembic_cfg, "base")
    command.upgrade(alembic_cfg, "head")

    yield


@pytest.fixture(scope="session")
def engine(migrated_test_database):
    from app.db.session import engine as app_engine

    return app_engine


@pytest.fixture()
def db_session(engine):
    connection = engine.connect()
    transaction = connection.begin()

    testing_session = sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=connection,
        expire_on_commit=False,
    )
    session = testing_session()

    session.begin_nested()

    @event.listens_for(session, "after_transaction_end")
    def _restart_savepoint(sess, trans):
        if trans.nested and not trans._parent.nested:
            sess.begin_nested()

    try:
        yield session
    finally:
        if session.is_active:
            session.close()
        if transaction.is_active:
            transaction.rollback()
        connection.close()


@pytest.fixture()
def client(db_session, tmp_path):
    from app.db.deps import get_db
    from app.main import app
    from app.storage.deps import get_storage
    from app.storage.local import LocalFileStorage

    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    storage = LocalFileStorage(tmp_path)

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_storage] = lambda: storage

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()
