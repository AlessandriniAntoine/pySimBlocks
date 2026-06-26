from PySide6.QtCore import QPointF

from pySimBlocks.gui.graphics.manual_boundary_wire_item import ManualBoundaryWireItem
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


def _manual_input_boundary(controller, view, group):
    view.enter_group(group.uid)
    return controller.add_manual_boundary_port(
        group.uid, "input", QPointF(40.0, 50.0)
    )


def _manual_output_boundary(controller, view, group):
    view.enter_group(group.uid)
    return controller.add_manual_boundary_port(
        group.uid, "output", QPointF(120.0, 50.0)
    )


def test_delete_incomplete_internal_boundary_wire_keeps_proxy(qtbot, tmp_path):
    window = _create_window(qtbot, tmp_path)
    controller = window.project_controller
    view = window.view

    src = controller.add_block("sources", "constant")
    gain = controller.add_block("operators", "gain")
    group = controller.group_blocks([src, gain])
    boundary = _manual_input_boundary(controller, view, group)
    controller._wire_manual_boundary_internal(
        group.uid, boundary.uid, _first_port(gain, "input")
    )

    view.refresh_manual_boundary_wires()
    wire = view.manual_boundary_wires[f"{boundary.uid}:internal"]
    wire.setSelected(True)
    view.delete_selected()

    boundary = controller._find_boundary_port(group, boundary.uid)
    assert boundary is not None
    assert boundary.linked_port_uid == ""
    assert boundary.uid in view.proxy_items
    assert f"{boundary.uid}:internal" not in view.manual_boundary_wires


def test_delete_incomplete_internal_boundary_wire_keeps_output_proxy(qtbot, tmp_path):
    window = _create_window(qtbot, tmp_path)
    controller = window.project_controller
    view = window.view

    src = controller.add_block("sources", "constant")
    gain = controller.add_block("operators", "gain")
    group = controller.group_blocks([src, gain])
    boundary = _manual_output_boundary(controller, view, group)
    controller._wire_manual_boundary_internal(
        group.uid, boundary.uid, _first_port(gain, "output")
    )

    view.refresh_manual_boundary_wires()
    wire = view.manual_boundary_wires[f"{boundary.uid}:internal"]
    wire.setSelected(True)
    view.delete_selected()

    boundary = controller._find_boundary_port(group, boundary.uid)
    assert boundary is not None
    assert boundary.linked_port_uid == ""
    assert boundary.uid in view.proxy_items
    assert f"{boundary.uid}:internal" not in view.manual_boundary_wires


def test_delete_incomplete_external_boundary_wire_keeps_group_port(qtbot, tmp_path):
    window = _create_window(qtbot, tmp_path)
    controller = window.project_controller
    view = window.view

    src = controller.add_block("sources", "constant")
    gain = controller.add_block("operators", "gain")
    external = controller.add_block("operators", "sum")
    group = controller.group_blocks([src, gain])
    boundary = _manual_input_boundary(controller, view, group)
    controller._wire_manual_boundary_internal(
        group.uid, boundary.uid, _first_port(gain, "input")
    )

    view.pop_view_level()
    controller._wire_manual_boundary_external(
        group.uid, boundary.uid, _first_port(external, "output")
    )
    boundary = controller._find_boundary_port(group, boundary.uid)
    assert boundary.linked_connection_uid

    controller.remove_connection(controller.project_state.connections[0])
    boundary = controller._find_boundary_port(group, boundary.uid)
    assert boundary is not None
    assert boundary.linked_port_uid
    assert boundary.external_port_uid == ""
    assert not boundary.linked_connection_uid

    view.enter_group(group.uid)
    view.refresh_manual_boundary_wires()
    wire = view.manual_boundary_wires[f"{boundary.uid}:internal"]
    assert isinstance(wire, ManualBoundaryWireItem)
    wire.setSelected(True)
    view.delete_selected()

    boundary = controller._find_boundary_port(group, boundary.uid)
    assert boundary is not None
    assert boundary.linked_port_uid == ""
    assert boundary.external_port_uid == ""
    assert boundary.uid in view.proxy_items


def test_delete_incomplete_external_boundary_wire_keeps_output_group_port(qtbot, tmp_path):
    window = _create_window(qtbot, tmp_path)
    controller = window.project_controller
    view = window.view

    src = controller.add_block("sources", "constant")
    gain = controller.add_block("operators", "gain")
    external = controller.add_block("operators", "sum")
    group = controller.group_blocks([src, gain])
    boundary = _manual_output_boundary(controller, view, group)
    controller._wire_manual_boundary_internal(
        group.uid, boundary.uid, _first_port(gain, "output")
    )

    view.pop_view_level()
    controller._wire_manual_boundary_external(
        group.uid, boundary.uid, _first_port(external, "input")
    )
    boundary = controller._find_boundary_port(group, boundary.uid)
    assert boundary.linked_connection_uid

    controller.remove_connection(controller.project_state.connections[0])
    boundary = controller._find_boundary_port(group, boundary.uid)
    assert boundary is not None
    assert boundary.linked_port_uid
    assert boundary.external_port_uid == ""
    assert not boundary.linked_connection_uid

    view.enter_group(group.uid)
    view.refresh_manual_boundary_wires()
    wire = view.manual_boundary_wires[f"{boundary.uid}:internal"]
    assert isinstance(wire, ManualBoundaryWireItem)
    wire.setSelected(True)
    view.delete_selected()

    boundary = controller._find_boundary_port(group, boundary.uid)
    assert boundary is not None
    assert boundary.linked_port_uid == ""
    assert boundary.external_port_uid == ""
    assert boundary.uid in view.proxy_items


