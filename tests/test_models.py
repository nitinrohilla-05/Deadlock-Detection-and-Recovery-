from __future__ import annotations
import pytest
from engine.models import Process, ResourceType, SystemState

def test_add_process_and_resource():
    state = SystemState()
    state.add_process(Process(0, "P0", 5))
    assert len(state.processes) == 1
    assert state.processes[0].id == 0
    assert state.processes[0].priority == 5
    
    state.add_resource(ResourceType("R0", 10))
    assert len(state.resources) == 1
    assert state.resources[0].total == 10
    
    # State matrices should be 1x1
    assert len(state.allocation) == 1
    assert len(state.allocation[0]) == 1
    assert state.allocation[0][0] == 0
    assert len(state.request) == 1
    assert state.request[0][0] == 0
    assert state.available == [10]

def test_checkpoint_and_clone():
    state = SystemState()
    state.add_process(Process(0, "P0"))
    state.add_resource(ResourceType("R0", 5))
    
    state.allocation[0][0] = 2
    state.checkpoint(0)
    
    assert state.checkpoints[0] == [2]
    
    cloned = state.clone()
    assert cloned.checkpoints[0] == [2]
    assert cloned.allocation[0][0] == 2
    
    # modify clone to ensure independence
    cloned.allocation[0][0] = 5
    assert state.allocation[0][0] == 2
