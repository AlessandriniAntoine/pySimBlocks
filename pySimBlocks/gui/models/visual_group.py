from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class BoundaryPort:
    """Describe one visual group boundary port."""

    uid: str
    direction: str
    linked_port_uid: str = ""
    external_port_uid: str = ""
    origin: str = "auto"
    linked_connection_uid: str = ""
    label: str = ""
    proxy_uid: str = ""
    proxy_layout: dict[str, float] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Serialize the boundary port to a YAML-friendly mapping."""
        out: dict[str, Any] = {
            "uid": self.uid,
            "direction": self.direction,
            "linked_port_uid": self.linked_port_uid,
            "external_port_uid": self.external_port_uid,
            "origin": self.origin,
            "linked_connection_uid": self.linked_connection_uid,
        }
        if self.label:
            out["label"] = self.label
        if self.proxy_uid:
            out["proxy_uid"] = self.proxy_uid
        if self.proxy_layout:
            out["proxy_layout"] = self.proxy_layout
        return out

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "BoundaryPort":
        """Build a boundary port from a raw mapping."""
        return cls(
            uid=str(data.get("uid", "")),
            direction=str(data.get("direction", "")),
            linked_port_uid=str(data.get("linked_port_uid", "")),
            external_port_uid=str(data.get("external_port_uid", "")),
            origin=str(data.get("origin", "auto")),
            linked_connection_uid=str(data.get("linked_connection_uid", "")),
            label=str(data.get("label", "")),
            proxy_uid=str(data.get("proxy_uid", "")),
            proxy_layout=dict(data.get("proxy_layout", {}))
            if isinstance(data.get("proxy_layout", {}), dict)
            else {},
        )


@dataclass
class VisualGroup:
    """Store one visual-only group definition."""

    uid: str
    name: str
    members: list[str] = field(default_factory=list)
    parent_uid: str | None = None
    layout: dict[str, float] = field(default_factory=dict)
    boundary_ports: list[BoundaryPort] = field(default_factory=list)
    child_group_uids: list[str] = field(default_factory=list)
    member_layouts: dict[str, dict[str, Any]] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Serialize the visual group to a YAML-friendly mapping."""
        out: dict[str, Any] = {
            "uid": self.uid,
            "name": self.name,
            "parent_uid": self.parent_uid,
            "members": list(self.members),
            "layout": dict(self.layout),
            "boundary_ports": [port.to_dict() for port in self.boundary_ports],
            "child_group_uids": list(self.child_group_uids),
            "member_layouts": {
                uid: dict(layout) for uid, layout in self.member_layouts.items()
            },
        }
        return out

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "VisualGroup":
        """Build a visual group from a raw mapping."""
        boundary_ports_raw = data.get("boundary_ports", [])
        boundary_ports = []
        if isinstance(boundary_ports_raw, list):
            boundary_ports = [
                BoundaryPort.from_dict(item)
                for item in boundary_ports_raw
                if isinstance(item, dict)
            ]

        members = data.get("members", [])
        if not isinstance(members, list):
            members = []

        layout = data.get("layout", {})
        if not isinstance(layout, dict):
            layout = {}

        children = data.get("child_group_uids", [])
        if not isinstance(children, list):
            children = []

        parent_uid = data.get("parent_uid", None)
        if parent_uid is not None:
            parent_uid = str(parent_uid)

        member_layouts_raw = data.get("member_layouts", {})
        member_layouts: dict[str, dict[str, Any]] = {}
        if isinstance(member_layouts_raw, dict):
            for uid, member_layout in member_layouts_raw.items():
                if isinstance(member_layout, dict):
                    member_layouts[str(uid)] = dict(member_layout)

        return cls(
            uid=str(data.get("uid", "")),
            name=str(data.get("name", "")),
            members=[str(m) for m in members],
            parent_uid=parent_uid,
            layout=dict(layout),
            boundary_ports=boundary_ports,
            child_group_uids=[str(c) for c in children],
            member_layouts=member_layouts,
        )
