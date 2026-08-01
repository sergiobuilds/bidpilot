from unittest.mock import MagicMock, patch

from bidpilot.snowflake_store import SnowflakeBidRoomStore, configured_connection_name


def test_connection_name_is_explicit_environment_configuration(monkeypatch) -> None:
    monkeypatch.delenv("BIDPILOT_SNOWFLAKE_CONNECTION", raising=False)
    assert configured_connection_name() is None
    monkeypatch.setenv("BIDPILOT_SNOWFLAKE_CONNECTION", "contest")
    assert configured_connection_name() == "contest"


@patch("bidpilot.snowflake_store.snowflake.connector.connect")
def test_authenticated_store_uses_named_connection_and_preserves_provenance(connect: MagicMock) -> None:
    cursor = connect.return_value.cursor.return_value
    cursor.description = [("RUN_ID",), ("PROVIDER",), ("TRACE",)]
    cursor.fetchall.side_effect = [
        [("run-1", "CORTEX_CODE_CLI", '{"status":"PURSUE"}')],
        [], [], [], [], [],
    ]
    result = SnowflakeBidRoomStore("contest").load_run("run-1")
    connect.assert_called_with(connection_name="contest")
    assert result["run"]["provider"] == "CORTEX_CODE_CLI"
    assert result["run"]["trace"]["status"] == "PURSUE"