def test_delete_completed_group_connection_keeps_proxy_and_shows_dashed_wire(
    qtbot, tmp_path
):
    window = _create_window(qtbot, tmp_path)
    controller = window.project_controller
    view = window.view

    src = controller.add_block("sources", "constant")
    gain = controller.add_block("operators", "gain")
    external = controller.add_block("operators", "sum")
    group = controller.group_blocks([src, gain])
    boundary = _manual_input_boundary(controller, view, group)
    controller._wire_manual_boundary_internal(
        group.uid, boundary.uid, _first_port(gain, "input")
    )

    view.pop_view_level()
    controller._wire_manual_boundary_external(
        group.uid, boundary.uid, _first_port(external, "output")
    )
    boundary = controller._find_boundary_port(group, boundary.uid)
    connection = controller.project_state.connections[0]
    assert boundary.linked_connection_uid

    controller.remove_connection(connection)
    boundary = controller._find_boundary_port(group, boundary.uid)
    assert boundary is not None
    assert not boundary.linked_connection_uid
    assert boundary.linked_port_uid
    assert boundary.external_port_uid == ""

    view.enter_group(group.uid)
    assert boundary.uid in view.proxy_items
    assert view.proxy_items[boundary.uid].isVisible()

    view.refresh_manual_boundary_wires()
    assert f"{boundary.uid}:internal" in view.manual_boundary_wires

    view.pop_view_level()
    view.refresh_manual_boundary_wires()
    assert f"{boundary.uid}:external" not in view.manual_boundary_wires


def test_delete_completed_group_connection_keeps_output_proxy_and_dashed_wire(
    qtbot, tmp_path
):
    window = _create_window(qtbot, tmp_path)
    controller = window.project_controller
    view = window.view

    src = controller.add_block("sources", "constant")
    gain = controller.add_block("operators", "gain")
    external = controller.add_block("operators", "sum")
    group = controller.group_blocks([src, gain])
    boundary = _manual_output_boundary(controller, view, group)
    controller._wire_manual_boundary_internal(
        group.uid, boundary.uid, _first_port(gain, "output")
    )

    view.pop_view_level()
    controller._wire_manual_boundary_external(
        group.uid, boundary.uid, _first_port(external, "input")
    )
    boundary = controller._find_boundary_port(group, boundary.uid)
    connection = controller.project_state.connections[0]
    assert boundary.linked_connection_uid

    controller.remove_connection(connection)
    boundary = controller._find_boundary_port(group, boundary.uid)
    assert boundary is not None
    assert not boundary.linked_connection_uid
    assert boundary.linked_port_uid
    assert boundary.external_port_uid == ""

    view.enter_group(group.uid)
    assert boundary.uid in view.proxy_items
    assert view.proxy_items[boundary.uid].isVisible()

    view.refresh_manual_boundary_wires()
    assert f"{boundary.uid}:internal" in view.manual_boundary_wires

    view.pop_view_level()
    view.refresh_manual_boundary_wires()
    assert f"{boundary.uid}:external" not in view.manual_boundary_wires


def test_delete_block_to_group_connection_keeps_internal_dashed_wire(qtbot, tmp_path):
    window = _create_window(qtbot, tmp_path)
    controller = window.project_controller
    view = window.view

    step = controller.add_block("sources", "step")
    member = controller.add_block("operators", "sum")
    group = controller.group_blocks([member, controller.add_block("operators", "gain")], name="ControlLoop")
    controller.add_connection(_first_port(step, "output"), _port_named(member, "in1"))
    view.refresh_visual_groups()

    connection = next(iter(controller.project_state.connections))
    controller.remove_connection(connection)
    view.refresh_visual_groups()
    view.refresh_manual_boundary_wires()

    assert len(view.manual_boundary_wires) == 0

    group = controller.project_state.get_visual_group(group.uid)
    boundary = next(port for port in group.boundary_ports if port.direction == "input")
    assert boundary.origin == "auto"
    assert boundary.external_port_uid == ""
    assert boundary.linked_port_uid

    view.enter_group(group.uid)
    view.refresh_manual_boundary_wires()
    assert f"{boundary.uid}:internal" in view.manual_boundary_wires


def test_delete_block_to_group_output_connection_keeps_internal_dashed_wire(qtbot, tmp_path):
    window = _create_window(qtbot, tmp_path)
    controller = window.project_controller
    view = window.view

    sink = controller.add_block("operators", "sum")
    member = controller.add_block("operators", "gain")
    group = controller.group_blocks(
        [member, controller.add_block("sources", "constant")],
        name="ControlLoop",
    )
    controller.add_connection(_first_port(member, "output"), _first_port(sink, "input"))
    view.refresh_visual_groups()

    connection = next(iter(controller.project_state.connections))
    controller.remove_connection(connection)
    view.refresh_visual_groups()
    view.refresh_manual_boundary_wires()

    assert len(view.manual_boundary_wires) == 0

    group = controller.project_state.get_visual_group(group.uid)
    boundary = next(port for port in group.boundary_ports if port.direction == "output")
    assert boundary.origin == "auto"
    assert boundary.external_port_uid == ""
    assert boundary.linked_port_uid

    view.enter_group(group.uid)
    view.refresh_manual_boundary_wires()
    assert f"{boundary.uid}:internal" in view.manual_boundary_wires


