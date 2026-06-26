# ******************************************************************************
#                                  pySimBlocks
#                     Copyright (c) 2026 Université de Lille & INRIA
# ******************************************************************************

from __future__ import annotations

import copy
import uuid
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

from PySide6.QtCore import QPointF

from pySimBlocks.gui.models.block_instance import BlockInstance
from pySimBlocks.gui.models.visual_group import BoundaryPort, VisualGroup
from pySimBlocks.gui.undo_redo.commands import ConnectionSnapshot

if TYPE_CHECKING:
    from pySimBlocks.gui.graphics.block_item import BlockItem
    from pySimBlocks.gui.project_controller import ProjectController


@dataclass
class ClipboardBlock:
    """Serializable block data for copy/paste."""

    source_uid: str
    category: str
    block_type: str
    name: str
    parameters: dict[str, Any]
    layout: dict[str, Any]


@dataclass
class ClipboardBoundaryPort:
    """Serializable GroupIn/GroupOut proxy for copy/paste."""

    source_uid: str
    direction: str
    label: str
    layout: dict[str, Any]
    linked_port_uid: str = ""
    external_port_uid: str = ""


@dataclass
class DiagramClipboard:
    """In-memory clipboard for diagram selections."""

    blocks: list[ClipboardBlock] = field(default_factory=list)
    connections: list[ConnectionSnapshot] = field(default_factory=list)
    groups: list[dict[str, Any]] = field(default_factory=list)
    root_group_uids: list[str] = field(default_factory=list)
    boundary_ports: list[ClipboardBoundaryPort] = field(default_factory=list)
    anchor_x: float = 0.0
    anchor_y: float = 0.0


def clipboard_has_content(clipboard: DiagramClipboard | None) -> bool:
    """Return whether a clipboard carries pasteable diagram data."""
    if clipboard is None:
        return False
    return bool(clipboard.blocks or clipboard.groups or clipboard.boundary_ports)


@dataclass
class PasteResult:
    """Entities created by a paste operation (for undo)."""

    blocks: list[BlockInstance] = field(default_factory=list)
    connections: list = field(default_factory=list)
    group_uids: list[str] = field(default_factory=list)
    boundary_ports: list[tuple[str, str]] = field(default_factory=list)


def _layout_anchor(layouts: list[dict[str, Any]]) -> tuple[float, float]:
    if not layouts:
        return 0.0, 0.0
    return (
        min(float(layout.get("x", 0.0)) for layout in layouts),
        min(float(layout.get("y", 0.0)) for layout in layouts),
    )


def _offset_layout(layout: dict[str, Any], dx: float, dy: float) -> dict[str, Any]:
    out = dict(layout)
    out["x"] = float(out.get("x", 0.0)) + dx
    out["y"] = float(out.get("y", 0.0)) + dy
    return out


def _collect_subgroup_uids_postorder(
    controller: ProjectController,
    group_uid: str,
) -> list[str]:
    """Return group uids in a subtree, children before parents."""
    group = controller.project_state.get_visual_group(group_uid)
    if group is None:
        return []
    ordered: list[str] = []
    for child_uid in group.child_group_uids:
        ordered.extend(_collect_subgroup_uids_postorder(controller, child_uid))
    ordered.append(group_uid)
    return ordered


def _root_groups_in_selection(
    controller: ProjectController,
    group_uids: set[str],
) -> list[str]:
    """Return selected groups whose parent is outside the selection."""
    roots: list[str] = []
    for uid in group_uids:
        group = controller.project_state.get_visual_group(uid)
        if group is None:
            continue
        if group.parent_uid not in group_uids:
            roots.append(uid)
    return roots


def _ordered_group_uids(
    controller: ProjectController,
    root_group_uids: list[str],
) -> list[str]:
    """Collect subtrees from several roots without duplicates (post-order)."""
    ordered: list[str] = []
    seen: set[str] = set()
    for root_uid in root_group_uids:
        for group_uid in _collect_subgroup_uids_postorder(controller, root_uid):
            if group_uid in seen:
                continue
            ordered.append(group_uid)
            seen.add(group_uid)
    return ordered


def _capture_internal_connections(
    controller: ProjectController,
    member_uids: set[str],
) -> list[ConnectionSnapshot]:
    connections: list[ConnectionSnapshot] = []
    for connection in controller.project_state.connections:
        src_uid = connection.src_block().uid
        dst_uid = connection.dst_block().uid
        if src_uid in member_uids and dst_uid in member_uids:
            connections.append(controller._capture_connection_snapshot(connection))
    return connections


