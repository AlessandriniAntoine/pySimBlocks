from PySide6.QtCore import QPointF, QRectF, Qt

from pySimBlocks.gui.main_window import MainWindow


def _create_window(qtbot, tmp_path):
    window = MainWindow(tmp_path)
    window.confirm_discard_or_save = lambda _action_name: True
    qtbot.addWidget(window)
    window.show()
    qtbot.waitUntil(lambda: window.isVisible())
    return window


def _first_port(block, direction: str):
    for port in block.ports:
        if port.direction == direction:
            return port
    raise AssertionError(f"No port with direction={direction} for block {block.name}")


def test_group_hides_members_and_shows_group_item(qtbot, tmp_path):
    window = _create_window(qtbot, tmp_path)
    controller = window.project_controller
    view = window.view

    src = controller.add_block("sources", "constant")
    gain = controller.add_block("operators", "gain")
    out = controller.add_block("operators", "sum")
    controller.add_connection(_first_port(src, "output"), _first_port(gain, "input"))
    controller.add_connection(_first_port(gain, "output"), _first_port(out, "input"))

    group = controller.group_blocks([src, gain])
    view.refresh_visual_groups()

    assert group is not None
    assert len(view.group_items) == 1
    group_item = view.group_items[group.uid]
    assert group_item.isVisible()

    src_item = view.get_block_item_from_instance(src)
    gain_item = view.get_block_item_from_instance(gain)
    out_item = view.get_block_item_from_instance(out)
    assert not src_item.isVisible()
    assert not gain_item.isVisible()
    assert out_item.isVisible()


def test_group_captures_member_layouts_and_internal_view_applies_them(qtbot, tmp_path):
    window = _create_window(qtbot, tmp_path)
    controller = window.project_controller
    view = window.view

    a = controller.add_block("sources", "constant")
    b = controller.add_block("operators", "gain")
    item_a = view.get_block_item_from_instance(a)
    item_b = view.get_block_item_from_instance(b)
    item_a.setPos(100.0, 50.0)
    item_b.setPos(200.0, 80.0)

    group = controller.group_blocks([a, b])
    assert group is not None
    assert group.member_layouts[a.uid]["x"] == 100.0
    assert group.member_layouts[b.uid]["x"] == 200.0

    item_a.setPos(999.0, 999.0)
    view.enter_group(group.uid)
    assert item_a.pos().x() == 100.0
    assert item_b.pos().x() == 200.0

    item_a.setPos(120.0, 60.0)
    view.exit_group_view()
    assert group.member_layouts[a.uid]["x"] == 120.0


def test_double_click_enters_group_view(qtbot, tmp_path):
    window = _create_window(qtbot, tmp_path)
    controller = window.project_controller
    view = window.view

    a = controller.add_block("sources", "constant")
    b = controller.add_block("operators", "gain")
    group = controller.group_blocks([a, b])
    view.refresh_visual_groups()

    view.enter_group(group.uid)
    assert view.current_view_group_uid == group.uid
    assert view.get_block_item_from_instance(a).isVisible()
    assert view.get_block_item_from_instance(b).isVisible()
    assert not view.group_items[group.uid].isVisible()


def test_keyboard_shortcut_groups_selection(qtbot, tmp_path):
    window = _create_window(qtbot, tmp_path)
    controller = window.project_controller
    view = window.view

    a = controller.add_block("sources", "constant")
    b = controller.add_block("operators", "gain")
    item_a = view.get_block_item_from_instance(a)
    item_b = view.get_block_item_from_instance(b)
    item_a.setSelected(True)
    item_b.setSelected(True)

    view.setFocus()
    qtbot.waitUntil(lambda: view.hasFocus())
    qtbot.keyClick(view.viewport(), Qt.Key_G, Qt.ControlModifier | Qt.ShiftModifier)

    assert len(controller.project_state.visual_groups) == 1


def test_keyboard_shortcut_ungroups_selection(qtbot, tmp_path):
    window = _create_window(qtbot, tmp_path)
    controller = window.project_controller
    view = window.view

    a = controller.add_block("sources", "constant")
    b = controller.add_block("operators", "gain")
    group = controller.group_blocks([a, b])
    view.refresh_visual_groups()

    group_item = view.group_items[group.uid]
    view.diagram_scene.clearSelection()
    group_item.setSelected(True)
    view.setFocus()
    qtbot.waitUntil(lambda: view.hasFocus())
    qtbot.keyClick(view.viewport(), Qt.Key_U, Qt.ControlModifier | Qt.ShiftModifier)

    assert controller.project_state.visual_groups == []
    assert view.get_block_item_from_instance(a).isVisible()
    assert view.get_block_item_from_instance(b).isVisible()


