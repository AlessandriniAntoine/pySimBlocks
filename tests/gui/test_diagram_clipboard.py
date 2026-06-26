from PySide6.QtCore import QPointF

from pySimBlocks.gui.diagram_clipboard import (
    capture_groups_clipboard,
    capture_proxies_clipboard,
    capture_selection_clipboard,
    clipboard_has_content,
    paste_clipboard,
    undo_paste,
)
from pySimBlocks.gui.main_window import MainWindow


def _create_window(qtbot, tmp_path):
    window = MainWindow(tmp_path)
    window.confirm_discard_or_save = lambda _action_name: True
    qtbot.addWidget(window)
    window.show()
    qtbot.waitUntil(lambda: window.isVisible())
    return window


def _select_items(view, *items):
    view.diagram_scene.clearSelection()
    for item in items:
        item.setSelected(True)


def _first_port(block, direction: str):
    for port in block.ports:
        if port.direction == direction:
            return port
    raise AssertionError(f"No {direction} port on {block.name}")


def _nested_control_loop(controller):
    sum_err = controller.add_block("operators", "sum")
    controller_block = controller.add_block("controllers", "state_feedback")
    sum_plant = controller.add_block("operators", "sum")
    system = controller.add_block("systems", "linear_state_space")
    regulator = controller.group_blocks([sum_err, controller_block], name="Regulator")
    plant = controller.group_blocks([sum_plant, system], name="Plant")
    control_loop = controller.group_blocks(
        [],
        child_group_uids=[regulator.uid, plant.uid],
        name="ControlLoop",
    )
    return control_loop, regulator, plant, [sum_err, controller_block, sum_plant, system]


def test_copy_paste_nested_group_preserves_hierarchy(qtbot, tmp_path):
    window = _create_window(qtbot, tmp_path)
    controller = window.project_controller
    view = window.view

    control_loop, regulator, plant, blocks = _nested_control_loop(controller)
    _select_items(view, view.group_items[control_loop.uid])
    clipboard = capture_selection_clipboard(controller)
    assert clipboard is not None
    assert len(clipboard.groups) == 3
    assert set(clipboard.root_group_uids) == {control_loop.uid}

    origin = QPointF(
        float(control_loop.layout.get("x", 0.0)) + 120.0,
        float(control_loop.layout.get("y", 0.0)) + 80.0,
    )
    result = paste_clipboard(controller, clipboard, origin)
    assert len(result.group_uids) == 3
    assert len(result.blocks) == 4

    pasted_roots = [
        group
        for group in controller.project_state.visual_groups
        if group.uid in result.group_uids and group.parent_uid is None
    ]
    assert len(pasted_roots) == 1
    pasted_root = pasted_roots[0]
    assert len(pasted_root.child_group_uids) == 2

    child_names = {
        controller.project_state.get_visual_group(uid).name
        for uid in pasted_root.child_group_uids
    }
    assert child_names == {"Regulator_1", "Plant_1"}

    pasted_block_uids = {block.uid for block in result.blocks}
    for child_uid in pasted_root.child_group_uids:
        child = controller.project_state.get_visual_group(child_uid)
        assert child is not None
        assert set(child.members).issubset(pasted_block_uids)


def test_copy_paste_multiple_root_groups(qtbot, tmp_path):
    window = _create_window(qtbot, tmp_path)
    controller = window.project_controller
    view = window.view

    a = controller.add_block("sources", "constant")
    b = controller.add_block("operators", "gain")
    c = controller.add_block("operators", "sum")
    d = controller.add_block("operators", "gain")
    group_a = controller.group_blocks([a, b], name="GroupA")
    group_b = controller.group_blocks([c, d], name="GroupB")

    clipboard = capture_groups_clipboard(controller, [group_a.uid, group_b.uid])
    assert clipboard is not None
    assert set(clipboard.root_group_uids) == {group_a.uid, group_b.uid}
    assert len(clipboard.groups) == 2
    assert len(clipboard.blocks) == 4

    result = paste_clipboard(controller, clipboard, QPointF(400.0, 200.0))
    pasted_roots = [
        controller.project_state.get_visual_group(uid)
        for uid in result.group_uids
        if controller.project_state.get_visual_group(uid).parent_uid is None
    ]
    assert len(pasted_roots) == 2
    assert {group.name for group in pasted_roots} == {"GroupA_1", "GroupB_1"}


def test_copy_paste_blocks_only(qtbot, tmp_path):
    window = _create_window(qtbot, tmp_path)
    controller = window.project_controller
    view = window.view

    a = controller.add_block("sources", "constant")
    b = controller.add_block("operators", "gain")
    controller.add_connection(_first_port(a, "output"), _first_port(b, "input"))

    _select_items(view, view.get_block_item_from_instance(a), view.get_block_item_from_instance(b))
    clipboard = capture_selection_clipboard(controller)
    assert clipboard is not None
    assert not clipboard.groups
    assert len(clipboard.blocks) == 2
    assert len(clipboard.connections) == 1

    before_blocks = len(controller.project_state.blocks)
    result = paste_clipboard(controller, clipboard, QPointF(300.0, 100.0))
    assert len(controller.project_state.blocks) == before_blocks + 2
    assert len(result.connections) == 1


def test_paste_nested_group_undo(qtbot, tmp_path):
    window = _create_window(qtbot, tmp_path)
    controller = window.project_controller
    view = window.view

    control_loop, _regulator, _plant, member_blocks = _nested_control_loop(controller)
    clipboard = capture_groups_clipboard(controller, [control_loop.uid])
    result = paste_clipboard(controller, clipboard, QPointF(500.0, 300.0))

    assert len(controller.project_state.visual_groups) == 6
    assert len(controller.project_state.blocks) == 8

    undo_paste(controller, result)
    assert len(controller.project_state.visual_groups) == 3
    assert len(controller.project_state.blocks) == 4
    for block in member_blocks:
        assert controller._find_block_by_uid(block.uid) is not None


