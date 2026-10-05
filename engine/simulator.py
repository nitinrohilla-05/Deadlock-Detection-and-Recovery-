from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional, Literal
from .models import SystemState, Process
from .metrics import SimulationMetrics
from .recovery import RecoveryStrategy
from .detection import detect_deadlock
from .validation import assert_invariant
import time
import copy

@dataclass
class Instruction:
    type: Literal["REQUEST", "COMPUTE", "CHECKPOINT", "RELEASE", "END"]
    resources: dict[str, int] = field(default_factory=dict)
    ticks: int = 0

@dataclass
class EventLog:
    tick: int
    event_type: str
    message: str

class Simulator:
    def __init__(
        self, 
        state: SystemState, 
        scripts: dict[int, list[Instruction]], 
        trigger_config: dict = None, 
        recovery_strategy: Optional[RecoveryStrategy] = None
    ):
        self.state = state
        self.original_scripts = copy.deepcopy(scripts)
        self.active_scripts = copy.deepcopy(scripts)
        self.script_checkpoints: dict[int, list[Instruction]] = {}
        
        self.blocked: set[int] = set()
        self.completed: set[int] = set()
        
        self.tick = 0
        self.metrics = SimulationMetrics()
        self.logs: list[EventLog] = []
        
        self.trigger_config = trigger_config or {"type": "blocked"} 
        self.recovery_strategy = recovery_strategy
        
        self.deadlocked_pids: set[int] = set()
        self.is_running = True
        
        self.wait_time: dict[int, int] = {pid: 0 for pid in scripts}
        
        for pid, script in self.original_scripts.items():
            total_compute = sum(inst.ticks for inst in script if inst.type == "COMPUTE")
            idx = self.state.get_process_index(pid)
            self.state.processes[idx].remaining_work = total_compute
            
    def log(self, event_type: str, message: str) -> None:
        self.logs.append(EventLog(self.tick, event_type, message))
        
    def step(self) -> None:
        if not self.is_running:
            return
            
        self.metrics.makespan = self.tick
        
        if self.deadlocked_pids and self.recovery_strategy:
            self._do_recovery()
            
        if self.deadlocked_pids:
            return

        num_procs = len(self.state.processes)
        active_pids = [p.id for p in self.state.processes if p.id not in self.blocked and p.id not in self.completed]
        
        for pid in active_pids:
            self._execute_process(pid)
            
        self._try_unblock()
        
        for pid in self.blocked:
            self.wait_time[pid] += 1
            self.metrics.total_wait_time += 1
            
        should_detect = False
        if self.trigger_config["type"] == "ticks":
            k = self.trigger_config.get("k", 5)
            if self.tick % k == 0 and self.tick > 0:
                should_detect = True
        
        if should_detect and not self.deadlocked_pids:
            self.run_detection()

        if len(self.completed) == num_procs:
            self.is_running = False
            self.log("INFO", "Simulation completed.")
            
        self.tick += 1

    def _execute_process(self, pid: int) -> None:
        idx = self.state.get_process_index(pid)
        p = self.state.processes[idx]
        script = self.active_scripts[pid]
        
        while script:
            inst = script[0]
            
            if inst.type == "COMPUTE":
                inst.ticks -= 1
                p.work_completed += 1
                p.remaining_work -= 1
                if inst.ticks <= 0:
                    script.pop(0)
                break
                
            elif inst.type == "CHECKPOINT":
                self.state.checkpoint(pid)
                script.pop(0)
                self.script_checkpoints[pid] = copy.deepcopy(script)
                self.log("CHECKPOINT", f"Process {p.name} checkpointed.")
                
            elif inst.type == "RELEASE":
                for res_name, qty in inst.resources.items():
                    res_idx = self.state.get_resource_index(res_name)
                    self.state.allocation[idx][res_idx] -= qty
                    self.state.available[res_idx] += qty
                self.state.mark_release(pid)
                self.log("RELEASE", f"Process {p.name} released {inst.resources}.")
                assert_invariant(self.state)
                script.pop(0)
                
            elif inst.type == "REQUEST":
                req_populated = sum(self.state.request[idx]) > 0
                if not req_populated:
                    for res_name, qty in inst.resources.items():
                        res_idx = self.state.get_resource_index(res_name)
                        if qty > self.state.resources[res_idx].total:
                            self.log("ERROR", f"Process {p.name} requested {qty} of {res_name}, exceeds total. Aborting.")
                            self._full_abort(pid)
                            return
                        self.state.request[idx][res_idx] = qty
                
                can_grant = True
                for r in range(len(self.state.resources)):
                    if self.state.request[idx][r] > self.state.available[r]:
                        can_grant = False
                        break
                        
                if can_grant:
                    for r in range(len(self.state.resources)):
                        req_qty = self.state.request[idx][r]
                        if req_qty > 0:
                            self.state.available[r] -= req_qty
                            self.state.allocation[idx][r] += req_qty
                            self.state.request[idx][r] = 0
                    self.log("GRANT", f"Process {p.name} granted {inst.resources}.")
                    assert_invariant(self.state)
                    script.pop(0)
                else:
                    self.blocked.add(pid)
                    self.log("BLOCK", f"Process {p.name} blocked on {inst.resources}.")
                    if self.trigger_config["type"] == "blocked":
                        self.run_detection()
                    break
                    
            elif inst.type == "END":
                self._release_all(pid)
                self.completed.add(pid)
                self.metrics.completed_processes += 1
                self.log("END", f"Process {p.name} ended.")
                script.pop(0)
                break

    def _try_unblock(self) -> None:
        blocked_pids = list(self.blocked)
        blocked_pids.sort(key=lambda pid: self.state.processes[self.state.get_process_index(pid)].priority, reverse=True)
        
        for pid in blocked_pids:
            idx = self.state.get_process_index(pid)
            can_grant = True
            for r in range(len(self.state.resources)):
                if self.state.request[idx][r] > self.state.available[r]:
                    can_grant = False
                    break
            
            if can_grant:
                self.blocked.remove(pid)
                p = self.state.processes[idx]
                inst = self.active_scripts[pid][0]
                for r in range(len(self.state.resources)):
                    req_qty = self.state.request[idx][r]
                    if req_qty > 0:
                        self.state.available[r] -= req_qty
                        self.state.allocation[idx][r] += req_qty
                        self.state.request[idx][r] = 0
                self.log("GRANT", f"Process {p.name} granted {inst.resources} and unblocked.")
                assert_invariant(self.state)
                self.active_scripts[pid].pop(0)

    def run_detection(self) -> None:
        start_time = time.time()
        result = detect_deadlock(self.state)
        elapsed = (time.time() - start_time) * 1000
        
        self.metrics.detection_runs += 1
        self.metrics.detection_time_ms += elapsed
        
        if result.is_deadlocked:
            self.deadlocked_pids = result.deadlocked_pids
            self.metrics.deadlocks_detected += 1
            names = [self.state.processes[self.state.get_process_index(p)].name for p in self.deadlocked_pids]
            self.log("DEADLOCK", f"Deadlock detected among: {', '.join(names)}")

    def _do_recovery(self) -> None:
        self.log("RECOVERY", "Starting automatic recovery.")
        res = self.recovery_strategy.recover(self.state, self.deadlocked_pids)
        for action in res.actions:
            pid = action.process_id
            idx = self.state.get_process_index(pid)
            name = self.state.processes[idx].name
            self.metrics.victims += 1
            
            if action.action_type == "ABORT":
                self.log("ABORT", f"Process {name} aborted.")
                self.metrics.aborted_processes += 1
                self.metrics.work_lost += self.state.processes[idx].work_completed
                
                self.active_scripts[pid] = copy.deepcopy(self.original_scripts[pid])
                if pid in self.blocked:
                    self.blocked.remove(pid)
                
            elif action.action_type == "ROLLBACK":
                self.log("ROLLBACK", f"Process {name} rolled back to checkpoint.")
                self.metrics.work_lost += self.state.processes[idx].work_completed
                
                self.active_scripts[pid] = copy.deepcopy(self.script_checkpoints[pid])
                if pid in self.blocked:
                    self.blocked.remove(pid)
                
        if res.is_resolved:
            self.deadlocked_pids.clear()
            self.log("RECOVERY_SUCCESS", "Deadlock resolved.")
        else:
            self.log("RECOVERY_FAIL", "Deadlock not resolved completely.")
            
    def _release_all(self, pid: int) -> None:
        idx = self.state.get_process_index(pid)
        for r in range(len(self.state.resources)):
            alloc = self.state.allocation[idx][r]
            if alloc > 0:
                self.state.available[r] += alloc
                self.state.allocation[idx][r] = 0
            self.state.request[idx][r] = 0
            
    def _full_abort(self, pid: int) -> None:
        self._release_all(pid)
        self.completed.add(pid)
        if pid in self.blocked:
            self.blocked.remove(pid)
        self.metrics.aborted_processes += 1
