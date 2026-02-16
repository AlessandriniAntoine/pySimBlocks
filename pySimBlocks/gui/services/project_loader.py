from abc import ABC, abstractmethod
from pathlib import Path

from pySimBlocks.gui.services.yaml_tools import load_yaml_file
from pySimBlocks.gui.project_controller import ProjectController
from PySide6.QtCore import QPointF

class ProjectLoader(ABC):
    
    @abstractmethod
    def load(self, controller: ProjectController, directory: Path):
        pass

class ProjectLoaderYaml(ProjectLoader):

    def load(self, controller: ProjectController, directory: Path):
        model_yaml = directory / "model.yaml"
        params_yaml = directory / "parameters.yaml"
        layout_yaml = directory / "layout.yaml"

        # 1. Parse YAML
        model_data = load_yaml_file(str(model_yaml))
        params_data = load_yaml_file(str(params_yaml))
        layout_blocks, layout_conns, layout_warnings = self._load_layout_data(
            layout_yaml
        )
        for w in layout_warnings:
            print(f"[Layout warning] {w}")

        # 2. Reset current state
        controller.clear()

        # 3. build model
        self._load_simulation(controller, params_data)
        self._load_blocks(controller, model_data, params_data, layout_blocks)
        self._load_connections(controller, model_data, layout_conns)
        self._load_logging(controller, params_data)
        self._load_plots(controller, params_data)

        controller.clear_dirty()

    
    def _load_simulation(self, controller: ProjectController, params_data: dict):
        sim_data: dict = params_data.get("simulation", {})
        controller.project_state.load_simulation(sim_data, params_data.get("external", None))

    def _load_blocks(self, 
                     controller: ProjectController, 
                     model_data: dict, 
                     params_data: dict,
                     layout_blocks: dict = {}):
        positions, position_warnings = self._compute_block_positions(
            model_data, layout_blocks
            )
        for w in position_warnings:
            print(f"[Layout blocks warning] {w}")
        
        blocks = model_data.get("blocks", [])
        params_blocks = params_data.get("blocks", {})

        for block in blocks:
            name = block["name"]
            category = block["category"]
            block_type = block["type"]
            
            block_layout = self._sanitize_block_layout(layout_blocks.get(name, {}))

            controller.view.drop_event_pos = positions.get(name, QPointF(0, 0))
            block = controller.add_block(category, block_type, block_layout)
            controller.rename_block(block, name)

            # ---- parameters ----
            raw_params = params_blocks.get(name, {})
            for pname, pvalue in raw_params.items():
                if pname in block.parameters:
                    block.parameters[pname] = pvalue

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

    def _load_connections(self, 
                          controller: ProjectController,
                          model_data: dict,
                          layout_conns: dict | None):
        connections = model_data.get("connections", [])

        routes, routes_warnings = self._parse_manual_routes(
                model_data, layout_conns
                )
        for w in routes_warnings:
            print(f"[Layout connections warning] {w}")

        for src, dst in connections:
            
            src_block_name, src_port_name = src.split(".")
            dst_block_name, dst_port_name = dst.split(".")

            src_block = controller.project_state.get_block(src_block_name)
            dst_block = controller.project_state.get_block(dst_block_name)

            src_port = next(
                (p for p in src_block.ports if p.name == src_port_name),
                None
            )
            dst_port = next(
                (p for p in dst_block.ports if p.name == dst_port_name),
                None
            )

            if src_port is None or dst_port is None:
                missing = []
                if src_port is None:
                    missing.append(f"{src_block_name}.{src_port_name}")
                if dst_port is None:
                    missing.append(f"{dst_block_name}.{dst_port_name}")
                print(f"[Connection warning] Cannot create connection {src} -> {dst}, missing port(s): {', '.join(missing)}")
                continue

            points = routes.get(f"{src} -> {dst}", None)
            controller.add_connection(src_port, dst_port, points)

    def _load_logging(self, 
                      controller: ProjectController,
                      params_data: dict):
        log_data = params_data.get("logging", {})
        controller.project_state.logging = log_data

    def _load_plots(self, 
                    controller: ProjectController,
                    params_data: dict):
        plot_data = params_data.get("plots", {})
        controller.project_state.plots = plot_data

    def _load_layout_data(self, layout_path: Path) -> tuple[dict, dict, list[str]]:
        """
        Load layout.yaml if it exists.

        Returns:
            layout_data: dict or None
            warnings: list of warning strings
        """
        warnings = []

        if not layout_path.exists():
            return {}, {}, warnings

        try:
            data = load_yaml_file(str(layout_path))
        except Exception as e:
            warnings.append(f"Failed to parse layout.yaml: {e}")
            return {}, {}, warnings

        if not isinstance(data, dict):
            warnings.append("layout.yaml is not a valid mapping, ignored.")
            return {}, {}, warnings

        blocks = data.get("blocks", {})
        if not isinstance(blocks, dict):
            warnings.append("layout.yaml.blocks is invalid, ignored.")
            return {}, {}, warnings

        conns = data.get("connections", {})
        if conns is not None and not isinstance(conns, dict):
            warnings.append("layout.yaml.connections is invalid, ignored.")
            conns = {}

        return blocks, conns, warnings

    def _compute_block_positions(
        self,
        model_data: dict, layout_blocks: dict | None
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

        blocks = model_data.get("blocks", [])

        model_block_names = {b["name"] for b in blocks}
        layout_block_names = set(layout_blocks.keys()) if layout_blocks else set()

        for block in blocks:
            name = block["name"]

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


    def _parse_manual_routes(
        self,
        model_data: dict,
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

        blocks = model_data.get("blocks", [])
        model_block_names = {b["name"] for b in blocks}
        model_conn_keys = model_data.get("connections", [])

        for key, payload in layout_connections.items():

            try:
                ports = payload["ports"]
                src_block, src_port = [s.strip() for s in ports[0].split(".", 1)]
                dst_block, dst_port = [s.strip() for s in ports[1].split(".", 1)]
            except Exception:
                warnings.append(f"Invalid connection key '{key}' in layout.yaml, ignored.")
                continue

            if src_block not in model_block_names or dst_block not in model_block_names:
                warnings.append(
                    f"layout.yaml contains connection '{key}' but a block is missing in model.yaml, ignored."
                )
                continue

            if ports not in model_conn_keys:
                warnings.append(
                    f"layout.yaml contains connection '{ports}' not present in model.yaml, ignored."
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
