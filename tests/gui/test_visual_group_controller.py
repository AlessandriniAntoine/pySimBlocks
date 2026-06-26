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


def test_group_blocks_creates_visual_group_with_boundaries(qtbot, tmp_path):
    window = _create_window(qtbot, tmp_path)
    controller = window.project_controller

    src = controller.add_block("sources", "constant")
    gain = controller.add_block("operators", "gain")
    out = controller.add_block("operators", "sum")

    controller.add_connection(_first_port(src, "output"), _first_port(gain, "input"))
    controller.add_connection(_first_port(gain, "output"), _first_port(out, "input"))

    group = controller.group_blocks([src, gain], name="Loop")

    assert group.name == "Loop"
    assert set(group.members) == {src.uid, gain.uid}
    assert len(group.boundary_ports) == 1
    assert group.boundary_ports[0].direction == "output"
    assert group.boundary_ports[0].origin == "auto"


def test_ungroup_removes_visual_group(qtbot, tmp_path):
    window = _create_window(qtbot, tmp_path)
    controller = window.project_controller

    a = controller.add_block("sources", "constant")
    b = controller.add_block("operators", "gain")
    group = controller.group_blocks([a, b])

    assert len(controller.project_state.visual_groups) == 1
    assert controller.ungroup(group.uid)
    assert controller.project_state.visual_groups == []
    assert not controller.ungroup("missing")


def test_remove_block_updates_group_membership(qtbot, tmp_path):
    window = _create_window(qtbot, tmp_path)
    controller = window.project_controller

    a = controller.add_block("sources", "constant")
    b = controller.add_block("operators", "gain")
    group = controller.group_blocks([a, b])

    controller.remove_block(a)
    restored = controller.project_state.get_visual_group(group.uid)
    assert restored is not None
    assert restored.members == [b.uid]

    controller.remove_block(b)
    assert controller.project_state.get_visual_group(group.uid) is None


def _port_named(block, name: str):
    for port in block.ports:
        if port.name == name:
            return port
    raise AssertionError(f"No port named {name} for block {block.name}")


def test_add_block_to_group_moves_membership(qtbot, tmp_path):
    window = _create_window(qtbot, tmp_path)
    controller = window.project_controller

    a = controller.add_block("sources", "constant")
    b = controller.add_block("operators", "gain")
    c = controller.add_block("operators", "sum")
    group = controller.group_blocks([a, b])

    assert controller.add_block_to_group(group.uid, c)
    restored = controller.project_state.get_visual_group(group.uid)
    assert restored is not None
    assert set(restored.members) == {a.uid, b.uid, c.uid}


def test_add_block_in_group_view_creates_member(qtbot, tmp_path):
    window = _create_window(qtbot, tmp_path)
    controller = window.project_controller
    view = window.view

    a = controller.add_block("sources", "constant")
    b = controller.add_block("operators", "gain")
    group = controller.group_blocks([a, b])
    view.enter_group(group.uid)

    added = controller.add_block_in_group_view("operators", "sum", group.uid)
    assert added is not None
    restored = controller.project_state.get_visual_group(group.uid)
    assert restored is not None
    assert added.uid in restored.members
    assert view.get_block_item_from_instance(added).isVisible()


def test_remove_block_from_group_keeps_block_visible_at_parent(qtbot, tmp_path):
    window = _create_window(qtbot, tmp_path)
    controller = window.project_controller
    view = window.view

    a = controller.add_block("sources", "constant")
    b = controller.add_block("operators", "gain")
    c = controller.add_block("operators", "sum")
    group = controller.group_blocks([a, b, c])
    view.refresh_visual_groups()

    assert controller.remove_block_from_group(group.uid, c.uid)
    restored = controller.project_state.get_visual_group(group.uid)
    assert restored is not None
    assert restored.members == [a.uid, b.uid]
    assert controller._find_block_by_uid(c.uid) is not None

    view.refresh_visual_groups()
    assert view.get_block_item_from_instance(c).isVisible()


def test_cannot_add_block_already_owned_by_another_group(qtbot, tmp_path):
    window = _create_window(qtbot, tmp_path)
    controller = window.project_controller

    a = controller.add_block("sources", "constant")
    b = controller.add_block("operators", "gain")
    c = controller.add_block("operators", "sum")
    d = controller.add_block("operators", "gain")
    group_a = controller.group_blocks([a, b])
    group_b = controller.group_blocks([c, d])

    assert not controller.add_block_to_group(group_b.uid, a)
    assert controller.project_state.get_visual_group(group_a.uid).members == [a.uid, b.uid]


def test_boundary_ports_recomputed_when_connections_change(qtbot, tmp_path):
    window = _create_window(qtbot, tmp_path)
    controller = window.project_controller

    src = controller.add_block("sources", "constant")
    summ = controller.add_block("operators", "sum")
    out = controller.add_block("operators", "sum")

    controller.add_connection(_first_port(src, "output"), _port_named(summ, "in1"))
    controller.add_connection(_first_port(summ, "output"), _first_port(out, "input"))

    group = controller.group_blocks([src, summ], name="Loop")
    assert len(group.boundary_ports) == 1
    assert group.boundary_ports[0].direction == "output"

    ext = controller.add_block("sources", "step")
    connections_before = len(controller.project_state.connections)
    controller.add_connection(_first_port(ext, "output"), _port_named(summ, "in2"))
    assert len(controller.project_state.connections) == connections_before + 1

    restored = controller.project_state.get_visual_group(group.uid)
    assert restored is not None
    assert len(restored.boundary_ports) == 2
    directions = {port.direction for port in restored.boundary_ports}
    assert directions == {"input", "output"}

    crossing = next(
        connection
        for connection in controller.project_state.connections
        if connection.src_block().uid == ext.uid
    )
    controller.remove_connection(crossing)

    restored = controller.project_state.get_visual_group(group.uid)
    assert restored is not None
    assert len(restored.boundary_ports) == 2
    input_boundary = next(
        port for port in restored.boundary_ports if port.direction == "input"
    )
    assert input_boundary.origin == "auto"
    assert not input_boundary.linked_connection_uid
    assert input_boundary.external_port_uid == ""
    assert input_boundary.linked_port_uid.endswith(":in2")
