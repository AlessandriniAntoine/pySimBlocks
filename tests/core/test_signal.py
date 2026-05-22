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

import numpy as np
import pytest
 
from pySimBlocks.core.model import Model
from pySimBlocks.core.config import SimulationConfig
from pySimBlocks.core.simulator import Simulator
from pySimBlocks.blocks.operators.gain import Gain
from pySimBlocks.blocks.operators.sum import Sum
from pySimBlocks.blocks.operators.delay import Delay
 
 
DT = 0.1
 
 
def make_sim(model: Model, T: float = 0.5) -> Simulator:
    """Build a Simulator with a fixed-step internal clock.

    Args:
        model: The block-diagram model to simulate.
        T: Simulation end time in seconds. Defaults to 0.5.

    Returns:
        Simulator configured with dt=0.1, t0=0.0, solver='fixed'.
    """
    cfg = SimulationConfig(dt=DT, T=T, t0=0.0, solver="fixed")
    return Simulator(model, cfg)
 

def test_connect_shares_signal_object():
    """Verify that model.connect() establishes a shared Signal reference.

    After connecting G.out to S.in1, both ports must point to the exact
    same Signal instance (identity, not equality).
    """
    m = Model("m")
    g = m.add_block(Gain("G", gain=2.0))
    s = m.add_block(Sum("S", signs="++"))
    s.set_input("in2", np.zeros((1, 1)))
 
    m.connect("G", "out", "S", "in1")
 
    assert g.outputs["out"] is s.inputs["in1"]
 
 
def test_signal_value_propagates_by_reference():
    """Verify that writing to a source output is immediately visible on the destination input.

    After connect(), mutating g.outputs['out'].value must be reflected
    in s.inputs['in1'].value without any copy or reassignment.
    """
    m = Model("m")
    g = m.add_block(Gain("G", gain=1.0))
    s = m.add_block(Sum("S", signs="++"))
    s.set_input("in2", np.zeros((1, 1)))
 
    m.connect("G", "out", "S", "in1")
 
    g.outputs["out"].value = np.array([[42.0]])
    assert np.allclose(s.inputs["in1"].value, np.array([[42.0]]))
 
 
def test_link_stable_across_steps():
    """Verify that the Signal link is never broken across multiple simulation steps.

    Topology: G(gain=3, u=2) -> S.in1, SRC(gain=1, u=1) -> S.in2.
    Expected: S.out == 7.0 at every step (3*2 + 1*1).
    """
    m = Model("m")
    src = m.add_block(Gain("SRC", gain=1.0))
    g   = m.add_block(Gain("G",   gain=3.0))
    s   = m.add_block(Sum("S",    signs="++"))
 
    src.set_input("in", np.array([[1.0]]))
    g.set_input("in",   np.array([[2.0]]))
 
    m.connect("G",   "out", "S", "in1")
    m.connect("SRC", "out", "S", "in2")
 
    sim = make_sim(m, T=0.5)
    logs = sim.run(logging=["S.outputs.out"])
 
    values = np.array(logs["S.outputs.out"])
    assert np.all(np.isclose(values, 7.0)), f"unexpected values: {values.flatten()}"
 
 
def test_link_stable_with_stateful_block():
    """Verify that the Signal link survives commit_state in a stateful chain.

    Topology: G(gain=2, u=1) -> D(num_delays=1) -> S.in2, G -> S.in1.
    Expected outputs:
        - step 0: S.out == 2.0  (delay buffer still zero)
        - step 1: S.out == 4.0  (delay outputs u[0] == 2)
    Also asserts object identity D.outputs['out'] is S.inputs['in2'] after run.
    """
    m = Model("m")
    g = m.add_block(Gain("G",  gain=2.0))
    d = m.add_block(Delay("D", num_delays=1))
    s = m.add_block(Sum("S",   signs="++"))
 
    g.set_input("in", np.array([[1.0]]))
 
    m.connect("G", "out", "D", "in")
    m.connect("G", "out", "S", "in1")
    m.connect("D", "out", "S", "in2")
 
    sim = make_sim(m, T=0.3)
    logs = sim.run(logging=["S.outputs.out"])
 
    out = logs["S.outputs.out"]
    assert np.allclose(out[0], 2.0), f"step 0: {out[0]}"  # 2 + 0
    assert np.allclose(out[1], 4.0), f"step 1: {out[1]}"  # 2 + 2
    # link must not break after commit_state
    assert m.blocks["D"].outputs["out"] is m.blocks["S"].inputs["in2"]
 
