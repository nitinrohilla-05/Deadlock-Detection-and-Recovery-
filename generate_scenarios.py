import json
import os
from engine.scenario import Scenario, generate_random_scenario

def save(scenario: Scenario, name: str):
    data = {
        "resources": scenario.resources,
        "processes": scenario.processes,
    }
    if scenario.allocation is not None: data["allocation"] = scenario.allocation
    if scenario.request is not None: data["request"] = scenario.request
    if scenario.available is not None: data["available"] = scenario.available
    if scenario.scripts is not None:
        data["scripts"] = {
            str(pid): [{"type": i.type, "resources": i.resources, "ticks": i.ticks} for i in insts]
            for pid, insts in scenario.scripts.items()
        }
        
    os.makedirs("scenarios", exist_ok=True)
    with open(f"scenarios/{name}.json", "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

# 1. textbook_safe
ts = Scenario(
    resources={"A": 7, "B": 2, "C": 6},
    processes=[{"id": i, "name": f"P{i}", "priority": 1} for i in range(5)],
    available=[0, 0, 0],
    allocation=[[0, 1, 0], [2, 0, 0], [3, 0, 3], [2, 1, 1], [0, 0, 2]],
    request=[[0, 0, 0], [2, 0, 2], [0, 0, 0], [1, 0, 0], [0, 0, 2]]
)
save(ts, "textbook_safe")

# 2. textbook_deadlock
td = Scenario(
    resources={"A": 7, "B": 2, "C": 6},
    processes=[{"id": i, "name": f"P{i}", "priority": 1} for i in range(5)],
    available=[0, 0, 0],
    allocation=[[0, 1, 0], [2, 0, 0], [3, 0, 3], [2, 1, 1], [0, 0, 2]],
    request=[[0, 0, 0], [2, 0, 2], [0, 0, 1], [1, 0, 0], [0, 0, 2]]
)
save(td, "textbook_deadlock")

# 3. cycle_without_deadlock
cwd = Scenario(
    resources={"R1": 2, "R2": 2},
    processes=[{"id": i, "name": f"P{i}", "priority": 1} for i in range(4)],
    available=[0, 0],
    allocation=[[0, 1], [1, 0], [1, 0], [0, 1]],
    request=[[1, 0], [0, 0], [0, 1], [0, 0]]
)
save(cwd, "cycle_without_deadlock")

# 4. two_process_circular
tpc = Scenario(
    resources={"R0": 1, "R1": 1},
    processes=[{"id": 0, "name": "P0", "priority": 1}, {"id": 1, "name": "P1", "priority": 1}],
    available=[0, 0],
    allocation=[[1, 0], [0, 1]],
    request=[[0, 1], [1, 0]]
)
save(tpc, "two_process_circular")

# 5. dining_philosophers
dp = Scenario(
    resources={f"Fork{i}": 1 for i in range(5)},
    processes=[{"id": i, "name": f"Phil{i}", "priority": 1} for i in range(5)],
    available=[0]*5,
    allocation=[[1 if j == i else 0 for j in range(5)] for i in range(5)],
    request=[[1 if j == (i+1)%5 else 0 for j in range(5)] for i in range(5)]
)
save(dp, "dining_philosophers")

# 6. two_independent_deadlocks
tid = Scenario(
    resources={"R0":1, "R1":1, "R2":1, "R3":1},
    processes=[{"id": i, "name": f"P{i}", "priority": 1} for i in range(4)],
    available=[0, 0, 0, 0],
    allocation=[[1,0,0,0], [0,1,0,0], [0,0,1,0], [0,0,0,1]],
    request=[[0,1,0,0], [1,0,0,0], [0,0,0,1], [0,0,1,0]]
)
save(tid, "two_independent_deadlocks")

# 7. large_random
lr = generate_random_scenario(seed=42, n_procs=15, n_res=8, max_instances=5)
save(lr, "large_random")

print("Scenarios created successfully.")
