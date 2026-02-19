import pytest

from pySimBlocks.gui.main_window import MainWindow

def test_main_window_opens(qtbot, tmp_path):

    window = MainWindow(tmp_path)

    qtbot.addWidget(window)
    window.show()

    qtbot.waitUntil(lambda: window.isVisible())

    assert window.isVisible()
    assert window.view is not None
    assert window.blocks is not None
    assert window.toolbar is not None
    assert window.project_controller is not None
    assert len(window.block_registry) > 0


@pytest.fixture
def minimal_project(tmp_path):
    """Create a minimal pySimBlocks project.yaml."""
    project_yaml = tmp_path / "project.yaml"
    project_yaml.write_text(
        """schema_version: 1
project:
  name: test_gui_project
simulation:
  dt: 0.01
  T: 3.0
  solver: fixed
  logging:
  - ref.outputs.out
  - plant.outputs.y
  - pid.outputs.u
  plots:
  - title: Ref vs Output
    signals: [ref.outputs.out, plant.outputs.y]
  - title: Command
    signals: [pid.outputs.u]
diagram:
  blocks:
  - name: ref
    category: sources
    type: step
    parameters:
      value_before: [[0.0]]
      value_after: [[1.0]]
      start_time: 0.5
  - name: error
    category: operators
    type: sum
    parameters:
      signs: +-
  - name: pid
    category: controllers
    type: pid
    parameters:
      controller: PI
      Kp: [[2.0]]
      Ki: [[1.0]]
      Kd: 0.0
  - name: plant
    category: systems
    type: linear_state_space
    parameters:
      A: [[0.95]]
      B: [[0.5]]
      C: [[1.0]]
      x0: [[0.0]]
  connections:
  - name: c1
    ports: [ref.out, error.in1]
  - name: c2
    ports: [plant.y, error.in2]
  - name: c3
    ports: [error.out, pid.e]
  - name: c4
    ports: [pid.u, plant.u]
gui:
  layout:
    blocks:
      ref:
        x: 0.0
        y: -80.0
        orientation: normal
      error:
        x: 195.0
        y: -71.0
        orientation: normal
      pid:
        x: 364.0
        y: -71.0
        orientation: normal
      plant:
        x: 535.0
        y: -70.0
        orientation: normal
"""
    )

    return tmp_path

def test_main_window_loads_project(qtbot, minimal_project):
    """Test that MainWindow opens and auto-loads a project from project.yaml."""
    window = MainWindow(minimal_project)
    qtbot.addWidget(window)
    window.show()
    qtbot.waitUntil(lambda: window.isVisible())

    assert window.isVisible()
    assert window.project_controller.project_state.directory_path == minimal_project
    assert window.view is not None
    assert window.blocks is not None
    assert window.toolbar is not None

    assert len(window.block_registry) > 0
    block_names = [item.instance.name for item in window.view.block_items.values()]
    for expected in ["ref", "error", "pid", "plant"]:
        assert expected in block_names

    expected_connections = [
        ("ref", "out", "error", "in1"),
        ("plant", "y", "error", "in2"),
        ("error", "out", "pid", "e"),
        ("pid", "u", "plant", "u"),
    ]

    actual_connections = [
        (
            conn.src_block().name,
            conn.src_port.name,
            conn.dst_block().name,
            conn.dst_port.name
        )
        for conn in window.view.connections.keys()
    ]

    for conn in expected_connections:
        assert conn in actual_connections

def test_run_simulation(qtbot, minimal_project):
    """
    Smoke test: Load a minimal project and run the simulation via ToolBarView.
    """
    window = MainWindow(minimal_project)
    qtbot.addWidget(window)
    window.show()
    qtbot.waitUntil(lambda: window.isVisible())

    project_state = window.project_state
    toolbar = window.toolbar

    assert not bool(project_state.logs)

    toolbar.on_run_sim()

    assert bool(project_state.logs)
    assert isinstance(project_state.logs, dict)
    assert all(isinstance(v, list) for v in project_state.logs.values())
