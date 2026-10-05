from __future__ import annotations
from .models import SystemState

def validate_state(state: SystemState) -> None:
    """Validates the state of the system."""
    for p in state.processes:
        if p.id < 0:
            raise ValueError(f"Process ID {p.id} must be non-negative.")
            
    for i, res in enumerate(state.resources):
        if res.total < 0:
            raise ValueError(f"Resource {res.name} total ({res.total}) cannot be negative.")
        
        # Check negatives in allocation and request
        for p_idx in range(len(state.processes)):
            alloc = state.allocation[p_idx][i]
            req = state.request[p_idx][i]
            if alloc < 0:
                raise ValueError(f"Process {state.processes[p_idx].id} allocation for {res.name} is negative: {alloc}")
            if req < 0:
                raise ValueError(f"Process {state.processes[p_idx].id} request for {res.name} is negative: {req}")
                
            # Request > Total is invalid
            if req > res.total:
                raise ValueError(f"Process {state.processes[p_idx].id} request for {res.name} ({req}) exceeds total ({res.total})")

def assert_invariant(state: SystemState) -> None:
    """Asserts that Available + sum(Allocation) = Total for all resources."""
    num_processes = len(state.processes)
    for i, res in enumerate(state.resources):
        total_alloc = sum(state.allocation[p][i] for p in range(num_processes))
        if state.available[i] + total_alloc != res.total:
            raise ValueError(
                f"Invariant violation for {res.name}: "
                f"Available ({state.available[i]}) + Allocation ({total_alloc}) "
                f"!= Total ({res.total})"
            )
