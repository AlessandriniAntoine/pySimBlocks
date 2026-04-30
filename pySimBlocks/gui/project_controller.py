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

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Any, Callable

from PySide6.QtCore import QObject, Signal, QPointF, QRectF

from pySimBlocks.gui.models import (
    BlockInstance,
    ConnectionInstance,
    PortInstance,
    ProjectState,
)
from pySimBlocks.gui.widgets.diagram_view import DiagramView
from pySimBlocks.gui.blocks.block_meta import BlockMeta
from pySimBlocks.gui.services.yaml_tools import cleanup_runtime_project_yaml
from pySimBlocks.gui.undo_redo.undo_redo_manager import UndoManager
from pySimBlocks.gui.undo_redo.commands import (
    AddBlockCommand,
    AddConnectionCommand,
    EditBlockParamsCommand,
    MoveResizeBlockCommand,
    RemoveBlockCommand,
    RemoveConnectionCommand,
    ToggleOrientationCommand,
    ConnectionSnapshot,
)

if TYPE_CHECKING:
    from pySimBlocks.gui.services.project_loader import ProjectLoader


class ProjectController(QObject):
    """Controller coordinating all mutations to the project model and diagram view.

    Acts as the single point of truth for block and connection lifecycle
    operations, dirty-state tracking, plot management, and simulation parameter
    updates.

    Attributes:
        project_state: Shared mutable state of the open project.
        view: The diagram canvas widget.
        resolve_block_meta: Callable returning :class:`BlockMeta` for a given
            category and block type.
        is_dirty: True if there are unsaved changes.
    """

    #: Signal emitted with the new dirty flag value whenever the unsaved-changes state changes.
    dirty_changed: Signal = Signal(bool)

    def __init__(
        self,
        project_state: ProjectState,
        view: DiagramView,
        resolve_block_meta: Callable[[str, str], BlockMeta],
        undo_manager: UndoManager,
    ):
        """Initialize the ProjectController.

        Args:
            project_state: Shared project state to read and mutate.
            view: The diagram view to keep in sync with the model.
            resolve_block_meta: Callable returning :class:`BlockMeta` for a
                given ``(category, block_type)`` pair.
        """
        super().__init__()
        self.project_state = project_state
        self.resolve_block_meta = resolve_block_meta
        self.view = view
        self.undo_manager = undo_manager

        self.is_dirty: bool = False


    # --------------------------------------------------------------------------
    # Block methods
    # --------------------------------------------------------------------------

    def add_block(
        self,
        category: str,
        block_type: str,
        block_layout: dict | None = None,
    ) -> BlockInstance:
        """Create and add a new block of the given type to the project.

        Args:
            category: Category name of the block.
            block_type: Type name of the block within the category.
            block_layout: Optional dict with position/size hints for the view.

        Returns:
            The newly created :class:`BlockInstance`.
        """
        block_meta = self.resolve_block_meta(category, block_type)
        block_instance = BlockInstance(block_meta)
        self.undo_manager.push(AddBlockCommand(self, block_instance, block_layout))
        return block_instance

    def add_copy_block(self, block_instance: BlockInstance) -> BlockInstance:
        """Add a copy of an existing block to the project.

        Args:
            block_instance: The block to copy.

        Returns:
            The newly created copy as a :class:`BlockInstance`.
        """
        copy = BlockInstance.copy(block_instance)
        self.undo_manager.push(AddBlockCommand(self, copy))
        return copy

    def rename_block(self, block_instance: BlockInstance, new_name: str) -> None:
        """Rename a block and update all references in logging and plot signals.

        Args:
            block_instance: The block to rename.
            new_name: Desired new name. A unique suffix is appended if the name
                is already taken.
        """
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

    def update_block_param(self, block_instance: BlockInstance, params: dict[str, Any]) -> None:
        """Apply new parameter values to a block, refreshing ports and connections as needed.

        Args:
            block_instance: The block to update.
            params: New parameter dict. If a ``'name'`` key is present the
                block is also renamed.
        """
        self.undo_manager.push(EditBlockParamsCommand(self, block_instance, params))

    def remove_block(self, block_instance: BlockInstance) -> None:
        """Remove a block, its connections, and its signals from the project.

        Args:
            block_instance: The block to remove.
        """
        self.undo_manager.push(RemoveBlockCommand(self, block_instance))

    def make_unique_name(self, base_name: str) -> str:
        """Return ``base_name`` or a suffixed variant that is unique across all blocks.

        Args:
            base_name: Desired block name.

        Returns:
            ``base_name`` if available, otherwise ``base_name_N`` for the
            smallest N that is not already taken.
        """
        existing = {b.name for b in self.project_state.blocks}

        if base_name not in existing:
            return base_name

        i = 1
        while f"{base_name}_{i}" in existing:
            i += 1

        return f"{base_name}_{i}"

    def is_name_available(self, name: str, current=None) -> bool:
        """Return True if ``name`` is not already used by another block.

        Args:
            name: Name to check for availability.
            current: Block instance to exclude from the check (e.g. the block
                being renamed).

        Returns:
            True if the name is free, False if it is taken by another block.
        """
        for b in self.project_state.blocks:
            if b is current:
                continue
            if b.name == name:
                return False
        return True


    # --------------------------------------------------------------------------
    # Connection methods
    # --------------------------------------------------------------------------

    def add_connection(
        self,
        port1: PortInstance,
        port2: PortInstance,
        points: list[QPointF] | None = None,
    ) -> None:
        """Create a connection between two ports if compatible.

        The method silently returns without creating a connection if the ports
        are not compatible or if the destination port cannot accept another
        connection.

        Args:
            port1: First port (output or input).
            port2: Second port (input or output).
            points: Optional list of intermediate waypoints for the wire.
        """
        if not port1.is_compatible(port2):
            return
        src_port, dst_port = (
            (port1, port2) if port1.direction == "output" else (port2, port1)
        )
        port_dst_connections = self.project_state.get_connections_of_port(dst_port)
        if not dst_port.can_accept_connection(port_dst_connections):
            return
        self.undo_manager.push(AddConnectionCommand(self, src_port, dst_port, points))

    def remove_connection(self, connection: ConnectionInstance) -> None:
        """Remove a connection from both the model and the view.

        Args:
            connection: The :class:`ConnectionInstance` to remove.
        """
        self.undo_manager.push(RemoveConnectionCommand(self, connection))

    def execute_move_resize_block(
        self,
        block_instance: BlockInstance,
        old_pos: QPointF,
        old_rect: QRectF,
        new_pos: QPointF,
        new_rect: QRectF,
    ) -> None:
        self.undo_manager.push(
            MoveResizeBlockCommand(
                self, block_instance.uid, old_pos, old_rect, new_pos, new_rect
            )
        )

    def execute_toggle_orientation(self, block_instance: BlockInstance) -> None:
        block_item = self.view.get_block_item_from_instance(block_instance)
        if block_item is None:
            return
        old_orientation = block_item.orientation
        new_orientation = "flipped" if old_orientation == "normal" else "normal"
        self.undo_manager.push(
            ToggleOrientationCommand(self, block_instance.uid, old_orientation, new_orientation)
        )

    def begin_macro(self, text: str) -> None:
        self.undo_manager.stack.beginMacro(text)

    def end_macro(self) -> None:
        self.undo_manager.stack.endMacro()


    # --------------------------------------------------------------------------
    # Project methods
    # --------------------------------------------------------------------------

    def make_dirty(self) -> None:
        """Mark the project as having unsaved changes and emit :attr:`dirty_changed`."""
        if not self.is_dirty:
            self.is_dirty = True
            self.dirty_changed.emit(True)

    def clear_dirty(self) -> None:
        """Clear the unsaved-changes flag and emit :attr:`dirty_changed`."""
        if self.is_dirty:
            self.is_dirty = False
            self.dirty_changed.emit(False)

    def clear(self) -> None:
        """Reset the project state and diagram view to an empty state."""
        self.project_state.clear()
        self.view.clear_scene()
        self.undo_manager.clear()
        self.clear_dirty()

    def update_project_param(self, new_path: Path, ext: str) -> None:
        """Update the project directory path and external module reference.

        Args:
            new_path: New project directory path.
            ext: New external module path string, or ``''`` to clear it.
        """
        cleanup_runtime_project_yaml(self.project_state.directory_path)
        if new_path != self.project_state.directory_path:
            self.make_dirty()
        self.project_state.directory_path = new_path

        if ext != self.project_state.external:
            self.make_dirty()
        self.project_state.external = None if ext == "" else ext

    def load_project(self, loader: "ProjectLoader") -> None:
        """Delegate project loading to the given loader service.

        Args:
            loader: A :class:`ProjectLoader` implementation that reads the
                project files and populates this controller.
        """
        loader.load(self, self.project_state.directory_path)


    # --------------------------------------------------------------------------
    # Plot methods
    # --------------------------------------------------------------------------

    def create_plot(self, title: str, signals: list[str]) -> None:
        """Append a new plot to the project configuration.

        Args:
            title: Title of the plot figure.
            signals: List of signal names to display in the plot. Any signal
                not already logged is automatically added to the logging list.
        """
        self._ensure_logged(signals)
        self.project_state.plots.append({
            "title": title,
            "signals": list(signals),
        })
        self.make_dirty()

    def update_plot(self, index: int, title: str, signals: list[str]) -> None:
        """Update the title and signals of an existing plot.

        Args:
            index: Index of the plot in :attr:`ProjectState.plots`.
            title: New title for the plot.
            signals: New list of signal names. Any signal not yet logged is
                automatically added.
        """
        self._ensure_logged(signals)
        plot = self.project_state.plots[index]
        if plot["signals"] == signals and plot["title"] == title:
            return
        plot["title"] = title
        plot["signals"] = list(signals)
        self.make_dirty()

    def delete_plot(self, index: int) -> None:
        """Remove a plot by index.

        Args:
            index: Index of the plot in :attr:`ProjectState.plots`.
        """
        del self.project_state.plots[index]
        self.make_dirty()

    def update_simulation_params(self, params: dict[str, float | str]) -> None:
        """Apply new simulation parameters to the project state.

        Args:
            params: Dict of simulation parameters (e.g. ``dt``, ``T``).
        """
        if self.project_state.simulation.__dict__ == params:
            return
        self.project_state.load_simulation(params)
        self.make_dirty()

    def set_logged_signals(self, signals: list[str]) -> None:
        """Replace the logging list with ``signals``, preserving insertion order.

        Args:
            signals: New list of signal names to log. Duplicates are removed
                while preserving the first occurrence.
        """
        new_logging = list(dict.fromkeys(signals))
        if set(self.project_state.logging) == set(new_logging):
            return
        self.project_state.logging = new_logging
        self.make_dirty()


    # --------------------------------------------------------------------------
    # Private methods
    # --------------------------------------------------------------------------

    def _add_block(
        self,
        block_instance: BlockInstance,
        block_layout: dict | None = None,
    ) -> BlockInstance:
        """Register a block instance in the model and add its visual item to the view."""
        self.make_dirty()
        block_instance.name = self.make_unique_name(block_instance.name)
        block_instance.resolve_ports()
        self.project_state.add_block(block_instance)
        self.view.add_block(block_instance, block_layout)

        return block_instance

    def _remove_connection_if_port_disapear(self, block_instance: BlockInstance) -> list[ConnectionSnapshot]:
        """Remove any connection whose source or destination port no longer exists."""
        removed: list[ConnectionSnapshot] = []
        for connection in self.project_state.get_connections_of_block(block_instance):
            src_exists = connection.src_port in connection.src_block().ports
            dst_exists = connection.dst_port in connection.dst_block().ports
            if not (src_exists and dst_exists):
                removed.append(self._capture_connection_snapshot(connection))
                self._remove_connection(connection)
        return removed

    def _ensure_logged(self, signals: list[str]) -> None:
        """Append any signal not yet in the logging list."""
        for sig in signals:
            if sig not in self.project_state.logging:
                self.project_state.logging.append(sig)

    def _remove_block(self, block_instance: BlockInstance) -> None:
        for connection in list(self.project_state.get_connections_of_block(block_instance)):
            self._remove_connection(connection)

        removed_signals = [
            f"{block_instance.name}.outputs.{p.name}"
            for p in block_instance.ports if p.direction == "output"
        ]
        self.project_state.logging = [s for s in self.project_state.logging if s not in removed_signals]

        for i in reversed(range(len(self.project_state.plots))):
            plot = self.project_state.plots[i]
            plot["signals"] = [s for s in plot["signals"] if s not in removed_signals]
            if not plot["signals"]:
                del self.project_state.plots[i]

        self.project_state.remove_block(block_instance)
        self.view.remove_block(block_instance)

    def _remove_connection(self, connection: ConnectionInstance) -> None:
        self.project_state.remove_connection(connection)
        self.view.remove_connection(connection)

    def _find_block_by_uid(self, block_uid: str) -> BlockInstance | None:
        for block in self.project_state.blocks:
            if block.uid == block_uid:
                return block
        return None

    def _find_port(self, block_uid: str, port_name: str) -> PortInstance | None:
        block = self._find_block_by_uid(block_uid)
        if block is None:
            return None
        for port in block.ports:
            if port.name == port_name:
                return port
        return None

    def _capture_block_layout(self, block_instance: BlockInstance) -> dict:
        block_item = self.view.get_block_item_from_instance(block_instance)
        if block_item is None:
            return {}
        pos = block_item.pos()
        rect = block_item.rect()
        return {
            "x": float(pos.x()),
            "y": float(pos.y()),
            "orientation": block_item.orientation,
            "width": float(rect.width()),
            "height": float(rect.height()),
        }

    def _capture_connection_snapshot(self, connection: ConnectionInstance) -> ConnectionSnapshot:
        points: list[QPointF] | None = None
        connection_item = self.view.connections.get(connection)
        if (
            connection_item is not None
            and connection_item.is_manual
            and connection_item.route is not None
        ):
            points = [QPointF(p) for p in connection_item.route.points]
        return ConnectionSnapshot(
            src_block_uid=connection.src_block().uid,
            src_port_name=connection.src_port.name,
            dst_block_uid=connection.dst_block().uid,
            dst_port_name=connection.dst_port.name,
            points=points,
        )

    def _add_connection_from_snapshot(self, snapshot: ConnectionSnapshot) -> ConnectionInstance | None:
        src_port = self._find_port(snapshot.src_block_uid, snapshot.src_port_name)
        dst_port = self._find_port(snapshot.dst_block_uid, snapshot.dst_port_name)
        if src_port is None or dst_port is None:
            return None
        if not src_port.is_compatible(dst_port):
            return None
        if not dst_port.can_accept_connection(self.project_state.get_connections_of_port(dst_port)):
            return None
        connection_instance = ConnectionInstance(src_port, dst_port)
        self.project_state.add_connection(connection_instance)
        self.view.add_connection(connection_instance, snapshot.points)
        return connection_instance

    def _set_block_geometry(self, block_uid: str, pos: QPointF, rect: QRectF) -> None:
        block = self._find_block_by_uid(block_uid)
        if block is None:
            return
        block_item = self.view.get_block_item_from_instance(block)
        if block_item is None:
            return
        block_item.setPos(QPointF(pos))
        block_item.setRect(0, 0, rect.width(), rect.height())
        block_item._layout_ports()
        self.view.on_block_moved(block_item)

    def _set_block_orientation(self, block_uid: str, orientation: str) -> None:
        block = self._find_block_by_uid(block_uid)
        if block is None:
            return
        block_item = self.view.get_block_item_from_instance(block)
        if block_item is None:
            return
        block_item.set_orientation(orientation)
        self.view.on_block_moved(block_item)

    def _apply_block_update(
        self,
        block_instance: BlockInstance,
        new_name: str,
        params: dict[str, Any],
    ) -> list[ConnectionSnapshot]:
        old_name = block_instance.name
        if old_name != new_name:
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

        if params != block_instance.parameters:
            block_instance.update_params(params)
            block_instance.resolve_ports()
            removed = self._remove_connection_if_port_disapear(block_instance)
            self.view.refresh_block_port(block_instance)
            return removed
        return []