def test_delete_inside_group_keeps_external_reconnect_state(qtbot, tmp_path):
    window = _create_window(qtbot, tmp_path)
    controller = window.project_controller
    view = window.view

    step = controller.add_block("sources", "step")
    gain = controller.add_block("operators", "gain")
    group = controller.group_blocks(
        [controller.add_block("sources", "constant"), gain],
        name="ControlLoop",
    )
    controller.add_connection(_first_port(step, "output"), _first_port(gain, "input"))
    view.refresh_visual_groups()

    group = controller.project_state.get_visual_group(group.uid)
    boundary = next(port for port in group.boundary_ports if port.origin == "auto")
    connection = next(iter(controller.project_state.connections))

    view.enter_group(group.uid)
    controller.remove_connection(connection)
    view.refresh_visual_groups()

    boundary = controller._find_boundary_port(group, boundary.uid)
    assert boundary.origin == "auto"
    assert boundary.external_port_uid
    assert boundary.linked_port_uid == ""

    view.pop_view_level()
    view.refresh_manual_boundary_wires()
    assert f"{boundary.uid}:external" in view.manual_boundary_wires

    border_port = view.group_items[group.uid].boundary_port_items[boundary.uid]
    step_port = view.get_block_item_from_instance(step).get_port_item(
        _first_port(step, "output").name
    )
    assert controller.try_wire_boundary_endpoints(step_port, border_port)
    assert len(controller.project_state.connections) == 0

    view.enter_group(group.uid)
    proxy_port = view.proxy_items[boundary.uid].port_item
    gain_port = view.get_block_item_from_instance(gain).get_port_item(
        _first_port(gain, "input").name
    )
    assert controller.try_wire_boundary_endpoints(proxy_port, gain_port)
    assert len(controller.project_state.connections) == 1

    controller.remove_connection(controller.project_state.connections[0])
    view.refresh_visual_groups()

    boundary = controller._find_boundary_port(group, boundary.uid)
    assert boundary.external_port_uid
    assert boundary.linked_port_uid == ""

    view.pop_view_level()
    view.refresh_manual_boundary_wires()
    assert f"{boundary.uid}:external" in view.manual_boundary_wires

    assert controller.try_wire_boundary_endpoints(step_port, border_port)
    view.enter_group(group.uid)
    assert controller.try_wire_boundary_endpoints(proxy_port, gain_port)
    assert len(controller.project_state.connections) == 1


def test_delete_inside_group_keeps_external_reconnect_state_for_output(qtbot, tmp_path):
    window = _create_window(qtbot, tmp_path)
    controller = window.project_controller
    view = window.view

    sink = controller.add_block("operators", "sum")
    gain = controller.add_block("operators", "gain")
    group = controller.group_blocks(
        [controller.add_block("sources", "constant"), gain],
        name="ControlLoop",
    )
    controller.add_connection(_first_port(gain, "output"), _first_port(sink, "input"))
    view.refresh_visual_groups()

    group = controller.project_state.get_visual_group(group.uid)
    boundary = next(
        port for port in group.boundary_ports
        if port.origin == "auto" and port.direction == "output"
    )
    connection = next(iter(controller.project_state.connections))

    view.enter_group(group.uid)
    controller.remove_connection(connection)
    view.refresh_visual_groups()

    boundary = controller._find_boundary_port(group, boundary.uid)
    assert boundary.origin == "auto"
    assert boundary.external_port_uid
    assert boundary.linked_port_uid == ""

    view.pop_view_level()
    view.refresh_manual_boundary_wires()
    assert f"{boundary.uid}:external" in view.manual_boundary_wires

    border_port = view.group_items[group.uid].boundary_port_items[boundary.uid]
    sink_port = view.get_block_item_from_instance(sink).get_port_item(
        _first_port(sink, "input").name
    )
    assert controller.try_wire_boundary_endpoints(border_port, sink_port)
    assert len(controller.project_state.connections) == 0

    view.enter_group(group.uid)
    proxy_port = view.proxy_items[boundary.uid].port_item
    gain_port = view.get_block_item_from_instance(gain).get_port_item(
        _first_port(gain, "output").name
    )
    assert controller.try_wire_boundary_endpoints(gain_port, proxy_port)
    assert len(controller.project_state.connections) == 1


