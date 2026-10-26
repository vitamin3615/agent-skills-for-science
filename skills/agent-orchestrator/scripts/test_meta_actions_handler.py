import pytest

from utils.meta_actions_handler import MetaActionsHandler


def test_parse_valid():
    meta = {
        "actions": [
            {"phase": 3, "action": "increase_workers"},
            {"phase": 7, "action": "re_execute_failed_workers", "params": {"retry": 1}}
        ]
    }

    parsed = MetaActionsHandler.parse(meta)
    assert isinstance(parsed, list)
    assert parsed[0]["phase"] == 3
    assert parsed[1]["action"] == "re_execute_failed_workers"
    assert parsed[1]["params"]["retry"] == 1


def test_parse_none():
    assert MetaActionsHandler.parse(None) == []


def test_parse_invalid_structure():
    with pytest.raises(ValueError):
        MetaActionsHandler.parse({"actions": "notalist"})
