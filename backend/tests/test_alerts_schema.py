import pytest
from pydantic import ValidationError

from app.schemas.alert import AlertCreate, AlertMute


def test_alert_create_valid() -> None:
    alert = AlertCreate(name="Errors", event_name="error_logged", threshold=5, window_minutes=10)
    assert alert.threshold == 5


def test_alert_create_invalid_threshold() -> None:
    with pytest.raises(ValidationError):
        AlertCreate(name="Errors", event_name="error_logged", threshold=0, window_minutes=10)


def test_alert_mute_minutes() -> None:
    mute = AlertMute(minutes=30)
    assert mute.minutes == 30
