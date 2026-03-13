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

from __future__ import annotations

from multiprocessing import Pipe, Process
from pathlib import Path
from typing import Any, Dict, List

import numpy as np

from pySimBlocks.core.block import Block


def sofa_worker(conn, scene_file, input_keys, output_keys):
    """Worker function executed in a subprocess to run the SOFA simulation."""
    import os
    import sys
    import Sofa
    import importlib.util

    scene_dir = os.path.dirname(os.path.abspath(scene_file))
    if scene_dir not in sys.path:
        sys.path.insert(0, scene_dir)

    spec = importlib.util.spec_from_file_location("scene", scene_file)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)

    root = Sofa.Core.Node("root")
    root, controller = mod.createScene(root)

    sofa_outputs_keys = set(controller.outputs.keys())
    if not set(output_keys).issubset(sofa_outputs_keys):
        conn.send({
            "cmd": "error",
            "message": (
                f"\n[pySimBlocks] ERROR: Output key not found in controller outputs.\n"
                f"Available keys: {sofa_outputs_keys}\n"
                f"Provided keys: {set(output_keys)}\n"
                f"Check the 'output_keys' parameter in your project.yaml."
            )
        })
        conn.close()
        return

    sofa_inputs_keys = set(controller.inputs.keys())
    if not set(input_keys).issubset(sofa_inputs_keys):
        conn.send({
            "cmd": "error",
            "message": (
                f"[pySimBlocks] ERROR: Input key not found in controller inputs.\n"
                f"Available keys: {sofa_inputs_keys}\n"
                f"Provided keys: {set(input_keys)}\n"
                f"Check the 'input_keys' parameter in your project.yaml."
            )
        })
        conn.close()
        return

    controller.SOFA_MASTER = False
    Sofa.Simulation.initRoot(root)

    dt = float(root.dt.value)

    while not controller.IS_READY:
        controller.prepare_scene()
        if controller.IS_READY:
            break
        Sofa.Simulation.animate(root, dt)

    try:
        controller.get_outputs()
        initial = {k: np.asarray(controller.outputs[k]).reshape(-1, 1) for k in output_keys}
        conn.send(initial)
    except Exception as e:
        conn.send({
            "cmd": "error",
            "message": f"[pySimBlocks] ERROR: Failed to get initial outputs.\n{e}"
        })
        conn.close()
        return

    while True:
        msg = conn.recv()

        if msg["cmd"] == "step":
            try:
                for key, val in msg["inputs"].items():
                    controller.inputs[key] = val

                controller.set_inputs()
                Sofa.Simulation.animate(root, dt)
                controller.get_outputs()

                outputs = {k: np.asarray(controller.outputs[k]).reshape(-1, 1)
                           for k in output_keys}
                conn.send(outputs)
            except Exception as e:
                conn.send({
                    "cmd": "error",
                    "message": f"[pySimBlocks] ERROR during step execution.\n{e}"
                })
                break

        elif msg["cmd"] == "stop":
            break

    conn.close()


