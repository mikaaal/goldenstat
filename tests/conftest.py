"""
Shared test fixtures for GoldenStat tests.

Creates a Flask test client backed by temporary copies of the real databases,
so tests can exercise every endpoint without touching production data.
"""
import os
import shutil
import tempfile

import pytest

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


@pytest.fixture(scope="session")
def test_db_dir():
    """Copy the real databases into a temp directory once per test session."""
    tmp = tempfile.mkdtemp(prefix="goldenstat_test_")
    for db_name in ("goldenstat.db", "riksserien.db", "cups.db"):
        src = os.path.join(ROOT_DIR, db_name)
        if os.path.exists(src):
            shutil.copy2(src, os.path.join(tmp, db_name))
    yield tmp
    shutil.rmtree(tmp, ignore_errors=True)


@pytest.fixture(scope="session")
def app(test_db_dir):
    """Create a Flask application configured for testing."""
    os.environ["DATABASE_PATH"] = os.path.join(test_db_dir, "goldenstat.db")
    os.environ["TOURNAMENTS_DATABASE_PATH"] = os.path.join(test_db_dir, "cups.db")

    # Change working directory so relative DB paths resolve inside temp dir
    original_cwd = os.getcwd()
    os.chdir(test_db_dir)

    # Copy templates/static so Flask can find them
    for folder in ("templates", "static"):
        src = os.path.join(ROOT_DIR, folder)
        if os.path.exists(src):
            dst = os.path.join(test_db_dir, folder)
            if not os.path.exists(dst):
                shutil.copytree(src, dst)

    # Now import and configure the app
    import importlib
    import sys

    # Ensure the project root is on sys.path
    if ROOT_DIR not in sys.path:
        sys.path.insert(0, ROOT_DIR)

    # Remove cached modules so they pick up the new env vars
    for mod_name in list(sys.modules):
        if mod_name in ("app", "database", "cup_database") or mod_name.startswith("routes."):
            del sys.modules[mod_name]

    import app as app_module

    app_module.app.config["TESTING"] = True
    app_module.app.config["CACHE_TYPE"] = "NullCache"

    yield app_module.app

    os.chdir(original_cwd)


@pytest.fixture(scope="session")
def client(app):
    """A Flask test client for making requests."""
    return app.test_client()
