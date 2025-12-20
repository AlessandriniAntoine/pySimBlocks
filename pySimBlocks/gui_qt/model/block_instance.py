from pySimBlocks.gui_qt.model.port_instance  import PortInstance

class BlockInstance:
    """
    GUI-side mutable instance of a block.

    - References an immutable BlockMeta
    - Stores instance-level data (name, parameters)
    - Used by BlockItem and BlockDialog
    """

    def __init__(self, meta):
        self.meta = meta
        self.name = meta.name
        self.parameters = self._init_parameters()
        self.ports: list[PortInstance] = []

    def _init_parameters(self) -> dict:
        """
        Initialize instance parameters from metadata.
        """
        params = {}

        for pname, pmeta in self.meta.parameters.items():
            if pmeta.get("autofill", False):
                params[pname] = pmeta.get("default")
            else:
                params[pname] = None

        return params

    def resolve_ports(self) -> None:
        ports = []

        for direction in ("input", "output"):
            for pmeta in self.meta.ports[f"{direction}s"]:
                ports.extend(self._resolve_port_group(pmeta, direction))
        self.ports = ports


    def _resolve_port_group(self, pmeta, direction) -> list[PortInstance]:
        if not pmeta["dynamic"]:
            return [PortInstance(pmeta["pattern"], direction, self, pmeta)]

        source = pmeta["source"]
        pattern = pmeta["pattern"]

        if source["type"] == "parameter":
            value = self.parameters.get(source["parameter"])

            if value is None and "fallback" in pmeta:
                value = self.parameters.get(
                    pmeta["fallback"]["parameter"],
                    pmeta["fallback"]["default"],
                )
            return self._expand_ports(pattern, value, direction, pmeta)

        return []


    def _expand_ports(self, pattern, value, direction, meta) -> list[PortInstance]:
        ports = []
        operation = meta["source"].get("operation", '')

        if operation == "len":
            for i in range(1, len(value) +1):
                ports.append(PortInstance(pattern.format(val=i), direction, self, meta))

        elif operation == "keys":
            if value:
                for key in value:
                    ports.append(PortInstance(pattern.format(val=key), direction, self, meta))

        elif operation == "value":
            for i in range(1, int(value)+1):
                ports.append(PortInstance(pattern.format(val=i), direction, self, meta))

        return ports