def _block_uids_in_group_templates(templates: list[dict[str, Any]]) -> set[str]:
    return {
        uid
        for template in templates
        for uid in template.get("members", [])
    }


def capture_blocks_clipboard(
    controller: ProjectController,
    block_items: list[BlockItem],
) -> DiagramClipboard | None:
    """Capture selected blocks and their internal connections."""
    if not block_items:
        return None

    member_uids = {item.instance.uid for item in block_items}
    blocks: list[ClipboardBlock] = []
    layouts: list[dict[str, Any]] = []

    for item in block_items:
        instance = item.instance
        layout = controller._capture_block_layout(instance)
        layouts.append(layout)
        blocks.append(
            ClipboardBlock(
                source_uid=instance.uid,
                category=instance.meta.category,
                block_type=instance.meta.type,
                name=instance.name,
                parameters=instance.parameters.copy(),
                layout=layout,
            )
        )

    anchor_x, anchor_y = _layout_anchor(layouts)
    return DiagramClipboard(
        blocks=blocks,
        connections=_capture_internal_connections(controller, member_uids),
        anchor_x=anchor_x,
        anchor_y=anchor_y,
    )


def capture_groups_clipboard(
    controller: ProjectController,
    selected_group_uids: list[str],
) -> DiagramClipboard | None:
    """Capture one or more visual groups with nested children and internal wiring."""
    if not selected_group_uids:
        return None

    selected_set = set(selected_group_uids)
    root_group_uids = _root_groups_in_selection(controller, selected_set)
    ordered_group_uids = _ordered_group_uids(controller, root_group_uids)
    if not ordered_group_uids:
        return None

    blocks: list[ClipboardBlock] = []
    seen_block_uids: set[str] = set()
    anchor_layouts: list[dict[str, Any]] = []

    for group_uid in ordered_group_uids:
        group = controller.project_state.get_visual_group(group_uid)
        if group is None:
            continue
        for member_uid in group.members:
            if member_uid in seen_block_uids:
                continue
            block = controller._find_block_by_uid(member_uid)
            if block is None:
                continue
            layout = dict(group.member_layouts.get(member_uid, {}))
            if not layout:
                layout = controller._capture_block_layout(block)
            seen_block_uids.add(member_uid)
            blocks.append(
                ClipboardBlock(
                    source_uid=block.uid,
                    category=block.meta.category,
                    block_type=block.meta.type,
                    name=block.name,
                    parameters=block.parameters.copy(),
                    layout=layout,
                )
            )

    for root_uid in root_group_uids:
        root = controller.project_state.get_visual_group(root_uid)
        if root is None:
            continue
        if root.layout:
            anchor_layouts.append(dict(root.layout))
        else:
            member_layouts = [
                dict(root.member_layouts.get(uid, {}))
                for uid in root.members
                if uid in root.member_layouts
            ]
            if member_layouts:
                anchor_layouts.extend(member_layouts)

    if not blocks and not ordered_group_uids:
        return None

    anchor_x, anchor_y = _layout_anchor(anchor_layouts)
    groups = [
        copy.deepcopy(controller.project_state.get_visual_group(group_uid).to_dict())
        for group_uid in ordered_group_uids
        if controller.project_state.get_visual_group(group_uid) is not None
    ]

    return DiagramClipboard(
        blocks=blocks,
        connections=_capture_internal_connections(controller, seen_block_uids),
        groups=groups,
        root_group_uids=root_group_uids,
        anchor_x=anchor_x,
        anchor_y=anchor_y,
    )


def capture_group_clipboard(
    controller: ProjectController,
    group: VisualGroup,
) -> DiagramClipboard | None:
    """Capture a visual group, its descendants, and internal connections."""
    return capture_groups_clipboard(controller, [group.uid])


