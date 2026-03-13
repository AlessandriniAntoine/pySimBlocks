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

import numpy as np

from pySimBlocks.core.block import Block


class BlockSource(Block):
    """Base class for all source blocks (Constant, Step, Ramp, Sinusoidal, ...).
 
    Provides normalization utilities for source parameters to produce 2D
    signals, strict scalar-only broadcasting to a common 2D shape, and no
    state update by default.
 
    Attributes:
        direct_feedthrough: Always False for sources.
        is_source: Always True for sources.
    """

    direct_feedthrough = False
    is_source = True

    def __init__(self, name: str, sample_time: float | None = None):
        """Initialize a source block.
 
        Args:
            name: Unique identifier for this block instance.
            sample_time: Sampling period in seconds, or None to use the
                global simulation dt.
        """
        super().__init__(name, sample_time)


    # --------------------------------------------------------------------------
    # Public methods
    # --------------------------------------------------------------------------

    def state_update(self, t: float, dt: float) -> None:
        """No-op: all source blocks are stateless."""


    # --------------------------------------------------------------------------
    # Private methods
    # --------------------------------------------------------------------------

    def _resolve_common_shape(self, params: dict[str, np.ndarray]) -> tuple[int, int]:
        """Determine the common target shape among parameters.
 
        Scalars (1,1) are broadcastable to any shape. Any non-scalar fixes
        the target shape. Multiple non-scalars must all share the same shape.
        If all parameters are scalar, returns (1,1).
 
        Args:
            params: Mapping of parameter names to their 2D arrays.
 
        Returns:
            The common (m, n) target shape.
 
        Raises:
            ValueError: If multiple non-scalar parameters have different shapes.
        """
        non_scalar_shapes = {a.shape for a in params.values() if not self._is_scalar_2d(a)}

        if len(non_scalar_shapes) == 0:
            return (1, 1)

        if len(non_scalar_shapes) == 1:
            return next(iter(non_scalar_shapes))

        details = ", ".join(f"{k}={v.shape}" for k, v in params.items())
        raise ValueError(
            f"[{self.name}] Inconsistent parameter shapes. "
            f"All non-scalar parameters must have the same (m,n) shape. Got: {details}"
        )

    def _broadcast_scalar_only(self,
                                param_name: str,
                                arr: np.ndarray,
                                target_shape: tuple[int, int]) -> np.ndarray:
        """Broadcast a scalar (1,1) array to target_shape; non-scalars must match exactly.
 
        Args:
            param_name: Name of the parameter, used in error messages.
            arr: 2D array to broadcast.
            target_shape: Target (m, n) shape.
 
        Returns:
            Array of shape target_shape with dtype float.
 
        Raises:
            ValueError: If arr is non-scalar and does not match target_shape.
        """
        if self._is_scalar_2d(arr):
            if target_shape == (1, 1):
                return arr.astype(float, copy=False)
            return np.full(target_shape, float(arr[0, 0]), dtype=float)

        if arr.shape != target_shape:
            raise ValueError(
                f"[{self.name}] '{param_name}' shape {arr.shape} is incompatible with "
                f"target shape {target_shape}. Only scalar-to-shape broadcasting is allowed."
            )

        return arr.astype(float, copy=False)
