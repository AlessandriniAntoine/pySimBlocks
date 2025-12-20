from pathlib import Path

from pySimBlocks.gui_qt.model.block_instance import BlockInstance
from pySimBlocks.gui_qt.model.connection_instance import ConnectionInstance

class ProjectState:
    def __init__(self, directory_path: Path):
        self.blocks: list[BlockInstance] = []
        self.connections: list[ConnectionInstance] = []
        self.simulation = {"dt": 0.1, "solver": "fixed", "T": 10.}
        self.external: str | None = None
        self.directory_path = directory_path
        self.logging: list = []
        self.logs: dict = {}
        self.plots: list = []


    def clear(self):
        self.blocks.clear()
        self.connections.clear()

        self.logs.clear()
        self.logging.clear()
        self.plots.clear()

        # simulation settings → on garde les defaults
        self.simulation = {
            "dt": self.simulation.get("dt", 0.01),
            "solver": self.simulation.get("solver", "fixed"),
            "T": self.simulation.get("T", 10.0),
        }

        self.external = None

    # -------------------------
    # Block management
    # -------------------------
    def get_block(self, name:str):
        for block in self.blocks:
            if name == block.name:
                return block

    def add_block(self, instance):
        instance.name = self.make_unique_name(instance.name)
        self.blocks.append(instance)

    def remove_block(self, block: BlockInstance):
        if block in self.blocks:
            # remove connections
            self.connections = [
                c for c in self.connections
                if c.src_block is not block and c.dst_block is not block
            ]
            # delete all outputs signal from logging
            removed_signals = [
                f"{block.name}.outputs.{p.name}"
                for p in block.ports if p.direction == "output"
            ]
            self.logging = [
                s for s in self.logging
                if s not in removed_signals
            ]
            # remove signals from plots and delete empty plot
            new_plots = []
            for plot in self.plots:
                plot["signals"] = [
                    s for s in plot["signals"]
                    if s not in removed_signals
                ]
                if plot["signals"]:
                    new_plots.append(plot)
            self.plots = new_plots
            # remove block
            self.blocks.remove(block)

    # -------------------------
    # Connection management
    # -------------------------
    def add_connection(self, conn: ConnectionInstance):
        self.connections.append(conn)

    def remove_connection(self, conn: ConnectionInstance):
        if conn in self.connections:
            self.connections.remove(conn)

    # -------------------------
    # Naming
    # -------------------------
    def make_unique_name(self, base_name: str) -> str:
        existing = {b.name for b in self.blocks}

        if base_name not in existing:
            return base_name

        i = 1
        while f"{base_name}_{i}" in existing:
            i += 1

        return f"{base_name}_{i}"

    def is_name_available(self, name: str, current=None) -> bool:
        for b in self.blocks:
            if b is current:
                continue
            if b.name == name:
                return False
        return True

     # -------------------------
     # Signals
     # -------------------------
    def get_output_signals(self) -> list[str]:
        signals = []

        for block in self.blocks:
            for port in block.ports:
                if port.direction == "output":
                    signals.append(f"{block.name}.outputs.{port.name}")

        return signals