def _capture_mixed_selection_clipboard(
    controller: ProjectController,
    selected_group_uids: list[str],
    block_items: list[BlockItem],
) -> DiagramClipboard | None:
    """Capture selected groups (full subtrees) plus standalone blocks."""
    group_clipboard = capture_groups_clipboard(controller, selected_group_uids)
    selected_set = set(selected_group_uids)
    grouped_block_uids: set[str] = set()
    for group_uid in selected_set:
        group = controller.project_state.get_visual_group(group_uid)
        if group is None:
            continue
        grouped_block_uids.update(controller._group_content_uids_for_group(group))

    standalone_items = [
        item for item in block_items if item.instance.uid not in grouped_block_uids
    ]
    if group_clipboard is None and not standalone_items:
        return None
    if group_clipboard is None:
        return capture_blocks_clipboard(controller, standalone_items)

    if not standalone_items:
        return group_clipboard

    block_clipboard = capture_blocks_clipboard(controller, standalone_items)
    if block_clipboard is None:
        return group_clipboard

    all_member_uids = {
        block.source_uid for block in group_clipboard.blocks + block_clipboard.blocks
    }
    anchor_layouts = [
        dict(block.layout)
        for block in block_clipboard.blocks
    ]
    for root_uid in group_clipboard.root_group_uids:
        root = controller.project_state.get_visual_group(root_uid)
        if root is not None and root.layout:
            anchor_layouts.append(dict(root.layout))

    anchor_x, anchor_y = _layout_anchor(anchor_layouts)
    return DiagramClipboard(
        blocks=group_clipboard.blocks + block_clipboard.blocks,
        connections=_capture_internal_connections(controller, all_member_uids),
        groups=group_clipboard.groups,
        root_group_uids=group_clipboard.root_group_uids,
        anchor_x=anchor_x,
        anchor_y=anchor_y,
    )


def _selected_proxy_items(selected) -> list:
    """Return unique GroupProxyItem instances from a scene selection."""
    from pySimBlocks.gui.graphics.group_proxy_item import GroupProxyItem, GroupProxyPortItem

    proxies: list[GroupProxyItem] = []
    seen: set[str] = set()
    for item in selected:
        if isinstance(item, GroupProxyPortItem):
            item = item.parent_proxy
        if not isinstance(item, GroupProxyItem):
            continue
        if item.boundary.uid in seen:
            continue
        seen.add(item.boundary.uid)
        proxies.append(item)
    return proxies


def capture_proxies_clipboard(
    controller: ProjectController,
    proxy_items: list,
) -> DiagramClipboard | None:
    """Capture selected GroupIn/GroupOut proxies from the active internal view."""
    if not proxy_items or controller.view.current_view_group_uid is None:
        return None

    boundary_ports: list[ClipboardBoundaryPort] = []
    layouts: list[dict[str, Any]] = []
    for proxy in proxy_items:
        boundary = proxy.boundary
        layout = dict(boundary.proxy_layout) if boundary.proxy_layout else {
            "x": float(proxy.pos().x()),
            "y": float(proxy.pos().y()),
        }
        layouts.append(layout)
        linked_port_uid = ""
        external_port_uid = ""
        if boundary.origin == "manual" and not boundary.linked_connection_uid:
            linked_port_uid = boundary.linked_port_uid
            external_port_uid = boundary.external_port_uid
        boundary_ports.append(
            ClipboardBoundaryPort(
                source_uid=boundary.uid,
                direction=boundary.direction,
                label=boundary.label,
                layout=layout,
                linked_port_uid=linked_port_uid,
                external_port_uid=external_port_uid,
            )
        )

    anchor_x, anchor_y = _layout_anchor(layouts)
    return DiagramClipboard(
        boundary_ports=boundary_ports,
        anchor_x=anchor_x,
        anchor_y=anchor_y,
    )


def capture_selection_clipboard(controller: ProjectController) -> DiagramClipboard | None:
    """Capture the current diagram selection for copy."""
    from pySimBlocks.gui.graphics.block_item import BlockItem
    from pySimBlocks.gui.graphics.group_item import GroupItem

    selected = controller.view.diagram_scene.selectedItems()
    groups = [item for item in selected if isinstance(item, GroupItem)]
    blocks = [item for item in selected if isinstance(item, BlockItem)]
    proxies = _selected_proxy_items(selected)

    if groups and blocks:
        clipboard = _capture_mixed_selection_clipboard(
            controller,
            [item.group.uid for item in groups],
            blocks,
        )
    elif groups:
        clipboard = capture_groups_clipboard(controller, [item.group.uid for item in groups])
    elif blocks:
        clipboard = capture_blocks_clipboard(controller, blocks)
    elif proxies:
        clipboard = capture_proxies_clipboard(controller, proxies)
    else:
        return None

    if clipboard is None:
        return None
    if not proxies:
        return clipboard

    proxy_clipboard = capture_proxies_clipboard(controller, proxies)
    if proxy_clipboard is None:
        return clipboard

    anchor_layouts = [
        dict(port.layout) for port in proxy_clipboard.boundary_ports
    ]
    for block in clipboard.blocks:
        anchor_layouts.append(dict(block.layout))
    for root_uid in clipboard.root_group_uids:
        root = controller.project_state.get_visual_group(root_uid)
        if root is not None and root.layout:
            anchor_layouts.append(dict(root.layout))

    anchor_x, anchor_y = _layout_anchor(anchor_layouts)
    clipboard.boundary_ports = proxy_clipboard.boundary_ports
    clipboard.anchor_x = anchor_x
    clipboard.anchor_y = anchor_y
    return clipboard


