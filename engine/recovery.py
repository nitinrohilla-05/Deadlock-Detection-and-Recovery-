from __future__ import annotations
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional
from .models import SystemState, Process
from .detection import detect_deadlock
from .validation import assert_invariant

@dataclass
class CostWeights:
    priority: float = 1.0
    work_lost: float = 1.0
    resources_held: float = 1.0
    remaining_work: float = 0.5
    times_victimized: float = 10.0 # High penalty to avoid starvation

@dataclass
class RecoveryAction:
    action_type: str # "ABORT" or "ROLLBACK"
    process_id: int

@dataclass
class RecoveryResult:
    actions: list[RecoveryAction]
    is_resolved: bool

class RecoveryStrategy(ABC):
    def __init__(self, weights: Optional[CostWeights] = None):
        self.weights = weights or CostWeights()

    @abstractmethod
    def recover(self, state: SystemState, deadlocked_pids: set[int]) -> RecoveryResult:
        pass
        
    def calculate_cost(self, state: SystemState, process_id: int) -> float:
        idx = state.get_process_index(process_id)
        p = state.processes[idx]
        
        resources_held = sum(state.allocation[idx])
        
        # Higher cost means less likely to be chosen as victim.
        cost = (
            (p.priority * self.weights.priority) +
            (p.work_completed * self.weights.work_lost) +
            (resources_held * self.weights.resources_held) +
            (p.remaining_work * self.weights.remaining_work) +
            (p.times_victimized * self.weights.times_victimized)
        )
        return cost

    def abort_process(self, state: SystemState, process_id: int) -> None:
        """Aborts a process: releases all its held resources and clears its requests."""
        idx = state.get_process_index(process_id)
        num_res = len(state.resources)
        for r in range(num_res):
            alloc = state.allocation[idx][r]
            if alloc > 0:
                state.available[r] += alloc
                state.allocation[idx][r] = 0
            state.request[idx][r] = 0
            
        state.processes[idx].work_completed = 0
        state.processes[idx].times_victimized += 1
        assert_invariant(state)

    def rollback_process(self, state: SystemState, process_id: int) -> bool:
        """
        Attempts to rollback a process to its last checkpoint.
        Returns True if partial rollback happened, False if full restart (abort) was required.
        """
        idx = state.get_process_index(process_id)
        p = state.processes[idx]
        
        has_checkpoint = process_id in state.checkpoints
        released_since = state.released_since_checkpoint.get(process_id, False)
        
        if not has_checkpoint or released_since:
            self.abort_process(state, process_id)
            return False
            
        # Rollback: release only resources acquired after the checkpoint
        checkpoint_alloc = state.checkpoints[process_id]
        num_res = len(state.resources)
        
        for r in range(num_res):
            acquired_after = state.allocation[idx][r] - checkpoint_alloc[r]
            if acquired_after > 0:
                state.available[r] += acquired_after
                state.allocation[idx][r] = checkpoint_alloc[r]
            # Clear pending requests
            state.request[idx][r] = 0
            
        p.work_completed = 0
        p.times_victimized += 1
        assert_invariant(state)
        return True


class TerminateAll(RecoveryStrategy):
    def recover(self, state: SystemState, deadlocked_pids: set[int]) -> RecoveryResult:
        actions = []
        for pid in list(deadlocked_pids):
            self.abort_process(state, pid)
            actions.append(RecoveryAction("ABORT", pid))
            
        result = detect_deadlock(state)
        return RecoveryResult(actions=actions, is_resolved=not result.is_deadlocked)

class TerminateOneAtATime(RecoveryStrategy):
    def recover(self, state: SystemState, deadlocked_pids: set[int]) -> RecoveryResult:
        actions = []
        current_deadlock = set(deadlocked_pids)
        
        while current_deadlock:
            # Pick minimum cost
            victim_id = min(current_deadlock, key=lambda pid: self.calculate_cost(state, pid))
            
            self.abort_process(state, victim_id)
            actions.append(RecoveryAction("ABORT", victim_id))
            
            # Re-detect
            det_result = detect_deadlock(state)
            if not det_result.is_deadlocked:
                return RecoveryResult(actions=actions, is_resolved=True)
            
            current_deadlock = det_result.deadlocked_pids
            
        return RecoveryResult(actions=actions, is_resolved=False)

class ResourcePreemption(RecoveryStrategy):
    def recover(self, state: SystemState, deadlocked_pids: set[int]) -> RecoveryResult:
        actions = []
        current_deadlock = set(deadlocked_pids)
        
        while current_deadlock:
            victim_id = min(current_deadlock, key=lambda pid: self.calculate_cost(state, pid))
            
            is_partial = self.rollback_process(state, victim_id)
            action_type = "ROLLBACK" if is_partial else "ABORT"
            actions.append(RecoveryAction(action_type, victim_id))
            
            # We must resolve requests for blocked processes using the newly freed resources.
            # In an actual OS, preemption hands freed resources to blocked processes.
            # Here, the simulator handles granting requests. Just releasing them makes the state safe.
            # Wait, our detection algorithm just uses Available matrix. So releasing makes Available larger,
            # which allows Matrix algorithm to succeed.
            
            det_result = detect_deadlock(state)
            if not det_result.is_deadlocked:
                return RecoveryResult(actions=actions, is_resolved=True)
                
            current_deadlock = det_result.deadlocked_pids
            
        return RecoveryResult(actions=actions, is_resolved=False)