def test_delete_internal_dashed_after_root_delete_keeps_nothing(qtbot, tmp_path):
    window = _create_window(qtbot, tmp_path)
    controller = window.project_controller
    view = window.view

    src = controller.add_block("sources", "constant")
    gain = controller.add_block("operators", "gain")
    external = controller.add_block("operators", "sum")
    group = controller.group_blocks([src, gain])
    boundary = _manual_input_boundary(controller, view, group)
    controller._wire_manual_boundary_internal(
        group.uid, boundary.uid, _first_port(gain, "input")
    )
    view.pop_view_level()
    controller._wire_manual_boundary_external(
        group.uid, boundary.uid, _first_port(external, "output")
    )
    controller.remove_connection(controller.project_state.connections[0])

    view.enter_group(group.uid)
    view.refresh_manual_boundary_wires()
    wire = view.manual_boundary_wires[f"{boundary.uid}:internal"]
    wire.setSelected(True)
    view.delete_selected()

    boundary = controller._find_boundary_port(group, boundary.uid)
    assert boundary.linked_port_uid == ""
    assert boundary.external_port_uid == ""


def test_delete_internal_dashed_after_root_delete_keeps_nothing_for_output(qtbot, tmp_path):
    window = _create_window(qtbot, tmp_path)
    controller = window.project_controller
    view = window.view

    src = controller.add_block("sources", "constant")
    gain = controller.add_block("operators", "gain")
    external = controller.add_block("operators", "sum")
    group = controller.group_blocks([src, gain])
    boundary = _manual_output_boundary(controller, view, group)
    controller._wire_manual_boundary_internal(
        group.uid, boundary.uid, _first_port(gain, "output")
    )
    view.pop_view_level()
    controller._wire_manual_boundary_external(
        group.uid, boundary.uid, _first_port(external, "input")
    )
    controller.remove_connection(controller.project_state.connections[0])

    view.enter_group(group.uid)
    view.refresh_manual_boundary_wires()
    wire = view.manual_boundary_wires[f"{boundary.uid}:internal"]
    wire.setSelected(True)
    view.delete_selected()

    boundary = controller._find_boundary_port(group, boundary.uid)
    assert boundary.linked_port_uid == ""
    assert boundary.external_port_uid == ""


def test_delete_auto_boundary_connection_keeps_proxy_in_group_view(qtbot, tmp_path):
    window = _create_window(qtbot, tmp_path)
    controller = window.project_controller
    view = window.view

    src = controller.add_block("sources", "constant")
    gain = controller.add_block("operators", "gain")
    external = controller.add_block("operators", "sum")
    group = controller.group_blocks([src, gain])
    controller.add_connection(_first_port(external, "output"), _first_port(gain, "input"))

    group = controller.project_state.get_visual_group(group.uid)
    auto_boundary = next(
        port for port in group.boundary_ports if port.origin == "auto"
    )
    connection = next(
        connection
        for connection in controller.project_state.connections
        if connection.dst_block().uid == gain.uid
        and connection.src_block().uid == external.uid
    )
    controller.remove_connection(connection)

    boundary = controller._find_boundary_port(group, auto_boundary.uid)
    assert boundary is not None
    assert boundary.origin == "auto"
    assert boundary.external_port_uid == ""
    assert boundary.linked_port_uid
    assert not boundary.linked_connection_uid

    view.enter_group(group.uid)
    view.refresh_manual_boundary_wires()
    assert f"{auto_boundary.uid}:internal" in view.manual_boundary_wires
    assert auto_boundary.uid in view.proxy_items

    view.pop_view_level()
    view.refresh_manual_boundary_wires()
    assert not view.manual_boundary_wires


def test_delete_auto_output_boundary_connection_keeps_proxy_in_group_view(qtbot, tmp_path):
    window = _create_window(qtbot, tmp_path)
    controller = window.project_controller
    view = window.view

    src = controller.add_block("sources", "constant")
    gain = controller.add_block("operators", "gain")
    external = controller.add_block("operators", "sum")
    group = controller.group_blocks([src, gain])
    controller.add_connection(_first_port(gain, "output"), _first_port(external, "input"))

    group = controller.project_state.get_visual_group(group.uid)
    auto_boundary = next(
        port for port in group.boundary_ports
        if port.origin == "auto" and port.direction == "output"
    )
    connection = next(
        connection
        for connection in controller.project_state.connections
        if connection.src_block().uid == gain.uid
        and connection.dst_block().uid == external.uid
    )
    controller.remove_connection(connection)

    boundary = controller._find_boundary_port(group, auto_boundary.uid)
    assert boundary is not None
    assert boundary.origin == "auto"
    assert boundary.external_port_uid == ""
    assert boundary.linked_port_uid
    assert not boundary.linked_connection_uid

    view.enter_group(group.uid)
    view.refresh_manual_boundary_wires()
    assert f"{auto_boundary.uid}:internal" in view.manual_boundary_wires
    assert auto_boundary.uid in view.proxy_items

    view.pop_view_level()
    view.refresh_manual_boundary_wires()
    assert not view.manual_boundary_wires


