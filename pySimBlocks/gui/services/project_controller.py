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
from typing import Callable
import shutil
from pySimBlocks.gui.model import BlockInstance, ConnectionInstance, PortInstance, ProjectState
from pySimBlocks.gui.widgets.diagram_view import DiagramView
from pySimBlocks.tools.blocks_registry import BlockMeta

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from pySimBlocks.gui.services.project_loader import ProjectLoader


class ProjectController:
    def __init__(self,
                 project_state: ProjectState,
                 view: DiagramView,
                 resolve_block_meta: Callable[[str, str], BlockMeta]
    ):
        self.project_state = project_state
        self.resolve_block_meta = resolve_block_meta
        self.view = view

    def add_block(self, category: str, block_type: str) -> BlockInstance:

        block_meta = self.resolve_block_meta(category, block_type)
        block_instance = BlockInstance(block_meta)

        block_instance.name = self.make_unique_name(block_instance.name)

        self.project_state.add_block(block_instance)
        self.view.add_block(block_instance)

        return block_instance

    def remove_block(self, block_instance: BlockInstance):
        
        # remove connections
        for connection in self.project_state.get_connections_of_block(block_instance):
            self.remove_connection(connection)

        # delete all outputs signal from logging
        removed_signals = [
            f"{block_instance.name}.outputs.{p.name}"
            for p in block_instance.ports if p.direction == "output"
        ]
        self.project_state.logging = [
            s for s in self.project_state.logging
            if s not in removed_signals
        ]
        # remove signals from plots and delete empty plot
        new_plots = []
        for plot in self.project_state.plots:
            plot["signals"] = [
                s for s in plot["signals"]
                if s not in removed_signals
            ]
            if plot["signals"]:
                new_plots.append(plot)
        self.project_state.plots = new_plots

        # remove block
        self.project_state.remove_block(block_instance)
        self.view.remove_block(block_instance)

    def add_connection(self, port1: PortInstance, port2: PortInstance):
    

        if not port1.is_compatible(port2):
            return
        
        src_port, dst_port = (
            (port1, port2) if port1.direction == "output" else (port2, port1)
        )

        port_dst_connections = self.project_state.get_connections_of_port(dst_port.block)


        if not dst_port.can_accept_connection(port_dst_connections):
            return
        
        connection_instance = ConnectionInstance(src_port, dst_port)

        self.project_state.add_connection(connection_instance)
        self.view.add_connecton(connection_instance)

    def remove_connection(self, connection: ConnectionInstance):
        
        self.project_state.remove_connection(connection)
        self.view.remove_connection(connection)

    def clear(self):
        self.project_state.clear()
        self.view.clear_scene()

    def make_unique_name(self, base_name: str) -> str:
        existing = {b.name for b in self.project_state.blocks}

        if base_name not in existing:
            return base_name

        i = 1
        while f"{base_name}_{i}" in existing:
            i += 1

        return f"{base_name}_{i}"
    
    def is_name_available(self, name: str, current=None) -> bool:
        for b in self.project_state.blocks:
            if b is current:
                continue
            if b.name == name:
                return False
        return True        

    def change_project_directory(self, new_path: Path):
        if self.project_state.directory_path:
            temp = self.project_state.directory_path / ".temp"
            if temp.exists():
                shutil.rmtree(temp, ignore_errors=True)
        self.project_state.directory_path = new_path

    def load_project(self, loader: 'ProjectLoader'):
        loader.load(self, self.project_state.directory_path)