def test_undo_redo_move_resize_group(qtbot, tmp_path):
    window = _create_window(qtbot, tmp_path)
    controller = window.project_controller
    view = window.view
    stack = window.undo_manager.stack

    a = controller.add_block("sources", "constant")
    b = controller.add_block("operators", "gain")
    group = controller.group_blocks([a, b])
    view.refresh_visual_groups()

    group_item = view.group_items[group.uid]
    old_pos = QPointF(group_item.pos())
    old_rect = QRectF(group_item.rect())
    new_pos = QPointF(old_pos.x() + 30.0, old_pos.y() + 15.0)
    new_rect = QRectF(0.0, 0.0, old_rect.width() + 40.0, old_rect.height() + 20.0)

    controller.execute_move_resize_group(
        group.uid, old_pos, old_rect, new_pos, new_rect
    )

    assert group_item.pos() == new_pos
    assert group_item.rect().width() == new_rect.width()
    assert group_item.rect().height() == new_rect.height()
    assert group.layout["width"] == new_rect.width()
    assert group.layout["height"] == new_rect.height()

    stack.undo()
    assert group_item.pos() == old_pos
    assert group_item.rect().width() == old_rect.width()
    assert group_item.rect().height() == old_rect.height()
    assert group.layout["width"] == old_rect.width()
    assert group.layout["height"] == old_rect.height()

    stack.redo()
    assert group_item.pos() == new_pos
    assert group_item.rect().width() == new_rect.width()
    assert group_item.rect().height() == new_rect.height()
    assert group.layout["width"] == new_rect.width()
    assert group.layout["height"] == new_rect.height()


def test_redo_move_resize_after_redo_group_keeps_same_uid(qtbot, tmp_path):
    """Move/resize commands must keep working after group undo then redo."""
    window = _create_window(qtbot, tmp_path)
    controller = window.project_controller
    view = window.view
    stack = window.undo_manager.stack

    a = controller.add_block("sources", "constant")
    b = controller.add_block("operators", "gain")
    group = controller.group_blocks([a, b])
    view.refresh_visual_groups()
    group_uid = group.uid

    group_item = view.group_items[group_uid]
    old_pos = QPointF(group_item.pos())
    old_rect = QRectF(group_item.rect())
    new_pos = QPointF(old_pos.x() + 30.0, old_pos.y() + 15.0)
    new_rect = QRectF(0.0, 0.0, old_rect.width() + 40.0, old_rect.height() + 20.0)

    controller.execute_move_resize_group(
        group_uid, old_pos, old_rect, new_pos, new_rect
    )

    stack.undo()  # undo move
    stack.undo()  # undo group

    assert controller.project_state.visual_groups == []
    assert group_uid not in view.group_items

    stack.redo()  # redo group
    assert len(controller.project_state.visual_groups) == 1
    restored = controller.project_state.visual_groups[0]
    assert restored.uid == group_uid
    group_item = view.group_items[group_uid]
    assert group_item.pos() == old_pos

    stack.redo()  # redo move
    assert group_item.pos() == new_pos
    assert group_item.rect().width() == new_rect.width()
    assert restored.layout["width"] == new_rect.width()


def test_group_boundary_proxies_assigned_on_creation(qtbot, tmp_path):
    window = _create_window(qtbot, tmp_path)
    controller = window.project_controller

    src = controller.add_block("sources", "constant")
    gain = controller.add_block("operators", "gain")
    out = controller.add_block("operators", "sum")
    controller.add_connection(_first_port(src, "output"), _first_port(gain, "input"))
    controller.add_connection(_first_port(gain, "output"), _first_port(out, "input"))

    group = controller.group_blocks([src, gain])
    assert len(group.boundary_ports) >= 1
    for boundary in group.boundary_ports:
        assert boundary.proxy_uid
        assert boundary.proxy_layout


def test_proxies_visible_only_in_internal_view(qtbot, tmp_path):
    window = _create_window(qtbot, tmp_path)
    controller = window.project_controller
    view = window.view

    a = controller.add_block("sources", "constant")
    b = controller.add_block("operators", "gain")
    group = controller.group_blocks([a, b])
    view.refresh_visual_groups()

    assert len(view.proxy_items) == 0

    view.enter_group(group.uid)
    assert len(view.proxy_items) == len(group.boundary_ports)
    for proxy in view.proxy_items.values():
        assert proxy.isVisible()

    view.exit_group_view()
    assert len(view.proxy_items) == len(group.boundary_ports)
    for proxy in view.proxy_items.values():
        assert not proxy.isVisible()


def test_palette_exposes_group_ports_in_internal_view(qtbot, tmp_path):
    window = _create_window(qtbot, tmp_path)
    controller = window.project_controller
    view = window.view

    a = controller.add_block("sources", "constant")
    b = controller.add_block("operators", "gain")
    group = controller.group_blocks([a, b])

    assert "group_ports" not in window.get_categories()

    view.enter_group(group.uid)
    assert "group_ports" in window.get_categories()
    assert window.get_blocks("group_ports") == ["In", "Out"]


