import pytest

from pySimBlocks.real_time.real_time_process import Gate, on, _ON_ATTR


# ---------------------------------------------------------------------------
# Gate
# ---------------------------------------------------------------------------

def test_gate_does_not_fire_on_first_event_of_two():
    g = Gate("tick", wait_for=["A", "B"])
    assert g.feed("A") is False


def test_gate_fires_when_all_events_received():
    g = Gate("tick", wait_for=["A", "B"])
    g.feed("A")
    assert g.feed("B") is True


def test_gate_fires_regardless_of_arrival_order():
    g = Gate("tick", wait_for=["A", "B", "C"])
    g.feed("C")
    g.feed("A")
    assert g.feed("B") is True


def test_gate_repeated_feed_of_same_event_does_not_fire_early():
    """
    Feeding the same event multiple times must not make the gate fire
    before all *other* events have also arrived.
    """
    g = Gate("tick", wait_for=["A", "B"])
    g.feed("A")
    g.feed("A")
    assert g.feed("A") is False


def test_gate_reset_clears_all_received_flags():
    g = Gate("tick", wait_for=["A", "B"])
    g.feed("A")
    g.feed("B")
    g.reset()
    assert g.feed("A") is False


def test_gate_fires_again_after_reset():
    g = Gate("tick", wait_for=["A", "B"])
    g.feed("A")
    g.feed("B")
    g.reset()
    g.feed("A")
    assert g.feed("B") is True


def test_gate_pending_events_reflects_missing():
    g = Gate("tick", wait_for=["A", "B", "C"])
    g.feed("B")
    assert set(g.pending_events) == {"A", "C"}


def test_gate_pending_events_empty_when_all_received():
    g = Gate("tick", wait_for=["A", "B"])
    g.feed("A")
    g.feed("B")
    assert g.pending_events == []


def test_gate_ignores_unknown_event():
    g = Gate("tick", wait_for=["A"])
    g.feed("UNKNOWN")
    assert g.feed("A") is True   # still fires when the real event arrives


def test_gate_empty_wait_for_raises():
    with pytest.raises(ValueError):
        Gate("tick", wait_for=[])


# ---------------------------------------------------------------------------
# @on decorator
# ---------------------------------------------------------------------------

def test_on_sets_event_attribute_on_function():
    @on("my_event")
    def handler():
        pass

    assert getattr(handler, _ON_ATTR) == "my_event"


def test_on_applied_twice_to_same_handler_raises():
    """
    A single handler is only allowed to react to one event.
    Stacking two @on decorators must raise TypeError immediately.
    """
    with pytest.raises(TypeError, match="once"):
        @on("second_event")
        @on("first_event")
        def handler():
            pass
