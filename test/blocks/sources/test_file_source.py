from pathlib import Path

import numpy as np
import pytest

from pySimBlocks.blocks.sources.file_source import FileSource


def test_file_source_npz_single_array(tmp_path: Path):
    path = tmp_path / "data.npz"
    np.savez(path, y=np.array([[1.0, 2.0], [3.0, 4.0]]))

    blk = FileSource("src", file_path=str(path), key="y")
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
        FileSource("src", file_path=str(path))


def test_file_source_npz_invalid_key(tmp_path: Path):
    path = tmp_path / "data.npz"
    np.savez(path, a=np.array([1.0]))

    with pytest.raises(KeyError):
        FileSource("src", file_path=str(path), key="missing")


def test_file_source_csv(tmp_path: Path):
    path = tmp_path / "data.csv"
    path.write_text("a,b\n1.0,2.0\n3.0,4.0\n", encoding="utf-8")

    blk = FileSource("src", file_path=str(path), key="b")
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
        FileSource("src", file_path=str(path), key="k")


def test_file_source_npy_use_time_not_allowed(tmp_path: Path):
    path = tmp_path / "data.npy"
    np.save(path, np.array([1.0, 2.0]))

    with pytest.raises(ValueError):
        FileSource("src", file_path=str(path), use_time=True)


def test_file_source_csv_missing_key(tmp_path: Path):
    path = tmp_path / "data.csv"
    path.write_text("a,b\n1.0,2.0\n", encoding="utf-8")

    with pytest.raises(ValueError):
        FileSource("src", file_path=str(path))


def test_file_source_invalid_extension(tmp_path: Path):
    path = tmp_path / "data.txt"
    path.write_text("1.0\n", encoding="utf-8")
    with pytest.raises(ValueError):
        FileSource("src", file_path=str(path))


def test_file_source_missing_file():
    with pytest.raises(FileNotFoundError):
        FileSource("src", file_path="does-not-exist.npz")


def test_file_source_npz_use_time_zoh(tmp_path: Path):
    path = tmp_path / "data.npz"
    t = np.array([0.0, 0.2, 0.5], dtype=float)
    y = np.array([[10.0], [20.0], [50.0]], dtype=float)
    np.savez(path, time=t, y=y)

    blk = FileSource("src", file_path=str(path), key="y", use_time=True)

    blk.initialize(0.0)
    assert np.allclose(blk.outputs["out"], [[10.0]])

    blk.output_update(0.19, 0.1)
    assert np.allclose(blk.outputs["out"], [[10.0]])

    blk.output_update(0.20, 0.1)
    assert np.allclose(blk.outputs["out"], [[20.0]])

    blk.output_update(0.8, 0.1)
    assert np.allclose(blk.outputs["out"], [[50.0]])


def test_file_source_csv_use_time_zoh(tmp_path: Path):
    path = tmp_path / "data.csv"
    path.write_text(
        "time,y\n0.0,1.0\n0.5,2.0\n1.0,3.0\n",
        encoding="utf-8",
    )

    blk = FileSource("src", file_path=str(path), key="y", use_time=True)
    blk.initialize(0.1)
    assert np.allclose(blk.outputs["out"], [[1.0]])

    blk.output_update(0.75, 0.1)
    assert np.allclose(blk.outputs["out"], [[2.0]])


def test_file_source_npz_time_must_be_strictly_increasing(tmp_path: Path):
    path = tmp_path / "data.npz"
    np.savez(path, time=np.array([0.0, 0.2, 0.2]), y=np.array([1.0, 2.0, 3.0]))

    with pytest.raises(ValueError):
        FileSource("src", file_path=str(path), key="y", use_time=True)


def test_file_source_csv_use_time_requires_time_column(tmp_path: Path):
    path = tmp_path / "data.csv"
    path.write_text("y\n1.0\n2.0\n", encoding="utf-8")

    with pytest.raises(KeyError):
        FileSource("src", file_path=str(path), key="y", use_time=True)
