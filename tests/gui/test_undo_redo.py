# Tests for the undo/redo feature
# to be executed with
# QT_QPA_PLATFORM=offscreen python -m pytest tests/gui/test_undo_redo.py -q
# otherwise the gui window will be opened by a test

import copy

from PySide6.QtCore import QPointF, QRectF, Qt

from pySimBlocks.gui.main_window import MainWindow


def _create_window(qtbot, tmp_path):
    window = MainWindow(tmp_path)
    window.confirm_discard_or_save = lambda _action_name: True
    qtbot.addWidget(window)
    window.show()
    qtbot.waitUntil(lambda: window.isVisible())
    return window


def _get_first_port(block, direction: str):
    for port in block.ports:
        if port.direction == direction:
            return port
    raise AssertionError(f"No port with direction={direction} for block {block.name}")


def _connection_count(window) -> int:
    return len(window.project_controller.project_state.connections)


def test_undo_redo_add_block(qtbot, tmp_path):
    window = _create_window(qtbot, tmp_path)
    controller = window.project_controller
    stack = window.undo_manager.stack

    initial_count = len(controller.project_state.blocks)
    block = controller.add_block("sources", "constant")

    assert len(controller.project_state.blocks) == initial_count + 1
    assert block in controller.project_state.blocks

    stack.undo()
    assert len(controller.project_state.blocks) == initial_count
    assert block not in controller.project_state.blocks

    stack.redo()
    assert len(controller.project_state.blocks) == initial_count + 1
    assert block in controller.project_state.blocks


def test_undo_redo_edit_block_name(qtbot, tmp_path):
    window = _create_window(qtbot, tmp_path)
    controller = window.project_controller
    stack = window.undo_manager.stack

    block = controller.add_block("sources", "constant")
    original_name = block.name
    new_name = f"{original_name}_edited"

    controller.update_block_param(block, {"name": new_name})
    assert block.name == new_name

    stack.undo()
    assert block.name == original_name

    stack.redo()
    assert block.name == new_name


def test_undo_redo_add_connection(qtbot, tmp_path):
    window = _create_window(qtbot, tmp_path)
    controller = window.project_controller
    stack = window.undo_manager.stack

    src_block = controller.add_block("sources", "constant")
    dst_block = controller.add_block("operators", "sum")
    src_port = _get_first_port(src_block, "output")
    dst_port = _get_first_port(dst_block, "input")

    controller.add_connection(src_port, dst_port)
    assert _connection_count(window) == 1

    stack.undo()
    assert _connection_count(window) == 0

    stack.redo()
    assert _connection_count(window) == 1


def test_undo_redo_remove_block_restores_connections(qtbot, tmp_path):
    window = _create_window(qtbot, tmp_path)
    controller = window.project_controller
    stack = window.undo_manager.stack

    src_block = controller.add_block("sources", "constant")
    dst_block = controller.add_block("operators", "sum")
    src_port = _get_first_port(src_block, "output")
    dst_port = _get_first_port(dst_block, "input")
    controller.add_connection(src_port, dst_port)

    assert _connection_count(window) == 1
    blocks_before_delete = len(controller.project_state.blocks)

    controller.remove_block(src_block)
    assert len(controller.project_state.blocks) == blocks_before_delete - 1
    assert _connection_count(window) == 0

    stack.undo()
    assert len(controller.project_state.blocks) == blocks_before_delete
    assert _connection_count(window) == 1

    stack.redo()
    assert len(controller.project_state.blocks) == blocks_before_delete - 1
    assert _connection_count(window) == 0


