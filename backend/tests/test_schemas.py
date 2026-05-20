from datetime import datetime, timezone

import pytest

from app.schemas.event import EventCreate


def test_event_schema_rejects_blank_name() -> None:
    with pytest.raises(ValueError):
        EventCreate(
            event_name="   ",
            timestamp=datetime.now(timezone.utc),
            user_id="user-1",
            properties={},
        )


def test_event_schema_accepts_valid_payload() -> None:
    event = EventCreate(
        event_name="signup_completed",
        timestamp=datetime.now(timezone.utc),
        user_id="user-1",
        properties={"plan": "pro"},
    )
    assert event.event_name == "signup_completed"
    assert event.properties["plan"] == "pro"
