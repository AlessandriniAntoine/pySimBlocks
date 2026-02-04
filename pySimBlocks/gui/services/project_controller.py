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
import shutil
import sys
from pathlib import Path
from typing import Callable

from PySide6.QtCore import QPointF

from pySimBlocks.gui.graphics import BlockItem, ConnectionItem
from pySimBlocks.gui.model import BlockInstance, ConnectionInstance, ProjectState
from pySimBlocks.gui.services.yaml_tools import load_yaml_file, save_yaml
from pySimBlocks.gui.widgets.diagram_view import DiagramView
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

    # --------------------------------------------------------------------------
    # Public methods
    # --------------------------------------------------------------------------
    def save(self):
        save_yaml(self.project_state, self.view.block_items)

    # ------------------------------------------------------------------
    def export(self):
        save_yaml(self.project_state, self.view.block_items)
        run_py = self.project_state.directory_path / "run.py"
        run_py.write_text(
            generate_python_content(
                model_yaml_path="model.yaml", parameters_yaml_path="parameters.yaml"
            )
        )

    # ------------------------------------------------------------------
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

    # ------------------------------------------------------------------
    def can_plot(self):
        if not bool(self.project_state.logs):
            return False, "Simulation has not been done.\nPlease run fist."

        if "time" not in self.project_state.logs:
            return False, "Time is not in logs."

        return True, "Plotting is available."

    # ------------------------------------------------------------------
    def change_project_directory(self, new_path: Path):
        if self.project_state.directory_path:
            temp = self.project_state.directory_path / ".temp"
            if temp.exists():
                shutil.rmtree(temp, ignore_errors=True)
        self.project_state.directory_path = new_path

    # ------------------------------------------------------------------
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
        layout_blocks, layout_conns, layout_warnings = self._load_layout_data(
                self.project_state.directory_path
        )
        for w in layout_warnings:
            print(f"[Layout warning] {w}")
        self._instantiate_blocks_in_view(layout_blocks)
        self._instantiate_connections_in_view(layout_conns)

    # --------------------------------------------------------------------------
    # Internal loading methods
    # --------------------------------------------------------------------------
    def _load_simulation(self, params_data: dict):
        sim_data: dict = params_data.get("simulation", {})
        self.project_state.load_simulation(sim_data, params_data.get("external", None))

    # ------------------------------------------------------------------
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

    # ------------------------------------------------------------------
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

    # ------------------------------------------------------------------
    def _load_logging(self, params_data):
        log_data = params_data.get("logging", {})
        self.project_state.logging = log_data

    # ------------------------------------------------------------------
    def _load_plots(self, params_data):
        plot_data = params_data.get("plots", {})
        self.project_state.plots = plot_data

    # ------------------------------------------------------------------
    def _instantiate_blocks_in_view(self, layout_blocks: dict | None):
        # --- load layout ---
        if layout_blocks is None:
            layout_blocks = {}
        
        positions, position_warnings = self._compute_block_positions(layout_blocks)

        for w in position_warnings:
            print(f"[Layout blocks warning] {w}")

        # --- instantiate blocks ---
        for block in self.project_state.blocks:
            pos = positions[block.name]
            block_layout = layout_blocks.get(block.name, {})
            orientation = block_layout.get("orientation", "normal")
            if orientation not in ("normal", "flipped"):
                print(f"[Layout blocks warning] Invalid orientation for block '{block.name}' in layout.yaml, set to 'normal'.")

            item = BlockItem(block, pos, self.view, orientation=orientation)
            self.view.scene.addItem(item)
            self.view.block_items[item.instance.uid] = item

    # ------------------------------------------------------------------
    def _instantiate_connections_in_view(self, layout_connections: dict | None):
        routes, route_warnings = self._parse_manual_routes(layout_connections)
        for w in route_warnings:
            print(f"[Layout connections warning] {w}")

        for conn in self.project_state.connections:
            src_item = self.view.block_items[conn.src_block.uid]
            dst_item = self.view.block_items[conn.dst_block.uid]

            src_port = src_item.get_port_item(conn.src_port)
            dst_port = dst_item.get_port_item(conn.dst_port)

            item = ConnectionItem(src_port, dst_port, conn)
            key = f"{conn.src_block.name}.{conn.src_port} -> {conn.dst_block.name}.{conn.dst_port}"
            if key in routes:
                item.apply_manual_route(routes[key])


            self.view.scene.addItem(item)
            src_port.add_connection(item)
            dst_port.add_connection(item)

    # ------------------------------------------------------------------
    def _load_layout_data(self, 
                          directory: Path
                          ) -> tuple[dict | None, dict | None, list[str]]:
        """
        Load layout.yaml if it exists.

        Returns:
            layout_data: dict or None
            warnings: list of warning strings
        """
        warnings = []
        layout_path = directory / "layout.yaml"

        if not layout_path.exists():
            return None, None, warnings 

        try:
            data = load_yaml_file(str(layout_path))
        except Exception as e:
            warnings.append(f"Failed to parse layout.yaml: {e}")
            return None, None, warnings

        if not isinstance(data, dict):
            warnings.append("layout.yaml is not a valid mapping, ignored.")
            return None, None, warnings

        blocks = data.get("blocks", None)
        if not isinstance(blocks, dict):
            warnings.append("layout.yaml.blocks is invalid, ignored.")
            blocks = None

        conns = data.get("connections", None)
        if conns is not None and not isinstance(conns, dict):
            warnings.append("layout.yaml.connections is invalid, ignored.")
            conns = None

        return blocks, conns, warnings

    # ------------------------------------------------------------------
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

    # ------------------------------------------------------------------
    def _parse_manual_routes(
        self,
        layout_connections: dict | None
    ) -> tuple[dict[str, list[QPointF]], list[str]]:
        """
        Returns:
            routes: dict[key -> list[QPointF]] for VALID routes only
            warnings: list[str]
        """
        warnings = []
        routes: dict[str, list[QPointF]] = {}

        if not layout_connections:
            return routes, warnings

        model_block_names = {b.name for b in self.project_state.blocks}
        model_conn_keys = {
            f"{c.src_block.name}.{c.src_port} -> {c.dst_block.name}.{c.dst_port}"
            for c in self.project_state.connections
        }

        for key, payload in layout_connections.items():
            # key format: "A.out -> B.in"
            try:
                left, right = [s.strip() for s in key.split("->")]
                src_block, src_port = [s.strip() for s in left.split(".", 1)]
                dst_block, dst_port = [s.strip() for s in right.split(".", 1)]
            except Exception:
                warnings.append(f"Invalid connection key '{key}' in layout.yaml, ignored.")
                continue

            if src_block not in model_block_names or dst_block not in model_block_names:
                warnings.append(
                    f"layout.yaml contains connection '{key}' but a block is missing in model.yaml, ignored."
                )
                continue

            if key not in model_conn_keys:
                warnings.append(
                    f"layout.yaml contains connection '{key}' not present in model.yaml, ignored."
                )
                continue

            if not isinstance(payload, dict) or "route" not in payload:
                warnings.append(f"layout.yaml connection '{key}' has no valid 'route', ignored.")
                continue

            raw_route = payload["route"]
            if not isinstance(raw_route, list) or len(raw_route) < 2:
                warnings.append(f"layout.yaml connection '{key}' route is invalid/too short, ignored.")
                continue

            pts: list[QPointF] = []
            ok = True
            for pt in raw_route:
                if (
                    not isinstance(pt, (list, tuple))
                    or len(pt) != 2
                    or not isinstance(pt[0], (int, float))
                    or not isinstance(pt[1], (int, float))
                ):
                    ok = False
                    break
                pts.append(QPointF(float(pt[0]), float(pt[1])))

            if not ok:
                warnings.append(f"layout.yaml connection '{key}' route has invalid points, ignored.")
                continue

            routes[key] = pts

        return routes, warnings
