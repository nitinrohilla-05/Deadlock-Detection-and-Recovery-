from __future__ import annotations
from dataclasses import dataclass
from typing import Optional
from .models import SystemState

@dataclass
class TraceStep:
    step: int
    work_vector: list[int]
    process_finished: Optional[int]

@dataclass
class DeadlockResult:
    is_deadlocked: bool
    deadlocked_pids: set[int]
    cycles: list[list[int]]
    trace: list[TraceStep]
    cycle_without_deadlock: bool = False

def build_wfg(state: SystemState) -> dict[int, set[int]]:
    num_processes = len(state.processes)
    num_resources = len(state.resources)
    wfg = {i: set() for i in range(num_processes)}
    for i in range(num_processes):
        for r in range(num_resources):
            if state.request[i][r] > 0:
                for j in range(num_processes):
                    if i != j and state.allocation[j][r] > 0:
                        wfg[i].add(j)
    return wfg

def tarjan_scc(wfg: dict[int, set[int]]) -> list[list[int]]:
    index = 0
    indices: dict[int, int] = {}
    lowlinks: dict[int, int] = {}
    stack: list[int] = []
    on_stack: set[int] = set()
    sccs: list[list[int]] = []

    def strongconnect(v: int) -> None:
        nonlocal index
        indices[v] = index
        lowlinks[v] = index
        index += 1
        stack.append(v)
        on_stack.add(v)

        for w in wfg[v]:
            if w not in indices:
                strongconnect(w)
                lowlinks[v] = min(lowlinks[v], lowlinks[w])
            elif w in on_stack:
                lowlinks[v] = min(lowlinks[v], indices[w])

        if lowlinks[v] == indices[v]:
            scc = []
            while True:
                w = stack.pop()
                on_stack.remove(w)
                scc.append(w)
                if w == v:
                    break
            sccs.append(scc)

    for v in wfg:
        if v not in indices:
            strongconnect(v)
            
    return [scc for scc in sccs if len(scc) > 1 or (len(scc) == 1 and scc[0] in wfg[scc[0]])]

def find_cycle_in_scc(scc: list[int], wfg: dict[int, set[int]]) -> list[int]:
    scc_set = set(scc)
    start_node = scc[0]
    visited: set[int] = set()
    path: list[int] = []

    def dfs(node: int) -> list[int] | None:
        visited.add(node)
        path.append(node)
        for neighbor in wfg[node]:
            if neighbor in scc_set:
                if neighbor in path:
                    idx = path.index(neighbor)
                    return path[idx:]
                elif neighbor not in visited:
                    cycle = dfs(neighbor)
                    if cycle:
                        return cycle
        path.pop()
        return None

    cycle = dfs(start_node)
    return cycle if cycle else []

def detect_multi_instance(state: SystemState) -> DeadlockResult:
    num_processes = len(state.processes)
    num_resources = len(state.resources)
    work = list(state.available)
    finish = [False] * num_processes

    for i in range(num_processes):
        if all(alloc == 0 for alloc in state.allocation[i]):
            finish[i] = True

    trace = [TraceStep(0, list(work), None)]
    step = 0

    while True:
        found = False
        for i in range(num_processes):
            if not finish[i]:
                if all(state.request[i][r] <= work[r] for r in range(num_resources)):
                    for r in range(num_resources):
                        work[r] += state.allocation[i][r]
                    finish[i] = True
                    found = True
                    step += 1
                    trace.append(TraceStep(step, list(work), state.processes[i].id))
                    break
        if not found:
            break

    deadlocked_pids = {state.processes[i].id for i in range(num_processes) if not finish[i]}
    is_deadlocked = len(deadlocked_pids) > 0
    
    return DeadlockResult(
        is_deadlocked=is_deadlocked,
        deadlocked_pids=deadlocked_pids,
        cycles=[],
        trace=trace
    )

def detect_deadlock(state: SystemState) -> DeadlockResult:
    num_resources = len(state.resources)
    is_single_instance = all(r.total == 1 for r in state.resources)
    
    wfg = build_wfg(state)
    sccs = tarjan_scc(wfg)
    cycles = []
    wfg_deadlocked_pids = set()
    for scc in sccs:
        cycle = find_cycle_in_scc(scc, wfg)
        cycles.append([state.processes[idx].id for idx in cycle])
        for idx in scc:
            wfg_deadlocked_pids.add(state.processes[idx].id)

    if is_single_instance:
        is_deadlocked = len(wfg_deadlocked_pids) > 0
        return DeadlockResult(
            is_deadlocked=is_deadlocked,
            deadlocked_pids=wfg_deadlocked_pids,
            cycles=cycles,
            trace=[],
            cycle_without_deadlock=False
        )
    else:
        result = detect_multi_instance(state)
        result.cycles = cycles
        if not result.is_deadlocked and len(cycles) > 0:
            result.cycle_without_deadlock = True
        # If deadlocked in multi-instance, the cycles might be related to it
        return result