def test_add_manual_boundary_port_creates_proxy(qtbot, tmp_path):
    window = _create_window(qtbot, tmp_path)
    controller = window.project_controller
    view = window.view

    a = controller.add_block("sources", "constant")
    b = controller.add_block("operators", "gain")
    group = controller.group_blocks([a, b])
    auto_count = len(group.boundary_ports)

    view.enter_group(group.uid)
    boundary = controller.add_manual_boundary_port(
        group.uid, "input", QPointF(50.0, 60.0)
    )

    assert boundary is not None
    assert boundary.origin == "manual"
    assert boundary.direction == "input"
    assert boundary.label == "In"
    assert len(group.boundary_ports) == auto_count + 1
    assert boundary.uid in view.proxy_items
    assert view.proxy_items[boundary.uid].isVisible()
    assert boundary.proxy_layout["x"] == 50.0


def test_add_second_manual_in_gets_unique_name(qtbot, tmp_path):
    window = _create_window(qtbot, tmp_path)
    controller = window.project_controller
    view = window.view

    a = controller.add_block("sources", "constant")
    b = controller.add_block("operators", "gain")
    group = controller.group_blocks([a, b])
    view.enter_group(group.uid)

    first = controller.add_manual_boundary_port(group.uid, "input", QPointF(40.0, 50.0))
    second = controller.add_manual_boundary_port(group.uid, "input", QPointF(80.0, 50.0))

    assert first.label == "In"
    assert second.label == "In_1"
    view.pop_view_level()
    view.refresh_visual_groups()
    group_item = view.group_items[group.uid]
    assert group_item.boundary_port_items[first.uid].label.toPlainText() == "In"
    assert group_item.boundary_port_items[second.uid].label.toPlainText() == "In_1"


def test_undo_removes_manual_ports_before_ungrouping(qtbot, tmp_path):
    window = _create_window(qtbot, tmp_path)
    controller = window.project_controller
    view = window.view
    stack = window.undo_manager.stack

    a = controller.add_block("sources", "constant")
    b = controller.add_block("operators", "gain")
    group = controller.group_blocks([a, b])

    view.enter_group(group.uid)
    controller.add_manual_boundary_port(group.uid, "input", QPointF(40.0, 50.0))
    assert any(port.origin == "manual" for port in group.boundary_ports)

    stack.undo()
    assert not any(port.origin == "manual" for port in group.boundary_ports)
    assert controller.project_state.get_visual_group(group.uid) is not None

    stack.undo()
    assert controller.project_state.get_visual_group(group.uid) is None


def test_undo_connection_route_edit(qtbot, tmp_path):
    window = _create_window(qtbot, tmp_path)
    controller = window.project_controller
    view = window.view
    stack = window.undo_manager.stack

    src = controller.add_block("sources", "constant")
    dst = controller.add_block("operators", "sum")
    controller.add_connection(_first_port(src, "output"), _first_port(dst, "input"))

    conn = controller.project_state.connections[0]
    conn_item = view.connections[conn]
    conn_item.update_position()
    old_points = [QPointF(point) for point in conn_item.route.points]
    new_points = [QPointF(point) for point in old_points]
    new_points[2] = QPointF(new_points[2].x() + 30.0, new_points[2].y())
    conn_item.apply_manual_route(new_points)

    controller.execute_edit_connection_route(conn, old_points, new_points)
    assert conn_item.route.points[2].x() == new_points[2].x()

    stack.undo()
    assert conn_item.route.points[2].x() == old_points[2].x()

    stack.redo()
    assert conn_item.route.points[2].x() == new_points[2].x()


def test_manual_route_preserved_when_block_moves(qtbot, tmp_path):
    window = _create_window(qtbot, tmp_path)
    controller = window.project_controller
    view = window.view

    src = controller.add_block("sources", "constant")
    dst = controller.add_block("operators", "sum")
    controller.add_connection(_first_port(src, "output"), _first_port(dst, "input"))

    conn = controller.project_state.connections[0]
    conn_item = view.connections[conn]
    conn_item.update_position()
    manual_points = [QPointF(point) for point in conn_item.route.points]
    manual_points[2] = QPointF(manual_points[2].x() + 40.0, manual_points[2].y())
    conn_item.apply_manual_route(manual_points)

    bend_x = conn_item.route.points[2].x()
    dst_item = view.get_block_item_from_instance(dst)
    dst_item.setPos(dst_item.pos() + QPointF(50.0, 20.0))
    qtbot.wait(10)

    assert conn_item.is_manual
    assert conn_item.route.points[2].x() == bend_x
