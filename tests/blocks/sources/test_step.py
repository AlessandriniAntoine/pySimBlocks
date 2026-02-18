import numpy as np
import pytest

from pySimBlocks.blocks.sources.step import Step


def test_step_scalar_before_after():
    s = Step("s", 0.0, 1.0, start_time=1.0)
    s.initialize(0.0)
    assert np.allclose(s.outputs["out"], [[0.0]])
    s.initialize(2.0)
    assert np.allclose(s.outputs["out"], [[1.0]])


def test_step_vector():
    s = Step("s", [0, 0], [1, 2], start_time=1.0)
    s.initialize(0.0)
    assert np.allclose(s.outputs["out"], [[0.0], [0.0]])
    s.initialize(2.0)
    assert np.allclose(s.outputs["out"], [[1.0], [2.0]])


def test_step_matrix_same_shape():
    vb = np.array([[0.0, 0.5],
                   [1.0, 1.5]])
    va = np.array([[2.0, 2.5],
                   [3.0, 3.5]])
    s = Step("s", vb, va, start_time=1.0)

    s.initialize(0.0)
    assert np.allclose(s.outputs["out"], vb)
    s.initialize(2.0)
    assert np.allclose(s.outputs["out"], va)


def test_step_scalar_broadcast_to_matrix_before():
    # value_before scalar, value_after matrix -> broadcast before
    vb = 0.0
    va = np.array([[1.0, 2.0],
                   [3.0, 4.0]])
    s = Step("s", vb, va, start_time=1.0)

    s.initialize(0.0)
    assert np.allclose(s.outputs["out"], np.zeros((2, 2)))
    s.initialize(2.0)
    assert np.allclose(s.outputs["out"], va)


def test_step_scalar_broadcast_to_matrix_after():
    # value_before matrix, value_after scalar -> broadcast after
    vb = np.array([[1.0, 2.0],
                   [3.0, 4.0]])
    va = 0.0
    s = Step("s", vb, va, start_time=1.0)

    s.initialize(0.0)
    assert np.allclose(s.outputs["out"], vb)
    s.initialize(2.0)
    assert np.allclose(s.outputs["out"], np.zeros((2, 2)))


def test_step_shape_mismatch_non_scalars():
    vb = np.zeros((2, 2))
    va = np.zeros((2, 3))
    with pytest.raises(ValueError):
        Step("s", vb, va, start_time=1.0)


def test_step_bad_start_time_type():
    with pytest.raises(TypeError):
        Step("s", 0, 1, start_time=[1.0])


def test_step_bad_ndim():
    with pytest.raises(ValueError):
        Step("s", np.zeros((2, 2, 2)), 1.0, start_time=1.0)
