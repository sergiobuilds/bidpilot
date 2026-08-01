from pathlib import Path

from streamlit.testing.v1 import AppTest


def test_bid_room_reopens_latest_matching_persisted_run(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.delenv("BIDPILOT_SNOWFLAKE_CONNECTION", raising=False)
    monkeypatch.chdir(tmp_path)
    app_path = Path(__file__).parents[1] / "app.py"

    first = AppTest.from_file(app_path)
    first.run(timeout=30)
    first.button[0].click()
    first.run(timeout=30)
    assert any("Bid Room run saved:" in item.value for item in first.success)

    reopened = AppTest.from_file(app_path)
    reopened.run(timeout=30)
    assert any("Bid Room run saved:" in item.value for item in reopened.success)
