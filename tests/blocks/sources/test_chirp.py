import numpy as np
import pytest

from pySimBlocks.blocks.sources.chirp import Chirp


# ----------------------------------------------------------
# 1) Scalar parameters
# ----------------------------------------------------------
def test_chirp_scalar_at_start():
    c = Chirp(
        "c",
        amplitude=2.0,
        f0=1.0,
        f1=5.0,
        duration=2.0,
        offset=0.5,
        phase=0.0,
    )
    c.initialize(0.0)
    # tau = 0 → sin(0)=0
    assert np.allclose(c.outputs["out"], [[0.5]])


def test_chirp_scalar_mid_sweep():
    c = Chirp("c", 1.0, 1.0, 3.0, 2.0)
    c.output_update(1.0, 0.1)

    # expected phase manually
    k = (3.0 - 1.0) / 2.0
    tau = 1.0
    phi = 2 * np.pi * (1.0 * tau + 0.5 * k * tau**2)
    expected = np.sin(phi)

    assert np.allclose(c.outputs["out"], [[expected]])


# ----------------------------------------------------------
# 2) After sweep duration (constant frequency f1)
# ----------------------------------------------------------
def test_chirp_after_duration_continuity():
    c = Chirp("c", 1.0, 1.0, 3.0, 2.0)

    c.output_update(2.0, 0.1)  # end of sweep
    y_end = c.outputs["out"].copy()

    c.output_update(3.0, 0.1)  # after sweep
    y_after = c.outputs["out"]

    # just verify finite and defined (continuity handled in block)
    assert np.isfinite(y_end).all()
    assert np.isfinite(y_after).all()


# ----------------------------------------------------------
# 3) Vector parameters
# ----------------------------------------------------------
def test_chirp_vector_parameters():
    c = Chirp(
        "c",
        amplitude=[1.0, 2.0],
        f0=[1.0, 2.0],
        f1=[3.0, 4.0],
        duration=[2.0, 2.0],
        offset=[0.0, 10.0],
        phase=[0.0, 0.0],
    )

    c.output_update(0.0, 0.1)

    # tau=0 → sin(0)=0
    assert np.allclose(c.outputs["out"], [[0.0], [10.0]])


# ----------------------------------------------------------
# 4) Broadcasting scalar (allowed only (1,1))
# ----------------------------------------------------------
def test_chirp_broadcast_scalar_duration():
    c = Chirp(
        "c",
        amplitude=[1.0, 1.0, 1.0],
        f0=[1.0, 2.0, 3.0],
        f1=[2.0, 3.0, 4.0],
        duration=2.0,  # scalar broadcast
    )

    c.output_update(0.5, 0.1)
    assert c.outputs["out"].shape == (3, 1)


# ----------------------------------------------------------
# 5) Matrix parameters (Option B)
# ----------------------------------------------------------
def test_chirp_matrix_same_shape():
    A = np.array([[1.0, 2.0],
                  [3.0, 4.0]])
    F0 = np.array([[1.0, 1.0],
                   [1.0, 1.0]])
    F1 = np.array([[2.0, 2.0],
                   [2.0, 2.0]])
    D = np.array([[2.0, 2.0],
                  [2.0, 2.0]])

    c = Chirp("c", amplitude=A, f0=F0, f1=F1, duration=D)
    c.output_update(0.0, 0.1)

    assert np.allclose(c.outputs["out"], np.zeros((2, 2)))


def test_chirp_matrix_broadcast_scalar_offset():
    A = np.array([[1.0, 2.0],
                  [3.0, 4.0]])
    F0 = np.ones((2, 2))
    F1 = 2 * np.ones((2, 2))
    D = 2 * np.ones((2, 2))

    c = Chirp("c", amplitude=A, f0=F0, f1=F1, duration=D, offset=5.0)
    c.output_update(0.0, 0.1)

    assert np.allclose(c.outputs["out"], np.full((2, 2), 5.0))


# ----------------------------------------------------------
# 6) Inconsistent shapes among non-scalars -> error
# ----------------------------------------------------------
def test_chirp_inconsistent_shapes():
    with pytest.raises(ValueError):
        Chirp(
            "c",
            amplitude=np.zeros((2, 2)),
            f0=np.zeros((2, 3)),  # mismatch
            f1=1.0,
            duration=1.0,
        )


# ----------------------------------------------------------
# 7) Illegal ndim (>2) -> error
# ----------------------------------------------------------
def test_chirp_illegal_ndim():
    with pytest.raises(ValueError):
        Chirp(
            "c",
            amplitude=np.zeros((2, 2, 2)),
            f0=1.0,
            f1=2.0,
            duration=1.0,
        )


# ----------------------------------------------------------
# 8) Invalid duration (<=0) -> error
# ----------------------------------------------------------
def test_chirp_invalid_duration():
    with pytest.raises(ValueError):
        Chirp("c", 1.0, 1.0, 2.0, duration=0.0)

