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

import os
import sys
from pathlib import Path
from typing import Callable
import shutil
from PySide6.QtCore import QPointF


from pySimBlocks.gui.graphics import BlockItem, ConnectionItem
from pySimBlocks.gui.model import BlockInstance, ConnectionInstance, PortInstance, ProjectState
from pySimBlocks.gui.widgets.diagram_view import DiagramView
from pySimBlocks.gui.services.yaml_tools import save_yaml, load_yaml_file
from pySimBlocks.project.generate_run_script import generate_python_content
from pySimBlocks.tools.blocks_registry import BlockMeta


class ProjectController:
    def __init__(self, 
                 project_state: ProjectState,
                 view: DiagramView,
                 resolve_block_meta: Callable[[str, str], BlockMeta]
    ):
        self.project_state = project_state
        self.resolve_block_meta = resolve_block_meta
        self.view = view

    def add_block(self, category: str, block_type: str):

        block_meta = self.resolve_block_meta(category, block_type)
        block_instance = BlockInstance(block_meta)

        block_instance.name = self.make_unique_name(block_instance.name)

        self.project_state.add_block(block_instance)
        self.view.add_block(block_instance)

    def remove_block(self, block_instance: BlockInstance):
        
        # remove connections
        for connection in self.project_state.get_connections_of_block(block_instance):
            self.remove_connection(connection)

        # delete all outputs signal from logging
        removed_signals = [
            f"{block_instance.name}.outputs.{p.name}"
            for p in block_instance.ports if p.direction == "output"
        ]
        self.project_state.logging = [
            s for s in self.project_state.logging
            if s not in removed_signals
        ]
        # remove signals from plots and delete empty plot
        new_plots = []
        for plot in self.project_state.plots:
            plot["signals"] = [
                s for s in plot["signals"]
                if s not in removed_signals
            ]
            if plot["signals"]:
                new_plots.append(plot)
        self.project_state.plots = new_plots

        # remove block
        self.project_state.remove_block(block_instance)
        self.view.remove_block(block_instance)

    def add_connecton(self, port1: PortInstance, port2: PortInstance):

        if not port1.is_compatible(port2):
            return
        
        src_port, dst_port = (
            (port1, port2) if port1.direction == "output" else (port2, port1)
        )

        port_dst_connections = self.project_state.get_connections_of_block(dst_port.block)

        if not dst_port.can_accept_connection(port_dst_connections):
            return
        
        connection_instance = ConnectionInstance(src_port, dst_port)

        self.project_state.add_connection(connection_instance)
        self.view.add_connecton(connection_instance)

    def remove_connection(self, connection: ConnectionInstance):
        
        self.project_state.remove_connection(connection)
        self.view.remove_connection(connection)

    def make_unique_name(self, base_name: str) -> str:
        existing = {b.name for b in self.project_state.blocks}

        if base_name not in existing:
            return base_name

        i = 1
        while f"{base_name}_{i}" in existing:
            i += 1

        return f"{base_name}_{i}"
    
    def is_name_available(self, name: str, current=None) -> bool:
        for b in self.project_state.blocks:
            if b is current:
                continue
            if b.name == name:
                return False
        return True

    def run(self):
        project_dir = self.project_state.directory_path
        if project_dir is None:
            return (
                {},
                False,
                "Project directory is not set.\nPlease define it in settings.",
            )

        temp_dir = project_dir / ".temp"

        if temp_dir.exists():
            shutil.rmtree(temp_dir)
        temp_dir.mkdir(parents=True)
        save_yaml(project_state=self.project_state, temp=True)

        model_path = temp_dir / "model.yaml"
        param_path = temp_dir / "parameters.yaml"

        code = generate_python_content(
            model_yaml_path=str(model_path),
            parameters_yaml_path=str(param_path),
            parameters_dir=str(project_dir),
            enable_plots=False,
        )

        old_cwd = os.getcwd()
        old_sys_path = list(sys.path)
        env = {}
        try:
            os.chdir(temp_dir)
            sys.path.insert(0, str(project_dir))
            exec(code, env, env)
            logs = env.get("logs")
            return logs, True, "Simulation success."
        except Exception as e:
            logs = {}
            return logs, False, f"Error: {e}"
        finally:
            os.chdir(old_cwd)
            sys.path[:] = old_sys_path

    def can_plot(self):
        if not bool(self.project_state.logs):
            return False, "Simulation has not been done.\nPlease run fist."

        if not ("time" in self.project_state.logs):
            return False, "Time is not in logs."

        return True, "Plotting is available."

    def change_project_directory(self, new_path: Path):
        if self.project_state.directory_path:
            temp = self.project_state.directory_path / ".temp"
            if temp.exists():
                shutil.rmtree(temp, ignore_errors=True)
        self.project_state.directory_path = new_path

    def load_project(self, directory: Path):
        model_yaml = directory / "model.yaml"
        params_yaml = directory / "parameters.yaml"

        # 1. Parse YAML
        model_data = load_yaml_file(str(model_yaml))
        params_data = load_yaml_file(str(params_yaml))

        # 2. Reset current state
        self.project_state.clear()
        self.view.clear_scene()

        # 3. Rebuild model
        self._load_simulation(params_data)
        self._load_blocks(model_data, params_data)
        self._load_connections(model_data)
        self._load_logging(params_data)
        self._load_plots(params_data)

        # 4. Rebuild view
        self._instantiate_blocks_in_view()
        self._instantiate_connections_in_view()

    def _load_simulation(self, params_data: dict):
        sim_data: dict = params_data.get("simulation", {})
        self.project_state.load_simulation(sim_data, params_data.get("external", None))

    def _load_blocks(self, model_data, params_data):
        blocks = model_data.get("blocks", [])
        params_blocks = params_data.get("blocks", {})

        for block in blocks:
            name = block["name"]
            category = block["category"]
            type_ = block["type"]

            meta = self.resolve_block_meta(category, type_)
            instance = BlockInstance(meta)
            instance.name = name

            # ---- parameters ----
            raw_params = params_blocks.get(name, {})
            for pname, pvalue in raw_params.items():
                if pname in meta.parameters:
                    instance.parameters[pname] = pvalue

            instance.resolve_ports()
            self.project_state.add_block(instance)

    def _load_connections(self, model_data):
        connections = model_data.get("connections", [])

        for src, dst in connections:
            src_block, src_port = src.split(".")
            dst_block, dst_port = dst.split(".")

            conn = ConnectionInstance(
                src_block=self.project_state.get_block(src_block),
                src_port=src_port,
                dst_block=self.project_state.get_block(dst_block),
                dst_port=dst_port,
            )
            self.project_state.add_connection(conn)

    def _load_logging(self, params_data):
        log_data = params_data.get("logging", {})
        self.project_state.logging = log_data

    def _load_plots(self, params_data):
        plot_data = params_data.get("plots", {})
        self.project_state.plots = plot_data

    def _instantiate_blocks_in_view(self):
        # --- load layout ---
        layout_blocks, layout_warnings = self._load_layout_data(
            self.project_state.directory_path
        )

        positions, position_warnings = self._compute_block_positions(layout_blocks)

        for w in layout_warnings + position_warnings:
            print(f"[Layout warning] {w}")

        # --- instantiate blocks ---
        for block in self.project_state.blocks:
            pos = positions[block.name]
            item = BlockItem(block, pos, self.view)
            self.view.scene.addItem(item)
            self.view.block_items[item.instance.uid] = item


    def _instantiate_connections_in_view(self):
        for conn in self.project_state.connections:
            src_item = self.view.block_items[conn.src_block.uid]
            dst_item = self.view.block_items[conn.dst_block.uid]

            src_port = src_item.get_port_item(conn.src_port)
            dst_port = dst_item.get_port_item(conn.dst_port)

            item = ConnectionItem(src_port, dst_port, conn)
            self.view.scene.addItem(item)

            src_port.add_connection(item)
            dst_port.add_connection(item)


    def _load_layout_data(self, directory: Path) -> tuple[dict | None, list[str]]:
        """
        Load layout.yaml if it exists.

        Returns:
            layout_data: dict or None
            warnings: list of warning strings
        """
        warnings = []
        layout_path = directory / "layout.yaml"

        if not layout_path.exists():
            return None, warnings  # Rule 1

        try:
            data = load_yaml_file(str(layout_path))
        except Exception as e:
            warnings.append(f"Failed to parse layout.yaml: {e}")
            return None, warnings

        if not isinstance(data, dict):
            warnings.append("layout.yaml is not a valid mapping, ignored.")
            return None, warnings

        blocks = data.get("blocks", {})
        if not isinstance(blocks, dict):
            warnings.append("layout.yaml.blocks is invalid, ignored.")
            return None, warnings

        return blocks, warnings


    def _compute_block_positions(
        self,
        layout_blocks: dict | None
    ) -> tuple[dict[str, QPointF], list[str]]:
        """
        Decide final positions for each block in the model.

        Returns:
            positions: dict[name -> QPointF]
            warnings: list of warning strings
        """
        warnings = []
        positions = {}

        # automatic layout parameters
        x, y = 0, 0
        dx, dy = 180, 120

        model_block_names = {b.name for b in self.project_state.blocks}
        layout_block_names = set(layout_blocks.keys()) if layout_blocks else set()

        for block in self.project_state.blocks:
            name = block.name

            if layout_blocks and name in layout_blocks:
                entry = layout_blocks[name]
                x_val = entry.get("x")
                y_val = entry.get("y")

                if isinstance(x_val, (int, float)) and isinstance(y_val, (int, float)):
                    positions[name] = QPointF(float(x_val), float(y_val))
                    continue
                else:
                    warnings.append(
                        f"Invalid position for block '{name}' in layout.yaml, auto-placed."
                    )

            else:
                if layout_blocks is not None:
                    warnings.append(
                        f"Block '{name}' not found in layout.yaml, auto-placed."
                    )

            # fallback automatic placement
            positions[name] = QPointF(x, y)
            x += dx
            if x > 800:
                x = 0
                y += dy

        # layout blocks not in model
        for name in layout_block_names - model_block_names:
            warnings.append(
                f"layout.yaml contains block '{name}' not present in model.yaml."
            )

        return positions, warnings
