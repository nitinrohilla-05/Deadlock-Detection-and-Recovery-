from __future__ import annotations
import pytest
from engine.scenario import load_scenario, scenario_to_state, generate_random_scenario
from engine.simulator import Simulator
from engine.recovery import TerminateAll, TerminateOneAtATime

def test_simulator_basic():
    scenario = generate_random_scenario(42, n_procs=2, n_res=1, max_instances=1)
    state = scenario_to_state(scenario)
    
    # We want a deterministic small script to test simulator directly
    from engine.simulator import Instruction
    scenario.scripts = {
        0: [
            Instruction("REQUEST", {"R0": 1}),
            Instruction("COMPUTE", ticks=2),
            Instruction("RELEASE", {"R0": 1}),
            Instruction("END")
        ],
        1: [
            Instruction("REQUEST", {"R0": 1}),
            Instruction("COMPUTE", ticks=1),
            Instruction("RELEASE", {"R0": 1}),
            Instruction("END")
        ]
    }
    
    sim = Simulator(state, scenario.scripts, trigger_config={"type": "blocked"})
    
    while sim.is_running and not sim.deadlocked_pids:
        sim.step()
        
    assert not sim.is_running
    assert len(sim.completed) == 2
    assert sim.metrics.makespan > 0

def test_simulator_deadlock_and_recovery():
    scenario = load_scenario("scenarios/two_process_circular.json")
    state = scenario_to_state(scenario)
    
    # Static scenario has no scripts, so we simulate scripts that cause the deadlock
    # Actually, if we just give them the requests they need, they will block immediately.
    from engine.simulator import Instruction
    scripts = {
        0: [Instruction("REQUEST", {"R1": 1}), Instruction("END")],
        1: [Instruction("REQUEST", {"R0": 1}), Instruction("END")],
    }
    
    sim = Simulator(state, scripts, trigger_config={"type": "blocked"}, recovery_strategy=TerminateOneAtATime())
    
    while sim.is_running:
        sim.step()
        
    assert sim.metrics.deadlocks_detected >= 1
    assert sim.metrics.victims == 1
    assert not sim.is_running
