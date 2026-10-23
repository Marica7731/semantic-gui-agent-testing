import pytest

from sgat.waiting import WaitTimeout, wait_until


class FakeClock:
    def __init__(self) -> None:
        self.now = 0.0

    def time(self) -> float:
        return self.now

    def sleep(self, seconds: float) -> None:
        self.now += seconds


def test_wait_until_returns_first_truthy_value():
    clock = FakeClock()
    calls = {"count": 0}

    def predicate():
        calls["count"] += 1
        return f"value-{calls['count']}" if calls["count"] >= 3 else None

    outcome = wait_until(predicate, timeout_s=10, poll_interval_s=0.1, clock=clock.time, sleep=clock.sleep)
    assert outcome == "value-3"


def test_wait_until_times_out():
    clock = FakeClock()
    with pytest.raises(WaitTimeout):
        wait_until(lambda: None, timeout_s=1.0, poll_interval_s=0.2, clock=clock.time, sleep=clock.sleep)
