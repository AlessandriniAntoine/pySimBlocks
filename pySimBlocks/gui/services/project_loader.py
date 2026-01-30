from abc import ABC, abstractmethod
from pathlib import Path

from pySimBlocks.gui.services.yaml_tools import load_yaml_file
from pySimBlocks.gui.services.project_controller import ProjectController
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
        layout_blocks, layout_warnings = self._load_layout_data(layout_yaml)

        # 2. Reset current state
        controller.clear()

        # 3. Compute positions
        positions, position_warnings = self._compute_block_positions(model_data, layout_blocks)
        for w in layout_warnings + position_warnings:
            print(f"[Layour warning] {w}")
            

        # 3. build model
        self._load_simulation(controller, params_data)
        self._load_blocks(controller, model_data, params_data, positions)
        self._load_connections(controller, model_data)
        self._load_logging(controller, params_data)
        self._load_plots(controller, params_data)

    
    def _load_simulation(self, controller: ProjectController, params_data: dict):
        sim_data: dict = params_data.get("simulation", {})
        controller.project_state.load_simulation(sim_data, params_data.get("external", None))

    def _load_blocks(self, 
                     controller: ProjectController, 
                     model_data: dict, 
                     params_data: dict,
                     positions: dict):
        
        blocks = model_data.get("blocks", [])
        params_blocks = params_data.get("blocks", {})

        for block in blocks:
            name = block["name"]
            category = block["category"]
            block_type = block["type"]

            controller.view.drop_event_pos = positions.get(name, QPointF(0, 0))
            block = controller.add_block(category, block_type)

            block.name = name

            # ---- parameters ----
            raw_params = params_blocks.get(name, {})
            for pname, pvalue in raw_params.items():
                if pname in block.parameters:
                    block.parameters[pname] = pvalue

            block.resolve_ports()

    def _load_connections(self, 
                          controller: ProjectController,
                          model_data: dict):
        connections = model_data.get("connections", [])

        for src, dst in connections:
            
            src_block_name, src_port_name = src.split(".")
            dst_block_name, dst_port_name = dst.split(".")

            src_block = controller.project_state.get_block(src_block_name)
            dst_block = controller.project_state.get_block(dst_block_name)

            src_port = next(p for p in src_block.ports if p.name == src_port_name)
            dst_port = next(p for p in dst_block.ports if p.name == dst_port_name)

            controller.add_connection(src_port, dst_port)

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

    def _load_layout_data(self, layout_path: Path) -> tuple[dict | None, list[str]]:
        """
        Load layout.yaml if it exists.

        Returns:
            layout_data: dict or None
            warnings: list of warning strings
        """
        warnings = []

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
