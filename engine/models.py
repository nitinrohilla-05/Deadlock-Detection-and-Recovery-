from __future__ import annotations
from dataclasses import dataclass, field

@dataclass
class Process:
    id: int
    name: str
    priority: int = 0  # Higher number = more important = higher cost to abort
    work_completed: int = 0 # Ticks done since last checkpoint or start (work lost)
    remaining_work: int = 0 # Total ticks left in script
    times_victimized: int = 0

@dataclass
class ResourceType:
    name: str
    total: int

class SystemState:
    def __init__(self) -> None:
        self.processes: list[Process] = []
        self.resources: list[ResourceType] = []
        self.available: list[int] = []
        self.allocation: list[list[int]] = []
        self.request: list[list[int]] = []
        self.checkpoints: dict[int, list[int]] = {}
        self.released_since_checkpoint: dict[int, bool] = {}

    def add_process(self, process: Process) -> None:
        self.processes.append(process)
        num_resources = len(self.resources)
        self.allocation.append([0] * num_resources)
        self.request.append([0] * num_resources)
        self.released_since_checkpoint[process.id] = False

    def add_resource(self, resource: ResourceType) -> None:
        self.resources.append(resource)
        self.available.append(resource.total)
        for i in range(len(self.processes)):
            self.allocation[i].append(0)
            self.request[i].append(0)

    def get_process_index(self, process_id: int) -> int:
        for i, p in enumerate(self.processes):
            if p.id == process_id:
                return i
        raise ValueError(f"Process {process_id} not found")

    def get_resource_index(self, resource_name: str) -> int:
        for i, r in enumerate(self.resources):
            if r.name == resource_name:
                return i
        raise ValueError(f"Resource {resource_name} not found")

    def checkpoint(self, process_id: int) -> None:
        """Saves the current allocation of the process and resets the release flag/work completed."""
        idx = self.get_process_index(process_id)
        self.checkpoints[process_id] = list(self.allocation[idx])
        self.released_since_checkpoint[process_id] = False
        self.processes[idx].work_completed = 0

    def mark_release(self, process_id: int) -> None:
        """Marks that the process released a resource."""
        self.released_since_checkpoint[process_id] = True

    def clone(self) -> SystemState:
        new_state = SystemState()
        new_state.processes = [Process(p.id, p.name, p.priority, p.work_completed, p.remaining_work, p.times_victimized) for p in self.processes]
        new_state.resources = [ResourceType(r.name, r.total) for r in self.resources]
        new_state.available = list(self.available)
        new_state.allocation = [list(row) for row in self.allocation]
        new_state.request = [list(row) for row in self.request]
        new_state.checkpoints = {pid: list(alloc) for pid, alloc in self.checkpoints.items()}
        new_state.released_since_checkpoint = dict(self.released_since_checkpoint)
        return new_state
