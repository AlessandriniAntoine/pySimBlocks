import numpy as np
import pytest

from pySimBlocks.blocks.sources.white_noise import WhiteNoise


# ----------------------------------------------------------
# 1) Scalar noise, deterministic with seed
# ----------------------------------------------------------
def test_white_noise_scalar_reproducible():
    s1 = WhiteNoise("n", mean=0.0, std=1.0, seed=42)
    s2 = WhiteNoise("n", mean=0.0, std=1.0, seed=42)

    s1.initialize(0.0)
    s2.initialize(0.0)

    assert np.allclose(s1.outputs["out"], s2.outputs["out"])


def test_white_noise_scalar_update_changes():
    s = WhiteNoise("n", mean=2.0, std=0.5, seed=0)
    s.initialize(0.0)
    first = s.outputs["out"].copy()
    s.output_update(0.1, 0.1)
    second = s.outputs["out"]

    assert not np.allclose(first, second)


# ----------------------------------------------------------
# 2) Vector parameters + broadcasting (still valid)
# ----------------------------------------------------------
def test_white_noise_vector_params_shape():
    s = WhiteNoise("n", mean=[1.0, 2.0], std=[0.1, 0.2], seed=10)
    s.initialize(0.0)
    assert s.outputs["out"].shape == (2, 1)


def test_white_noise_broadcast_scalar_mean():
    s = WhiteNoise("n", mean=0.0, std=[1.0, 2.0, 3.0], seed=1)
    s.initialize(0.0)
    assert s.mean.shape == (3, 1)
    assert s.std.shape == (3, 1)
    assert s.outputs["out"].shape == (3, 1)


# ----------------------------------------------------------
# 3) Matrix parameters (Option B)
# ----------------------------------------------------------
def test_white_noise_matrix_params_shape():
    mean = np.array([[0.0, 1.0],
                     [2.0, 3.0]])
    std = np.array([[1.0, 2.0],
                    [3.0, 4.0]])
    s = WhiteNoise("n", mean=mean, std=std, seed=123)
    s.initialize(0.0)
    assert s.outputs["out"].shape == (2, 2)


def test_white_noise_matrix_broadcast_scalar_std():
    mean = np.array([[0.0, 1.0],
                     [2.0, 3.0]])
    s = WhiteNoise("n", mean=mean, std=1.0, seed=123)  # scalar broadcast
    s.initialize(0.0)
    assert s.mean.shape == (2, 2)
    assert s.std.shape == (2, 2)
    assert s.outputs["out"].shape == (2, 2)


def test_white_noise_matrix_reproducible_same_seed():
    mean = np.array([[0.0, 1.0],
                     [2.0, 3.0]])
    std = np.array([[1.0, 1.0],
                    [1.0, 1.0]])

    s1 = WhiteNoise("n", mean=mean, std=std, seed=999)
    s2 = WhiteNoise("n", mean=mean, std=std, seed=999)

    s1.initialize(0.0)
    s2.initialize(0.0)
    assert np.allclose(s1.outputs["out"], s2.outputs["out"])


# ----------------------------------------------------------
# 4) Error cases
# ----------------------------------------------------------
def test_white_noise_inconsistent_shapes():
    with pytest.raises(ValueError):
        WhiteNoise(
            "n",
            mean=np.zeros((2, 2)),
            std=np.zeros((2, 3)),  # mismatch among non-scalars
        )


def test_white_noise_negative_std_scalar():
    with pytest.raises(ValueError):
        WhiteNoise("n", mean=0.0, std=-1.0)


def test_white_noise_negative_std_matrix_elementwise():
    with pytest.raises(ValueError):
        WhiteNoise("n", mean=np.zeros((2, 2)), std=np.array([[1.0, -1.0], [1.0, 1.0]]))


def test_white_noise_illegal_ndim():
    with pytest.raises(ValueError):
        WhiteNoise("n", mean=np.zeros((2, 2, 2)), std=1.0)