def test_reconnect_block_to_group_via_border_port(qtbot, tmp_path):
    window = _create_window(qtbot, tmp_path)
    controller = window.project_controller
    view = window.view

    step = controller.add_block("sources", "step")
    gain = controller.add_block("operators", "gain")
    group = controller.group_blocks(
        [controller.add_block("sources", "constant"), gain],
        name="ControlLoop",
    )
    controller.add_connection(_first_port(step, "output"), _first_port(gain, "input"))
    view.refresh_visual_groups()

    group = controller.project_state.get_visual_group(group.uid)
    boundary = next(port for port in group.boundary_ports if port.origin == "auto")
    connection = next(iter(controller.project_state.connections))
    controller.remove_connection(connection)
    view.refresh_visual_groups()

    border_port = view.group_items[group.uid].boundary_port_items[boundary.uid]
    step_port = view.get_block_item_from_instance(step).get_port_item(
        _first_port(step, "output").name
    )
    assert controller.try_wire_boundary_endpoints(step_port, border_port)

    boundary = controller._find_boundary_port(group, boundary.uid)
    assert boundary.linked_connection_uid
    assert len(controller.project_state.connections) == 1
    view.refresh_manual_boundary_wires()
    assert not view.manual_boundary_wires


def test_reconnect_after_delete_via_boundary_ports(qtbot, tmp_path):
    window = _create_window(qtbot, tmp_path)
    controller = window.project_controller

    gain = controller.add_block("operators", "gain")
    external = controller.add_block("operators", "sum")
    group = controller.group_blocks([controller.add_block("sources", "constant"), gain])
    controller.add_connection(_first_port(external, "output"), _first_port(gain, "input"))

    group = controller.project_state.get_visual_group(group.uid)
    boundary = next(port for port in group.boundary_ports if port.origin == "auto")
    connection = next(
        conn
        for conn in controller.project_state.connections
        if conn.dst_block().uid == gain.uid and conn.src_block().uid == external.uid
    )
    controller.remove_connection(connection)

    controller.add_connection(
        _first_port(external, "output"),
        _first_port(gain, "input"),
    )
    boundary = controller._find_boundary_port(group, boundary.uid)
    assert boundary.linked_connection_uid
    assert len(controller.project_state.connections) == 1


def test_cross_group_delete_keeps_border_ports_without_dashed_wires(qtbot, tmp_path):
    window = _create_window(qtbot, tmp_path)
    controller = window.project_controller
    view = window.view

    a = controller.add_block("sources", "constant")
    b = controller.add_block("operators", "gain")
    c = controller.add_block("operators", "sum")
    d = controller.add_block("operators", "gain")
    group_a = controller.group_blocks([a, b], name="GroupA")
    group_b = controller.group_blocks([c, d], name="GroupB")
    controller.add_connection(_first_port(b, "output"), _first_port(c, "input"))
    view.refresh_visual_groups()

    connection = next(iter(controller.project_state.connections))
    boundary_a = next(port for port in group_a.boundary_ports if port.origin == "auto")
    boundary_b = next(port for port in group_b.boundary_ports if port.origin == "auto")

    controller.remove_connection(connection)
    view.refresh_visual_groups()
    view.refresh_manual_boundary_wires()

    assert not view.manual_boundary_wires
    assert boundary_a.uid in view.group_items[group_a.uid].boundary_port_items
    assert boundary_b.uid in view.group_items[group_b.uid].boundary_port_items
    assert not boundary_a.linked_connection_uid
    assert not boundary_b.linked_connection_uid


def test_cross_group_reconnect_via_group_boundary_ports(qtbot, tmp_path):
    window = _create_window(qtbot, tmp_path)
    controller = window.project_controller
    view = window.view

    a = controller.add_block("sources", "constant")
    b = controller.add_block("operators", "gain")
    c = controller.add_block("operators", "sum")
    d = controller.add_block("operators", "gain")
    group_a = controller.group_blocks([a, b], name="GroupA")
    group_b = controller.group_blocks([c, d], name="GroupB")
    controller.add_connection(_first_port(b, "output"), _first_port(c, "input"))

    connection = next(iter(controller.project_state.connections))
    controller.remove_connection(connection)
    view.refresh_visual_groups()

    port_a = view.group_items[group_a.uid].boundary_port_items[
        next(port.uid for port in group_a.boundary_ports if port.direction == "output")
    ]
    port_b = view.group_items[group_b.uid].boundary_port_items[
        next(port.uid for port in group_b.boundary_ports if port.direction == "input")
    ]

    assert controller._wire_group_boundaries_together(port_a, port_b)
    assert len(controller.project_state.connections) == 1
    restored = controller.project_state.connections[0]
    assert restored.src_block().uid == b.uid
    assert restored.dst_block().uid == c.uid


def test_auto_boundary_internal_dashed_after_cross_group_delete(qtbot, tmp_path):
    window = _create_window(qtbot, tmp_path)
    controller = window.project_controller
    view = window.view

    dist = controller.add_block("sources", "constant")
    gain = controller.add_block("operators", "gain")
    plant_in = controller.add_block("operators", "sum")
    group_a = controller.group_blocks([dist, gain], name="Disturbance")
    group_b = controller.group_blocks([plant_in], name="Plant")
    controller.add_connection(_first_port(gain, "output"), _first_port(plant_in, "input"))
    view.refresh_visual_groups()

    connection = next(iter(controller.project_state.connections))
    out_boundary = next(
        port for port in group_a.boundary_ports if port.direction == "output"
    )
    controller.remove_connection(connection)
    view.refresh_visual_groups()

    view.enter_group(group_a.uid)
    view.refresh_manual_boundary_wires()
    assert f"{out_boundary.uid}:internal" in view.manual_boundary_wires
    assert out_boundary.uid in view.proxy_items


