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

from abc import ABC, abstractmethod
from pathlib import Path

from PySide6.QtCore import QPointF

from pySimBlocks.gui.project_controller import ProjectController
from pySimBlocks.gui.services.yaml_tools import load_yaml_file


class ProjectLoader(ABC):
    @abstractmethod
    def load(self, controller: ProjectController, directory: Path):
        pass


class ProjectLoaderYaml(ProjectLoader):
    def load(self, controller: ProjectController, directory: Path):
        project_yaml = directory / "project.yaml"
        project_data = load_yaml_file(str(project_yaml))

        if not isinstance(project_data, dict):
            raise ValueError("project.yaml is not a valid mapping.")

        sim_data = project_data.get("simulation", {})
        diagram_data = project_data.get("diagram", {})
        gui_data = project_data.get("gui", {})

        layout_blocks, layout_conns, layout_warnings = self._load_layout_data(gui_data)
        for w in layout_warnings:
            print(f"[Layout warning] {w}")

        controller.clear()

        self._load_simulation(controller, sim_data)
        self._load_blocks(controller, diagram_data, layout_blocks)
        self._load_connections(controller, diagram_data, layout_conns)
        self._load_logging(controller, sim_data)
        self._load_plots(controller, sim_data)

        controller.clear_dirty()

    def _load_simulation(self, controller: ProjectController, sim_data: dict):
        if not isinstance(sim_data, dict):
            sim_data = {}
        controller.project_state.load_simulation(
            sim_data, sim_data.get("external_module", None)
        )

    def _load_blocks(
        self,
        controller: ProjectController,
        diagram_data: dict,
        layout_blocks: dict | None = None,
    ):
        positions, position_warnings = self._compute_block_positions(
            diagram_data, layout_blocks
        )
        for w in position_warnings:
            print(f"[Layout blocks warning] {w}")

        blocks = diagram_data.get("blocks", [])
        if not isinstance(blocks, list):
            raise ValueError("'diagram.blocks' must be a list.")

        for desc in blocks:
            if not isinstance(desc, dict):
                print("[Block warning] Invalid block entry in diagram.blocks, ignored.")
                continue

            name = desc.get("name")
            category = desc.get("category")
            block_type = desc.get("type")
            if not isinstance(name, str) or not isinstance(category, str) or not isinstance(block_type, str):
                print("[Block warning] Block missing required fields (name/category/type), ignored.")
                continue

            block_layout = self._sanitize_block_layout((layout_blocks or {}).get(name, {}))

            controller.view.drop_event_pos = positions.get(name, QPointF(0, 0))
            block = controller.add_block(category, block_type, block_layout)
            controller.rename_block(block, name)

            raw_params = desc.get("parameters", {})
            if not isinstance(raw_params, dict):
                print(f"[Block warning] Invalid parameters for block '{name}', ignored.")
                raw_params = {}

            for pmeta in block.meta.parameters:
                pname = pmeta.name
                if pname in raw_params:
                    block.parameters[pname] = raw_params[pname]
                elif pmeta.autofill and pmeta.default is not None:
                    block.parameters[pname] = pmeta.default

            block.resolve_ports()
            controller.view.refresh_block_port(block)

    def _sanitize_block_layout(self, block_layout: dict | None) -> dict:
        if not isinstance(block_layout, dict):
            return {}

        out = {}

        orientation = block_layout.get("orientation")
        if orientation in {"normal", "flipped"}:
            out["orientation"] = orientation

        width = block_layout.get("width")
        if isinstance(width, (int, float)) and width > 0:
            out["width"] = float(width)

        height = block_layout.get("height")
        if isinstance(height, (int, float)) and height > 0:
            out["height"] = float(height)

        return out

    def _load_connections(
        self,
        controller: ProjectController,
        diagram_data: dict,
        layout_conns: dict | None,
    ):
        connections = diagram_data.get("connections", [])
        if not isinstance(connections, list):
            raise ValueError("'diagram.connections' must be a list.")

        routes, routes_warnings = self._parse_manual_routes(diagram_data, layout_conns)
        for w in routes_warnings:
            print(f"[Layout connections warning] {w}")

        for conn in connections:
            if not isinstance(conn, dict):
                print("[Connection warning] Invalid connection entry, ignored.")
                continue

            conn_name = conn.get("name", None)
            ports = conn.get("ports", None)
            if not isinstance(ports, list) or len(ports) != 2:
                print("[Connection warning] Connection has invalid ports, ignored.")
                continue
            src, dst = ports
            if not isinstance(src, str) or not isinstance(dst, str):
                print("[Connection warning] Connection ports must be strings, ignored.")
                continue

            src_block_name, src_port_name = src.split(".")
            dst_block_name, dst_port_name = dst.split(".")

            src_block = controller.project_state.get_block(src_block_name)
            dst_block = controller.project_state.get_block(dst_block_name)

            if src_block is None or dst_block is None:
                print(
                    f"[Connection warning] Cannot create connection {src} -> {dst}, missing block(s)."
                )
                continue

            src_port = next((p for p in src_block.ports if p.name == src_port_name), None)
            dst_port = next((p for p in dst_block.ports if p.name == dst_port_name), None)

            if src_port is None or dst_port is None:
                missing = []
                if src_port is None:
                    missing.append(f"{src_block_name}.{src_port_name}")
                if dst_port is None:
                    missing.append(f"{dst_block_name}.{dst_port_name}")
                print(
                    f"[Connection warning] Cannot create connection {src} -> {dst}, "
                    f"missing port(s): {', '.join(missing)}"
                )
                continue

            points = routes.get(conn_name, None) if isinstance(conn_name, str) else None
            controller.add_connection(src_port, dst_port, points)

    def _load_logging(self, controller: ProjectController, sim_data: dict):
        log_data = sim_data.get("logging", [])
        controller.project_state.logging = log_data if isinstance(log_data, list) else []

    def _load_plots(self, controller: ProjectController, sim_data: dict):
        plot_data = sim_data.get("plots", [])
        controller.project_state.plots = plot_data if isinstance(plot_data, list) else []

    def _load_layout_data(self, gui_data: dict) -> tuple[dict, dict, list[str]]:
        """
        Load layout data from:
            gui.layout.blocks
            gui.layout.connections
        """
        warnings = []

        if not isinstance(gui_data, dict):
            return {}, {}, warnings

        layout = gui_data.get("layout", {})
        if layout is None:
            return {}, {}, warnings
        if not isinstance(layout, dict):
            warnings.append("project.yaml gui.layout is invalid, ignored.")
            return {}, {}, warnings

        blocks = layout.get("blocks", {})
        if not isinstance(blocks, dict):
            warnings.append("project.yaml gui.layout.blocks is invalid, ignored.")
            return {}, {}, warnings

        conns = layout.get("connections", {})
        if conns is not None and not isinstance(conns, dict):
            warnings.append("project.yaml gui.layout.connections is invalid, ignored.")
            conns = {}

        return blocks, conns, warnings

    def _compute_block_positions(
        self,
        diagram_data: dict,
        layout_blocks: dict | None,
    ) -> tuple[dict[str, QPointF], list[str]]:
        warnings = []
        positions = {}

        x, y = 0, 0
        dx, dy = 180, 120

        blocks = diagram_data.get("blocks", [])
        if not isinstance(blocks, list):
            return positions, ["'diagram.blocks' must be a list."]

        model_block_names = {
            b.get("name")
            for b in blocks
            if isinstance(b, dict) and isinstance(b.get("name"), str)
        }
        layout_block_names = set(layout_blocks.keys()) if layout_blocks else set()

        for block in blocks:
            if not isinstance(block, dict) or not isinstance(block.get("name"), str):
                continue

            name = block["name"]

            if layout_blocks and name in layout_blocks:
                entry = layout_blocks[name]
                x_val = entry.get("x")
                y_val = entry.get("y")

                if isinstance(x_val, (int, float)) and isinstance(y_val, (int, float)):
                    positions[name] = QPointF(float(x_val), float(y_val))
                    continue
                warnings.append(
                    f"Invalid position for block '{name}' in project.yaml gui.layout.blocks, auto-placed."
                )

            else:
                if layout_blocks is not None:
                    warnings.append(
                        f"Block '{name}' not found in project.yaml gui.layout.blocks, auto-placed."
                    )

            positions[name] = QPointF(x, y)
            x += dx
            if x > 800:
                x = 0
                y += dy

        for name in layout_block_names - model_block_names:
            warnings.append(
                f"project.yaml gui.layout.blocks contains '{name}' not present in diagram.blocks."
            )

        return positions, warnings

    def _parse_manual_routes(
        self,
        diagram_data: dict,
        layout_connections: dict | None,
    ) -> tuple[dict[str, list[QPointF]], list[str]]:
        warnings = []
        routes: dict[str, list[QPointF]] = {}

        if not layout_connections:
            return routes, warnings

        blocks = diagram_data.get("blocks", [])
        connections = diagram_data.get("connections", [])
        if not isinstance(blocks, list) or not isinstance(connections, list):
            return routes, warnings

        model_block_names = {
            b.get("name")
            for b in blocks
            if isinstance(b, dict) and isinstance(b.get("name"), str)
        }
        model_connections_by_name = {}
        for conn in connections:
            if not isinstance(conn, dict):
                continue
            name = conn.get("name")
            ports = conn.get("ports")
            if isinstance(name, str) and isinstance(ports, list) and len(ports) == 2:
                model_connections_by_name[name] = ports

        for conn_name, payload in layout_connections.items():
            if conn_name not in model_connections_by_name:
                warnings.append(
                    f"project.yaml gui.layout.connections contains unknown connection '{conn_name}', ignored."
                )
                continue

            ports = model_connections_by_name[conn_name]
            try:
                src_block, _src_port = [s.strip() for s in ports[0].split(".", 1)]
                dst_block, _dst_port = [s.strip() for s in ports[1].split(".", 1)]
            except Exception:
                warnings.append(
                    f"Invalid ports for connection '{conn_name}' in diagram.connections, ignored."
                )
                continue

            if src_block not in model_block_names or dst_block not in model_block_names:
                warnings.append(
                    f"project.yaml layout connection '{conn_name}' references missing block(s), ignored."
                )
                continue

            if not isinstance(payload, dict) or "route" not in payload:
                warnings.append(
                    f"project.yaml layout connection '{conn_name}' has no valid 'route', ignored."
                )
                continue

            raw_route = payload["route"]
            if not isinstance(raw_route, list) or len(raw_route) < 2:
                warnings.append(
                    f"project.yaml layout connection '{conn_name}' route is invalid/too short, ignored."
                )
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
                warnings.append(
                    f"project.yaml layout connection '{conn_name}' route has invalid points, ignored."
                )
                continue

            routes[conn_name] = pts

        return routes, warnings
