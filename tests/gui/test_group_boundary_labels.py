from PySide6.QtCore import QPointF

from pySimBlocks.gui.group_boundary_labels import (
    boundary_port_label,
    manual_boundary_display_label,
)
from pySimBlocks.gui.models.visual_group import BoundaryPort, VisualGroup


def _first_port(block, direction: str):
    for port in block.ports:
        if port.direction == direction:
            return port
    raise AssertionError(f"No {direction} port on {block.name}")


def _port_named(block, name: str):
    for port in block.ports:
        if port.name == name:
            return port
    raise AssertionError(f"No port named {name} for block {block.name}")


def _create_window(qtbot, tmp_path):
    from pySimBlocks.gui.main_window import MainWindow

    window = MainWindow(tmp_path)
    window.confirm_discard_or_save = lambda _action_name: True
    qtbot.addWidget(window)
    window.show()
    qtbot.waitUntil(lambda: window.isVisible())
    return window


def test_boundary_port_label_input_shows_external_source(qtbot, tmp_path):
    window = _create_window(qtbot, tmp_path)
    controller = window.project_controller

    src = controller.add_block("sources", "constant")
    _first_port(src, "output").display_as = "u"
    gain = controller.add_block("operators", "gain")
    out = controller.add_block("operators", "sum")
    controller.add_connection(_first_port(src, "output"), _first_port(gain, "input"))
    controller.add_connection(_first_port(gain, "output"), _first_port(out, "input"))

    group = controller.group_blocks([gain, out], name="G")
    boundary = next(p for p in group.boundary_ports if p.direction == "input")

    assert boundary_port_label(controller.project_state, group, boundary) == "u"


def test_boundary_port_label_output_shows_external_destination(qtbot, tmp_path):
    window = _create_window(qtbot, tmp_path)
    controller = window.project_controller

    src = controller.add_block("sources", "constant")
    gain = controller.add_block("operators", "gain")
    sink = controller.add_block("operators", "sum")
    _port_named(sink, "in1").display_as = "y"
    controller.add_connection(_first_port(src, "output"), _first_port(gain, "input"))
    controller.add_connection(_first_port(gain, "output"), _port_named(sink, "in1"))

    group = controller.group_blocks([src, gain], name="G")
    boundary = next(p for p in group.boundary_ports if p.direction == "output")

    assert boundary_port_label(controller.project_state, group, boundary) == "y"


def test_boundary_port_label_manual_defaults_to_in_or_out():
    boundary = BoundaryPort(uid="b1", direction="input", origin="manual")
    group = VisualGroup(uid="g1", name="G", members=["m1"], boundary_ports=[boundary])

    class _State:
        connections = []

    assert boundary_port_label(_State(), group, boundary) == "In"
    assert manual_boundary_display_label(boundary) == "In"

    out = BoundaryPort(uid="b2", direction="output", origin="manual")
    assert manual_boundary_display_label(out) == "Out"


def test_boundary_port_label_manual_keeps_proxy_name_when_internally_wired(qtbot, tmp_path):
    window = _create_window(qtbot, tmp_path)
    controller = window.project_controller
    view = window.view

    src = controller.add_block("sources", "constant")
    gain = controller.add_block("operators", "gain")
    group = controller.group_blocks([src, gain])
    view.enter_group(group.uid)
    boundary = controller.add_manual_boundary_port(group.uid, "input", QPointF(40.0, 50.0))
    controller._wire_manual_boundary_internal(
        group.uid, boundary.uid, _first_port(gain, "input")
    )

    assert boundary.label == "In"
    assert boundary_port_label(controller.project_state, group, boundary) == "In"
    assert controller.boundary_proxy_label(boundary) == "In"
