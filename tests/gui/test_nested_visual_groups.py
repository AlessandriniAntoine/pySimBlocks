from PySide6.QtCore import QPointF

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
    raise AssertionError(f"No {direction} port on {block.name}")


def _select_items(view, *items):
    view.diagram_scene.clearSelection()
    for item in items:
        item.setSelected(True)


def test_group_block_with_existing_subgroup(qtbot, tmp_path):
    window = _create_window(qtbot, tmp_path)
    controller = window.project_controller
    view = window.view

    a = controller.add_block("sources", "constant")
    b = controller.add_block("operators", "gain")
    c = controller.add_block("operators", "sum")
    inner = controller.group_blocks([a, b], name="Inner")

    assert inner is not None
    parent = controller.group_blocks(
        [c],
        child_group_uids=[inner.uid],
        name="Outer",
    )

    assert parent is not None
    assert parent.parent_uid is None
    assert inner.parent_uid == parent.uid
    assert parent.child_group_uids == [inner.uid]
    assert set(parent.members) == {c.uid}


def test_nested_group_visibility_at_root_and_inside_parent(qtbot, tmp_path):
    window = _create_window(qtbot, tmp_path)
    controller = window.project_controller
    view = window.view

    a = controller.add_block("sources", "constant")
    b = controller.add_block("operators", "gain")
    c = controller.add_block("operators", "sum")
    inner = controller.group_blocks([a, b], name="Inner")
    parent = controller.group_blocks([c], child_group_uids=[inner.uid], name="Outer")

    view.refresh_visual_groups()
    assert view.get_block_item_from_instance(a).isVisible() is False
    assert view.group_items[inner.uid].isVisible() is False
    assert view.group_items[parent.uid].isVisible() is True

    view.enter_group(parent.uid)
    assert view.get_block_item_from_instance(c).isVisible() is True
    assert view.get_block_item_from_instance(a).isVisible() is False
    assert view.group_items[inner.uid].isVisible() is True


def test_group_selected_block_and_subgroup_from_context_menu(qtbot, tmp_path):
    window = _create_window(qtbot, tmp_path)
    controller = window.project_controller
    view = window.view

    a = controller.add_block("sources", "constant")
    b = controller.add_block("operators", "gain")
    c = controller.add_block("operators", "sum")
    inner = controller.group_blocks([a, b], name="Inner")

    _select_items(
        view,
        view.get_block_item_from_instance(c),
        view.group_items[inner.uid],
    )
    controller.group_selected_blocks()

    outer = next(
        group
        for group in controller.project_state.visual_groups
        if group.uid != inner.uid
    )
    assert outer.child_group_uids == [inner.uid]
    assert inner.parent_uid == outer.uid


def test_ungroup_parent_promotes_child_groups(qtbot, tmp_path):
    window = _create_window(qtbot, tmp_path)
    controller = window.project_controller

    a = controller.add_block("sources", "constant")
    b = controller.add_block("operators", "gain")
    c = controller.add_block("operators", "sum")
    inner = controller.group_blocks([a, b], name="Inner")
    parent = controller.group_blocks([c], child_group_uids=[inner.uid], name="Outer")

    assert controller.ungroup(parent.uid)
    promoted = controller.project_state.get_visual_group(inner.uid)
    assert promoted is not None
    assert promoted.parent_uid is None
    assert controller.project_state.get_visual_group(parent.uid) is None


def test_create_subgroup_inside_parent_view(qtbot, tmp_path):
    window = _create_window(qtbot, tmp_path)
    controller = window.project_controller
    view = window.view

    a = controller.add_block("sources", "constant")
    b = controller.add_block("operators", "gain")
    c = controller.add_block("operators", "sum")
    parent = controller.group_blocks([a, b, c], name="Parent")
    view.enter_group(parent.uid)

    child = controller.group_blocks([a, b], name="Child", parent_uid=parent.uid)

    assert child is not None
    assert child.parent_uid == parent.uid
    assert child.uid in parent.child_group_uids
    assert set(parent.members) == {c.uid}
    assert set(child.members) == {a.uid, b.uid}


def test_cross_group_connection_visible_at_root(qtbot, tmp_path):
    window = _create_window(qtbot, tmp_path)
    controller = window.project_controller
    view = window.view

    a = controller.add_block("sources", "constant")
    b = controller.add_block("operators", "gain")
    c = controller.add_block("operators", "sum")
    d = controller.add_block("operators", "gain")
    controller.group_blocks([a, b], name="GroupA")
    controller.group_blocks([c, d], name="GroupB")

    controller.add_connection(_first_port(b, "output"), _first_port(c, "input"))
    view.refresh_visual_groups()

    connection = next(iter(controller.project_state.connections))
    assert view.connections[connection].isVisible() is True


def test_cross_child_connection_visible_inside_parent(qtbot, tmp_path):
    window = _create_window(qtbot, tmp_path)
    controller = window.project_controller
    view = window.view

    a = controller.add_block("sources", "constant")
    b = controller.add_block("operators", "gain")
    c = controller.add_block("operators", "sum")
    d = controller.add_block("operators", "gain")
    inner_a = controller.group_blocks([a, b], name="InnerA")
    inner_b = controller.group_blocks([c, d], name="InnerB")
    parent = controller.group_blocks(
        [],
        child_group_uids=[inner_a.uid, inner_b.uid],
        name="Parent",
    )
    assert parent is not None

    controller.add_connection(_first_port(b, "output"), _first_port(c, "input"))
    view.refresh_visual_groups()

    connection = next(iter(controller.project_state.connections))
    conn_item = view.connections[connection]
    assert conn_item.isVisible() is False

    view.enter_group(parent.uid)
    view.refresh_visual_groups()
    assert conn_item.isVisible() is True