def test_parent_group_shows_proxies_for_child_boundaries(qtbot, tmp_path):
    window = _create_window(qtbot, tmp_path)
    controller = window.project_controller
    view = window.view

    a = controller.add_block("sources", "constant")
    b = controller.add_block("operators", "gain")
    c = controller.add_block("operators", "sum")
    d = controller.add_block("operators", "gain")
    monitor = controller.add_block("operators", "gain")
    inner = controller.group_blocks([c, d], name="Plant")
    parent = controller.group_blocks(
        [monitor],
        child_group_uids=[inner.uid],
        name="ControlLoop",
    )
    external = controller.add_block("sources", "constant")
    controller.add_connection(_first_port(external, "output"), _first_port(c, "input"))

    parent_boundary = next(
        port
        for port in controller.project_state.get_visual_group(parent.uid).boundary_ports
        if port.linked_port_uid.startswith(c.uid)
    )
    view.enter_group(parent.uid)
    assert parent_boundary.uid in view.proxy_items
    assert view.proxy_items[parent_boundary.uid].isVisible()

    view.enter_group(inner.uid)
    inner_boundary = next(
        port for port in controller.project_state.get_visual_group(inner.uid).boundary_ports
        if port.direction == "input"
    )
    assert inner_boundary.uid in view.proxy_items


def test_parent_with_only_child_groups_shows_proxies(qtbot, tmp_path):
    window = _create_window(qtbot, tmp_path)
    controller = window.project_controller
    view = window.view

    regulator_a = controller.add_block("operators", "sum")
    regulator_b = controller.add_block("controllers", "state_feedback")
    plant_a = controller.add_block("operators", "sum")
    plant_b = controller.add_block("systems", "linear_state_space")
    regulator = controller.group_blocks([regulator_a, regulator_b], name="Regulator")
    plant = controller.group_blocks([plant_a, plant_b], name="Plant")
    control_loop = controller.group_blocks(
        [],
        child_group_uids=[regulator.uid, plant.uid],
        name="ControlLoop",
    )
    step = controller.add_block("sources", "step")
    controller.add_connection(_first_port(step, "output"), _first_port(regulator_a, "input"))

    view.enter_group(control_loop.uid)
    assert len(view.proxy_items) == len(control_loop.boundary_ports)
    for proxy in view.proxy_items.values():
        assert proxy.isVisible()


def test_cross_child_group_delete_and_reconnect_inside_parent(qtbot, tmp_path):
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
    controller.add_connection(_first_port(b, "output"), _first_port(c, "input"))

    connection = next(iter(controller.project_state.connections))
    controller.remove_connection(connection)
    view.enter_group(parent.uid)
    view.refresh_visual_groups()
    view.refresh_manual_boundary_wires()

    assert not view.manual_boundary_wires
    inner_a = controller.project_state.get_visual_group(inner_a.uid)
    inner_b = controller.project_state.get_visual_group(inner_b.uid)
    out_uid = next(port.uid for port in inner_a.boundary_ports if port.direction == "output")
    in_uid = next(port.uid for port in inner_b.boundary_ports if port.direction == "input")
    assert out_uid in view.group_items[inner_a.uid].boundary_port_items
    assert in_uid in view.group_items[inner_b.uid].boundary_port_items

    port_out = view.group_items[inner_a.uid].boundary_port_items[out_uid]
    port_in = view.group_items[inner_b.uid].boundary_port_items[in_uid]
    assert controller._wire_group_boundaries_together(port_out, port_in)
    assert len(controller.project_state.connections) == 1


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
    return control_loop, regulator, plant, sum_err


def test_delete_inside_nested_group_preserves_parent_external(qtbot, tmp_path):
    window = _create_window(qtbot, tmp_path)
    controller = window.project_controller
    view = window.view

    step = controller.add_block("sources", "step")
    control_loop, regulator, _plant, sum_err = _nested_control_loop(controller)
    controller.add_connection(_first_port(step, "output"), _port_named(sum_err, "in1"))
    view.refresh_visual_groups()

    control_loop = controller.project_state.get_visual_group(control_loop.uid)
    regulator = controller.project_state.get_visual_group(regulator.uid)
    connection = next(iter(controller.project_state.connections))

    view.enter_group(regulator.uid)
    controller.remove_connection(connection)
    view.refresh_visual_groups()

    assert len(controller.project_state.connections) == 0
    regulator_boundary = next(
        port for port in regulator.boundary_ports if port.direction == "input"
    )
    assert regulator_boundary.external_port_uid
    assert regulator_boundary.linked_port_uid == ""
    assert not regulator_boundary.linked_connection_uid

    parent_boundary = next(
        port for port in control_loop.boundary_ports if port.direction == "input"
    )
    assert parent_boundary.origin == "auto"
    assert parent_boundary.external_port_uid == f"{step.uid}:{_first_port(step, 'output').name}"
    assert parent_boundary.linked_port_uid == ""
    assert not parent_boundary.linked_connection_uid

    while view.current_view_group_uid is not None:
        view.pop_view_level()
    view.refresh_manual_boundary_wires()
    assert f"{parent_boundary.uid}:external" in view.manual_boundary_wires


