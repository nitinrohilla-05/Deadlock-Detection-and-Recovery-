from __future__ import annotations
import json
import random
from dataclasses import dataclass
from typing import Optional
from .simulator import Instruction
from .models import SystemState, Process, ResourceType

@dataclass
class Scenario:
    resources: dict[str, int]
    processes: list[dict] # keys: id, name, priority
    allocation: Optional[list[list[int]]] = None
    request: Optional[list[list[int]]] = None
    available: Optional[list[int]] = None
    scripts: Optional[dict[int, list[Instruction]]] = None

def load_scenario(path: str) -> Scenario:
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
        
    resources = data.get("resources", {})
    processes = data.get("processes", [])
    
    scripts = None
    if "scripts" in data:
        scripts = {}
        for pid_str, inst_list in data["scripts"].items():
            pid = int(pid_str)
            scripts[pid] = [
                Instruction(
                    type=inst["type"],
                    resources=inst.get("resources", {}),
                    ticks=inst.get("ticks", 0)
                )
                for inst in inst_list
            ]
            
    return Scenario(
        resources=resources,
        processes=processes,
        allocation=data.get("allocation"),
        request=data.get("request"),
        available=data.get("available"),
        scripts=scripts
    )

def scenario_to_state(scenario: Scenario) -> SystemState:
    state = SystemState()
    for pid_dict in scenario.processes:
        state.add_process(Process(
            id=pid_dict["id"], 
            name=pid_dict["name"], 
            priority=pid_dict.get("priority", 0)
        ))
        
    for res_name, total in scenario.resources.items():
        state.add_resource(ResourceType(res_name, total))
        
    if scenario.allocation is not None:
        state.allocation = [list(row) for row in scenario.allocation]
    if scenario.request is not None:
        state.request = [list(row) for row in scenario.request]
    if scenario.available is not None:
        state.available = list(scenario.available)
        
    return state

def generate_random_scenario(
    seed: int, 
    n_procs: int = 10, 
    n_res: int = 5, 
    max_instances: int = 3, 
    req_prob: float = 0.3
) -> Scenario:
    random.seed(seed)
    resources = {f"R{i}": random.randint(1, max_instances) for i in range(n_res)}
    processes = [{"id": i, "name": f"P{i}", "priority": random.randint(1, 10)} for i in range(n_procs)]
    
    scripts = {}
    for i in range(n_procs):
        script = []
        # Random sequence of compute and requests
        held = {f"R{r}": 0 for r in range(n_res)}
        
        for _ in range(random.randint(3, 8)):
            action = random.random()
            if action < 0.4:
                script.append(Instruction("COMPUTE", ticks=random.randint(1, 5)))
            elif action < 0.7:
                # Request
                req = {}
                for r in range(n_res):
                    if random.random() < req_prob:
                        qty = random.randint(1, resources[f"R{r}"])
                        req[f"R{r}"] = qty
                        held[f"R{r}"] += qty
                if req:
                    script.append(Instruction("REQUEST", resources=req))
            elif action < 0.9:
                # Checkpoint
                script.append(Instruction("CHECKPOINT"))
            else:
                # Release something held
                rel = {}
                for r, qty in held.items():
                    if qty > 0 and random.random() < 0.5:
                        rel_qty = random.randint(1, qty)
                        rel[r] = rel_qty
                        held[r] -= rel_qty
                if rel:
                    script.append(Instruction("RELEASE", resources=rel))
                    
        # Final release
        final_rel = {r: qty for r, qty in held.items() if qty > 0}
        if final_rel:
            script.append(Instruction("RELEASE", resources=final_rel))
        script.append(Instruction("END"))
        scripts[i] = script
        
    return Scenario(resources=resources, processes=processes, scripts=scripts)
