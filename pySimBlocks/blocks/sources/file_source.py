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
        key: str | None = None,
        repeat: bool = False,
        use_time: bool = False,
        sample_time: float | None = None,
    ):
        super().__init__(name, sample_time)

        self.file_path = str(file_path)
        self.file_type = self._infer_file_type(self.file_path)
        self.key = key
        self.repeat = self._to_bool(repeat, "repeat")
        self.use_time = self._to_bool(use_time, "use_time")

        if self.use_time and self.file_type == "npy":
            raise ValueError(
                f"[{self.name}] use_time is supported only for NPZ and CSV inputs."
            )
        if self.use_time and self.repeat:
            raise ValueError(
                f"[{self.name}] repeat cannot be used when use_time=True."
            )

        self._time: np.ndarray | None = None
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
        # Backward compatibility with older models that still contain file_type
        adapted.pop("file_type", None)
        return adapted

    # --------------------------------------------------------------------------
    # Public methods
    # --------------------------------------------------------------------------
    def initialize(self, t0: float) -> None:
        if self.use_time:
            self.outputs["out"] = self._current_output_at_time(t0)
        else:
            self._index = 0
            self.outputs["out"] = self._current_output()

    # ------------------------------------------------------------------
    def output_update(self, t: float, dt: float) -> None:
        if self.use_time:
            self.outputs["out"] = self._current_output_at_time(t)
        else:
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
            arr, time = self._load_npz(path)
        elif self.file_type == "npy":
            arr, time = self._load_npy(path)
        else:
            arr, time = self._load_csv(path)

        if arr.ndim == 1:
            arr = arr.reshape(-1, 1)
        elif arr.ndim != 2:
            raise ValueError(
                f"[{self.name}] Loaded data must be 1D or 2D. Got shape {arr.shape}."
            )

        if arr.shape[0] == 0:
            raise ValueError(f"[{self.name}] Loaded file contains no samples.")

        self._time = time

        return arr.astype(float, copy=False)

    # ------------------------------------------------------------------
    def _load_npz(self, path: Path) -> tuple[np.ndarray, np.ndarray | None]:
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

            arr = np.asarray(data[selected_key], dtype=float)
            time = None
            if self.use_time:
                if "time" not in data:
                    raise KeyError(
                        f"[{self.name}] use_time=True requires NPZ key 'time'."
                    )
                time = np.asarray(data["time"], dtype=float).reshape(-1)
                self._validate_time(time, arr.shape[0])
            return arr, time

    # ------------------------------------------------------------------
    def _load_npy(self, path: Path) -> tuple[np.ndarray, np.ndarray | None]:
        if self.key not in (None, ""):
            raise ValueError(
                f"[{self.name}] key is not used for NPY input."
            )
        return np.asarray(np.load(path), dtype=float), None

    # ------------------------------------------------------------------
    def _load_csv(self, path: Path) -> tuple[np.ndarray, np.ndarray | None]:
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
        time = None
        if self.use_time:
            if "time" not in arr.dtype.names:
                raise KeyError(
                    f"[{self.name}] use_time=True requires CSV column 'time'."
                )
            time = np.asarray(arr["time"], dtype=float).reshape(-1)
            self._validate_time(time, col.shape[0])
        return col, time

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
    def _infer_file_type(self, file_path: str) -> str:
        ext = Path(file_path).suffix.lower().lstrip(".")
        if ext not in self.VALID_FILE_TYPES:
            raise ValueError(
                f"[{self.name}] Unsupported file extension '.{ext}'. "
                f"Supported extensions: {sorted(self.VALID_FILE_TYPES)}"
            )
        return ext

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

    # ------------------------------------------------------------------
    def _current_output_at_time(self, t: float) -> np.ndarray:
        if self._time is None:
            raise RuntimeError(
                f"[{self.name}] Internal error: use_time=True but time data is missing."
            )

        idx = int(np.searchsorted(self._time, t, side="right") - 1)
        if idx < 0:
            idx = 0

        row = self._samples[idx]
        return np.asarray(row, dtype=float).reshape(-1, 1)

    # ------------------------------------------------------------------
    def _validate_time(self, time: np.ndarray, n_samples: int) -> None:
        if time.ndim != 1:
            raise ValueError(f"[{self.name}] time must be a 1D array.")
        if time.shape[0] != n_samples:
            raise ValueError(
                f"[{self.name}] time length ({time.shape[0]}) must match number of samples ({n_samples})."
            )
        if np.isnan(time).any():
            raise ValueError(f"[{self.name}] time contains NaN values.")
        if not np.all(np.diff(time) > 0.0):
            raise ValueError(
                f"[{self.name}] time must be strictly increasing."
            )
