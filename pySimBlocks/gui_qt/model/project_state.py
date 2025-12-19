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
        self.logs: dict = {}
        self.plots: list = []

    # -------------------------
    # Block management
    # -------------------------
    def add_block(self, instance):
        instance.name = self.make_unique_name(instance.name)
        self.blocks.append(instance)

    def remove_block(self, instance):
        if instance in self.blocks:
            self.blocks.remove(instance)


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
