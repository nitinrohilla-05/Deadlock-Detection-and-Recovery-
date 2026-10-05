from __future__ import annotations
import copy
from dataclasses import dataclass, field

@dataclass
class Process:
    id: int
    name: str
    priority: int = 0

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

    def add_process(self, process: Process) -> None:
        self.processes.append(process)
        num_resources = len(self.resources)
        self.allocation.append([0] * num_resources)
        self.request.append([0] * num_resources)

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
        """Saves the current allocation of the process."""
        idx = self.get_process_index(process_id)
        self.checkpoints[process_id] = list(self.allocation[idx])

    def clone(self) -> SystemState:
        new_state = SystemState()
        new_state.processes = [Process(p.id, p.name, p.priority) for p in self.processes]
        new_state.resources = [ResourceType(r.name, r.total) for r in self.resources]
        new_state.available = list(self.available)
        new_state.allocation = [list(row) for row in self.allocation]
        new_state.request = [list(row) for row in self.request]
        new_state.checkpoints = {pid: list(alloc) for pid, alloc in self.checkpoints.items()}
        return new_state
