from __future__ import annotations
import pytest
from engine.scenario import load_scenario, generate_random_scenario, scenario_to_state
import os

def test_generate_random_scenario():
    scenario = generate_random_scenario(42, n_procs=5, n_res=3)
    assert len(scenario.processes) == 5
    assert len(scenario.resources) == 3
    assert len(scenario.scripts) == 5
    
def test_load_all_shipped_scenarios():
    files = os.listdir("scenarios")
    for f in files:
        if f.endswith(".json"):
            sc = load_scenario(f"scenarios/{f}")
            state = scenario_to_state(sc)
            assert len(state.processes) == len(sc.processes)
            assert len(state.resources) == len(sc.resources)
            # The scenarios should be loadable
