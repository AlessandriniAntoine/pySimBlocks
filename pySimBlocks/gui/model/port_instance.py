
class PortInstance:
    def __init__(
        self,
        name: str,
        direction: str,
        block,
        meta: dict,
    ):
        self.name = name
        self.direction = direction
        self.block = block
        self.meta = meta
