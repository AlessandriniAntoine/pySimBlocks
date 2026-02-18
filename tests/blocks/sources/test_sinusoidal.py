import numpy as np
import pytest

from pySimBlocks.blocks.sources.sinusoidal import Sinusoidal


# ----------------------------------------------------------
# 1) Scalar parameters
# ----------------------------------------------------------
def test_sinusoidal_scalar():
    s = Sinusoidal("s", amplitude=2.0, frequency=1.0, offset=0.5, phase=0.0)
    s.initialize(0.0)
    assert np.allclose(s.outputs["out"], [[0.5]])  # sin(0)=0


def test_sinusoidal_scalar_time():
    s = Sinusoidal("s", 2.0, 1.0, 0.0, 0.0)
    s.output_update(0.25, 0.1)  # sin(2π * 1 * 0.25) = sin(π/2) = 1
    assert np.allclose(s.outputs["out"], [[2.0]])


# ----------------------------------------------------------
# 2) Vector parameters (still valid)
# ----------------------------------------------------------
def test_sinusoidal_vector():
    s = Sinusoidal(
        "s",
        amplitude=[1.0, 2.0],
        frequency=[1.0, 0.5],
        offset=[0.0, 10.0],
        phase=[0.0, np.pi / 2],
    )
    s.output_update(0.0, 0.1)
    # out(0): [1*sin(0)+0, 2*sin(pi/2)+10] = [0, 12]
    assert np.allclose(s.outputs["out"], [[0.0], [12.0]])


# ----------------------------------------------------------
# 3) Broadcasting scalar to match non-scalar shape
#    (allowed only for scalar (1,1))
# ----------------------------------------------------------
def test_sinusoidal_broadcast_scalar_frequency():
    s = Sinusoidal(
        "s",
        amplitude=[1.0, 1.0, 1.0],
        frequency=0.5,  # scalar broadcast
        offset=0.0,
        phase=0.0,
    )
    s.output_update(1.0, 0.1)
    expected = np.sin(2 * np.pi * 0.5 * 1.0) * np.ones((3, 1))
    assert np.allclose(s.outputs["out"], expected)


# ----------------------------------------------------------
# 4) Matrix parameters (Option B)
# ----------------------------------------------------------
def test_sinusoidal_matrix_same_shape():
    A = np.array([[1.0, 2.0],
                  [3.0, 4.0]])
    F = np.array([[1.0, 0.5],
                  [2.0, 1.0]])
    O = np.array([[0.0, 10.0],
                  [20.0, 30.0]])
    P = np.array([[0.0, np.pi / 2],
                  [np.pi, 0.0]])

    s = Sinusoidal("s", amplitude=A, frequency=F, offset=O, phase=P)
    s.output_update(0.0, 0.1)

    expected = A * np.sin(2 * np.pi * F * 0.0 + P) + O
    assert np.allclose(s.outputs["out"], expected)


def test_sinusoidal_matrix_broadcast_scalar_phase():
    A = np.array([[1.0, 2.0],
                  [3.0, 4.0]])
    F = np.array([[1.0, 0.5],
                  [2.0, 1.0]])

    s = Sinusoidal("s", amplitude=A, frequency=F, offset=0.0, phase=0.0)  # scalars broadcast
    s.output_update(0.0, 0.1)

    expected = A * np.sin(2 * np.pi * F * 0.0 + 0.0) + 0.0
    assert np.allclose(s.outputs["out"], expected)


# ----------------------------------------------------------
# 5) Inconsistent parameter shapes among non-scalars -> error
# ----------------------------------------------------------
def test_sinusoidal_inconsistent_shapes():
    with pytest.raises(ValueError):
        Sinusoidal(
            "s",
            amplitude=np.zeros((2, 2)),
            frequency=np.zeros((2, 3)),  # mismatch
            offset=0.0,
            phase=0.0,
        )


# ----------------------------------------------------------
# 6) Illegal ndims (>2) -> error
# ----------------------------------------------------------
def test_sinusoidal_illegal_ndim():
    with pytest.raises(ValueError):
        Sinusoidal(
            "s",
            amplitude=np.zeros((2, 2, 2)),  # ndim=3 forbidden
            frequency=1.0,
            offset=0.0,
            phase=0.0,
        )
