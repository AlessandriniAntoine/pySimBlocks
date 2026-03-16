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

from pathlib import Path
from typing import Any, Dict, List

import numpy as np
import Sofa

from pySimBlocks import Model, Simulator
from pySimBlocks.project.load_project_config import load_project_config
from pySimBlocks.project.build_model import build_model_from_dict


try:
    import Sofa.ImGui as MyGui
    _imgui = hasattr(MyGui, "MyRobotWindow")
except ImportError:
    _imgui = False


class SofaPysimBlocksController(Sofa.Core.Controller):
    """Base SOFA controller class bridging the SOFA simulation loop and pySimBlocks.

    Supports two operating modes:

    **SOFA_MASTER** (``SOFA_MASTER=True``): SOFA drives the time loop. A
    ``project_yaml`` must be provided. At each pySimBlocks step the
    controller reads SOFA outputs, runs one pySimBlocks step, and applies
    the resulting inputs back to SOFA.

    **pySimBlocks master** (``SOFA_MASTER=False``): pySimBlocks drives the
    time loop. The controller acts as a pure I/O shell — no model is built
    or executed internally.

    Subclasses must implement :meth:`set_inputs` and :meth:`get_outputs`.

    Attributes:
        IS_READY: Set to True by :meth:`prepare_scene` when the scene is
            ready to start the control loop.
        SOFA_MASTER: If True, SOFA is the time master.
        root: SOFA root node.
        inputs: Dict of input signals written by :meth:`set_inputs`.
        outputs: Dict of output signals populated by :meth:`get_outputs`.
        variables_to_log: List of signal names to log at each step.
        verbose: If True, print logged variables at each control step.
        dt: SOFA simulation time step in seconds. Must be set by the subclass.
        sim: The pySimBlocks :class:`Simulator` instance, or None.
        step_index: Total number of SOFA animation steps executed.
        project_yaml: Path to the pySimBlocks YAML project file.
    """

    def __init__(self, root: Sofa.Core.Node, name: str = "SofaControllerGui"):
        """Initialize the SOFA–pySimBlocks controller.

        Args:
            root: SOFA root node.
            name: Name passed to the SOFA controller base class.
        """
        super().__init__(name=name)

        self.IS_READY = False
        self.SOFA_MASTER = True
        self._imgui = _imgui

        self.root = root
        self.inputs: Dict[str, np.ndarray] = {}
        self.outputs: Dict[str, np.ndarray] = {}
        self.variables_to_log: List[str] = []
        self.verbose = False

        self.dt: float | None = None
        self.sim: Simulator | None = None
        self.step_index: int = 0

        self.project_yaml: str | None = None
        self._init_failed = False


    # --------------------------------------------------------------------------
    # Public methods
    # --------------------------------------------------------------------------

    def prepare_scene(self) -> None:
        """Optional hook executed before the pySimBlocks control loop starts.

        Override this method to wait for a preparation condition (e.g. a
        fixed number of warm-up steps or scene stabilization). Set
        ``self.IS_READY = True`` when the scene is ready. The default
        implementation sets ``IS_READY`` immediately.
        """
        self.IS_READY = True

    def set_inputs(self) -> None:
        """Apply inputs from pySimBlocks to SOFA components.

        Raises:
            NotImplementedError: Always — must be implemented by subclasses.
        """
        raise NotImplementedError("[pySimBlocks] ERROR: set_inputs() must be implemented by subclass.")

    def get_outputs(self) -> None:
        """Read state from SOFA components and populate ``self.outputs``.

        Must always succeed and return consistent shapes across calls.

        Raises:
            NotImplementedError: Always — must be implemented by subclasses.
        """
        raise NotImplementedError("[pySimBlocks] ERROR: get_outputs() must be implemented by subclass.")

    def save(self) -> None:
        """Optional hook executed at each control step.

        Override to save logs or export custom data. The default
        implementation does nothing.
        """

    def get_block(self, block_name: str):
        """Return a block from the pySimBlocks model by name.

        Args:
            block_name: Name of the block to retrieve.

        Returns:
            The block instance with the specified name.

        Raises:
            RuntimeError: If the simulator is not initialized or if the
                block is not found in the model.
        """
        if self.sim is None:
            raise RuntimeError("[pySimBlocks] ERROR: Simulator not initialized. Cannot get block.")
        if block_name not in self.sim.model.blocks:
            raise RuntimeError(f"[pySimBlocks] ERROR: Block '{block_name}' not found in the model.")
        return self.sim.model.blocks[block_name]

    def onAnimateBeginEvent(self, event) -> None:
        """SOFA callback executed before each physical integration step.

        When ``SOFA_MASTER=True``, runs the following sequence at each
        pySimBlocks step:

        1. Read SOFA outputs via :meth:`get_outputs`.
        2. Push them into the exchange block.
        3. Advance pySimBlocks one step.
        4. Retrieve controller inputs from the exchange block.
        5. Apply them to SOFA via :meth:`set_inputs`.

        Args:
            event: SOFA animation event (unused).
        """
        if self.SOFA_MASTER:
            if self._init_failed:
                return

            if self.sim is None:
                self._prepare_pysimblocks()
                self._get_sofa_outputs()
                self._set_sofa_plot()
                self._set_sofa_slider()

            if not self.IS_READY:
                self.prepare_scene()

            if self.IS_READY:
                if self.counter % self.ratio == 0:
                    self._get_sofa_outputs()
                    self.sim.step()
                    self.sim._log(self.sim_cfg.logging)
                    self._set_sofa_inputs()

                    if self.verbose:
                        self._print_logs()

                    self.save()
                    self._update_sofa_slider()
                    self._update_sofa_plot()

                    self.sim_index += 1
                    self.counter = 0
                self.counter += 1

        self.step_index += 1


    # --------------------------------------------------------------------------
    # Private methods
    # --------------------------------------------------------------------------

    def _build_model(self) -> None:
        """Load the pySimBlocks model from ``project_yaml``."""
        project_path = self.project_yaml
        if project_path is None:
            raise RuntimeError("[pySimBlocks] ERROR: SOFA_MASTER=True requires project_yaml to be set.")

        self.sim_cfg, model_dict, self.plot_cfg, _, params_dir = load_project_config(project_path)
        model_dict = self._adapt_model_for_sofa(model_dict)
        self.model = Model("sofa_model")
        build_model_from_dict(self.model, model_dict, params_dir=params_dir)

    def _prepare_pysimblocks(self) -> None:
        """Initialize the pySimBlocks simulator once SOFA is ready."""
        try:
            if self.SOFA_MASTER and self.project_yaml is None:
                self._init_failed = True
                raise RuntimeError("[pySimBlocks] ERROR: SOFA_MASTER=True requires project_yaml.")
            if self.dt is None:
                self._init_failed = True
                raise ValueError("[pySimBlocks] ERROR: SOFA_MASTER=True requires self.dt to be set to the SOFA time step.")

            self._build_model()
            self._detect_sofa_exchange_block()
            self._secure_keys()
            self.sim = Simulator(self.model, self.sim_cfg, verbose=self.verbose)
            self._get_sofa_outputs()
            self.sim.initialize()
            self.sim_index = 0

            ratio = self.sim_cfg.dt / self.dt
            if abs(ratio - round(ratio)) > 1e-12:
                self._init_failed = True
                raise ValueError(
                    "[pySimBlocks] ERROR: Sample time mismatch.\n"
                    f"pySimBlocks sample time={self.sim_cfg.dt} "
                    f"is not a multiple of Sofa sample time={self.dt}."
                )
            self.ratio = int(round(ratio))
            self.counter = 0
        except Exception as e:
            self._init_failed = True
            raise

    def _secure_keys(self) -> None:
        """Validate that model port keys are a subset of SOFA controller keys."""
        model_inputs_keys = set(self._sofa_block.inputs.keys())
        sofa_inputs_keys = set(self.inputs.keys())
        if not model_inputs_keys.issubset(sofa_inputs_keys):
            self._init_failed = True
            raise RuntimeError(
                "[pySimBlocks] ERROR: model input_keys are missing from controller inputs.\n"
                f"SOFA controller inputs: {sofa_inputs_keys}\n"
                f"Model block inputs: {model_inputs_keys}\n"
                f"Ensure that the controller in the SOFA block contains at least the same input keys as the SofaExchangeIO block."
            )

        model_outputs_keys = set(self._sofa_block.outputs.keys())
        sofa_outputs_keys = set(self.outputs.keys())
        if not model_outputs_keys.issubset(sofa_outputs_keys):
            self._init_failed = True
            raise RuntimeError(
                "[pySimBlocks] ERROR: model output_keys are missing from controller outputs.\n"
                f"SOFA controller outputs: {sofa_outputs_keys}\n"
                f"Model block outputs: {model_outputs_keys}\n"
                f"Ensure that the controller in the SOFA block contains at least the same output keys as the SofaExchangeIO block."
            )

    def _print_logs(self) -> None:
        """Print selected logged variables at the current control step."""
        print(f"\nStep: {self.sim_index}")
        for variable in self.sim_cfg.logging:
            print(f"{variable}: {self.sim.logs[variable][-1]}")

    def _detect_sofa_exchange_block(self) -> None:
        """Find the unique SofaExchangeIO block inside the model."""
        from pySimBlocks.blocks.systems.sofa.sofa_exchange_i_o import SofaExchangeIO

        candidates = [blk for blk in self.model.blocks.values() if isinstance(blk, SofaExchangeIO)]

        if len(candidates) == 0:
            self._init_failed = True
            raise RuntimeError(
                "[pySimBlocks] ERROR: No SofaExchangeIO block found in the model.\n"
                "The controller must include exactly one SOFA exchange block."
            )

        if len(candidates) > 1:
            self._init_failed = True
            raise RuntimeError(
                "[pySimBlocks] ERROR: Multiple SofaExchangeIO blocks found ({len(candidates)}).\n"
                "Only one SOFA IO block is allowed."
            )

        self._sofa_block = candidates[0]

    def _get_sofa_outputs(self) -> None:
        """Read SOFA outputs and push them into the exchange block."""
        self.get_outputs()
        for keys, val in self.outputs.items():
            self._sofa_block.outputs[keys] = val

    def _set_sofa_inputs(self) -> None:
        """Pull inputs from the exchange block and apply them to SOFA."""
        for key, val in self._sofa_block.inputs.items():
            self.inputs[key] = val
        self.set_inputs()

    def _set_sofa_plot(self) -> None:
        """Set up ImGui plotting nodes for the configured signals."""
        if not self._imgui:
            return

        if self.sim is None:
            raise RuntimeError("[pySimBlocks] ERROR: Simulator not initialized.")

        self._plot_node = self.root.addChild("PLOT")
        self._plot_data = {}
        for plot in self.plot_cfg.plots:
            for var in plot["signals"]:
                block_name, _, key = var.split(".")
                block = self.get_block(block_name)
                self._plot_data[f"{block_name}.{key}"] = self._plot_node.addChild(f"{block_name}_{key}")
                value = block.outputs[key].flatten()
                for i in range(len(value)):
                    self._plot_data[f"{block_name}.{key}"].addData(name=f"value{i}", type="float", value=value[i])
                    MyGui.PlottingWindow.addData(f"{block_name}.{key}[{i}]", self._plot_data[f"{block_name}.{key}"].getData(f"value{i}"))

    def _update_sofa_plot(self) -> None:
        """Update ImGui plot values for the configured signals."""
        if not self._imgui:
            return

        for name, node in self._plot_data.items():
            block_name, key = name.split(".")
            block = self.get_block(block_name)
            value = block.outputs[key].flatten()
            for i in range(len(value)):
                node.getData(f"value{i}").value = float(value[i])

    def _set_sofa_slider(self) -> None:
        """Set up ImGui slider nodes for the configured block attributes."""
        if not self._imgui:
            return

        if self.sim is None:
            raise RuntimeError("[pySimBlocks] ERROR: Simulator not initialized.")

        data = self._sofa_block.slider_params
        data = data if data is not None else {}

        self._slider_node = self.root.addChild("SLIDERS")
        self._slider_data = {}
        for var, extremum in data.items():
            block_name, key = var.split(".")
            node = self._slider_node.addChild(f"{block_name}_{key}")
            block = self.get_block(block_name)
            value = getattr(block, key)
            self._slider_data[f"{block_name}.{key}"] = {"node": node, "shape": value.shape}
            value = value.flatten()
            for i in range(len(value)):
                d = node.addData(name=f"value{i}", type="float", value=value[i])
                MyGui.MyRobotWindow.addSettingInGroup(f"{key}[{i}]", d, extremum[0], extremum[1], f"{block_name}")

    def _update_sofa_slider(self) -> None:
        """Read ImGui slider values and apply them to the corresponding block attributes."""
        if not self._imgui:
            return

        for var in self._slider_data:
            block_name, key = var.split(".")
            block = self.get_block(block_name)
            node = self._slider_data[var]["node"]
            shape = self._slider_data[var]["shape"]
            new_values = []
            for i in range(np.prod(shape)):
                new_values.append(node.getData(f"value{i}").value)
            setattr(block, key, np.array(new_values).reshape(shape))

    def _adapt_model_for_sofa(self, model_data: Dict[str, Any]) -> Dict[str, Any]:
        """Replace any SofaPlant block with a SofaExchangeIO block.

        Preserves block names and connections so the model topology is
        unchanged. Used when SOFA itself runs the simulation and the plant
        block is not needed.

        Args:
            model_data: Model dictionary loaded from the YAML project file.

        Returns:
            Adapted model dictionary with SofaPlant replaced by SofaExchangeIO.
        """
        adapted = dict(model_data)
        adapted_blocks = []

        for block in model_data.get("blocks", []):
            if not isinstance(block, dict):
                adapted_blocks.append(block)
                continue

            block_type = str(block.get("type", "")).lower()
            if block_type == "sofa_plant":
                patched = dict(block).copy()
                patched["type"] = "sofa_exchange_i_o"
                patched.pop("scene_file", None)
                adapted_blocks.append(patched)
            else:
                adapted_blocks.append(block)

        adapted["blocks"] = adapted_blocks
        return adapted
