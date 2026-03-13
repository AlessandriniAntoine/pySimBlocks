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

from pathlib import Path

from pySimBlocks.gui.models.block_instance import BlockInstance, PortInstance
from pySimBlocks.gui.models.connection_instance import ConnectionInstance
from pySimBlocks.gui.models.project_simulation_params import ProjectSimulationParams

class ProjectState:
    """Store the editable state of a GUI project.

    Attributes:
        blocks: Block instances currently present in the project.
        connections: Connections currently present in the project.
        simulation: Simulation parameter set for the project.
        external: Optional external runtime path or identifier.
        directory_path: Project directory on disk.
        logging: Signals selected for logging.
        logs: Last simulation logs.
        plots: Plot configurations defined for the project.
    """

    def __init__(self, directory_path: Path):
        """Initialize an empty project state.

        Args:
            directory_path: Project directory on disk.

        Raises:
            None.
        """
        self.blocks: list[BlockInstance] = []
        self.connections: list[ConnectionInstance] = []
        self.simulation = ProjectSimulationParams()
        self.external: str | None = None
        self.directory_path = directory_path
        self.logging: list[str] = []
        self.logs: dict = {}
        self.plots: list[dict[str, str | list[str]]] = []


    # --- Public methods ---

    def clear(self):
        """Reset blocks, connections, logs, plots, and simulation settings."""
        self.blocks.clear()
        self.connections.clear()

        self.logs.clear()
        self.logging.clear()
        self.plots.clear()

        self.simulation.clear()

        self.external = None

    def load_simulation(self, sim_data: dict, external = None):
        """Load simulation settings into the project state.

        Args:
            sim_data: Serialized simulation settings.
            external: Optional external runtime value.
        """
        self.simulation.load_from_dict(sim_data)

        if external:
            self.external = external

    def get_block(self, name:str):
        """Return the block with the given name if it exists.

        Args:
            name: Block instance name.

        Returns:
            Matching block instance, or None if not found.
        """
        for block in self.blocks:
            if name == block.name:
                return block

    def add_block(self, block_instance: BlockInstance):
        """Add a block instance to the project.

        Args:
            block_instance: Block instance to add.
        """
        self.blocks.append(block_instance)

    def remove_block(self, block_instance: BlockInstance):
        """Remove a block instance from the project if present.

        Args:
            block_instance: Block instance to remove.
        """
        if block_instance in self.blocks:
            self.blocks.remove(block_instance)

    def add_connection(self, conn: ConnectionInstance):
        """Add a connection instance to the project.

        Args:
            conn: Connection instance to add.
        """
        self.connections.append(conn)

    def remove_connection(self, conn: ConnectionInstance):
        """Remove a connection instance from the project if present.

        Args:
            conn: Connection instance to remove.
        """
        if conn in self.connections:
            self.connections.remove(conn)

    def get_connections_of_block(self, block_instance: BlockInstance) -> list[ConnectionInstance]:
        """Return all connections touching the given block.

        Args:
            block_instance: Block instance to inspect.

        Returns:
            Connections where the block is either source or destination.
        """
        return [
            c for c in self.connections
            if block_instance is c.src_block() or block_instance is c.dst_block()
        ]

    def get_connections_of_port(self, port_instance: PortInstance) -> list[ConnectionInstance]:
        """Return all connections attached to the given port.

        Args:
            port_instance: Port instance to inspect.

        Returns:
            Connections where the port is either source or destination.
        """
        return [
            c for c in self.connections
            if port_instance is c.src_port or port_instance is c.dst_port
        ]

    def get_output_signals(self) -> list[str]:
        """Return all output signal paths currently available in the project.

        Returns:
            Output signal identifiers in ``Block.outputs.port`` format.
        """
        signals = []

        for block in self.blocks:
            for port in block.ports:
                if port.direction == "output":
                    signals.append(f"{block.name}.outputs.{port.name}")

        return signals

    def can_plot(self) -> tuple[bool, str]:
        """Return whether plot generation is currently possible.

        Returns:
            Tuple containing the availability flag and the reason message.
        """
        if not bool(self.logs):
            return False, "Simulation has not been done.\nPlease run fist."

        if not ("time" in self.logs):
            return False, "Time is not in logs."

        return True, "Plotting is available."
