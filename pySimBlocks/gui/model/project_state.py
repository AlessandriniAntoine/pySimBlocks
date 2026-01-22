# ******************************************************************************
#                                 pySimBlocks                                 
#                Copyright (c) 2026 The pySimBlocks Authors               
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

from pySimBlocks.gui.model.block_instance import BlockInstance
from pySimBlocks.gui.model.connection_instance import ConnectionInstance
from pySimBlocks.gui.model.project_simulation_params import ProjectSimulationParams

class ProjectState:
    def __init__(self, directory_path: Path):
        self.blocks: list[BlockInstance] = []
        self.connections: list[ConnectionInstance] = []
        self.simulation = ProjectSimulationParams()
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

        self.simulation.clear()

        self.external = None

    def load_simulation(self, sim_data: dict, external):
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
        block_instance.name = self.make_unique_name(block_instance.name)
        self.blocks.append(block_instance)

    def remove_block(self, block_instance: BlockInstance):
        if block_instance in self.blocks:
            # remove connections
            self.connections = [
                c for c in self.connections
                if c.src_block is not block_instance and c.dst_block is not block_instance
            ]
            # delete all outputs signal from logging
            removed_signals = [
                f"{block_instance.name}.outputs.{p.name}"
                for p in block_instance.ports if p.direction == "output"
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
            self.blocks.remove(block_instance)

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
