import numpy as np
import pytest

from pySimBlocks.blocks.sources.ramp import Ramp


# ----------------------------------------------------------
# 1) Scalar slope and scalar start_time
# ----------------------------------------------------------
def test_ramp_scalar_before_start():
    r = Ramp("r", slope=2.0, start_time=1.0, offset=0.0)
    r.initialize(0.0)
    assert np.allclose(r.outputs["out"], [[0.0]])  # before start_time


def test_ramp_scalar_after_start():
    r = Ramp("r", slope=2.0, start_time=1.0, offset=0.0)
    r.output_update(2.0, 0.1)
    assert np.allclose(r.outputs["out"], [[2.0]])  # slope * (2 - 1) = 2


# ----------------------------------------------------------
# 2) Vector parameters (still valid)
# ----------------------------------------------------------
def test_ramp_vector_parameters():
    r = Ramp(
        "r",
        slope=[1.0, 2.0],
        start_time=[0.0, 1.0],
        offset=[0.0, 10.0],
    )
    r.output_update(2.0, 0.1)
    # first: 0 + 1*(2-0)=2
    # second: 10 + 2*(2-1)=12
    assert np.allclose(r.outputs["out"], [[2.0], [12.0]])


# ----------------------------------------------------------
# 3) Broadcasting scalar to match non-scalar shape
#    (broadcast allowed ONLY for scalar (1,1))
# ----------------------------------------------------------
def test_ramp_broadcast_scalar_start_time():
    r = Ramp(
        "r",
        slope=[1.0, 1.0, 1.0],
        start_time=0.0,  # scalar broadcast
        offset=0.0,      # scalar broadcast
    )
    r.output_update(2.0, 0.1)
    assert np.allclose(r.outputs["out"], [[2.0], [2.0], [2.0]])


# ----------------------------------------------------------
# 4) Matrix parameters (Option B)
# ----------------------------------------------------------
def test_ramp_matrix_parameters_same_shape():
    slope = np.array([[1.0, 2.0],
                      [3.0, 4.0]])
    start_time = np.array([[0.0, 1.0],
                           [1.0, 0.0]])
    offset = np.array([[10.0, 20.0],
                       [30.0, 40.0]])

    r = Ramp("r", slope=slope, start_time=start_time, offset=offset)
    r.output_update(2.0, 0.1)

    # dt = max(0, t - start_time)
    dt_mat = np.maximum(0.0, 2.0 - start_time)
    expected = offset + slope * dt_mat
    assert np.allclose(r.outputs["out"], expected)


def test_ramp_matrix_broadcast_scalar_offset():
    slope = np.array([[1.0, 2.0],
                      [3.0, 4.0]])
    start_time = np.array([[0.0, 1.0],
                           [1.0, 0.0]])

    r = Ramp("r", slope=slope, start_time=start_time, offset=5.0)  # scalar broadcast
    r.output_update(2.0, 0.1)

    dt_mat = np.maximum(0.0, 2.0 - start_time)
    expected = np.full((2, 2), 5.0) + slope * dt_mat
    assert np.allclose(r.outputs["out"], expected)


# ----------------------------------------------------------
# 5) Inconsistent shapes among non-scalars -> error
# ----------------------------------------------------------
def test_ramp_inconsistent_dimensions():
    with pytest.raises(ValueError):
        Ramp(
            "r",
            slope=np.zeros((2, 2)),
            start_time=np.zeros((2, 3)),  # mismatch
            offset=0.0,
        )


# ----------------------------------------------------------
# 6) Illegal ndims (>2) -> error
# ----------------------------------------------------------
def test_ramp_illegal_ndim():
    with pytest.raises(ValueError):
        Ramp(
            "r",
            slope=np.zeros((2, 2, 2)),  # ndim=3 forbidden
            start_time=0.0,
            offset=0.0,
        )