def test_reconnect_inside_nested_group_after_delete(qtbot, tmp_path):
    window = _create_window(qtbot, tmp_path)
    controller = window.project_controller
    view = window.view

    step = controller.add_block("sources", "step")
    control_loop, regulator, _plant, sum_err = _nested_control_loop(controller)
    controller.add_connection(_first_port(step, "output"), _port_named(sum_err, "in1"))
    view.refresh_visual_groups()

    regulator = controller.project_state.get_visual_group(regulator.uid)
    connection = next(iter(controller.project_state.connections))
    boundary = next(port for port in regulator.boundary_ports if port.direction == "input")

    view.enter_group(regulator.uid)
    controller.remove_connection(connection)
    view.refresh_visual_groups()

    proxy_port = view.proxy_items[boundary.uid].port_item
    sum_port = view.get_block_item_from_instance(sum_err).get_port_item(
        _port_named(sum_err, "in1").name
    )
    assert controller.try_wire_boundary_endpoints(proxy_port, sum_port)
    assert len(controller.project_state.connections) == 1
    restored = controller.project_state.connections[0]
    assert restored.src_block().uid == step.uid
    assert restored.dst_block().uid == sum_err.uid


def test_reconnect_outside_nested_group_after_delete(qtbot, tmp_path):
    window = _create_window(qtbot, tmp_path)
    controller = window.project_controller
    view = window.view

    step = controller.add_block("sources", "step")
    control_loop, regulator, _plant, sum_err = _nested_control_loop(controller)
    controller.add_connection(_first_port(step, "output"), _port_named(sum_err, "in1"))
    view.refresh_visual_groups()

    control_loop = controller.project_state.get_visual_group(control_loop.uid)
    connection = next(iter(controller.project_state.connections))
    parent_boundary = next(
        port for port in control_loop.boundary_ports if port.direction == "input"
    )

    view.enter_group(regulator.uid)
    controller.remove_connection(connection)
    view.pop_view_level()
    view.refresh_visual_groups()

    border_port = view.group_items[control_loop.uid].boundary_port_items[parent_boundary.uid]
    step_port = view.get_block_item_from_instance(step).get_port_item(
        _first_port(step, "output").name
    )
    assert controller.try_wire_boundary_endpoints(step_port, border_port)
    assert len(controller.project_state.connections) == 0

    view.enter_group(regulator.uid)
    regulator = controller.project_state.get_visual_group(regulator.uid)
    boundary = next(port for port in regulator.boundary_ports if port.direction == "input")
    proxy_port = view.proxy_items[boundary.uid].port_item
    sum_port = view.get_block_item_from_instance(sum_err).get_port_item(
        _port_named(sum_err, "in1").name
    )
    assert controller.try_wire_boundary_endpoints(proxy_port, sum_port)
    assert len(controller.project_state.connections) == 1


def _port_named(block, name: str):
    for port in block.ports:
        if port.name == name:
            return port
    raise AssertionError(f"No port named {name} for block {block.name}")


def test_group_border_ports_keep_vertical_order_after_rebuild(qtbot, tmp_path):
    window = _create_window(qtbot, tmp_path)
    controller = window.project_controller
    view = window.view

    top = controller.add_block("operators", "sum")
    middle = controller.add_block("operators", "sum")
    bottom = controller.add_block("operators", "sum")
    ext_top = controller.add_block("sources", "constant")
    ext_middle = controller.add_block("sources", "step")
    ext_bottom = controller.add_block("sources", "constant")
    controller.add_connection(_first_port(ext_top, "output"), _port_named(top, "in1"))
    controller.add_connection(_first_port(ext_middle, "output"), _port_named(middle, "in1"))
    controller.add_connection(_first_port(ext_bottom, "output"), _port_named(bottom, "in1"))
    group = controller.group_blocks([top, middle, bottom], name="Plant")
    view.refresh_visual_groups()

    group_item = view.group_items[group.uid]
    positions_before = {
        uid: float(item.pos().y())
        for uid, item in group_item.boundary_port_items.items()
    }

    inputs = [p for p in group.boundary_ports if p.direction == "input"]
    outputs = [p for p in group.boundary_ports if p.direction == "output"]
    group.boundary_ports = list(reversed(inputs)) + outputs
    controller._rebuild_group_boundary_ports(group)
    group_item.sync_boundary_ports()

    for uid, y in positions_before.items():
        assert float(group_item.boundary_port_items[uid].pos().y()) == y


def test_cross_group_delete_does_not_spawn_multiple_root_dashed_wires(qtbot, tmp_path):
    window = _create_window(qtbot, tmp_path)
    controller = window.project_controller
    view = window.view

    a = controller.add_block("sources", "constant")
    b = controller.add_block("operators", "gain")
    c = controller.add_block("operators", "sum")
    d = controller.add_block("operators", "gain")
    group_a = controller.group_blocks([a, b], name="Disturbance")
    group_b = controller.group_blocks([c, d], name="ControlLoop")
    controller.add_connection(_first_port(b, "output"), _first_port(c, "input"))
    view.refresh_visual_groups()

    connection = next(iter(controller.project_state.connections))
    controller.remove_connection(connection)
    view.refresh_visual_groups()
    view.refresh_manual_boundary_wires()

    assert len(view.manual_boundary_wires) == 0


