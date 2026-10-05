from __future__ import annotations
import random
import pytest
from engine.models import Process, ResourceType, SystemState
from engine.detection import detect_deadlock, detect_multi_instance

def generate_random_single_instance_state(seed: int) -> SystemState:
    random.seed(seed)
    num_procs = random.randint(2, 10)
    num_res = random.randint(2, 10)
    
    state = SystemState()
    for i in range(num_procs):
        state.add_process(Process(i, f"P{i}"))
    for i in range(num_res):
        state.add_resource(ResourceType(f"R{i}", 1))
        
    # Allocate resources
    available = [1] * num_res
    for r in range(num_res):
        if random.random() < 0.7: # 70% chance to be allocated
            p = random.randint(0, num_procs - 1)
            state.allocation[p][r] = 1
            available[r] = 0
            
    state.available = available
    
    # Make requests
    for p in range(num_procs):
        for r in range(num_res):
            # Cannot request what is already held
            if state.allocation[p][r] == 0:
                if random.random() < 0.2: # 20% chance to request
                    state.request[p][r] = 1
                    
    return state

@pytest.mark.parametrize("seed", range(1000))
def test_random_equivalence(seed: int):
    state = generate_random_single_instance_state(seed)
    
    wfg_result = detect_deadlock(state)
    matrix_result = detect_multi_instance(state)
    
    # In single-instance state, if matrix says deadlock, WFG must also say deadlock.
    # WFG Result deadlocked_pids are the processes IN cycles.
    # Matrix Result deadlocked_pids are ALL deadlocked processes (in cycles + blocked behind cycles).
    assert wfg_result.is_deadlocked == matrix_result.is_deadlocked
    if wfg_result.is_deadlocked:
        # Every process in a WFG cycle is part of the deadlocked set found by the matrix
        assert wfg_result.deadlocked_pids.issubset(matrix_result.deadlocked_pids)
