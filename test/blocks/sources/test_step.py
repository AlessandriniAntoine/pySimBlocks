import numpy as np
import pytest

from pySimBlocks.blocks.sources.step import Step


# ----------------------------------------------
# 1) Basic scalar test
# ----------------------------------------------
def test_step_scalar_before():
    s = Step("s", 0.0, 1.0, start_time=1.0)
    s.initialize(0.0)
    assert np.allclose(s.outputs["out"], [[0.0]])
    s.initialize(1.5)
    assert np.allclose(s.outputs["out"], [[1.0]])


def test_step_scalar_after():
    s = Step("s", 0.0, 1.0, start_time=1.0)
    s.initialize(2.0)
    assert np.allclose(s.outputs["out"], [[1.0]])


# ----------------------------------------------
# 2) Vector values
# ----------------------------------------------
def test_step_vector():
    s = Step("s", [0, 0], [1, 2], start_time=1.0)
    s.initialize(0.0)
    assert np.allclose(s.outputs["out"], [[0.0], [0.0]])
    s.initialize(2.0)
    assert np.allclose(s.outputs["out"], [[1.0], [2.0]])


def test_step_vector_shape_mismatch():
    with pytest.raises(ValueError):
        Step("s", [0, 0], [[1], [2], [3]], start_time=1.0)


# ----------------------------------------------
# 3) Bad shapes (matrices)
# ----------------------------------------------
def test_step_bad_shape_matrix():
    with pytest.raises(ValueError):
        Step("s", np.zeros((2, 3)), [1, 2, 3], start_time=1.0)


# ----------------------------------------------
# 4) Bad start_time type
# ----------------------------------------------
def test_step_bad_start_time_type():
    with pytest.raises(TypeError):
        Step("s", 0, 1, start_time=[1.0])
