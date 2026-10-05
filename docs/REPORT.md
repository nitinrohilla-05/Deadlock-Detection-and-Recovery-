# Deadlock Lab Design Report

## 1. System Architecture
Deadlock Lab separates logic from representation:
- **Core Engine**: Handles detection, validation, recovery, and state metrics (`engine/`).
- **REST API**: Exposes the core functionalities over HTTP using FastAPI (`api/`).
- **Web UI**: A responsive, vanilla JS and SVG-based dashboard to visualize and interact with the system (`static/`).

## 2. Detection Algorithms
The system includes a smart dispatcher (`engine.detection.detect_deadlock`):
- **Wait-For-Graph (WFG)**: Used exclusively when all resources are single-instance. WFG reduces deadlock detection to cycle detection. We use Tarjan's Strongly Connected Components algorithm.
- **Matrix Algorithm**: Used when there are multi-instance resources. It simulates potential allocations by granting requests to processes that can finish, verifying if all processes can eventually complete.
- **Cycle Without Deadlock Edge Case**: Handled accurately by verifying that while a structural dependency cycle exists, if other processes can satisfy the requests, a true deadlock has not occurred.

## 3. Recovery Mechanisms
1. **Terminate All**: Aborts all processes involved in the deadlock, guaranteeing resolution but losing all completed work.
2. **Terminate One At A Time**: Iteratively selects a "victim" based on a cost function: `work_completed / (priority + 1)`. Processes with low priority and little work are aborted first.
3. **Resource Preemption**: Forces a process to rollback a portion of its execution, relinquishing specific resources temporarily without fully aborting. Includes a starvation guard to prevent infinite victim cycles.

## 4. Simulator
The `Simulator` models OS time in "ticks". It manages a blocked queue and an active instruction set (scripts) for each process. Processes request resources, execute simulated work, and end. The simulator integrates with detection and auto-recovery seamlessly.
