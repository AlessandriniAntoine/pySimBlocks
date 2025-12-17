from pathlib import Path
from typing import Dict, List, Tuple
from pySimBlocks.core.block import Block
from pySimBlocks.core.config import ModelConfig


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

    def __init__(
            self,
            name: str = "model",
            model_yaml: str | Path | None = None,
            model_cfg: ModelConfig | None = None,
            verbose: bool = False,
        ):
        self.name = name
        self.verbose = verbose

        self.blocks: Dict[str, Block] = {}
        self.connections: List[Connection] = []

        self._output_execution_order: List[Block] = []
        self._state_execution_order: List[Block] = []

        if model_yaml is not None:
            if model_cfg is not None and not isinstance(model_cfg, ModelConfig):
                raise TypeError("model_cfg must be a ModelConfig")

            from pySimBlocks.project.build_model import build_model_from_yaml
            build_model_from_yaml(self, Path(model_yaml), model_cfg)
            if model_cfg is not None:
                model_cfg.validate(list(self.blocks.keys()))

    # ----------------------------------------------------------------------
    # Public methods
    # ----------------------------------------------------------------------
    def add_block(self, block: Block) -> Block:
        if block.name in self.blocks:
            raise ValueError(f"Block name '{block.name}' already exists.")

        self.blocks[block.name] = block
        return block


    def connect(self, src_block: str, src_port: str,
                      dst_block: str, dst_port: str) -> None:
        """
        Connect:
            blocks[src_block].outputs[src_port]
        to:
            blocks[dst_block].inputs[dst_port]
        """
        if src_block not in self.blocks:
            raise ValueError(
                    f"Unknown source block '{src_block}'. "
                    f"Known blocks: {list(self.blocks.keys())}"
                )
        if dst_block not in self.blocks:
            raise ValueError(
                    f"Unknown destination block '{dst_block}'. "
                    f"Known blocks: {list(self.blocks.keys())}"
                )

        self.connections.append(
            ((src_block, src_port), (dst_block, dst_port))
        )


    def build_execution_order(self):
        """
        Build Simulink-like execution order based solely on direct-feedthrough
        causal dependencies (Simulink PDF p.7).
        """

        blocks = self.blocks
        names = list(blocks.keys())

        vprint = print if self.verbose else (lambda *a, **k: None)

        vprint("\n================= BUILD EXECUTION ORDER =================")
        vprint(f"Blocks in model: {names}")

        # STEP 1 — Build dependency graph
        vprint("\n--- STEP 1: CONNECTION ANALYSIS (direct-feedthrough rules) ---")

        graph = {name: [] for name in names}
        indegree = {name: 0 for name in names}

        for (src, dst) in self.connections:
            src_block, src_port = src
            dst_block, dst_port = dst

            A = blocks[src_block]
            B = blocks[dst_block]

            if B.direct_feedthrough:
                graph[src_block].append(dst_block)
                indegree[dst_block] += 1
                vprint(f"  DEPENDENCY: {src_block}.{src_port} → {dst_block}.{dst_port} "
                       f"(direct-feedthrough)")
            else:
                vprint(f"  NO DEPENDENCY: {src_block}.{src_port} → {dst_block}.{dst_port} "
                       f"(destination NOT direct-feedthrough)")

        # Show resulting graph
        vprint("\nGraph adjacency list:")
        for k, v in graph.items():
            vprint(f"  {k}: {v}")

        vprint("\nInitial indegree:")
        for k, v in indegree.items():
            vprint(f"  {k}: {v}")

        # STEP 2 — Kahn topological sort
        vprint("\n--- STEP 2: TOPOLOGICAL SORT ---")

        from collections import deque
        ready = deque([b for b in names if indegree[b] == 0])

        vprint(f"Initial READY queue: {list(ready)}")

        execution_order = []

        while ready:
            current = ready.popleft()
            execution_order.append(current)

            vprint(f"\n==> EXECUTE: '{current}'")

            # Decrease indegree for successors
            for succ in graph[current]:
                indegree[succ] -= 1
                vprint(f"    indegree[{succ}] → {indegree[succ]}")
                if indegree[succ] == 0:
                    ready.append(succ)
                    vprint(f"    '{succ}' added to READY")

        # STEP 3 — Detect algebraic loops
        if len(execution_order) != len(names):
            vprint("\n!!! ALGEBRAIC LOOP DETECTED !!!")
            raise RuntimeError(
                "Algebraic loop detected: direct-feedthrough cycle exists."
            )

        # STEP 4 — Final result
        vprint("\n--- FINAL SIMULINK-LIKE EXECUTION ORDER ---")
        for i, b in enumerate(execution_order, 1):
            vprint(f"  {i}. {b}")
        vprint("========================================================\n")

        # Final storage
        self._output_execution_order = [blocks[n] for n in execution_order]

        return self._output_execution_order

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

    def execution_order(self):
        if not self._output_execution_order:
            return self.build_execution_order()
        return self._output_execution_order


    def predecessors_of(self, block_name):
        for (src, dst) in self.connections:
            if dst[0] == block_name:
                yield src[0]


    def resolve_sample_times(self, dt):
        """
        Resolve effective sample times for all blocks.

        Returns:
            has_explicit_rate (bool): True if at least one block defines a sample_time.
        """

        for b in self.blocks.values():
            if b.sample_time is None:
                b._effective_sample_time = dt
            else:
                b._effective_sample_time = b.sample_time
