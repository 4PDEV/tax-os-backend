from datetime import timezone

from app.core.datetime_utils import utc_now


def test_utc_now_returns_timezone_aware_utc():
    value = utc_now()
    assert value.tzinfo is not None
    assert value.tzinfo == timezone.utc
    assert value.utcoffset().total_seconds() == 0
