from __future__ import annotations
import pytest
from engine.models import Process, ResourceType, SystemState
from engine.detection import detect_deadlock
from engine.recovery import TerminateAll, TerminateOneAtATime, ResourcePreemption, CostWeights

def setup_deadlocked_state() -> SystemState:
    totals = [1, 1, 1, 1]
    state = SystemState()
    for i in range(4):
        state.add_process(Process(i, f"P{i}"))
        state.add_resource(ResourceType(f"R{i}", totals[i]))
        
    state.available = [0, 0, 0, 0]
    state.allocation = [
        [1, 0, 0, 0],
        [0, 1, 0, 0],
        [0, 0, 1, 0],
        [0, 0, 0, 1],
    ]
    state.request = [
        [0, 1, 0, 0],
        [0, 0, 1, 0],
        [0, 0, 0, 1],
        [1, 0, 0, 0],
    ]
    return state

def test_terminate_all():
    state = setup_deadlocked_state()
    det = detect_deadlock(state)
    assert det.is_deadlocked
    
    strategy = TerminateAll()
    result = strategy.recover(state, det.deadlocked_pids)
    
    assert result.is_resolved
    assert len(result.actions) == 4
    for action in result.actions:
        assert action.action_type == "ABORT"
    
    # Check that available resources returned to 1
    assert state.available == [1, 1, 1, 1]
    
def test_terminate_one_at_a_time():
    state = setup_deadlocked_state()
    # P1 has higher priority, so P1 should NOT be victimized first
    state.processes[1].priority = 100
    
    det = detect_deadlock(state)
    
    strategy = TerminateOneAtATime()
    result = strategy.recover(state, det.deadlocked_pids)
    
    assert result.is_resolved
    # Only 1 process needs to be aborted to break this ring
    assert len(result.actions) == 1
    assert result.actions[0].action_type == "ABORT"
    assert result.actions[0].process_id != 1
    
def test_starvation_guard():
    state = setup_deadlocked_state()
    # Make all processes identical
    
    strategy = TerminateOneAtATime()
    # P0 is somehow always first if costs are equal due to min() stability.
    # Let's manually set P0's times_victimized high
    state.processes[0].times_victimized = 5
    
    det = detect_deadlock(state)
    result = strategy.recover(state, det.deadlocked_pids)
    
    assert result.actions[0].process_id != 0 # P0 should be protected

def test_resource_preemption_partial_rollback():
    state = setup_deadlocked_state()
    # Checkpoint P0 at an earlier allocation
    state.checkpoints[0] = [0, 0, 0, 0] # Suppose P0 had no resources at checkpoint
    state.released_since_checkpoint[0] = False
    
    # Make P0 the cheapest victim
    state.processes[0].priority = -100
    
    det = detect_deadlock(state)
    strategy = ResourcePreemption()
    result = strategy.recover(state, det.deadlocked_pids)
    
    assert result.is_resolved
    assert len(result.actions) == 1
    assert result.actions[0].action_type == "ROLLBACK"
    assert result.actions[0].process_id == 0
    assert state.allocation[0] == [0, 0, 0, 0] # Rolled back!

def test_resource_preemption_full_restart_if_released():
    state = setup_deadlocked_state()
    state.checkpoints[0] = [0, 0, 0, 0]
    # P0 released something since checkpoint
    state.released_since_checkpoint[0] = True
    
    state.processes[0].priority = -100
    
    det = detect_deadlock(state)
    strategy = ResourcePreemption()
    result = strategy.recover(state, det.deadlocked_pids)
    
    assert result.actions[0].action_type == "ABORT" # Full restart instead of partial