def test_undo_redo_move_resize_block(qtbot, tmp_path):
    window = _create_window(qtbot, tmp_path)
    controller = window.project_controller
    stack = window.undo_manager.stack

    block = controller.add_block("sources", "constant")
    block_item = window.view.get_block_item_from_instance(block)

    old_pos = QPointF(block_item.pos())
    old_rect = QRectF(block_item.rect())
    new_pos = QPointF(old_pos.x() + 25.0, old_pos.y() + 10.0)
    new_rect = QRectF(0.0, 0.0, old_rect.width() + 20.0, old_rect.height() + 10.0)

    controller.execute_move_resize_block(block, old_pos, old_rect, new_pos, new_rect)

    assert block_item.pos() == new_pos
    assert block_item.rect().width() == new_rect.width()
    assert block_item.rect().height() == new_rect.height()

    stack.undo()
    assert block_item.pos() == old_pos
    assert block_item.rect().width() == old_rect.width()
    assert block_item.rect().height() == old_rect.height()

    stack.redo()
    assert block_item.pos() == new_pos
    assert block_item.rect().width() == new_rect.width()
    assert block_item.rect().height() == new_rect.height()


def test_undo_redo_orientation_toggle(qtbot, tmp_path):
    window = _create_window(qtbot, tmp_path)
    controller = window.project_controller
    stack = window.undo_manager.stack

    block = controller.add_block("sources", "constant")
    block_item = window.view.get_block_item_from_instance(block)
    old_orientation = block_item.orientation

    controller.execute_toggle_orientation(block)
    assert block_item.orientation != old_orientation
    toggled_orientation = block_item.orientation

    stack.undo()
    assert block_item.orientation == old_orientation

    stack.redo()
    assert block_item.orientation == toggled_orientation


def test_redo_cleared_after_new_action(qtbot, tmp_path):
    window = _create_window(qtbot, tmp_path)
    controller = window.project_controller
    stack = window.undo_manager.stack

    block = controller.add_block("sources", "constant")
    assert block in controller.project_state.blocks

    stack.undo()
    assert stack.canRedo()

    controller.add_block("sources", "constant")
    assert not stack.canRedo()


def test_multistep_undo_redo_chain(qtbot, tmp_path):
    window = _create_window(qtbot, tmp_path)
    controller = window.project_controller
    stack = window.undo_manager.stack

    src_block = controller.add_block("sources", "constant")
    dst_block = controller.add_block("operators", "sum")
    controller.add_connection(_get_first_port(src_block, "output"), _get_first_port(dst_block, "input"))

    block_item = window.view.get_block_item_from_instance(src_block)
    old_pos = QPointF(block_item.pos())
    old_rect = QRectF(block_item.rect())
    new_pos = QPointF(old_pos.x() + 15.0, old_pos.y() + 15.0)
    new_rect = QRectF(0.0, 0.0, old_rect.width() + 10.0, old_rect.height() + 10.0)
    controller.execute_move_resize_block(src_block, old_pos, old_rect, new_pos, new_rect)

    old_params = copy.deepcopy(src_block.parameters)
    controller.update_block_param(src_block, {"name": f"{src_block.name}_v2"})

    assert len(controller.project_state.blocks) == 2
    assert _connection_count(window) == 1
    assert src_block.parameters == old_params

    for _ in range(5):
        stack.undo()

    assert len(controller.project_state.blocks) == 0
    assert _connection_count(window) == 0

    for _ in range(5):
        stack.redo()

    assert len(controller.project_state.blocks) == 2
    assert _connection_count(window) == 1


def test_keyboard_shortcuts_undo_redo(qtbot, tmp_path):
    window = _create_window(qtbot, tmp_path)
    controller = window.project_controller
    stack = window.undo_manager.stack

    controller.add_block("sources", "constant")
    assert len(controller.project_state.blocks) == 1

    window.view.setFocus()
    qtbot.waitUntil(lambda: window.view.hasFocus())

    qtbot.keyClick(window.view.viewport(), Qt.Key_Z, Qt.ControlModifier)
    assert len(controller.project_state.blocks) == 0

    qtbot.keyClick(window.view.viewport(), Qt.Key_Z, Qt.ControlModifier | Qt.ShiftModifier)
    assert len(controller.project_state.blocks) == 1
    assert stack.canUndo()

