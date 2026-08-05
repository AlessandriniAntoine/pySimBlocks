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
    if boundary.label.strip():
        return boundary.label.strip()
    return proxy_default_label(boundary)
