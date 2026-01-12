import os
import sys
from pathlib import Path
import shutil
from PySide6.QtCore import QPointF


from pySimBlocks.gui.graphics import BlockItem, ConnectionItem
from pySimBlocks.gui.model import BlockInstance, ConnectionInstance, ProjectState
from pySimBlocks.gui.widgets.diagram_view import DiagramView
from pySimBlocks.gui.services.yaml_tools import save_yaml, load_yaml_file
from pySimBlocks.project.generate_run_script import generate_python_content


class ProjectController:
    def __init__(self, project_state: ProjectState, resolve_block_meta):
        self.project_state = project_state
        self.resolve_block_meta = resolve_block_meta
        self.view: DiagramView | None = None

    def save(self):
        save_yaml(self.project_state)

    def export(self):
        save_yaml(self.project_state)
        run_py = self.project_state.directory_path / "run.py"
        run_py.write_text(
            generate_python_content(
                model_yaml_path="model.yaml", parameters_yaml_path="parameters.yaml"
            )
        )

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
        save_yaml(self.project_state, True)

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

    def _load_simulation(self, params_data):
        sim_data = params_data.get("simulation", {})
        if "dt" not in sim_data:
            sim_data["dt"] = self.project_state.simulation["dt"]
        if "solver" not in sim_data:
            sim_data["solver"] = self.project_state.simulation["solver"]
        if "T" not in sim_data:
            sim_data["T"] = self.project_state.simulation["T"]
        self.project_state.simulation = sim_data
        if "external" in params_data:
            self.project_state.external = params_data["external"]

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
        x, y = 0, 0
        dx, dy = 180, 120

        for i, block in enumerate(self.project_state.blocks):
            pos = QPointF(x, y)
            item = BlockItem(block, pos, self.view)
            self.view.scene.addItem(item)
            self.view.block_items[block.name] = item
            x += dx
            if x > 800:
                x = 0
                y += dy

    def _instantiate_connections_in_view(self):
        for conn in self.project_state.connections:
            src_item = self.view.block_items[conn.src_block.name]
            dst_item = self.view.block_items[conn.dst_block.name]

            src_port = src_item.get_port_item(conn.src_port)
            dst_port = dst_item.get_port_item(conn.dst_port)

            item = ConnectionItem(src_port, dst_port, conn)
            self.view.scene.addItem(item)

            src_port.add_connection(item)
            dst_port.add_connection(item)
