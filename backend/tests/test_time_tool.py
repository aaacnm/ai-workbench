import pytest

from app.tools.time_tool import TimeInput, TimeToolError, current_time


def test_current_time_utc():
    result = current_time(TimeInput())
    assert result["timezone"] == "UTC"
    assert "T" in result["iso"]


def test_current_time_named_timezone():
    result = current_time(TimeInput(timezone="Asia/Shanghai"))
    assert result["timezone"] == "Asia/Shanghai"
    assert result["formatted"].endswith("CST") or "UTC+08" in result["formatted"]


def test_rejects_unknown_timezone():
    with pytest.raises(TimeToolError):
        current_time(TimeInput(timezone="Not/A_Timezone"))