def test_delete_group_removes_nested_members_and_child_groups(qtbot, tmp_path):
    window = _create_window(qtbot, tmp_path)
    controller = window.project_controller

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
    assert control_loop is not None

    member_uids = {
        sum_err.uid,
        controller_block.uid,
        sum_plant.uid,
        system.uid,
    }
    assert controller.delete_group(control_loop.uid)

    assert controller.project_state.get_visual_group(control_loop.uid) is None
    assert controller.project_state.get_visual_group(regulator.uid) is None
    assert controller.project_state.get_visual_group(plant.uid) is None
    for uid in member_uids:
        assert controller._find_block_by_uid(uid) is None

    window.undo_manager.stack.undo()
    assert controller.project_state.get_visual_group(control_loop.uid) is not None
    for uid in member_uids:
        assert controller._find_block_by_uid(uid) is not None


def _wire_length(points) -> float:
    total = 0.0
    for index in range(len(points) - 1):
        a = points[index]
        b = points[index + 1]
        total += abs(a.x() - b.x()) + abs(a.y() - b.y())
    return total


def test_manual_route_recomputed_in_nested_group_view(qtbot, tmp_path):
    window = _create_window(qtbot, tmp_path)
    controller = window.project_controller
    view = window.view

    external = controller.add_block("sources", "constant")
    inner_a = controller.add_block("operators", "sum")
    inner_b = controller.add_block("controllers", "state_feedback")
    controller.add_connection(_first_port(external, "output"), _first_port(inner_a, "input"))
    inner = controller.group_blocks([inner_a, inner_b], name="Regulator")
    controller.group_blocks(
        [controller.add_block("operators", "gain")],
        child_group_uids=[inner.uid],
        name="ControlLoop",
    )

    connection = next(iter(controller.project_state.connections))
    conn_item = view.connections[connection]
    conn_item.update_position()
    manual_points = [QPointF(point) for point in conn_item.route.points]
    manual_points.insert(2, QPointF(manual_points[1].x() + 300.0, manual_points[1].y() + 250.0))
    conn_item.apply_manual_route(manual_points)
    absurd_length = _wire_length(conn_item.route.points)

    view.enter_group(inner.uid)
    view.refresh_visual_groups()
    conn_item.update_position()

    assert not conn_item.is_manual
    assert _wire_length(conn_item.route.points) < absurd_length * 0.5


def test_undo_connection_delete_does_not_duplicate_output_proxy(qtbot, tmp_path):
    import shutil
    from pathlib import Path

    example_dir = (
        Path(__file__).resolve().parents[2] / "examples/basics/nested_groups/gui"
    )
    project_dir = tmp_path / "nested"
    shutil.copytree(example_dir, project_dir)

    window = _create_window(qtbot, project_dir)
    controller = window.project_controller
    view = window.view

    control_loop_uid = "3729168ddf894f62a7b4f1633b4b3014"
    system_uid = "3f552e25cb9647bba4ce08cf897de600"
    monitor_uid = "5417b603712a41db8d3ef5d0df87b393"

    connection = next(
        conn
        for conn in controller.project_state.connections
        if conn.src_block().uid == system_uid
        and conn.src_port.name == "y"
        and conn.dst_block().uid == monitor_uid
    )

    view.enter_group(control_loop_uid)
    controller.remove_connection(connection)

    control_loop = controller.project_state.get_visual_group(control_loop_uid)
    assert control_loop is not None

    window.undo_manager.stack.undo()

    output_boundaries = [
        port for port in control_loop.boundary_ports if port.direction == "output"
    ]
    assert len(output_boundaries) == 1
    assert output_boundaries[0].linked_connection_uid
    assert len(controller.project_state.connections) == 9

    view.refresh_visual_groups()
    visible_outputs = [
        boundary_uid
        for boundary_uid, proxy in view.proxy_items.items()
        if proxy.isVisible() and proxy.boundary.direction == "output"
    ]
    assert len(visible_outputs) == 1


def test_manual_route_recomputed_when_entering_control_loop_from_root(qtbot, tmp_path):
    import shutil
    from pathlib import Path

    example_dir = (
        Path(__file__).resolve().parents[2] / "examples/basics/nested_groups/gui"
    )
    project_dir = tmp_path / "nested"
    shutil.copytree(example_dir, project_dir)

    window = _create_window(qtbot, project_dir)
    controller = window.project_controller
    view = window.view

    control_loop_uid = "3729168ddf894f62a7b4f1633b4b3014"
    controller_uid = "3643a75d10754f21afb56a8a24844cdb"
    sum_plant_uid = "db6d7d946a14478fa5fed05018e0a64a"

    connection = next(
        conn
        for conn in controller.project_state.connections
        if conn.src_block().uid == controller_uid
        and conn.src_port.name == "u"
        and conn.dst_block().uid == sum_plant_uid
        and conn.dst_port.name == "in1"
    )
    conn_item = view.connections[connection]
    conn_item.update_position()
    manual_points = [QPointF(point) for point in conn_item.route.points]
    manual_points.insert(2, QPointF(manual_points[1].x() + 350.0, manual_points[1].y() + 200.0))
    conn_item.apply_manual_route(manual_points)
    absurd_length = _wire_length(conn_item.route.points)

    view.enter_group(control_loop_uid)
    view.refresh_visual_groups()
    conn_item.update_position()

    assert not conn_item.is_manual
    assert _wire_length(conn_item.route.points) < absurd_length * 0.5
