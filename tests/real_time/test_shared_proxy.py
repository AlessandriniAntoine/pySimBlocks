import multiprocessing

import numpy as np
import pytest

from pySimBlocks.real_time.real_time_process import _SharedProxy


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _proxy(fields: dict) -> _SharedProxy:
    """Build a _SharedProxy with float64 arrays of the given sizes."""
    arrays = {name: multiprocessing.Array("d", [0.0] * size)
              for name, size in fields.items()}
    dtypes = {name: np.float64 for name in fields}
    return _SharedProxy(arrays, dtypes)


# ---------------------------------------------------------------------------
# Single-field read / write
# ---------------------------------------------------------------------------

def test_write_then_read_scalar_field():
    proxy = _proxy({"X": 1})
    proxy.X = np.array([42.0])
    assert float(proxy.X[0]) == pytest.approx(42.0)


def test_write_then_read_vector_field():
    proxy = _proxy({"V": 3})
    proxy.V = np.array([1.0, 2.0, 3.0])
    np.testing.assert_array_almost_equal(proxy.V, [1.0, 2.0, 3.0])


def test_read_returns_same_preallocated_buffer():
    """
    After the first read, the proxy caches a buffer per field.
    Subsequent reads must return the same object (zero allocation on hot path).
    """
    proxy = _proxy({"X": 2})
    proxy.X = np.array([1.0, 2.0])
    buf1 = proxy.X
    buf2 = proxy.X
    assert buf1 is buf2


def test_write_updates_buffer_content():
    proxy = _proxy({"X": 1})
    proxy.X = np.array([10.0])
    buf = proxy.X
    proxy.X = np.array([20.0])
    assert float(proxy.X[0]) == pytest.approx(20.0)
    assert buf is proxy.X   # same buffer object, updated in place


# ---------------------------------------------------------------------------
# Grouped read
# ---------------------------------------------------------------------------

def test_grouped_read_returns_all_requested_fields():
    proxy = _proxy({"A": 1, "B": 1})
    proxy.A = np.array([10.0])
    proxy.B = np.array([20.0])
    result = proxy.read("A", "B")
    assert set(result.keys()) == {"A", "B"}
    assert float(result["A"][0]) == pytest.approx(10.0)
    assert float(result["B"][0]) == pytest.approx(20.0)


def test_grouped_read_subset_of_fields():
    proxy = _proxy({"A": 1, "B": 1, "C": 1})
    proxy.A = np.array([1.0])
    proxy.C = np.array([3.0])
    result = proxy.read("A", "C")
    assert "B" not in result
    assert float(result["A"][0]) == pytest.approx(1.0)


# ---------------------------------------------------------------------------
# Grouped write
# ---------------------------------------------------------------------------

def test_grouped_write_updates_multiple_fields():
    proxy = _proxy({"A": 1, "B": 1})
    proxy.write(A=np.array([5.0]), B=np.array([9.0]))
    assert float(proxy.A[0]) == pytest.approx(5.0)
    assert float(proxy.B[0]) == pytest.approx(9.0)


def test_grouped_write_partial_update_does_not_touch_other_fields():
    proxy = _proxy({"A": 1, "B": 1})
    proxy.A = np.array([1.0])
    proxy.B = np.array([2.0])
    proxy.write(A=np.array([99.0]))
    assert float(proxy.B[0]) == pytest.approx(2.0)


# ---------------------------------------------------------------------------
# Error cases
# ---------------------------------------------------------------------------

def test_getattr_unknown_field_raises():
    proxy = _proxy({"X": 1})
    with pytest.raises(AttributeError, match="No shared field"):
        _ = proxy.Missing


def test_setattr_unknown_field_raises():
    proxy = _proxy({"X": 1})
    with pytest.raises(AttributeError, match="No shared field"):
        proxy.Missing = np.array([1.0])


def test_grouped_read_unknown_field_raises():
    proxy = _proxy({"X": 1})
    with pytest.raises(AttributeError, match="No shared field"):
        proxy.read("X", "Missing")


def test_grouped_write_unknown_field_raises():
    proxy = _proxy({"X": 1})
    with pytest.raises(AttributeError, match="No shared field"):
        proxy.write(Missing=np.array([1.0]))


# ---------------------------------------------------------------------------
# Repr
# ---------------------------------------------------------------------------

def test_repr_contains_field_names():
    proxy = _proxy({"Alpha": 2, "Beta": 1})
    r = repr(proxy)
    assert "Alpha" in r
    assert "Beta" in r
