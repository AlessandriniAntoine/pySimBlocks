from pySimBlocks.gui.main_window import MainWindow
from pySimBlocks.gui.models.visual_group import BoundaryPort, VisualGroup
from pySimBlocks.gui.services.yaml_tools import build_project_yaml


def _create_window(qtbot, tmp_path):
    window = MainWindow(tmp_path)
    window.confirm_discard_or_save = lambda _action_name: True
    qtbot.addWidget(window)
    window.show()
    qtbot.waitUntil(lambda: window.isVisible())
    return window


def test_visual_group_from_dict_preserves_group_layout_with_member_layouts():
    group = VisualGroup.from_dict(
        {
            "uid": "grp_1",
            "name": "Group",
            "members": ["a", "b"],
            "layout": {"x": -24.0, "y": -24.0, "width": 168.0, "height": 108.0},
            "member_layouts": {
                "a": {"x": 0.0, "y": 0.0, "width": 120.0, "height": 60.0},
            },
        }
    )
    assert group.layout["x"] == -24.0
    assert group.layout["width"] == 168.0


def test_build_project_yaml_includes_gui_groups(qtbot, tmp_path):
    window = _create_window(qtbot, tmp_path)
    state = window.project_state

    state.visual_groups = [
        VisualGroup(
            uid="grp_1",
            name="Group 1",
            parent_uid=None,
            members=["a", "b"],
            layout={"x": 10.0, "y": 20.0, "width": 120.0, "height": 70.0},
            boundary_ports=[
                BoundaryPort(
                    uid="bp_1",
                    direction="input",
                    linked_port_uid="p_1",
                    origin="manual",
                    linked_connection_uid="",
                    proxy_layout={"x": 1.0, "y": 2.0},
                )
            ],
            child_group_uids=[],
            member_layouts={
                "a": {"x": 10.0, "y": 20.0, "width": 120.0, "height": 60.0},
            },
        )
    ]

    raw = build_project_yaml(state, {})
    assert "gui" in raw
    assert "groups" in raw["gui"]
    assert len(raw["gui"]["groups"]) == 1
    group = raw["gui"]["groups"][0]
    assert group["uid"] == "grp_1"
    assert group["boundary_ports"][0]["origin"] == "manual"
    assert group["member_layouts"]["a"]["x"] == 10.0


def test_loader_restores_visual_groups_from_yaml(qtbot, tmp_path):
    project_yaml = tmp_path / "project.yaml"
    project_yaml.write_text(
        """schema_version: 1
project:
  name: grouped_project
simulation:
  dt: 0.01
  T: 1.0
  solver: fixed
diagram:
  blocks: []
  connections: []
gui:
  layout:
    blocks: {}
  groups:
    - uid: "grp_1"
      name: "Loop"
      parent_uid: null
      members: ["a", "b"]
      layout:
        x: 10.0
        y: 20.0
        width: 120.0
        height: 70.0
      boundary_ports:
        - uid: "bp_1"
          direction: input
          linked_port_uid: "port_a"
          origin: manual
          linked_connection_uid: ""
          proxy_layout: {x: 0.0, y: 0.0}
      child_group_uids: []
      member_layouts:
        a: {x: 5.0, y: 6.0, width: 120.0, height: 60.0}
"""
    )

    window = _create_window(qtbot, tmp_path)

    groups = window.project_state.visual_groups
    assert len(groups) == 1
    assert groups[0].uid == "grp_1"
    assert groups[0].boundary_ports[0].origin == "manual"
    assert groups[0].member_layouts["a"]["x"] == 5.0


def test_loader_keeps_backward_compatibility_without_gui_groups(qtbot, tmp_path):
    project_yaml = tmp_path / "project.yaml"
    project_yaml.write_text(
        """schema_version: 1
project:
  name: no_groups
simulation:
  dt: 0.01
  T: 1.0
  solver: fixed
diagram:
  blocks: []
  connections: []
gui:
  layout:
    blocks: {}
"""
    )

    window = _create_window(qtbot, tmp_path)

    assert window.project_state.visual_groups == []
