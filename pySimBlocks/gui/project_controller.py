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
from typing import Any, Callable
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
        return self._add_block(block_instance)

    def add_copy_block(self, block_instance: BlockInstance) -> BlockInstance:
        copy = BlockInstance.copy(block_instance)
        return self._add_block(copy)

    def _add_block(self, block_instance: BlockInstance) -> BlockInstance:
        block_instance.name = self.make_unique_name(block_instance.name)

        self.project_state.add_block(block_instance)
        self.view.add_block(block_instance)

        return block_instance

    def rename_block(self, block_instance: BlockInstance, new_name: str):
        old_name = block_instance.name

        if old_name == new_name:
            return

        new_name = self.make_unique_name(new_name)
        
        block_instance.name = new_name
        prefix_old = f"{old_name}.outputs."
        prefix_new = f"{new_name}.outputs."

        self.project_state.logging = [
            s.replace(prefix_old, prefix_new)
            if s.startswith(prefix_old) else s
            for s in self.project_state.logging
        ]

        for plot in self.project_state.plots:
            plot["signals"] = [
                s.replace(prefix_old, prefix_new)
                if s.startswith(prefix_old) else s
                for s in plot["signals"]
            ]

    def update_block_param(self, block_instance: BlockInstance, params: dict[str, Any]):
        self.rename_block(block_instance, params.pop("name", block_instance.name))
        block_instance.update_params(params)
        self.view.refresh_block_port(block_instance)

    def remove_block(self, block_instance: BlockInstance):
        
        # remove connections
        for connection in self.project_state.get_connections_of_block(block_instance):
            self.remove_connection(connection)

        # delete all outputs signal from logging
        removed_signals = [
            f"{block_instance.name}.outputs.{p.name}"
            for p in block_instance.ports if p.direction == "output"
        ]
        remaining_signals = [
            s for s in self.project_state.logging
            if s not in removed_signals
        ]
        self.set_logged_signals(remaining_signals)

        # remove signals from plots and delete empty plot
        for i in reversed(range(len(self.project_state.plots))):
            plot = self.project_state.plots[i]
            # Keep only signals that are not removed
            plot["signals"] = [s for s in plot["signals"] if s not in removed_signals]
            # Delete the plot if it has no signals left
            if not plot["signals"]:
                self.delete_plot(i)

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

    def create_plot(self, title: str, signals: list[str]) -> None:
        self._ensure_logged(signals)
        self.project_state.plots.append({
            "title": title,
            "signals": list(signals),
        })

    def update_plot(self, index: int, title: str, signals: list[str]) -> None:
        self._ensure_logged(signals)
        plot = self.project_state.plots[index]
        plot["title"] = title
        plot["signals"] = list(signals)

    def delete_plot(self, index: int) -> None:
        del self.project_state.plots[index]

    def _ensure_logged(self, signals: list[str]):
        for sig in signals:
            if sig not in self.project_state.logging:
                self.project_state.logging.append(sig)

    def update_simulation_params(self, params: dict[str, float | str]):
        self.project_state.load_simulation(params)

    def set_logged_signals(self, signals: list[str]):
        self.project_state.logging = list(dict.fromkeys(signals))