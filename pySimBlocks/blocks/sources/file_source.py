# ******************************************************************************
#                                  pySimBlocks
#                     Copyright (c) 2026 Université de Lille & INRIA
# ******************************************************************************
#  This program is free software: you can redistribute it and/or modify it
#  under the terms of the GNU Lesser General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or (at your
#  option) any later version.
#
#  This program is distributed in the hope that it will be useful, but WITHOUT
#  ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
#  FITNESS FOR A PARTICULAR PURPOSE.  See the GNU Lesser General Public License
#  for more details.
#
#  You should have received a copy of the GNU Lesser General Public License
#  along with this program.  If not, see <https://www.gnu.org/licenses/>.
# ******************************************************************************
#  Authors: see Authors.txt
# ******************************************************************************

from pathlib import Path
from typing import Any, Dict

import numpy as np

from pySimBlocks.core.block_source import BlockSource


class FileSource(BlockSource):
    """
    Source block that plays samples loaded from a file.

    Supported file types:
        - npz: load an array from a key in a .npz archive (key mandatory)
        - npy: load an array from a .npy file (no key)
        - csv: load one numeric column by name (key=column name)

    Output policy:
        - loaded data must be 1D or 2D
        - each simulation step emits one row as a column vector
        - when the end is reached:
            * repeat=True  -> restart from first sample
            * repeat=False -> output zeros
    """

    VALID_FILE_TYPES = {"npz", "npy", "csv"}

    def __init__(
        self,
        name: str,
        file_path: str,
        file_type: str = "npz",
        key: str | None = None,
        repeat: bool = False,
        sample_time: float | None = None,
    ):
        super().__init__(name, sample_time)

        if file_type not in self.VALID_FILE_TYPES:
            raise ValueError(
                f"[{self.name}] file_type must be one of {self.VALID_FILE_TYPES}."
            )

        self.file_path = str(file_path)
        self.file_type = file_type
        self.key = key
        self.repeat = self._to_bool(repeat, "repeat")

        self._samples = self._load_samples()
        self._index = 0
        self._output_shape = (self._samples.shape[1], 1)

        self.outputs["out"] = np.zeros(self._output_shape, dtype=float)

    # --------------------------------------------------------------------------
    # Class Methods
    # --------------------------------------------------------------------------
    @classmethod
    def adapt_params(
        cls,
        params: Dict[str, Any],
        params_dir: Path | None = None,
    ) -> Dict[str, Any]:
        """
        Resolve relative file_path against parameters directory when provided.
        """
        adapted = dict(params)
        file_path = adapted.get("file_path")
        if file_path is None:
            return adapted

        path = Path(file_path)
        if not path.is_absolute() and params_dir is not None:
            path = (params_dir / path).resolve()

        adapted["file_path"] = str(path)
        return adapted

    # --------------------------------------------------------------------------
    # Public methods
    # --------------------------------------------------------------------------
    def initialize(self, t0: float) -> None:
        self._index = 0
        self.outputs["out"] = self._current_output()

    # ------------------------------------------------------------------
    def output_update(self, t: float, dt: float) -> None:
        self.outputs["out"] = self._current_output()
        self._index += 1

    # ------------------------------------------------------------------
    def state_update(self, t: float, dt: float) -> None:
        pass

    # --------------------------------------------------------------------------
    # Private methods
    # --------------------------------------------------------------------------
    def _load_samples(self) -> np.ndarray:
        path = Path(self.file_path)
        if not path.exists():
            raise FileNotFoundError(f"[{self.name}] File not found: {path}")

        if self.file_type == "npz":
            arr = self._load_npz(path)
        elif self.file_type == "npy":
            arr = self._load_npy(path)
        else:
            arr = self._load_csv(path)

        if arr.ndim == 1:
            arr = arr.reshape(-1, 1)
        elif arr.ndim != 2:
            raise ValueError(
                f"[{self.name}] Loaded data must be 1D or 2D. Got shape {arr.shape}."
            )

        if arr.shape[0] == 0:
            raise ValueError(f"[{self.name}] Loaded file contains no samples.")

        return arr.astype(float, copy=False)

    # ------------------------------------------------------------------
    def _load_npz(self, path: Path) -> np.ndarray:
        with np.load(path) as data:
            keys = list(data.files)
            if len(keys) == 0:
                raise ValueError(f"[{self.name}] NPZ archive contains no arrays.")

            selected_key = self.key
            if not selected_key:
                raise ValueError(
                    f"[{self.name}] key is mandatory for NPZ input."
                )

            if selected_key not in data:
                raise KeyError(
                    f"[{self.name}] key '{selected_key}' not found in NPZ. "
                    f"Available keys: {keys}"
                )

            return np.asarray(data[selected_key], dtype=float)

    # ------------------------------------------------------------------
    def _load_npy(self, path: Path) -> np.ndarray:
        if self.key not in (None, ""):
            raise ValueError(
                f"[{self.name}] key is not used for NPY input."
            )
        return np.asarray(np.load(path), dtype=float)

    # ------------------------------------------------------------------
    def _load_csv(self, path: Path) -> np.ndarray:
        if not self.key:
            raise ValueError(
                f"[{self.name}] key is mandatory for CSV input and must be a column name."
            )

        arr = np.genfromtxt(path, delimiter=",", names=True, dtype=float)

        if arr.size == 0:
            raise ValueError(f"[{self.name}] CSV file is empty.")
        if arr.dtype.names is None:
            raise ValueError(
                f"[{self.name}] CSV must contain a header row with column names."
            )
        if self.key not in arr.dtype.names:
            raise KeyError(
                f"[{self.name}] column '{self.key}' not found in CSV. "
                f"Available columns: {list(arr.dtype.names)}"
            )

        col = np.asarray(arr[self.key], dtype=float).reshape(-1, 1)
        if np.isnan(col).any():
            raise ValueError(
                f"[{self.name}] CSV column '{self.key}' contains non-numeric or missing values."
            )
        return col

    # ------------------------------------------------------------------
    def _to_bool(self, value: bool | str, name: str) -> bool:
        if isinstance(value, bool):
            return value
        if isinstance(value, str):
            lowered = value.strip().lower()
            if lowered in {"true", "1", "yes"}:
                return True
            if lowered in {"false", "0", "no"}:
                return False
        raise ValueError(f"[{self.name}] '{name}' must be a bool.")

    # ------------------------------------------------------------------
    def _current_output(self) -> np.ndarray:
        n = self._samples.shape[0]
        if self._index < n:
            idx = self._index
        elif self.repeat:
            idx = self._index % n
        else:
            return np.zeros(self._output_shape, dtype=float)

        row = self._samples[idx]
        return np.asarray(row, dtype=float).reshape(-1, 1)
