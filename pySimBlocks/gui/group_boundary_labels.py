# ******************************************************************************
#                                  pySimBlocks
#                     Copyright (c) 2026 Université de Lille & INRIA
# ******************************************************************************

from __future__ import annotations

from pySimBlocks.gui.services.group_boundary_service import (
    find_connection_for_boundary,
    find_port,
)
from pySimBlocks.gui.models.visual_group import BoundaryPort, VisualGroup


def _port_display(port) -> str:
    return str(port.display_as or port.name)


def proxy_default_label(boundary: BoundaryPort) -> str:
    """Return the default GroupIn/GroupOut name for one boundary direction."""
    return "In" if boundary.direction == "input" else "Out"


def manual_boundary_display_label(boundary: BoundaryPort) -> str:
    """Return the proxy name shown on the group border and inside the group."""
    if boundary.label.strip():
        return boundary.label.strip()
    return proxy_default_label(boundary)


def boundary_port_label(
    state: ProjectState,
    group: VisualGroup,
    boundary: BoundaryPort,
) -> str:
    """Return the label shown on a group border port."""
    if boundary.origin == "manual":
        return manual_boundary_display_label(boundary)
    if boundary.label.strip():
        return boundary.label.strip()

    internal = (
        find_port(state, boundary.linked_port_uid)
        if boundary.linked_port_uid
        else None
    )
    if internal is None:
        return ""

    connection = find_connection_for_boundary(state, boundary)
    if connection is None:
        return _port_display(internal)

    if boundary.direction == "input":
        return _port_display(connection.src_port)
    return _port_display(connection.dst_port)
