import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from pos_engine.engine import PobEngine  # noqa: E402


@pytest.fixture(scope="session")
def engine():
    eng = PobEngine()
    yield eng
    eng.close()


@pytest.fixture()
def fireball(engine):
    engine.new_build()
    engine.paste_skill("Fireball 20/0  1")
    return engine
