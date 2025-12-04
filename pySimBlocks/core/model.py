from typing import Dict, List, Tuple
from pySimBlocks.core.block import Block


# A connection is:
#    ( (src_block, src_port), (dst_block, dst_port) )
Connection = Tuple[Tuple[str, str], Tuple[str, str]]


class Model:
    """
    Discrete-time block-diagram model (Simulink-like).

    Responsibilities:
      - Store blocks.
      - Store signal connections.
      - Build execution order (topological sort).
      - Provide fast access to downstream connections.

    Notes:
      * Topological sorting is applied only to the combinational graph.
      * Blocks with state (i.e., blocks where next_state is non-empty)
        are treated as "cycle breakers" (delay elements),
        exactly like Simulink does for algebraic loops.
    """

    def __init__(self, name: str = "model"):
        self.name = name

        # Dict[str -> Block]
        self.blocks: Dict[str, Block] = {}

        # List of connections (src, dst)
        self.connections: List[Connection] = []

        # Internally stored execution order (computed on build)
        self._execution_order: List[Block] = []

    # ----------------------------------------------------------------------
    # BLOCK REGISTRATION
    # ----------------------------------------------------------------------
    def add_block(self, block: Block) -> Block:
        if block.name in self.blocks:
            raise ValueError(f"Block name '{block.name}' already exists.")

        self.blocks[block.name] = block
        return block

    # ----------------------------------------------------------------------
    # CONNECTIONS
    # ----------------------------------------------------------------------
    def connect(self, src_block: str, src_port: str,
                      dst_block: str, dst_port: str) -> None:
        """
        Connect:
            blocks[src_block].outputs[src_port]
        to:
            blocks[dst_block].inputs[dst_port]
        """
        if src_block not in self.blocks:
            raise ValueError(f"Unknown source block '{src_block}'.")
        if dst_block not in self.blocks:
            raise ValueError(f"Unknown destination block '{dst_block}'.")

        self.connections.append(
            ((src_block, src_port), (dst_block, dst_port))
        )

    # ----------------------------------------------------------------------
    # GRAPH TOPOLOGY
    # ----------------------------------------------------------------------
    def build_execution_order(self) -> List[Block]:
        graph = {name: [] for name in self.blocks}
        indegree = {name: 0 for name in self.blocks}

        for (src, dst) in self.connections:
            src_block, _ = src
            dst_block, _ = dst

            # Nouvelle règle :
            #   - on ignore les arêtes ENTRANT dans un bloc à état
            #     (ses entrées servent au calcul de x[k+1], donc pas
            #      dans le graphe combinatoire du pas k)
            #   - on garde toutes les autres arêtes
            if len(self.blocks[dst_block].state) == 0:
                graph[src_block].append(dst_block)
                indegree[dst_block] += 1

        # Topological sort identique ensuite...
        queue = [name for name in self.blocks if indegree[name] == 0]
        topo_order = []

        while queue:
            node = queue.pop(0)
            topo_order.append(node)

            for neigh in graph[node]:
                indegree[neigh] -= 1
                if indegree[neigh] == 0:
                    queue.append(neigh)

        if len(topo_order) != len(self.blocks):
            raise RuntimeError(
                "Algebraic loop detected: a feedback loop exists without a "
                "stateful block to break it."
            )

        self._execution_order = [self.blocks[name] for name in topo_order]
        return self._execution_order


    # ----------------------------------------------------------------------
    # HELPERS FOR THE SIMULATOR
    # ----------------------------------------------------------------------
    def downstream_of(self, block_name: str):
        """
        Returns all connections where block_name is the source.
        """
        for (src, dst) in self.connections:
            if src[0] == block_name:
                yield (src, dst)

    def execution_order(self) -> List[Block]:
        if not self._execution_order:
            return self.build_execution_order()
        return self._execution_order
