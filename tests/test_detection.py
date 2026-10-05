from __future__ import annotations
import pytest
from engine.models import Process, ResourceType, SystemState
from engine.detection import detect_deadlock, detect_multi_instance, build_wfg

def setup_state_from_data(
    available: list[int],
    allocation: list[list[int]],
    request: list[list[int]],
    totals: list[int]
) -> SystemState:
    state = SystemState()
    for i in range(len(allocation)):
        state.add_process(Process(i, f"P{i}"))
    for i, t in enumerate(totals):
        state.add_resource(ResourceType(f"R{i}", t))
        
    state.available = list(available)
    state.allocation = [list(row) for row in allocation]
    state.request = [list(row) for row in request]
    return state

def test_textbook_safe():
    # Resource types A=7, B=2, C=6
    totals = [7, 2, 6]
    available = [0, 0, 0]
    allocation = [
        [0, 1, 0], # P0
        [2, 0, 0], # P1
        [3, 0, 3], # P2
        [2, 1, 1], # P3
        [0, 0, 2], # P4
    ]
    request = [
        [0, 0, 0],
        [2, 0, 2],
        [0, 0, 0],
        [1, 0, 0],
        [0, 0, 2],
    ]
    state = setup_state_from_data(available, allocation, request, totals)
    result = detect_deadlock(state)
    assert not result.is_deadlocked
    assert len(result.deadlocked_pids) == 0

def test_textbook_deadlock():
    totals = [7, 2, 6]
    available = [0, 0, 0]
    allocation = [
        [0, 1, 0],
        [2, 0, 0],
        [3, 0, 3],
        [2, 1, 1],
        [0, 0, 2],
    ]
    request = [
        [0, 0, 0],
        [2, 0, 2],
        [0, 0, 1], # P2 changed from 0,0,0 to 0,0,1
        [1, 0, 0],
        [0, 0, 2],
    ]
    state = setup_state_from_data(available, allocation, request, totals)
    result = detect_deadlock(state)
    assert result.is_deadlocked
    assert result.deadlocked_pids == {1, 2, 3, 4}

def test_cycle_without_deadlock():
    # R1 and R2 have 2 instances each; 
    # R1 is held by P2 and P3, R2 by P1 and P4; 
    # P1 requests R1, P3 requests R2; 
    # P2 and P4 are not waiting.
    # We map P1->0, P2->1, P3->2, P4->3
    # R1->0, R2->1
    totals = [2, 2]
    # P1(0) holds R2(1)
    # P2(1) holds R1(0)
    # P3(2) holds R1(0)
    # P4(3) holds R2(1)
    allocation = [
        [0, 1], # P1
        [1, 0], # P2
        [1, 0], # P3
        [0, 1], # P4
    ]
    # P1(0) requests R1(0)
    # P3(2) requests R2(1)
    request = [
        [1, 0], # P1
        [0, 0], # P2
        [0, 1], # P3
        [0, 0], # P4
    ]
    available = [0, 0] # all 2 instances of R1 and R2 are allocated
    
    state = setup_state_from_data(available, allocation, request, totals)
    
    # Check WFG specifically
    wfg = build_wfg(state)
    # P1(0) requests R1(0), which is held by P2(1) and P3(2). So 0 -> {1, 2}
    # P3(2) requests R2(1), which is held by P1(0) and P4(3). So 2 -> {0, 3}
    assert 1 in wfg[0] and 2 in wfg[0]
    assert 0 in wfg[2] and 3 in wfg[2]
    
    # 0 -> 2 and 2 -> 0 is a cycle!
    result = detect_deadlock(state)
    assert not result.is_deadlocked # matrix says safe
    assert result.cycle_without_deadlock # but WFG found a cycle

def test_two_independent_deadlocks():
    totals = [1, 1, 1, 1]
    available = [0, 0, 0, 0]
    allocation = [
        [1, 0, 0, 0], # P0 holds R0
        [0, 1, 0, 0], # P1 holds R1
        [0, 0, 1, 0], # P2 holds R2
        [0, 0, 0, 1], # P3 holds R3
    ]
    request = [
        [0, 1, 0, 0], # P0 requests R1
        [1, 0, 0, 0], # P1 requests R0
        [0, 0, 0, 1], # P2 requests R3
        [0, 0, 1, 0], # P3 requests R2
    ]
    state = setup_state_from_data(available, allocation, request, totals)
    result = detect_deadlock(state)
    assert result.is_deadlocked
    assert result.deadlocked_pids == {0, 1, 2, 3}
    # Should report two cycles
    assert len(result.cycles) == 2
