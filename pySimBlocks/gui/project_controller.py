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

import copy
import shutil
from pathlib import Path
from typing import TYPE_CHECKING, Any, Callable

from PySide6.QtCore import QObject, Signal, QPointF

from pySimBlocks.gui.model import (
    BlockInstance,
    ConnectionInstance,
    PortInstance,
    ProjectState,
    port_instance,
)
from pySimBlocks.gui.widgets.diagram_view import DiagramView
from pySimBlocks.gui.blocks.block_meta import BlockMeta

if TYPE_CHECKING:
    from pySimBlocks.gui.services.project_loader import ProjectLoader


class ProjectController(QObject):

    dirty_changed: Signal = Signal(bool)

    def __init__(self,
                 project_state: ProjectState,
                 view: DiagramView,
                 resolve_block_meta: Callable[[str, str], BlockMeta]
    ):
        super().__init__()
        self.project_state = project_state
        self.resolve_block_meta = resolve_block_meta
        self.view = view

        self.is_dirty: bool = False

    # --------------------------------------------------------------------------
    # Blocks methods
    # --------------------------------------------------------------------------
    def add_block(self, category: str,
                  block_type: str,
                  block_layout: dict | None = None) -> BlockInstance:
        block_meta = self.resolve_block_meta(category, block_type)
        block_instance = BlockInstance(block_meta)
        return self._add_block(block_instance, block_layout)

    # ------------------------------------------------------------------
    def add_copy_block(self, block_instance: BlockInstance) -> BlockInstance:
        copy = BlockInstance.copy(block_instance)
        return self._add_block(copy)

    # ------------------------------------------------------------------
    def _add_block(self, block_instance: BlockInstance,
                   block_layout: dict | None = None) -> BlockInstance:
        self.make_dirty()
        block_instance.name = self.make_unique_name(block_instance.name)
        block_instance.resolve_ports()
        self.project_state.add_block(block_instance)
        self.view.add_block(block_instance, block_layout)

        return block_instance

    # ------------------------------------------------------------------
    def rename_block(self, block_instance: BlockInstance, new_name: str):
        old_name = block_instance.name

        if old_name == new_name:
            return

        self.make_dirty()
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

    # ------------------------------------------------------------------
    def update_block_param(self, block_instance: BlockInstance, params: dict[str, Any]):
        
        self.rename_block(block_instance, params.pop("name", block_instance.name))

        if params == block_instance.parameters:
            return

        block_instance.update_params(params)
        block_instance.resolve_ports()
        self._remove_connection_if_port_disapear(block_instance)
        self.view.refresh_block_port(block_instance)
        self.make_dirty()

    # ------------------------------------------------------------------
    def remove_block(self, block_instance: BlockInstance):
        self.make_dirty()

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

    # ------------------------------------------------------------------
    def make_unique_name(self, base_name: str) -> str:
        existing = {b.name for b in self.project_state.blocks}

        if base_name not in existing:
            return base_name

        i = 1
        while f"{base_name}_{i}" in existing:
            i += 1

        return f"{base_name}_{i}"

    # ------------------------------------------------------------------
    def is_name_available(self, name: str, current=None) -> bool:
        for b in self.project_state.blocks:
            if b is current:
                continue
            if b.name == name:
                return False
        return True

    # --------------------------------------------------------------------------
    # connection methods
    # --------------------------------------------------------------------------
    def add_connection(self,
                       port1: PortInstance,
                       port2: PortInstance,
                       points: list[QPointF] | None = None):

        if not port1.is_compatible(port2):
            return

        src_port, dst_port = (
            (port1, port2) if port1.direction == "output" else (port2, port1)
        )

        port_dst_connections = self.project_state.get_connections_of_port(dst_port)

        if not dst_port.can_accept_connection(port_dst_connections):
            return

        connection_instance = ConnectionInstance(src_port, dst_port)

        self.project_state.add_connection(connection_instance)
        self.view.add_connection(connection_instance, points)
        self.make_dirty()

    # ------------------------------------------------------------------

    def _remove_connection_if_port_disapear(self, block_instance: BlockInstance) -> None:
        
        for connection in self.project_state.get_connections_of_block(block_instance):

            src_exists = connection.src_port in connection.src_block().ports
            dst_exists = connection.dst_port in connection.dst_block().ports
            if not (src_exists and dst_exists):
                self.remove_connection(connection)

    # ------------------------------------------------------------------
    def remove_connection(self, connection: ConnectionInstance):

        self.project_state.remove_connection(connection)
        self.view.remove_connection(connection)
        self.make_dirty()

    # --------------------------------------------------------------------------
    # Project methods
    # --------------------------------------------------------------------------
    def make_dirty(self):
        if not self.is_dirty:
            self.is_dirty = True
            self.dirty_changed.emit(True)

    # ------------------------------------------------------------------
    def clear_dirty(self):
        if self.is_dirty:
            self.is_dirty = False
            self.dirty_changed.emit(False)

    # ------------------------------------------------------------------
    def clear(self):
        self.project_state.clear()
        self.view.clear_scene()

    # ------------------------------------------------------------------
    def update_project_param(self, new_path: Path, ext: str):
        if self.project_state.directory_path:
            temp = self.project_state.directory_path / ".temp"
            if temp.exists():
                shutil.rmtree(temp, ignore_errors=True)
        if new_path != self.project_state.directory_path:
            self.make_dirty()
        self.project_state.directory_path = new_path

        if ext != self.project_state.external:
            self.make_dirty()
        self.project_state.external = None if ext == "" else ext

    # ------------------------------------------------------------------
    def load_project(self, loader: 'ProjectLoader'):
        loader.load(self, self.project_state.directory_path)

    # --------------------------------------------------------------------------
    # Plot methods
    # --------------------------------------------------------------------------
    def create_plot(self, title: str, signals: list[str]) -> None:
        self._ensure_logged(signals)
        self.project_state.plots.append({
            "title": title,
            "signals": list(signals),
        })
        self.make_dirty()

    # ------------------------------------------------------------------
    def update_plot(self, index: int, title: str, signals: list[str]) -> None:
        self._ensure_logged(signals)
        plot = self.project_state.plots[index]
        if plot["signals"] == signals and plot["title"] == title:
            return
        plot["title"] = title
        plot["signals"] = list(signals)
        self.make_dirty()

    # ------------------------------------------------------------------
    def delete_plot(self, index: int) -> None:
        del self.project_state.plots[index]
        self.make_dirty()

    # ------------------------------------------------------------------
    def _ensure_logged(self, signals: list[str]):
        for sig in signals:
            if sig not in self.project_state.logging:
                self.project_state.logging.append(sig)

    # ------------------------------------------------------------------
    def update_simulation_params(self, params: dict[str, float | str]):
        if self.project_state.simulation.__dict__ == params:
            return
        self.project_state.load_simulation(params)
        self.make_dirty()

    # ------------------------------------------------------------------
    def set_logged_signals(self, signals: list[str]):
        new_logging = list(dict.fromkeys(signals))
        if set(self.project_state.logging) == set(new_logging):
            return
        self.project_state.logging = new_logging
        self.make_dirty()