def _remap_connection(
    snapshot: ConnectionSnapshot,
    uid_map: dict[str, str],
    dx: float = 0.0,
    dy: float = 0.0,
) -> ConnectionSnapshot | None:
    if snapshot.src_block_uid not in uid_map or snapshot.dst_block_uid not in uid_map:
        return None
    points: list[QPointF] | None = None
    if snapshot.points:
        points = [QPointF(point.x() + dx, point.y() + dy) for point in snapshot.points]
    return ConnectionSnapshot(
        src_block_uid=uid_map[snapshot.src_block_uid],
        src_port_name=snapshot.src_port_name,
        dst_block_uid=uid_map[snapshot.dst_block_uid],
        dst_port_name=snapshot.dst_port_name,
        points=points,
    )


def _duplicate_group(
    controller: ProjectController,
    template: dict[str, Any],
    uid_map: dict[str, str],
    gid_map: dict[str, str],
    dx: float,
    dy: float,
) -> VisualGroup:
    group = VisualGroup.from_dict(copy.deepcopy(template))
    group.uid = uuid.uuid4().hex
    group.name = controller._make_unique_group_name(group.name)
    group.parent_uid = None
    group.members = [uid_map[uid] for uid in template.get("members", []) if uid in uid_map]
    group.child_group_uids = [
        gid_map[uid] for uid in template.get("child_group_uids", []) if uid in gid_map
    ]

    member_layouts: dict[str, dict[str, Any]] = {}
    for old_uid, layout in (template.get("member_layouts") or {}).items():
        if old_uid not in uid_map:
            continue
        member_layouts[uid_map[old_uid]] = dict(layout)
    group.member_layouts = member_layouts

    if group.layout:
        group.layout = _offset_layout(dict(group.layout), dx, dy)

    new_boundaries: list[BoundaryPort] = []
    for boundary in group.boundary_ports:
        remapped = BoundaryPort(
            uid=uuid.uuid4().hex,
            direction=boundary.direction,
            linked_port_uid="",
            external_port_uid="",
            origin=boundary.origin,
            linked_connection_uid="",
            label=boundary.label,
            proxy_uid=uuid.uuid4().hex,
            proxy_layout=dict(boundary.proxy_layout) if boundary.proxy_layout else {},
        )
        if boundary.linked_port_uid and ":" in boundary.linked_port_uid:
            old_uid, port_name = boundary.linked_port_uid.split(":", 1)
            if old_uid in uid_map:
                remapped.linked_port_uid = f"{uid_map[old_uid]}:{port_name}"
        new_boundaries.append(remapped)
    group.boundary_ports = new_boundaries

    controller.project_state.visual_groups.append(group)
    controller._rebuild_group_boundary_ports(group)
    controller.ensure_group_boundary_proxies(group)
    return group


def _paste_boundary_label(
    controller: ProjectController,
    group: VisualGroup,
    port_data: ClipboardBoundaryPort,
) -> str:
    """Choose a unique label for a pasted GroupIn/GroupOut."""
    preferred = port_data.label.strip() or controller._proxy_default_label(port_data.direction)
    used: set[str] = set()
    for port in group.boundary_ports:
        if port.origin != "manual" or port.direction != port_data.direction:
            continue
        name = port.label.strip() or controller._proxy_default_label(port.direction)
        used.add(name)
    if preferred not in used:
        return preferred
    index = 1
    while f"{preferred}_{index}" in used:
        index += 1
    return f"{preferred}_{index}"


def _paste_boundary_ports(
    controller: ProjectController,
    clipboard: DiagramClipboard,
    origin: QPointF,
    uid_map: dict[str, str],
    *,
    parent_group_uid: str | None,
    result: PasteResult,
) -> None:
    """Create GroupIn/GroupOut proxies from clipboard boundary ports."""
    if not clipboard.boundary_ports or parent_group_uid is None:
        return

    group = controller.project_state.get_visual_group(parent_group_uid)
    if group is None:
        return

    dx = float(origin.x()) - clipboard.anchor_x
    dy = float(origin.y()) - clipboard.anchor_y
    for port_data in clipboard.boundary_ports:
        layout = _offset_layout(dict(port_data.layout), dx, dy)
        boundary = BoundaryPort(
            uid=uuid.uuid4().hex,
            direction=port_data.direction,
            origin="manual",
            label=_paste_boundary_label(controller, group, port_data),
            proxy_uid=uuid.uuid4().hex,
            proxy_layout=layout,
        )
        if port_data.linked_port_uid and ":" in port_data.linked_port_uid:
            old_uid, port_name = port_data.linked_port_uid.split(":", 1)
            if old_uid in uid_map:
                boundary.linked_port_uid = f"{uid_map[old_uid]}:{port_name}"
        if port_data.external_port_uid and ":" in port_data.external_port_uid:
            old_uid, port_name = port_data.external_port_uid.split(":", 1)
            if old_uid in uid_map:
                boundary.external_port_uid = f"{uid_map[old_uid]}:{port_name}"
        controller._add_manual_boundary_port(parent_group_uid, boundary)
        result.boundary_ports.append((parent_group_uid, boundary.uid))


