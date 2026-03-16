# ******************************************************************************
#                                  pySimBlocks
#                     Copyright (c) 2026 Université de Lille & INRIA
# ******************************************************************************
#  This program is free software: you can redistribute it and/or modify it
#  under the terms of the GNU Lesser General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or (at your
#  option) any later version.
#
#  This program is distributed in the hope that it will be useful, but WITHOUT
#  ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
#  FITNESS FOR A PARTICULAR PURPOSE.  See the GNU Lesser General Public License
#  for more details.
#
#  You should have received a copy of the GNU Lesser General Public License
#  along with this program.  If not, see <https://www.gnu.org/licenses/>.
# ******************************************************************************
#  Authors: see Authors.txt
# ******************************************************************************

from collections import deque
from pathlib import Path
from typing import Any, Dict, List, Tuple

from pySimBlocks.core.block import Block

# A connection is:
#    ( (src_block, src_port), (dst_block, dst_port) )
Connection = Tuple[Tuple[str, str], Tuple[str, str]]


class Model:
    """Discrete-time block-diagram model (Simulink-like).
 
    Stores blocks and signal connections, builds the topological execution
    order, and provides fast access to downstream connections.
 
    Topological sorting is applied only to the combinational (direct-
    feedthrough) graph. Stateful blocks act as cycle breakers, exactly as
    Simulink handles algebraic loops (see Simulink PDF p.7).
 
    Attributes:
        name: Identifier for this model.
        verbose: If True, print detailed execution-order build logs.
        blocks: Registry of blocks keyed by name.
        connections: List of signal connections.
    """

    def __init__(
            self,
            name: str = "model",
            model_data: Dict[str, Any] | None = None,
            params_dir: Path | None = None,
            verbose: bool = False,
        ):
        """Initialize a model.
 
        Args:
            name: Identifier for this model.
            model_data: Optional dict loaded from a YAML project file.
                If provided, blocks and connections are built immediately.
            params_dir: Directory of the project file, for resolving
                relative paths. None if not applicable.
            verbose: If True, print execution-order build logs.
        """
        self.name = name
        self.verbose = verbose

        self.blocks: Dict[str, Block] = {}
        self.connections: List[Connection] = []

        self._output_execution_order: List[Block] = []
        self._state_execution_order: List[Block] = []

        self._downstream_map: Dict[str, List[Connection]] = {}
        self._connections_dirty: bool = True

        if model_data is not None:
            from pySimBlocks.project.build_model import build_model_from_dict
            build_model_from_dict(self, model_data, params_dir=params_dir)

    # --------------------------------------------------------------------------
    # Public methods
    # --------------------------------------------------------------------------

    def add_block(self, block: Block) -> Block:
        """Add a block to the model.
 
        Args:
            block: Block instance to register.
 
        Returns:
            The registered block.
 
        Raises:
            ValueError: If a block with the same name already exists.
        """
        if block.name in self.blocks:
            raise ValueError(f"Block name '{block.name}' already exists.")

        self.blocks[block.name] = block
        return block

    def get_block_by_name(self, name: str) -> Block:
        """Return a block by its name.
 
        Args:
            name: Name of the block to retrieve.
 
        Returns:
            The matching Block instance.
 
        Raises:
            ValueError: If no block with that name exists.
        """
        if name not in self.blocks:
            raise ValueError(
                f"Block name '{name}' not found. Known blocks: {list(self.blocks.keys())}"
            )
        return self.blocks[name]

    def connect(self, src_block: str, src_port: str,
                      dst_block: str, dst_port: str) -> None:
        """Connect an output port to an input port.
 
        Registers a connection from ``blocks[src_block].outputs[src_port]``
        to ``blocks[dst_block].inputs[dst_port]``.
 
        Args:
            src_block: Name of the source block.
            src_port: Name of the source output port.
            dst_block: Name of the destination block.
            dst_port: Name of the destination input port.
 
        Raises:
            ValueError: If src_block or dst_block is not registered.
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
        self._connections_dirty = True

    def build_execution_order(self):
        """Build the Simulink-like output execution order.
 
        Runs a Kahn topological sort on the direct-feedthrough dependency
        graph. Blocks without direct feedthrough act as cycle breakers.
 
        Returns:
            Ordered list of blocks for output_update execution.
 
        Raises:
            RuntimeError: If a direct-feedthrough cycle (algebraic loop)
                is detected.
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

            block_dist = blocks[dst_block]

            if block_dist.direct_feedthrough:
                graph[src_block].append(dst_block)
                indegree[dst_block] += 1
                vprint(f"  DEPENDENCY: {src_block}.{src_port} -> {dst_block}.{dst_port} "
                       f"(direct-feedthrough)")
            else:
                vprint(f"  NO DEPENDENCY: {src_block}.{src_port} -> {dst_block}.{dst_port} "
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
                vprint(f"    indegree[{succ}] -> {indegree[succ]}")
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

    def downstream_of(self, block_name: str) -> List[Connection]:
        """Return all connections where block_name is the source.
 
        Args:
            block_name: Name of the source block.
 
        Returns:
            List of connections originating from block_name.
        """
        """
        Returns all connections where block_name is the source.
        """
        if self._connections_dirty or not self._downstream_map:
            self._rebuild_downstream_map()
        return self._downstream_map.get(block_name, [])

    def execution_order(self) -> List[Block]:
        """Return the output execution order, building it if necessary.
 
        Returns:
            Ordered list of blocks for output_update execution.
        """
        if not self._output_execution_order:
            return self.build_execution_order()
        return self._output_execution_order

    def predecessors_of(self, block_name):
        """Yield the names of all blocks that feed into block_name.
 
        Args:
            block_name: Name of the destination block.
 
        Yields:
            Source block names connected to block_name.
        """
        for (src, dst) in self.connections:
            if dst[0] == block_name:
                yield src[0]

    def resolve_sample_times(self, dt) -> None:
        """Resolve effective sample times for all blocks.
 
        Blocks with an explicit sample_time keep it; others inherit dt.
 
        Args:
            dt: Global simulation time step in seconds.
        """        
        for b in self.blocks.values():
            if b.sample_time is None:
                b._effective_sample_time = dt
            else:
                b._effective_sample_time = b.sample_time


    # --------------------------------------------------------------------------
    # Private methods
    # --------------------------------------------------------------------------

    def _rebuild_downstream_map(self) -> None:
        """Rebuild the downstream connection map from the current connections."""
        downstream = {name: [] for name in self.blocks.keys()}
        for (src, dst) in self.connections:
            downstream[src[0]].append((src, dst))
        self._downstream_map = downstream
        self._connections_dirty = False
