import numpy as np
import pytest

from pySimBlocks.blocks.sources.function_source import FunctionSource


def test_function_source_single_output():
    def f(t, dt):
        return {"y": 2.0 * t + dt}

    src = FunctionSource(name="f", function=f, output_keys=["y"])
    src.initialize(0.0)
    assert np.allclose(src.outputs["y"], [[0.0]])

    src.output_update(1.0, 0.1)
    assert np.allclose(src.outputs["y"], [[2.1]])


def test_function_source_multiple_outputs():
    def f(t, dt):
        return {
            "y1": np.array([t, t + dt]),
            "y2": np.array([[2.0 * t]]),
        }

    src = FunctionSource(name="f", function=f, output_keys=["y1", "y2"])
    src.initialize(0.0)
    src.output_update(0.2, 0.1)

    assert src.outputs["y1"].shape == (2, 1)
    assert np.allclose(src.outputs["y1"], [[0.2], [0.3]])
    assert np.allclose(src.outputs["y2"], [[0.4]])


def test_function_source_signature_mismatch_raises():
    def f(t, dt, u):
        return {"out": np.array([[u]])}

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


def test_function_source_return_not_dict_raises():
    def f(t, dt):
        return np.array([[1.0]])

    src = FunctionSource(name="f", function=f, output_keys=["out"])

    with pytest.raises(RuntimeError) as err:
        src.initialize(0.0)

    assert "must return a dict" in str(err.value).lower()


def test_function_source_output_keys_mismatch_raises():
    def f(t, dt):
        return {"z": np.array([[1.0]])}

    src = FunctionSource(name="f", function=f, output_keys=["out"])

    with pytest.raises(RuntimeError) as err:
        src.initialize(0.0)

    assert "output keys mismatch" in str(err.value).lower()


def test_function_source_output_shape_change_raises_per_key():
    def f(t, dt):
        if t < 0.1:
            return {"y1": np.array([[1.0]]), "y2": np.array([[2.0]])}
        return {"y1": np.array([[1.0, 2.0]]), "y2": np.array([[2.0]])}

    src = FunctionSource(name="f", function=f, output_keys=["y1", "y2"])
    src.initialize(0.0)

    with pytest.raises(ValueError) as err:
        src.output_update(0.1, 0.1)

    assert "shape changed" in str(err.value).lower()


def test_function_source_adapt_params_loads_function(tmp_path):
    py_file = tmp_path / "my_function.py"
    py_file.write_text(
        "def my_source(t, dt):\n"
        "    return {'y': [[t + dt]]}\n",
        encoding="utf-8",
    )

    adapted = FunctionSource.adapt_params(
        {
            "file_path": "my_function.py",
            "function_name": "my_source",
            "output_keys": ["y"],
        },
        params_dir=tmp_path,
    )
    src = FunctionSource(name="f", **adapted)

    src.initialize(0.0)
    src.output_update(0.2, 0.1)
    assert np.allclose(src.outputs["y"], [[0.3]])


def test_function_source_adapt_params_missing_key_raises():
    with pytest.raises(ValueError):
        FunctionSource.adapt_params({"file_path": "foo.py"}, params_dir=None)


def test_function_source_adapt_params_sets_default_output_keys(tmp_path):
    py_file = tmp_path / "my_function.py"
    py_file.write_text(
        "def my_source(t, dt):\n"
        "    return {'out': [[t + dt]]}\n",
        encoding="utf-8",
    )

    adapted = FunctionSource.adapt_params(
        {"file_path": "my_function.py", "function_name": "my_source"},
        params_dir=tmp_path,
    )

    assert adapted["output_keys"] == ["out"]
