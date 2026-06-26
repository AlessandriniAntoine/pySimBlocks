# ******************************************************************************
#                                  pySimBlocks
#                     Copyright (c) 2026 Université de Lille & INRIA
# ******************************************************************************

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from pySimBlocks.gui.models.port_instance import PortInstance
from pySimBlocks.gui.models.visual_group import BoundaryPort, VisualGroup

if TYPE_CHECKING:
    from pySimBlocks.gui.models.connection_instance import ConnectionInstance
    from pySimBlocks.gui.models.project_state import ProjectState


def port_key(port: PortInstance) -> str:
    """Build a stable key for a simulation port."""
    return f"{port.block.uid}:{port.name}"


def parse_port_key(key: str) -> tuple[str, str] | None:
    if not key or ":" not in key:
        return None
    block_uid, port_name = key.split(":", 1)
    return block_uid, port_name


def find_port(state: ProjectState, key: str) -> PortInstance | None:
    parsed = parse_port_key(key)
    if parsed is None:
        return None
    block_uid, port_name = parsed
    for block in state.blocks:
        if block.uid != block_uid:
            continue
        for port in block.ports:
            if port.name == port_name:
                return port
    return None


def is_manual(boundary: BoundaryPort) -> bool:
    return boundary.origin == "manual"


def is_complete(boundary: BoundaryPort) -> bool:
    return bool(boundary.linked_connection_uid)


@dataclass
class BoundaryWiringState:
    """Snapshot of a manual boundary wiring state."""

    linked_port_uid: str = ""
    external_port_uid: str = ""
    linked_connection_uid: str = ""


def capture_wiring_state(boundary: BoundaryPort) -> BoundaryWiringState:
    return BoundaryWiringState(
        linked_port_uid=boundary.linked_port_uid,
        external_port_uid=boundary.external_port_uid,
        linked_connection_uid=boundary.linked_connection_uid,
    )


def apply_wiring_state(boundary: BoundaryPort, state: BoundaryWiringState) -> None:
    boundary.linked_port_uid = state.linked_port_uid
    boundary.external_port_uid = state.external_port_uid
    boundary.linked_connection_uid = state.linked_connection_uid


def validate_internal_link(
    group: VisualGroup,
    boundary: BoundaryPort,
    member_port: PortInstance,
    *,
    content_uids: set[str] | None = None,
) -> bool:
    """Return whether a member port may be wired to a boundary proxy."""
    if is_complete(boundary):
        return False
    scope = content_uids if content_uids is not None else set(group.members)
    if member_port.block.uid not in scope:
        return False
    if boundary.direction == "input" and member_port.direction != "input":
        return False
    if boundary.direction == "output" and member_port.direction != "output":
        return False
    return True


def validate_external_link(
    group: VisualGroup,
    boundary: BoundaryPort,
    external_port: PortInstance,
) -> bool:
    """Return whether an external port may be wired to a group border port."""
    if is_complete(boundary):
        return False
    if boundary.origin not in ("manual", "auto"):
        return False
    if external_port.block.uid in group.members:
        return False
    if boundary.direction == "input" and external_port.direction != "output":
        return False
    if boundary.direction == "output" and external_port.direction != "input":
        return False
    return True


def connection_endpoints(
    state: ProjectState,
    boundary: BoundaryPort,
) -> tuple[PortInstance, PortInstance] | None:
    """Return src/dst simulation ports when a manual boundary is ready to complete."""
    member_port = find_port(state, boundary.linked_port_uid)
    external_port = find_port(state, boundary.external_port_uid)
    if member_port is None or external_port is None:
        return None
    if boundary.direction == "input":
        return external_port, member_port
    return member_port, external_port


def can_complete(state: ProjectState, boundary: BoundaryPort) -> bool:
    if is_complete(boundary):
        return False
    if boundary.origin not in ("manual", "auto"):
        return False
    if not boundary.linked_port_uid or not boundary.external_port_uid:
        return False
    endpoints = connection_endpoints(state, boundary)
    if endpoints is None:
        return False
    src_port, dst_port = endpoints
    if not src_port.is_compatible(dst_port):
        return False
    return True


def connection_key(connection: ConnectionInstance) -> str:
    """Build a stable key for one diagram connection."""
    return (
        f"{connection.src_block().uid}:{connection.src_port.name}->"
        f"{connection.dst_block().uid}:{connection.dst_port.name}"
    )


def find_connection_for_boundary(
    state: ProjectState,
    boundary: BoundaryPort,
) -> ConnectionInstance | None:
    endpoints = connection_endpoints(state, boundary)
    if endpoints is not None:
        src_port, dst_port = endpoints
        for connection in state.connections:
            if connection.src_port is src_port and connection.dst_port is dst_port:
                return connection

    if boundary.linked_connection_uid:
        for connection in state.connections:
            if connection_key(connection) == boundary.linked_connection_uid:
                return connection
    return None
