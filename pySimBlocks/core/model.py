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
        Build execution order respecting Simulink semantics:

            RULE 1 : Combinational graph G_stateless contains ONLY stateless→stateless.
            RULE 2 : Stable topological sort of G_stateless.
            RULE 3 : Build full causal graph G_all (all blocks, with all edges).
            RULE 4 : Insert stateful blocks AFTER all their producers from G_all.
        """

        blocks = self.blocks
        names = list(blocks.keys())  # stable priority = order of addition

        if self.verbose:
            print("\n===== BUILD EXECUTION ORDER =====")
            print("Block list:", names)

        # ------------------------------------------------------------
        # Identify stateless vs stateful
        # ------------------------------------------------------------
        stateless = {n for n in names if len(blocks[n].state) == 0}
        stateful  = {n for n in names if len(blocks[n].state) != 0}

        if self.verbose:
            print("STATELESS:", stateless)
            print("STATEFUL :", stateful)

        # ------------------------------------------------------------
        # RULE 1 — Build combinational graph G_stateless
        # ------------------------------------------------------------
        G_stateless = {n: [] for n in names}
        indegree = {n: 0 for n in names}

        for (src, dst) in self.connections:
            src_block, _ = src
            dst_block, _ = dst

            if src_block in stateless and dst_block in stateless:
                G_stateless[src_block].append(dst_block)
                indegree[dst_block] += 1

        if self.verbose:
            print("\nG_stateless (only stateless→stateless):")
            for k in names:
                print(f"  {k}: {G_stateless[k]}")
            print("INDEGREE:", indegree)

        # ------------------------------------------------------------
        # RULE 2 — Topological sort of G_stateless (stable)
        # ------------------------------------------------------------
        queue = [n for n in names if indegree[n] == 0]
        queue.sort(key=lambda x: names.index(x))

        topo_stateless = []
        indeg = indegree.copy()

        while queue:
            node = queue.pop(0)
            topo_stateless.append(node)

            for neigh in G_stateless[node]:
                indeg[neigh] -= 1
                if indeg[neigh] == 0:
                    queue.append(neigh)

            queue.sort(key=lambda x: names.index(x))

        if self.verbose:
            print("\nTopological order from G_stateless:")
            print("  topo_stateless:", topo_stateless)

        # STAT CHECK
        # (stateless nodes will be reordered later; stateful temporarily appear here
        #  but will be repositioned using RULE 4)
        # ------------------------------------------------------------

        # ------------------------------------------------------------
        # RULE 3 — Build causal graph G_all
        #
        # Full graph including stateful and stateless; used to position stateful.
        # ------------------------------------------------------------
        G_all = {n: [] for n in names}
        preds = {n: set() for n in names}

        for (src, dst) in self.connections:
            src_block, _ = src
            dst_block, _ = dst

            # ALL edges matter for causal ordering
            G_all[src_block].append(dst_block)
            preds[dst_block].add(src_block)

        if self.verbose:
            print("\nG_all (full causal graph):")
            for k in names:
                print(f"  {k}: {G_all[k]}")

            print("\nPredecessors (for stateful positioning):")
            for k in names:
                print(f"  {k}: {preds[k]}")

        # ------------------------------------------------------------
        # RULE 4 — Build final order:
        #
        # 1. Start with the stateless topo order, but KEEP ONLY STATELESS there.
        # 2. Insert stateful blocks after ALL their predecessors (from G_all).
        # ------------------------------------------------------------
        stateless_order = [n for n in topo_stateless if n in stateless]

        final_order = stateless_order.copy()

        if self.verbose:
            print("\nInitial stateless order:", stateless_order)

        # Insert each stateful block
        for sf in stateful:
            # find all producers of sf
            producers = preds[sf]  # set of predecessor blocks

            # position = index just AFTER the max position of its producers
            max_pos = -1
            for p in producers:
                if p in final_order:
                    max_pos = max(max_pos, final_order.index(p))

            insert_pos = max_pos + 1

            if self.verbose:
                print(f"\nPlacing stateful block '{sf}' after producers {producers}")
                print(f" -> insert at position {insert_pos}")

            final_order.insert(insert_pos, sf)

        if self.verbose:
            print("\nFINAL EXECUTION ORDER:", final_order)
            print("===== END BUILD =====\n")

        # Save
        self._execution_order = [blocks[n] for n in final_order]
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
