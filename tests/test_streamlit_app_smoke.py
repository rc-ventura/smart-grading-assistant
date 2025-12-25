import sys
from pathlib import Path


def test_streamlit_app_smoke():
    repo_root = Path(__file__).resolve().parents[1]
    if str(repo_root) not in sys.path:
        sys.path.insert(0, str(repo_root))

    from streamlit.testing.v1 import AppTest

    at = AppTest.from_file(str(repo_root / "ui" / "app.py")).run(timeout=10)
    assert len(at.exception) == 0