def paste_clipboard(
    controller: ProjectController,
    clipboard: DiagramClipboard,
    origin: QPointF,
    *,
    parent_group_uid: str | None = None,
) -> PasteResult:
    """Paste clipboard contents at ``origin`` without pushing undo."""
    result = PasteResult()
    if not clipboard_has_content(clipboard):
        return result

    dx = float(origin.x()) - clipboard.anchor_x
    dy = float(origin.y()) - clipboard.anchor_y
    uid_map: dict[str, str] = {}
    has_groups = bool(clipboard.groups)
    grouped_source_uids = _block_uids_in_group_templates(clipboard.groups)

    for block_data in clipboard.blocks:
        meta = controller.resolve_block_meta(block_data.category, block_data.block_type)
        block = BlockInstance(meta)
        block.parameters = block_data.parameters.copy()
        block.name = block_data.name
        if has_groups and block_data.source_uid in grouped_source_uids:
            layout = dict(block_data.layout)
        else:
            layout = _offset_layout(block_data.layout, dx, dy)
        created = controller._add_block(block, layout)
        uid_map[block_data.source_uid] = created.uid
        result.blocks.append(created)
        if (
            parent_group_uid is not None
            and (not has_groups or block_data.source_uid not in grouped_source_uids)
        ):
            controller._add_member_to_group(parent_group_uid, created.uid, layout)

    connection_offset_dx = 0.0 if has_groups else dx
    connection_offset_dy = 0.0 if has_groups else dy
    for snapshot in clipboard.connections:
        remapped = _remap_connection(
            snapshot,
            uid_map,
            connection_offset_dx,
            connection_offset_dy,
        )
        if remapped is None:
            continue
        connection = controller._add_connection_from_snapshot(remapped)
        if connection is not None:
            result.connections.append(connection)

    gid_map: dict[str, str] = {}
    created_groups: list[tuple[dict[str, Any], VisualGroup]] = []
    for template in clipboard.groups:
        old_uid = str(template["uid"])
        root_offset_dx = dx if old_uid in clipboard.root_group_uids else 0.0
        root_offset_dy = dy if old_uid in clipboard.root_group_uids else 0.0
        group = _duplicate_group(
            controller,
            template,
            uid_map,
            gid_map,
            root_offset_dx,
            root_offset_dy,
        )
        gid_map[old_uid] = group.uid
        created_groups.append((template, group))
        result.group_uids.append(group.uid)

    for template, group in created_groups:
        old_uid = str(template["uid"])
        parent_old = template.get("parent_uid")
        if parent_old and parent_old in gid_map:
            group.parent_uid = gid_map[str(parent_old)]
            controller._attach_group_to_parent(group)
        elif old_uid in clipboard.root_group_uids:
            group.parent_uid = parent_group_uid
            if parent_group_uid is not None:
                controller._attach_group_to_parent(group)

    target_group_uid = parent_group_uid
    if target_group_uid is None and clipboard.boundary_ports:
        target_group_uid = controller.view.current_view_group_uid

    _paste_boundary_ports(
        controller,
        clipboard,
        origin,
        uid_map,
        parent_group_uid=target_group_uid,
        result=result,
    )

    controller.view.refresh_visual_groups()
    return result


def undo_paste(controller: ProjectController, result: PasteResult) -> None:
    """Remove entities created by a paste operation."""
    for group_uid, boundary_uid in reversed(result.boundary_ports):
        controller._remove_boundary_port(group_uid, boundary_uid)

    for group_uid in reversed(result.group_uids):
        if group_uid in controller.view.view_stack:
            controller.view.navigate_out_of_group(group_uid)
        controller._remove_visual_group(group_uid)

    for connection in list(result.connections):
        controller._remove_connection(connection, refresh_boundaries=False)

    for block in list(result.blocks):
        controller._remove_block(block)

    controller.view.refresh_visual_groups()
