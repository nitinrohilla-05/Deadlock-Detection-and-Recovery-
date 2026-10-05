from __future__ import annotations
import pytest
from engine.models import Process, ResourceType, SystemState
from engine.validation import validate_state, assert_invariant

def test_validate_state_valid():
    state = SystemState()
    state.add_process(Process(0, "P0"))
    state.add_resource(ResourceType("R0", 5))
    state.allocation[0][0] = 2
    state.request[0][0] = 3
    state.available[0] = 3
    validate_state(state) # should not raise

def test_validate_negative_pid():
    state = SystemState()
    state.add_process(Process(-1, "P0"))
    with pytest.raises(ValueError, match="must be non-negative"):
        validate_state(state)

def test_validate_negative_resource_total():
    state = SystemState()
    state.add_process(Process(0, "P0"))
    state.add_resource(ResourceType("R0", -5))
    with pytest.raises(ValueError, match="cannot be negative"):
        validate_state(state)

def test_validate_request_exceeds_total():
    state = SystemState()
    state.add_process(Process(0, "P0"))
    state.add_resource(ResourceType("R0", 5))
    state.request[0][0] = 6
    with pytest.raises(ValueError, match="exceeds total"):
        validate_state(state)

def test_assert_invariant():
    state = SystemState()
    state.add_process(Process(0, "P0"))
    state.add_process(Process(1, "P1"))
    state.add_resource(ResourceType("R0", 5))
    
    state.allocation[0][0] = 2
    state.allocation[1][0] = 2
    state.available[0] = 1
    
    assert_invariant(state) # should not raise
    
    state.available[0] = 2 # invalid
    with pytest.raises(ValueError, match="Invariant violation"):
        assert_invariant(state)