def test_proxy_wires_to_child_group_border_inside_parent(qtbot, tmp_path):
    window = _create_window(qtbot, tmp_path)
    controller = window.project_controller
    view = window.view

    external = controller.add_block("sources", "constant")
    inner_a = controller.add_block("operators", "sum")
    inner_b = controller.add_block("controllers", "state_feedback")
    controller.add_connection(_first_port(external, "output"), _port_named(inner_a, "in1"))
    inner = controller.group_blocks([inner_a, inner_b], name="Regulator")
    monitor = controller.add_block("operators", "gain")
    parent = controller.group_blocks(
        [monitor],
        child_group_uids=[inner.uid],
        name="ControlLoop",
    )
    view.enter_group(parent.uid)

    boundary = controller.add_manual_boundary_port(parent.uid, "input", QPointF(20.0, 40.0))
    inner_group = controller.project_state.get_visual_group(inner.uid)
    child_boundary = next(
        port for port in inner_group.boundary_ports if port.direction == "input"
    )
    child_port = view.group_items[inner.uid].boundary_port_items[child_boundary.uid]

    assert controller.try_wire_boundary_endpoints(
        view.proxy_items[boundary.uid].port_item,
        child_port,
    )

    parent = controller.project_state.get_visual_group(parent.uid)
    wired = controller._find_boundary_port(parent, boundary.uid)
    assert wired.linked_port_uid == f"{inner_a.uid}:{_port_named(inner_a, 'in1').name}"
    view.refresh_manual_boundary_wires()
    assert f"{boundary.uid}:internal" in view.manual_boundary_wires


def _wire_path_end(wire: ManualBoundaryWireItem) -> QPointF:
    path = wire.path()
    return path.pointAtPercent(1.0)


def test_dashed_wire_follows_child_group_move_in_parent_view(qtbot, tmp_path):
    window = _create_window(qtbot, tmp_path)
    controller = window.project_controller
    view = window.view

    external = controller.add_block("sources", "constant")
    inner_a = controller.add_block("operators", "sum")
    inner_b = controller.add_block("controllers", "state_feedback")
    controller.add_connection(_first_port(external, "output"), _port_named(inner_a, "in1"))
    inner = controller.group_blocks([inner_a, inner_b], name="Regulator")
    monitor = controller.add_block("operators", "gain")
    parent = controller.group_blocks(
        [monitor],
        child_group_uids=[inner.uid],
        name="ControlLoop",
    )
    view.enter_group(parent.uid)

    boundary = controller.add_manual_boundary_port(parent.uid, "input", QPointF(20.0, 40.0))
    inner_group = controller.project_state.get_visual_group(inner.uid)
    child_boundary = next(
        port for port in inner_group.boundary_ports if port.direction == "input"
    )
    child_port = view.group_items[inner.uid].boundary_port_items[child_boundary.uid]
    assert controller.try_wire_boundary_endpoints(
        view.proxy_items[boundary.uid].port_item,
        child_port,
    )

    view.pop_view_level()
    controller.remove_connection(controller.project_state.connections[0])
    view.enter_group(parent.uid)
    view.refresh_manual_boundary_wires()

    wire = view.manual_boundary_wires[f"{boundary.uid}:internal"]
    child_item = view.group_items[inner.uid]
    anchor_before = child_item.get_boundary_anchor(child_boundary.uid)

    child_item.setPos(child_item.pos() + QPointF(50.0, 30.0))
    qtbot.wait(10)

    anchor_after = child_item.get_boundary_anchor(child_boundary.uid)
    wire_end = _wire_path_end(wire)
    assert anchor_before != anchor_after
    assert abs(wire_end.x() - anchor_after.x()) < 1.0
    assert abs(wire_end.y() - anchor_after.y()) < 1.0


def test_dashed_wire_follows_member_block_move_in_group_view(qtbot, tmp_path):
    window = _create_window(qtbot, tmp_path)
    controller = window.project_controller
    view = window.view

    src = controller.add_block("sources", "constant")
    gain = controller.add_block("operators", "gain")
    external = controller.add_block("operators", "sum")
    group = controller.group_blocks([src, gain])
    boundary = _manual_input_boundary(controller, view, group)
    controller._wire_manual_boundary_internal(
        group.uid, boundary.uid, _first_port(gain, "input")
    )

    view.pop_view_level()
    controller._wire_manual_boundary_external(
        group.uid, boundary.uid, _first_port(external, "output")
    )
    controller.remove_connection(controller.project_state.connections[0])

    view.enter_group(group.uid)
    view.refresh_manual_boundary_wires()
    wire = view.manual_boundary_wires[f"{boundary.uid}:internal"]
    gain_item = view.get_block_item_from_instance(gain)
    port_item = gain_item.get_port_item(_first_port(gain, "input").name)

    gain_item.setPos(gain_item.pos() + QPointF(40.0, 25.0))
    qtbot.wait(10)

    wire_end = _wire_path_end(wire)
    anchor_after = port_item.connection_anchor()
    assert abs(wire_end.x() - anchor_after.x()) < 1.0
    assert abs(wire_end.y() - anchor_after.y()) < 1.0
