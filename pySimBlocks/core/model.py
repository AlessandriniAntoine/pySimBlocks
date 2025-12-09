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

    def __init__(self, name: str = "model", verbose: bool = False):
        self.name = name
        self.verbose = verbose

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
    # BUILD EXECUTION ORDER
    # ----------------------------------------------------------------------
    def build_execution_order(self):
        """
        Build execution order following Simulink-like scheduling:

            1) Memory blocks (stateful)       → no direct feedthrough
            2) Sources (no state, no inputs)  → no direct feedthrough
            3) Combinational blocks           → direct feedthrough (topo sort)

        State update order = only stateful blocks (topo sorted if needed).
        """

        blocks = self.blocks
        names = list(blocks.keys())

        # ------------------------------
        # CATEGORY A: stateful blocks
        # ------------------------------
        stateful = []
        for n in names:
            blk = blocks[n]
            if len(blk.state) > 0:
                stateful.append(n)

        # topo sort inside stateful if needed
        Gs = {n: [] for n in stateful}
        indeg_s = {n: 0 for n in stateful}
        for (src, dst) in self.connections:
            s, _ = src
            d, _ = dst
            if s in stateful and d in stateful:
                Gs[s].append(d)
                indeg_s[d] += 1

        q = [n for n in stateful if indeg_s[n] == 0]
        state_order = []
        indeg_tmp = indeg_s.copy()

        while q:
            n = q.pop(0)
            state_order.append(n)
            for v in Gs[n]:
                indeg_tmp[v] -= 1
                if indeg_tmp[v] == 0:
                    q.append(v)

        # -----------------------------------
        # CATEGORY B: source blocks
        # -----------------------------------
        sources = [n for n in names if blocks[n].is_source]

        # -----------------------------------
        # CATEGORY C: direct-feedthrough blocks
        # -----------------------------------
        combinational = [
            n for n in names
            if blocks[n].direct_feedthrough and not blocks[n].is_source
        ]

        # topo sort combinational-only subgraph
        Gc = {n: [] for n in combinational}
        indeg_c = {n: 0 for n in combinational}

        for (src, dst) in self.connections:
            s, _ = src
            d, _ = dst
            if s in combinational and d in combinational:
                Gc[s].append(d)
                indeg_c[d] += 1

        q = [n for n in combinational if indeg_c[n] == 0]
        comb_order = []
        indeg_tmp2 = indeg_c.copy()

        while q:
            n = q.pop(0)
            comb_order.append(n)
            for v in Gc[n]:
                indeg_tmp2[v] -= 1
                if indeg_tmp2[v] == 0:
                    q.append(v)

        # ------------------------------
        # FINAL OUTPUT UPDATE ORDER
        # ------------------------------
        output_order = state_order + sources + comb_order

        if self.verbose:
            print("===== BUILD EXECUTION ORDER =====")
            print("Blocks:", names)
            print("Stateful:", state_order)
            print("Sources:", sources)
            print("Combinational:", comb_order)
            print("OUTPUT ORDER:", output_order)
            print("STATE ORDER :", state_order)
            print("=================================\n")

        self.output_update_order = [blocks[n] for n in output_order]
        self.state_update_order  = [blocks[n] for n in state_order]

        return self.output_update_order, self.state_update_order




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
