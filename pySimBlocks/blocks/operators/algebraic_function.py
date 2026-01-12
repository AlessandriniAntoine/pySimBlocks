import inspect
from typing import Callable, List, Dict

import numpy as np

from pySimBlocks.core.block import Block


class AlgebraicFunction(Block):
    """
    User-defined algebraic function block.

    Summary:
        Stateless block defined by a user-provided Python function:
            y = g(t, dt, u1, u2, ...)

    Parameters:
        function : callable
            User-defined function.
        input_keys : list[str]
            Names of input ports.
        output_keys : list[str]
            Names of output ports.
        sample_time : float, optional
            Block execution period.

    I/O:
        Inputs:
            Defined dynamically by input_keys.
        Outputs:
            Defined dynamically by output_keys.

    Notes:
        - This block is stateless.
        - Ports are fully declarative (V1).
        - The function must return a dict with exactly output_keys.
        - All inputs and outputs must be numpy arrays of shape (n,1).
    """

    direct_feedthrough = True
    is_source = False

    # ------------------------------------------------------------------
    def __init__(
        self,
        name: str,
        function: callable,
        input_keys: List[str],
        output_keys: List[str],
        sample_time: float | None = None,
    ):
        super().__init__(name=name, sample_time=sample_time)

        # ---- parameters
        self._func = function
        self.input_keys = list(input_keys)
        self.output_keys = list(output_keys)

    # ------------------------------------------------------------------
    def initialize(self, t0: float):
        """
        Load the user function and validate its signature.
        """
        self._validate_signature()

        # ---- declare ports
        for k in self.input_keys:
            self.inputs[k] = None

        for k in self.output_keys:
            # Initialized lazily at first output_update
            self.outputs[k] = None

    # ------------------------------------------------------------------
    def _validate_signature(self):
        """
        Validate function signature against input_keys.
        """
        assert self._func is not None

        sig = inspect.signature(self._func)
        params = list(sig.parameters.values())

        # ---- minimum signature: (t, dt, ...)
        if len(params) < 2:
            raise ValueError(
                f"{self.name}: function must have at least arguments (t, dt)"
            )

        if params[0].name != "t" or params[1].name != "dt":
            raise ValueError(
                f"{self.name}: first arguments must be (t, dt)"
            )

        # ---- no *args / **kwargs / defaults
        for p in params:
            if p.kind not in (
                inspect.Parameter.POSITIONAL_OR_KEYWORD,
            ):
                raise ValueError(
                    f"{self.name}: *args and **kwargs are not allowed"
                )
            if p.default is not inspect.Parameter.empty:
                raise ValueError(
                    f"{self.name}: default arguments are not allowed"
                )

    # ------------------------------------------------------------------
    def output_update(self, t: float, dt: float):
        """
        Compute outputs from current inputs.
        """
        assert self._func is not None

        # ---- collect inputs
        kwargs: Dict[str, np.ndarray] = {}

        for k in self.input_keys:
            u = self.inputs[k]
            if not isinstance(u, np.ndarray):
                raise TypeError(
                    f"{self.name}: input '{k}' is not a numpy array"
                )
            if u.ndim != 2 or u.shape[1] != 1:
                raise ValueError(
                    f"{self.name}: input '{k}' must have shape (n,1)"
                )

            kwargs[k] = u

        # ---- call function
        out = self._func(t, dt, **kwargs)

        if not isinstance(out, dict):
            raise RuntimeError(
                f"{self.name}: function must return a dict"
            )

        if set(out.keys()) != set(self.output_keys):
            raise RuntimeError(
                f"{self.name}: output keys mismatch "
                f"(expected {self.output_keys}, got {list(out.keys())})"
            )

        # ---- assign outputs
        for k in self.output_keys:
            y = out[k]
            if not isinstance(y, np.ndarray):
                raise TypeError(
                    f"{self.name}: output '{k}' is not a numpy array"
                )
            if y.ndim != 2 or y.shape[1] != 1:
                raise ValueError(
                    f"{self.name}: output '{k}' must have shape (n,1)"
                )

            self.outputs[k] = y

    def state_update(self, t: float, dt: float):
        """Nothing"""
