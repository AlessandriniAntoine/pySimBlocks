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

from pySimBlocks.gui.model.block_instance import BlockInstance, PortInstance
from pySimBlocks.gui.model.connection_instance import ConnectionInstance
from pySimBlocks.gui.model.project_simulation_params import ProjectSimulationParams

class ProjectState:
    def __init__(self, directory_path: Path):
        self.blocks: list[BlockInstance] = []
        self.connections: list[ConnectionInstance] = []
        self.simulation = ProjectSimulationParams()
        self.external: str | None = None
        self.directory_path = directory_path
        self.logging: list[str] = []
        self.logs: dict = {}
        self.plots: list[dict[str, str | list[str]]] = []


    def clear(self):
        self.blocks.clear()
        self.connections.clear()

        self.logs.clear()
        self.logging.clear()
        self.plots.clear()

        self.simulation.clear()

        self.external = None

    def load_simulation(self, sim_data: dict, external = None):
        self.simulation.load_from_dict(sim_data)

        if external:
            self.external = external

    # -------------------------
    # Block management
    # -------------------------
    def get_block(self, name:str):
        for block in self.blocks:
            if name == block.name:
                return block

    def add_block(self, block_instance: BlockInstance):
        self.blocks.append(block_instance)

    def remove_block(self, block_instance: BlockInstance):
        if block_instance in self.blocks:
            self.blocks.remove(block_instance)

    # -------------------------
    # Connection management
    # -------------------------
    def add_connection(self, conn: ConnectionInstance):
        self.connections.append(conn)

    def remove_connection(self, conn: ConnectionInstance):
        if conn in self.connections:
            self.connections.remove(conn)

    def get_connections_of_block(self, block_instance: BlockInstance) -> list[ConnectionInstance]: 
        return [
            c for c in self.connections
            if block_instance is c.src_block() or block_instance is c.dst_block()
        ]

    def get_connections_of_port(self, port_instance: PortInstance) -> list[ConnectionInstance]:
        return [
            c for c in self.connections
            if port_instance is c.src_port or port_instance is c.dst_port
        ]

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
    
    def can_plot(self) -> tuple[bool, str]:
        if not bool(self.logs):
            return False, "Simulation has not been done.\nPlease run fist."

        if not ("time" in self.logs):
            return False, "Time is not in logs."

        return True, "Plotting is available."