def test_paste_group_inside_parent_view(qtbot, tmp_path):
    window = _create_window(qtbot, tmp_path)
    controller = window.project_controller
    view = window.view

    a = controller.add_block("sources", "constant")
    b = controller.add_block("operators", "gain")
    c = controller.add_block("operators", "sum")
    inner = controller.group_blocks([a, b], name="Inner")
    parent = controller.group_blocks([c], child_group_uids=[inner.uid], name="Parent")

    clipboard = capture_groups_clipboard(controller, [inner.uid])
    view.enter_group(parent.uid)

    result = paste_clipboard(
        controller,
        clipboard,
        QPointF(200.0, 150.0),
        parent_group_uid=parent.uid,
    )
    pasted_groups = [
        controller.project_state.get_visual_group(uid) for uid in result.group_uids
    ]
    assert len(pasted_groups) == 1
    assert pasted_groups[0].parent_uid == parent.uid
    assert pasted_groups[0].uid in parent.child_group_uids


def test_copy_paste_manual_in_out_proxies(qtbot, tmp_path):
    window = _create_window(qtbot, tmp_path)
    controller = window.project_controller
    view = window.view

    a = controller.add_block("sources", "constant")
    b = controller.add_block("operators", "gain")
    group = controller.group_blocks([a, b], name="Group")
    view.enter_group(group.uid)

    first = controller.add_manual_boundary_port(group.uid, "input", QPointF(40.0, 50.0))
    second = controller.add_manual_boundary_port(group.uid, "output", QPointF(120.0, 50.0))
    _select_items(
        view,
        view.proxy_items[first.uid],
        view.proxy_items[second.uid],
    )

    clipboard = capture_selection_clipboard(controller)
    assert clipboard is not None
    assert clipboard_has_content(clipboard)
    assert len(clipboard.boundary_ports) == 2
    assert not clipboard.blocks

    manual_before = sum(
        1 for port in group.boundary_ports if port.origin == "manual"
    )
    result = paste_clipboard(controller, clipboard, QPointF(70.0, 80.0))
    assert len(result.boundary_ports) == 2

    group = controller.project_state.get_visual_group(group.uid)
    manual_after = [port for port in group.boundary_ports if port.origin == "manual"]
    assert len(manual_after) == manual_before + 2
    pasted_uids = {uid for _, uid in result.boundary_ports}
    pasted = sorted(
        [port for port in manual_after if port.uid in pasted_uids],
        key=lambda port: port.proxy_layout.get("x", 0.0),
    )
    assert {port.direction for port in pasted} == {"input", "output"}
    assert {port.label for port in pasted} == {"In_1", "Out_1"}
    assert pasted[0].proxy_layout["x"] == 70.0
    assert pasted[0].proxy_layout["y"] == 80.0
    assert pasted[1].proxy_layout["x"] == 150.0
    assert pasted[1].proxy_layout["y"] == 80.0
    assert all(port.uid in view.proxy_items for port in pasted)

    undo_paste(controller, result)
    group = controller.project_state.get_visual_group(group.uid)
    assert len([port for port in group.boundary_ports if port.origin == "manual"]) == manual_before


def test_copy_paste_proxy_with_member_block_preserves_internal_link(qtbot, tmp_path):
    window = _create_window(qtbot, tmp_path)
    controller = window.project_controller
    view = window.view

    a = controller.add_block("sources", "constant")
    b = controller.add_block("operators", "gain")
    group = controller.group_blocks([a, b], name="Group")
    view.enter_group(group.uid)

    boundary = controller.add_manual_boundary_port(group.uid, "input", QPointF(30.0, 40.0))
    gain_in = view.get_block_item_from_instance(b).get_port_item(_first_port(b, "input").name)
    assert controller.try_wire_boundary_endpoints(
        view.proxy_items[boundary.uid].port_item,
        gain_in,
    )

    _select_items(
        view,
        view.proxy_items[boundary.uid],
        view.get_block_item_from_instance(b),
    )
    clipboard = capture_selection_clipboard(controller)
    assert clipboard is not None
    assert len(clipboard.boundary_ports) == 1
    assert len(clipboard.blocks) == 1

    result = paste_clipboard(controller, clipboard, QPointF(60.0, 70.0))
    assert len(result.boundary_ports) == 1
    assert len(result.blocks) == 1

    pasted_boundary_uid = result.boundary_ports[0][1]
    pasted_block_uid = result.blocks[0].uid
    group = controller.project_state.get_visual_group(group.uid)
    pasted_boundary = next(
        port for port in group.boundary_ports if port.uid == pasted_boundary_uid
    )
    assert pasted_boundary.linked_port_uid == f"{pasted_block_uid}:{_first_port(b, 'input').name}"


def test_paste_proxies_requires_internal_group_view(qtbot, tmp_path):
    window = _create_window(qtbot, tmp_path)
    controller = window.project_controller
    view = window.view

    a = controller.add_block("sources", "constant")
    b = controller.add_block("operators", "gain")
    group = controller.group_blocks([a, b], name="Group")
    view.enter_group(group.uid)
    boundary = controller.add_manual_boundary_port(group.uid, "input", QPointF(20.0, 30.0))
    clipboard = capture_proxies_clipboard(controller, [view.proxy_items[boundary.uid]])
    view.exit_group_view()

    assert controller.paste_clipboard_at(QPointF(50.0, 60.0)) is False
    result = paste_clipboard(controller, clipboard, QPointF(50.0, 60.0), parent_group_uid=None)
    assert not result.boundary_ports
