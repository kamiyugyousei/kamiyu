import os
import sys

# ensure project root on path
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

# force in-memory sqlite for tests BEFORE importing app modules
os.environ["DATABASE_URL"] = "sqlite:///./data/test_threads_ai.db"

import pytest  # noqa: E402


@pytest.fixture()
def db():
    # fresh schema per test (drop+create rather than unlinking the open file)
    from app.database import Base, SessionLocal, engine, init_db

    engine.dispose()
    Base.metadata.drop_all(bind=engine)
    init_db()
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()
