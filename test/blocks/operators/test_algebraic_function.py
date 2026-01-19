
import numpy as np
import pytest

from pySimBlocks.blocks.operators.algebraic_function import AlgebraicFunction


# ---------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------
def make_block(func, input_keys=("u",), output_keys=("y",)):
    return AlgebraicFunction(
        name="F",
        function=func,
        input_keys=list(input_keys),
        output_keys=list(output_keys),
    )


# ---------------------------------------------------------------------
# 1) Basic pass-through (scalar as (1,1))
# ---------------------------------------------------------------------
def test_algebraic_function_pass_through_scalar():
    def f(t, dt, u):
        return {"y": u}

    blk = make_block(f, input_keys=("u",), output_keys=("y",))
    blk.initialize(0.0)

    blk.inputs["u"] = np.array([[2.0]])
    blk.output_update(0.0, 0.1)

    assert np.allclose(blk.outputs["y"], [[2.0]])


# ---------------------------------------------------------------------
# 2) Matrix support
# ---------------------------------------------------------------------
def test_algebraic_function_matrix_support():
    def f(t, dt, A, B):
        return {"Y": A @ B}

    blk = make_block(f, input_keys=("A", "B"), output_keys=("Y",))
    blk.initialize(0.0)

    A = np.array([[1.0, 2.0],
                  [3.0, 4.0]])
    B = np.array([[5.0],
                  [6.0]])

    blk.inputs["A"] = A
    blk.inputs["B"] = B
    blk.output_update(0.0, 0.1)

    assert np.allclose(blk.outputs["Y"], A @ B)
    assert blk.outputs["Y"].shape == (2, 1)


# ---------------------------------------------------------------------
# 3) Multiple outputs
# ---------------------------------------------------------------------
def test_algebraic_function_multiple_outputs():
    def f(t, dt, u):
        return {"y1": u, "y2": 2.0 * u}

    blk = make_block(f, input_keys=("u",), output_keys=("y1", "y2"))
    blk.initialize(0.0)

    u = np.array([[3.0], [4.0]])
    blk.inputs["u"] = u
    blk.output_update(0.0, 0.1)

    assert np.allclose(blk.outputs["y1"], u)
    assert np.allclose(blk.outputs["y2"], 2.0 * u)


# ---------------------------------------------------------------------
# 4) Missing input -> RuntimeError
# ---------------------------------------------------------------------
def test_algebraic_function_missing_input_raises():
    def f(t, dt, u):
        return {"y": u}

    blk = make_block(f, input_keys=("u",), output_keys=("y",))
    blk.initialize(0.0)

    blk.inputs["u"] = None
    with pytest.raises(RuntimeError) as err:
        blk.output_update(0.0, 0.1)

    assert "not set" in str(err.value).lower()


# ---------------------------------------------------------------------
# 5) Signature mismatch (input_keys != function args) -> ValueError in initialize
# ---------------------------------------------------------------------
def test_algebraic_function_signature_mismatch_raises():
    # function declares 'u', but block expects 'x'
    def f(t, dt, u):
        return {"y": u}

    blk = make_block(f, input_keys=("x",), output_keys=("y",))
    with pytest.raises(ValueError) as err:
        blk.initialize(0.0)

    assert "arguments mismatch" in str(err.value).lower()


# ---------------------------------------------------------------------
# 6) Function must return a dict
# ---------------------------------------------------------------------
def test_algebraic_function_return_not_dict_raises():
    def f(t, dt, u):
        return u  # invalid

    blk = make_block(f, input_keys=("u",), output_keys=("y",))
    blk.initialize(0.0)

    blk.inputs["u"] = np.array([[1.0]])
    with pytest.raises(RuntimeError) as err:
        blk.output_update(0.0, 0.1)

    assert "must return a dict" in str(err.value).lower()


# ---------------------------------------------------------------------
# 7) Output keys mismatch
# ---------------------------------------------------------------------
def test_algebraic_function_output_keys_mismatch_raises():
    def f(t, dt, u):
        return {"z": u}  # wrong key

    blk = make_block(f, input_keys=("u",), output_keys=("y",))
    blk.initialize(0.0)

    blk.inputs["u"] = np.array([[1.0]])
    with pytest.raises(RuntimeError) as err:
        blk.output_update(0.0, 0.1)

    assert "output keys mismatch" in str(err.value).lower()


# ---------------------------------------------------------------------
# 8) Output must be 2D
# ---------------------------------------------------------------------
def test_algebraic_function_output_must_be_2d():
    def f(t, dt, u):
        return {"y": np.array([1.0, 2.0])}  # 1D invalid

    blk = make_block(f, input_keys=("u",), output_keys=("y",))
    blk.initialize(0.0)

    blk.inputs["u"] = np.array([[1.0]])
    with pytest.raises(ValueError) as err:
        blk.output_update(0.0, 0.1)

    assert "must be a 2d" in str(err.value).lower()


# ---------------------------------------------------------------------
# 9) Input shape freeze: once seen, shape cannot change
# ---------------------------------------------------------------------
def test_algebraic_function_input_shape_change_raises():
    def f(t, dt, u):
        return {"y": u}

    blk = make_block(f, input_keys=("u",), output_keys=("y",))
    blk.initialize(0.0)

    blk.inputs["u"] = np.array([[1.0]])  # (1,1)
    blk.output_update(0.0, 0.1)

    blk.inputs["u"] = np.array([[1.0, 2.0],
                                [3.0, 4.0]])  # (2,2) -> shape change
    with pytest.raises(ValueError) as err:
        blk.output_update(0.1, 0.1)

    assert "shape changed" in str(err.value).lower()


# ---------------------------------------------------------------------
# 10) Output shape freeze: once produced, shape cannot change
# ---------------------------------------------------------------------
def test_algebraic_function_output_shape_change_raises():
    # function changes output shape depending on time -> should raise at second call
    def f(t, dt, u):
        if t < 0.1:
            return {"y": np.array([[1.0]])}  # (1,1)
        return {"y": np.array([[1.0, 2.0]])}  # (1,2) -> shape change

    blk = make_block(f, input_keys=("u",), output_keys=("y",))
    blk.initialize(0.0)

    blk.inputs["u"] = np.array([[0.0]])  # dummy input (shape fixed too)
    blk.output_update(0.0, 0.1)

    with pytest.raises(ValueError) as err:
        blk.output_update(0.1, 0.1)

    assert "shape changed" in str(err.value).lower()
