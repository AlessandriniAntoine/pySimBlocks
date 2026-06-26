from PySide6.QtCore import Qt, QPointF
from PySide6.QtGui import QKeyEvent

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


def test_ctrl_r_flips_group_display_without_touching_members(qtbot, tmp_path):
    window = _create_window(qtbot, tmp_path)
    controller = window.project_controller
    view = window.view

    src = controller.add_block("sources", "constant")
    gain = controller.add_block("operators", "gain")
    out = controller.add_block("operators", "sum")
    controller.add_connection(_first_port(src, "output"), _first_port(gain, "input"))
    controller.add_connection(_first_port(gain, "output"), _first_port(out, "input"))
    group = controller.group_blocks([src, gain], name="Loop")

    src_item = view.get_block_item_from_instance(src)
    gain_item = view.get_block_item_from_instance(gain)
    group_item = view.group_items[group.uid]
    assert group_item.orientation == "normal"

    output_ports = [
        item
        for item in group_item.boundary_port_items.values()
        if item.boundary.direction == "output"
    ]
    assert output_ports
    assert output_ports[0].pos().x() == group_item.rect().width()

    view.diagram_scene.clearSelection()
    group_item.setSelected(True)
    view.keyPressEvent(
        QKeyEvent(
            QKeyEvent.Type.KeyPress, Qt.Key.Key_R, Qt.KeyboardModifier.ControlModifier
        )
    )

    assert group_item.orientation == "flipped"
    assert group.layout["orientation"] == "flipped"
    assert src_item.orientation == "normal"
    assert gain_item.orientation == "normal"
    flipped_outputs = [
        item
        for item in group_item.boundary_port_items.values()
        if item.boundary.direction == "output"
    ]
    assert flipped_outputs
    assert flipped_outputs[0].pos().x() == 0


def test_flipped_group_wire_exits_away_from_anchor(qtbot, tmp_path):
    window = _create_window(qtbot, tmp_path)
    controller = window.project_controller
    view = window.view

    src = controller.add_block("sources", "constant")
    gain = controller.add_block("operators", "gain")
    out = controller.add_block("operators", "sum")
    controller.add_connection(_first_port(src, "output"), _first_port(gain, "input"))
    controller.add_connection(_first_port(gain, "output"), _first_port(out, "input"))
    group = controller.group_blocks([src, gain], name="Loop")

    group_item = view.group_items[group.uid]
    connection = next(
        conn
        for conn in controller.project_state.connections
        if {conn.src_block().uid, conn.dst_block().uid} == {gain.uid, out.uid}
    )
    conn_item = view.connections[connection]

    anchor_before, outbound_before = conn_item.route.points[:2]
    assert outbound_before.x() > anchor_before.x()

    view.diagram_scene.clearSelection()
    group_item.setSelected(True)
    view.keyPressEvent(
        QKeyEvent(
            QKeyEvent.Type.KeyPress, Qt.Key.Key_R, Qt.KeyboardModifier.ControlModifier
        )
    )

    anchor_after, outbound_after = conn_item.route.points[:2]
    assert outbound_after.x() < anchor_after.x()


def test_ctrl_r_flips_proxy_display_without_touching_members(qtbot, tmp_path):
    window = _create_window(qtbot, tmp_path)
    controller = window.project_controller
    view = window.view

    gain = controller.add_block("operators", "gain")
    out = controller.add_block("operators", "sum")
    group = controller.group_blocks([gain, out], name="Loop")
    view.enter_group(group.uid)

    boundary = controller.add_manual_boundary_port(
        group.uid, "input", QPointF(50.0, 60.0)
    )
    proxy = view.proxy_items[boundary.uid]
    gain_item = view.get_block_item_from_instance(gain)
    assert gain_item.orientation == "normal"
    assert proxy.port_item.pos().x() == proxy.rect().width()

    view.diagram_scene.clearSelection()
    proxy.setSelected(True)
    view.keyPressEvent(
        QKeyEvent(
            QKeyEvent.Type.KeyPress, Qt.Key.Key_R, Qt.KeyboardModifier.ControlModifier
        )
    )

    assert proxy.orientation == "flipped"
    assert boundary.proxy_layout["orientation"] == "flipped"
    assert gain_item.orientation == "normal"
    assert proxy.port_item.pos().x() == 0



