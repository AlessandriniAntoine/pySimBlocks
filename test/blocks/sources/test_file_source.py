from pathlib import Path

import numpy as np
import pytest

from pySimBlocks.blocks.sources.file_source import FileSource


def test_file_source_npz_single_array(tmp_path: Path):
    path = tmp_path / "data.npz"
    np.savez(path, y=np.array([[1.0, 2.0], [3.0, 4.0]]))

    blk = FileSource("src", file_path=str(path), file_type="npz", key="y")
    blk.initialize(0.0)
    assert np.allclose(blk.outputs["out"], [[1.0], [2.0]])

    blk.output_update(0.0, 0.1)
    assert np.allclose(blk.outputs["out"], [[1.0], [2.0]])

    blk.output_update(0.1, 0.1)
    assert np.allclose(blk.outputs["out"], [[3.0], [4.0]])


def test_file_source_npz_requires_key(tmp_path: Path):
    path = tmp_path / "data.npz"
    np.savez(path, a=np.array([1.0]), b=np.array([2.0]))

    with pytest.raises(ValueError):
        FileSource("src", file_path=str(path), file_type="npz")


def test_file_source_npz_invalid_key(tmp_path: Path):
    path = tmp_path / "data.npz"
    np.savez(path, a=np.array([1.0]))

    with pytest.raises(KeyError):
        FileSource("src", file_path=str(path), file_type="npz", key="missing")


def test_file_source_csv(tmp_path: Path):
    path = tmp_path / "data.csv"
    path.write_text("a,b\n1.0,2.0\n3.0,4.0\n", encoding="utf-8")

    blk = FileSource("src", file_path=str(path), file_type="csv", key="b")
    blk.initialize(0.0)
    assert np.allclose(blk.outputs["out"], [[2.0]])

    blk.output_update(0.0, 0.1)
    assert np.allclose(blk.outputs["out"], [[2.0]])

    blk.output_update(0.1, 0.1)
    assert np.allclose(blk.outputs["out"], [[4.0]])


def test_file_source_repeat_false_outputs_zeros_after_end(tmp_path: Path):
    path = tmp_path / "data.npz"
    np.savez(path, y=np.array([[5.0], [7.0]]))

    blk = FileSource(
        "src",
        file_path=str(path),
        file_type="npz",
        key="y",
        repeat=False,
    )
    blk.initialize(0.0)
    assert np.allclose(blk.outputs["out"], [[5.0]])

    blk.output_update(0.0, 0.1)
    assert np.allclose(blk.outputs["out"], [[5.0]])

    blk.output_update(0.1, 0.1)
    assert np.allclose(blk.outputs["out"], [[7.0]])

    blk.output_update(0.2, 0.1)
    assert np.allclose(blk.outputs["out"], [[0.0]])


def test_file_source_repeat_true_restarts_after_end(tmp_path: Path):
    path = tmp_path / "data.npy"
    np.save(path, np.array([[10.0], [20.0]]))

    blk = FileSource(
        "src",
        file_path=str(path),
        file_type="npy",
        repeat=True,
    )
    blk.initialize(0.0)
    assert np.allclose(blk.outputs["out"], [[10.0]])

    blk.output_update(0.0, 0.1)
    assert np.allclose(blk.outputs["out"], [[10.0]])

    blk.output_update(0.1, 0.1)
    assert np.allclose(blk.outputs["out"], [[20.0]])

    blk.output_update(0.2, 0.1)
    assert np.allclose(blk.outputs["out"], [[10.0]])


def test_file_source_npy_key_not_allowed(tmp_path: Path):
    path = tmp_path / "data.npy"
    np.save(path, np.array([1.0, 2.0]))

    with pytest.raises(ValueError):
        FileSource("src", file_path=str(path), file_type="npy", key="k")


def test_file_source_csv_missing_key(tmp_path: Path):
    path = tmp_path / "data.csv"
    path.write_text("a,b\n1.0,2.0\n", encoding="utf-8")

    with pytest.raises(ValueError):
        FileSource("src", file_path=str(path), file_type="csv")


def test_file_source_invalid_file_type(tmp_path: Path):
    path = tmp_path / "data.npz"
    np.savez(path, y=np.array([1.0]))

    with pytest.raises(ValueError):
        FileSource("src", file_path=str(path), file_type="txt")


def test_file_source_missing_file():
    with pytest.raises(FileNotFoundError):
        FileSource("src", file_path="does-not-exist.npz", file_type="npz")
