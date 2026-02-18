import numpy as np
import pytest

from pySimBlocks.blocks.sources.function_source import FunctionSource


def test_function_source_scalar_output():
    def f(t, dt):
        return 2.0 * t + dt

    src = FunctionSource(name="f", function=f)
    src.initialize(0.0)
    assert np.allclose(src.outputs["out"], [[0.0]])

    src.output_update(1.0, 0.1)
    assert np.allclose(src.outputs["out"], [[2.1]])


def test_function_source_vector_output_normalized_to_column():
    def f(t, dt):
        return np.array([t, t + dt])

    src = FunctionSource(name="f", function=f)
    src.initialize(0.0)
    src.output_update(0.2, 0.1)

    assert src.outputs["out"].shape == (2, 1)
    assert np.allclose(src.outputs["out"], [[0.2], [0.3]])


def test_function_source_signature_mismatch_raises():
    def f(t, dt, u):
        return np.array([[u]])

    src = FunctionSource(name="f", function=f)
    with pytest.raises(ValueError):
        src.initialize(0.0)


def test_function_source_function_error_is_wrapped():
    def f(t, dt):
        raise RuntimeError("boom")

    src = FunctionSource(name="f", function=f)
    with pytest.raises(RuntimeError) as err:
        src.initialize(0.0)

    assert "function call error" in str(err.value).lower()


def test_function_source_output_shape_change_raises():
    def f(t, dt):
        if t < 0.1:
            return np.array([[1.0]])
        return np.array([[1.0, 2.0]])

    src = FunctionSource(name="f", function=f)
    src.initialize(0.0)

    with pytest.raises(ValueError) as err:
        src.output_update(0.1, 0.1)

    assert "shape changed" in str(err.value).lower()


def test_function_source_adapt_params_loads_function(tmp_path):
    py_file = tmp_path / "my_function.py"
    py_file.write_text(
        "def my_source(t, dt):\n"
        "    return [[t + dt]]\n",
        encoding="utf-8",
    )

    adapted = FunctionSource.adapt_params(
        {"file_path": "my_function.py", "function_name": "my_source"},
        params_dir=tmp_path,
    )
    src = FunctionSource(name="f", **adapted)

    src.initialize(0.0)
    src.output_update(0.2, 0.1)
    assert np.allclose(src.outputs["out"], [[0.3]])


def test_function_source_adapt_params_missing_key_raises():
    with pytest.raises(ValueError):
        FunctionSource.adapt_params({"file_path": "foo.py"}, params_dir=None)
