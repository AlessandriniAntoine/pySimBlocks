# ******************************************************************************
#                                  pySimBlocks
#                     Copyright (c) 2026 Antoine Alessandrini
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
from typing import Dict, Any, List
import yaml
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
    """
    Base class for controller to enable Sofa Simulation Loop and pySimBlocks to interact.

    Description:
        - SOFA_MASTER: SOFA is the time master.
            model_yaml + parameters_yaml required
            pysimblocks time step must be a multiple of sofa time step.
            At each pysimblocks step, the controller:
                1) reads measurements from the scene
                2) performs one pySimBlocks step
                3) applies the computed control inputs

        - Non-SOFA_MASTER: pySimBlocks is the time master.
                            The controller is used ONLY as an I/O shell.
                            No pySimBlocks model is built or executed.

    Required methods:
        - set_inputs(self)
        - get_outputs(self)

    Optional methods:
        - build_model()  : create self.model, self.sofa_block and variables_to_log
        - print_logs()  : print logs at each step (already implemented)
        - save()

    optional parameter:
        - variables_to_log: list of signal to log

    Note:
        - get_outputs() MUST ALWAYS WORK AND RETURN CONSISTENT SHAPES.
    """

    def __init__(self, root: Sofa.Core.Node, name: str ="SofaControllerGui"):
        super().__init__(name=name)

        self.IS_READY = False
        self.SOFA_MASTER = True
        self._imgui = _imgui

        # MUST be filled by child controllers
        self.root = root
        self.inputs: Dict[str, np.ndarray] = {}
        self.outputs: Dict[str, np.ndarray] = {}
        self.variables_to_log: List[str] = []
        self.verbose = False

        self.dt: float | None = None
        self.sim: Simulator | None = None
        self.step_index: int = 0

        self.model_yaml: str | None = None
        self.parameters_yaml: str | None = None

    # --------------------------------------------------------------------------
    # Public methods
    # --------------------------------------------------------------------------
    # --- Mandatory methods. ---
    def prepare_scene(self):
        """
        Optional initialization hook executed before pySimBlocks starts.

        Purpose:
            - wait for any preparation condition (fixed number of steps,
            convergence, stabilization, etc.),
            - optionally record initial measurements or offsets.

        The user must set `self.IS_READY = True` when the scene is ready to start
        the pySimBlocks control loop.
        """
        self.IS_READY = True

    # ------------------------------------------------------------------
    def set_inputs(self):
        """
        Apply inputs from pySimBlocks to SOFA components.
        Must be implemented by child classes.
        """
        raise NotImplementedError("set_inputs() must be implemented by subclass.")

    # ------------------------------------------------------------------
    def get_outputs(self):
        """
        Read state from SOFA components and populate self.outputs.
        MUST ALWAYS WORK AND RETURN CONSISTENT SHAPES.
        Must be implemented by child classes.
        """
        raise NotImplementedError("get_outputs() must be implemented by subclass.")

    # --- Optionnal methods. ---
    def save(self):
        """
        Optional: executed at each control step.
        Override this method to save logs or export custom data.
        The default implementation does nothing.
        """
        pass

    # ----------------------------------------------------------------------
    # SOFA event callback 
    # ----------------------------------------------------------------------
    def onAnimateBeginEvent(self, event):
        """
        SOFA callback executed before each physical integration step.

        Sequence:
            1. Read SOFA outputs  → get_outputs()
            2. Push them into the exchange block
            3. Advance pySimBlocks one step → sim.step()
            4. Retrieve controller inputs from exchange block
            5. Apply them to SOFA → set_inputs()
        """
        if self.SOFA_MASTER:
            if self.sim is None:
                self._prepare_pysimblocks()
                self._get_sofa_outputs()
                self._set_sofa_plot()
                self._set_sofa_slider()

            if not self.IS_READY:
                self.prepare_scene()

            if self.IS_READY:
                if self.counter % self.ratio ==0:
                    
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
    def _build_model(self):
        """
        Define the internal pySimBlocks controller model.
        Mandatory if purpose to be used in Sofa Simulation (SOFA_MASTER)

        Must create:
            - self.model
            - the exchange block self.sofa_block (SofaExchangeIO)
            - self.variables_to_log
        """
        if self.parameters_yaml is not None:
            self.sim_cfg, self.model_cfg, self.plot_cfg = load_project_config(self.parameters_yaml)
        if self.model_yaml is not None:
            model_dict = self._adapt_model_for_sofa(self.model_yaml)
            self.model = Model("sofa_model")
            build_model_from_dict(self.model, model_dict, self.model_cfg)


    # ------------------------------------------------------------------
    def _prepare_pysimblocks(self):
        """
        Called once SOFA is initialized AND if SOFA is the master.
        Initialize the pysimblock struture.
        """
        if self.SOFA_MASTER and (self.model_yaml is None or self.parameters_yaml is None):
            raise RuntimeError("SOFA_MASTER=True requires model_yaml and parameters_yaml.")
        if self.dt is None:
            raise ValueError("Sample time dt Must be set at initialization.")

        self._build_model()
        self._detect_sofa_exchange_block()
        self.sim = Simulator(self.model, self.sim_cfg, verbose=self.verbose)
        self._get_sofa_outputs()
        self.sim.initialize()
        self.sim_index = 0

        ratio = self.sim_cfg.dt / self.dt
        if abs(ratio - round(ratio)) > 1e-12:
            raise ValueError(
                            f"pySimBlocks sample time={self.sim_cfg.dt} "
                            f"is not a multiple of Sofa sample time={self.dt}."
                        )
        self.ratio = int(round(ratio))
        self.counter = 0


    # ------------------------------------------------------------------
    def _print_logs(self):
        """
        Optional: print selected logged variables at each control step.
        Already implemented
        """
        print(f"\nStep: {self.sim_index}")
        for variable in self.sim_cfg.logging:
            print(f"{variable}: {self.sim.logs[variable][-1]}")


    # ------------------------------------------------------------------
    def _detect_sofa_exchange_block(self):
        """
        Detect the SofaExchangeIO block inside self.model.
        Must be called after build_model().
        """
        from pySimBlocks.blocks.systems.sofa.sofa_exchange_i_o import SofaExchangeIO

        candidates = [blk for blk in self.model.blocks.values() if isinstance(blk, SofaExchangeIO)]

        if len(candidates) == 0:
            raise RuntimeError(
                "No SofaExchangeIO block found in the model. "
                "The controller must include exactly one SOFA exchange block."
            )

        if len(candidates) > 1:
            raise RuntimeError(
                f"Multiple SofaExchangeIO blocks found ({len(candidates)}). "
                "Only one SOFA IO block is allowed."
            )

        self._sofa_block = candidates[0]

    # ------------------------------------------------------------------
    def _get_sofa_outputs(self):
        """
        Read outputs from SOFA components and push them to pySimBlocks.
        """
        self.get_outputs()
        for keys, val in self.outputs.items():
            self._sofa_block.outputs[keys] = val

    # ------------------------------------------------------------------
    def _set_sofa_inputs(self):
        """
        Apply inputs from pySimBlocks to SOFA components.
        """
        for key, val in self._sofa_block.inputs.items():
            self.inputs[key] = val
        self.set_inputs()

    # ------------------------------------------------------------------
    def _set_sofa_plot(self):
        """
        Setup ImGui plotting for selected variables.
        """
        if not self._imgui:
            return 

        if self.sim is None:
            raise RuntimeError("Simulator not initialized.")

        self._plot_node = self.root.addChild("PLOT")
        self._plot_data = {}
        for plot in self.plot_cfg.plots:
            for var in plot["signals"]:
                block_name, _, key = var.split(".")
                self._plot_data[f"{block_name}.{key}"] = self._plot_node.addChild(f"{block_name}_{key}")
                value = self.sim.model.blocks[block_name].outputs[key].flatten()
                for i in range(len(value)):
                    self._plot_data[f"{block_name}.{key}"].addData(name=f"value{i}", type="float", value=value[i])
                    MyGui.PlottingWindow.addData(f"{block_name}.{key}[{i}]", self._plot_data[f"{block_name}.{key}"].getData(f"value{i}"))

    # ------------------------------------------------------------------
    def _update_sofa_plot(self):
        """
        Update ImGui plotting for selected variables.
        """
        if not self._imgui:
            return 

        for name, node in self._plot_data.items():
            block_name, key = name.split(".")
            value = self.sim.model.blocks[block_name].outputs[key].flatten()
            for i in range(len(value)):
                node.getData(f"value{i}").value = float(value[i])

    # ------------------------------------------------------------------
    def _set_sofa_slider(self):
        """
        Setup ImGui sliders for selected variables.
        """
        if not self._imgui:
            return 
        if self.sim is None:
            raise RuntimeError("Simulator not initialized.")

        data = self._sofa_block.slider_params 
        data = data if data is not None else {}

        self._slider_node = self.root.addChild("SLIDERS")
        self._slider_data = {}
        for var, extremum in data.items():
            block_name, key = var.split(".")
            node = self._slider_node.addChild(f"{block_name}_{key}")
            block = self.sim.model.blocks[block_name]
            value = getattr(block, key)
            self._slider_data[f"{block_name}.{key}"] = {"node": node, "shape": value.shape}
            value = value.flatten()
            for i in range(len(value)):
                d = node.addData(name=f"value{i}", type="float", value=value[i])
                MyGui.MyRobotWindow.addSettingInGroup( f"{key}[{i}]", d, extremum[0], extremum[1], f"{block_name}")

    # ------------------------------------------------------------------
    def _update_sofa_slider(self):
        """
        Update ImGui sliders for selected variables.
        """
        for var in self._slider_data:
            block_name, key = var.split(".")
            block = self.sim.model.blocks[block_name]
            node = self._slider_data[var]["node"]
            shape = self._slider_data[var]["shape"]
            new_values = []
            for i in range(np.prod(shape)):
                new_values.append(node.getData(f"value{i}").value)
            setattr(block, key, np.array(new_values).reshape(shape))

    # ------------------------------------------------------------------
    def _adapt_model_for_sofa(self, model_yaml: str) -> Dict[str, Any]:
        """
        Load model.yaml and adapt it for SOFA execution.

        This replaces any SofaPlant block by a SofaExchangeIO block,
        while preserving block name and connections.

        Parameters
        ----------
        model_yaml : Path
            Path to model.yaml

        Returns
        -------
        dict
            Adapted model dictionary
        """
        model_path = Path(model_yaml)
        if not model_path.exists():
            raise FileNotFoundError(f"Model YAML file not found: {model_yaml}")

        with model_path.open("r") as f:
            model_data = yaml.safe_load(f) or {}

        adapted = dict(model_data)
        adapted_blocks = []

        for block in model_data.get("blocks", []):
            if block["type"].lower() == "sofa_plant":
                adapted_blocks.append({
                    "name": block["name"],
                    "category": "systems",
                    "type": "sofa_exchange_i_o",
                })
            else:
                adapted_blocks.append(block)

        adapted["blocks"] = adapted_blocks
        return adapted