class SofaPlant(Block):
    """SOFA-based dynamic plant block.

    Executes a SOFA simulation as a dynamic system driven by pySimBlocks.
    SOFA runs in a separate subprocess. At each control step, inputs are sent
    to the worker process, the SOFA scene advances by one step, and updated
    outputs are returned.

    Attributes:
        scene_file: Resolved path to the SOFA scene file.
        input_keys: Names of input ports sent to SOFA at each step.
        output_keys: Names of output ports received from SOFA at each step.
        slider_params: Optional ImGui slider configuration, mapping
            ``"BlockName.attr"`` to ``[min, max]`` bounds.
    """

    direct_feedthrough = False
    need_first = True

    def __init__(
        self,
        name: str,
        scene_file: str,
        input_keys: list[str],
        output_keys: list[str],
        slider_params: Dict[str, List[float]] | None = None,
        sample_time: float | None = None,
    ):
        """Initialize a SofaPlant block.

        Args:
            name: Unique identifier for this block instance.
            scene_file: Path to the SOFA scene file. Relative paths are
                resolved against the project file directory via
                ``adapt_params``.
            input_keys: Names of input ports to send to SOFA.
            output_keys: Names of output ports to receive from SOFA.
            slider_params: Optional ImGui slider configuration. None to
                disable sliders.
            sample_time: Sampling period in seconds, or None to use the
                global simulation dt.
        """
        super().__init__(name, sample_time)

        self.scene_file = scene_file
        self.input_keys = input_keys
        self.output_keys = output_keys
        self.slider_params = slider_params

        for k in input_keys:
            self.inputs[k] = None
            self.next_outputs = {}
        for k in output_keys:
            self.outputs[k] = None
            self.state[k] = None
            self.next_state[k] = None

        self.process = None
        self.conn = None


    # --------------------------------------------------------------------------
    # Class methods
    # --------------------------------------------------------------------------

    @classmethod
    def adapt_params(
        cls,
        params: Dict[str, Any],
        params_dir: Path | None = None,
    ) -> Dict[str, Any]:
        """Resolve a relative ``scene_file`` path against the project directory.

        Args:
            params: Raw parameter dict loaded from the YAML project file.
            params_dir: Directory of the project file, for resolving relative
                paths. Must not be None.

        Returns:
            Parameter dict with ``scene_file`` resolved to an absolute path.

        Raises:
            ValueError: If ``params_dir`` is None or ``scene_file`` is
                missing from ``params``.
        """
        if params_dir is None:
            raise ValueError("params_dir must be provided for SofaPlant adaptation")

        scene_file = params.get("scene_file")
        if scene_file is None:
            raise ValueError("Missing 'scene_file' parameter")

        path = Path(scene_file).expanduser()
        if not path.is_absolute():
            path = (params_dir / path).resolve()

        adapted = dict(params)
        adapted["scene_file"] = str(path)

        return adapted


    # --------------------------------------------------------------------------
    # Public methods
    # --------------------------------------------------------------------------

    def initialize(self, t0: float) -> None:
        """Start the SOFA worker process and receive initial outputs.

        Args:
            t0: Initial simulation time in seconds.

        Raises:
            RuntimeError: If the SOFA worker reports an error during startup.
        """
        parent_conn, child_conn = Pipe()
        self.conn = parent_conn

        self.process = Process(
            target=sofa_worker,
            args=(child_conn, self.scene_file, self.input_keys, self.output_keys)
        )
        self.process.start()

        initial_outputs = self.conn.recv()

        if isinstance(initial_outputs, dict) and initial_outputs.get("cmd") == "error":
            raise RuntimeError(initial_outputs["message"])

        for k in self.output_keys:
            self.outputs[k] = initial_outputs[k]
            self.state[k] = initial_outputs[k]
            self.next_state[k] = initial_outputs[k]

    def output_update(self, t: float, dt: float) -> None:
        """Forward the committed state outputs to the output ports.

        Args:
            t: Current simulation time in seconds.
            dt: Current time step in seconds.
        """
        for key in self.output_keys:
            self.outputs[key] = self.state[key]

    def state_update(self, t: float, dt: float) -> None:
        """Send inputs to SOFA, advance one step, and store the new outputs.

        Args:
            t: Current simulation time in seconds.
            dt: Current time step in seconds.

        Raises:
            RuntimeError: If any input is missing or the SOFA worker reports
                an error.
        """
        msg = {"cmd": "step", "inputs": {}}
        for k in self.input_keys:
            val = self.inputs[k]
            if val is None:
                raise RuntimeError(
                    f"[{self.name}] Input '{k}' is missing at time {t}."
                )
            msg["inputs"][k] = val

        self.conn.send(msg)

        outputs = self.conn.recv()
        if isinstance(outputs, dict) and outputs.get("cmd") == "error":
            raise RuntimeError(outputs["message"])

        for k in self.output_keys:
            self.next_state[k] = outputs[k]

    def finalize(self) -> None:
        """Shut down the SOFA worker process cleanly."""
        if self.conn:
            try:
                self.conn.send({"cmd": "stop"})
            except Exception:
                pass
            try:
                self.conn.close()
            except Exception:
                pass

        if self.process:
            self.process.join(timeout=1.0)
            if self.process.is_alive():
                self.process.kill()


    # --------------------------------------------------------------------------
    # Private methods
    # --------------------------------------------------------------------------

    def __del__(self) -> None:
        """Attempt to stop the worker process on garbage collection."""
        if self.conn:
            try:
                self.conn.send({"cmd": "stop"})
            except Exception:
                pass
        if self.process:
            self.process.join(timeout=0.5)
