# Project Procedure Guide (How to Recreate Deadlock Lab from Scratch)

This document details the complete, phase-by-phase procedure to design, implement, test, and deploy the **Deadlock Detection, Simulation & Recovery Lab** from scratch.

---

## Overview of the Development Lifecycle

```
[ Phase 1: Formal Models & Invariants ]
                 │
                 ▼
[ Phase 2: Dual Detection Engine (Tarjan SCC & Matrix Reduction) ]
                 │
                 ▼
[ Phase 3: Recovery Algorithms (Terminate, Cost Victim, Preempt) ]
                 │
                 ▼
[ Phase 4: Discrete-Event Simulator & Script Synthesizer ]
                 │
                 ▼
[ Phase 5: RESTful API Layer (FastAPI) ]
                 │
                 ▼
[ Phase 6: High-Performance Glassmorphic Web UI (Canvas/SVG + JS) ]
                 │
                 ▼
[ Phase 7: Scenario Benchmark Suite & Automated Testing (1000+ Tests) ]
```

---

## Phase 1: Formal Models & Invariant Validation

### Goal
Define the mathematical abstractions of processes, resources, system states, and actions, ensuring state invariants are enforced at all times.

### Step-by-Step Procedure:
1. **Define Core Data Classes (`engine/models.py`)**:
   - `Process`: Unique integer ID, human-readable name, priority (integer $\ge 0$), and `work_completed` counter.
   - `ResourceType`: Name (e.g., `"R0"`, `"MutexA"`), total available instances ($> 0$).
   - `SystemState`:
     - `processes`: List of `Process` objects.
     - `resources`: List of `ResourceType` objects.
     - `allocation`: Matrix of dimensions $P \times R$ where $A_{i,j}$ is instances of resource $j$ currently held by process $i$.
     - `request`: Matrix of dimensions $P \times R$ where $Q_{i,j}$ is instances of resource $j$ requested by process $i$.
     - `available`: Vector of length $R$ where $V_j$ is instances of resource $j$ free in the system.
2. **Implement Conservation Invariant (`engine/validation.py`)**:
   - Enforce the fundamental Operating System resource invariant:
     $$\text{Total}_j = \text{Available}_j + \sum_{i=0}^{P-1} \text{Allocation}_{i,j} \quad \forall j \in [0, R-1]$$
   - Raise a descriptive `StateValidationError` if dimensions mismatch or if the invariant is violated.

---

## Phase 2: Dual Algorithmic Detection Engine

### Goal
Detect deadlocks accurately across single-instance and multi-instance resource systems, distinguishing between structural cycles and genuine deadlocks.

### Step-by-Step Procedure:
1. **Create the Dispatcher (`engine/detection.py` -> `detect_deadlock`)**:
   - Inspect all resource types in the state.
   - If **all** resources have $\text{total} = 1$: Execute the **Wait-For-Graph (WFG)** cycle detector.
   - If **any** resource has $\text{total} > 1$: Execute the **Matrix Reduction Algorithm**.
2. **Implement Wait-For-Graph with Tarjan's SCC Algorithm**:
   - Construct directed edges: Process $P_i \to P_k$ exists if $P_i$ requests resource $R_m$ and $R_m$ is currently held by $P_k$.
   - Execute Tarjan’s Strongly Connected Components (SCC) or DFS cycle search with an explicit recursion stack.
   - Any SCC containing $> 1$ node or a self-loop is a confirmed deadlock.
3. **Implement General Matrix Reduction (Silberschatz / Banker's Variant)**:
   - Initialize work vector $W = \text{Available}$.
   - Initialize boolean vector $\text{Finish} = [False, \dots, False]$.
   - For any process where $\text{Allocation}_i = \vec{0}$, set $\text{Finish}_i = True$.
   - Iteratively find an unfinished process $P_i$ such that $\text{Request}_i \le W$.
     - If found: $W \leftarrow W + \text{Allocation}_i$, $\text{Finish}_i \leftarrow True$, record step in trace.
     - If no such process exists: Break loop.
   - The set of deadlocked processes is $\{ P_i \mid \text{Finish}_i = False \}$.
4. **Handle Cycle-Without-Deadlock Edge Case**:
   - When a cycle of requests exists in the graph but additional instances of resources can satisfy processes outside or within the cycle, flag `cycle_without_deadlock = True` and return `is_deadlocked = False`.

---

## Phase 3: Deadlock Recovery Mechanisms

### Goal
Implement automated strategies to break deadlocks by aborting or rolling back processes.

### Step-by-Step Procedure:
1. **Define Recovery Interface (`engine/recovery.py` -> `RecoveryStrategy`)**:
   - Define abstract method `recover(state: SystemState, deadlocked_pids: set[int]) -> RecoveryResult`.
2. **Strategy A: Terminate All (`TerminateAll`)**:
   - Abort all processes in `deadlocked_pids`.
   - Release all their allocations back to `available`.
   - Clear their pending requests.
3. **Strategy B: Cost-Based Single Victim Termination (`TerminateOneAtATime`)**:
   - Formulate a victim cost function that minimizes lost work while respecting process priority:
     $$\text{Cost}(P_i) = \frac{\text{work\_completed}(P_i)}{\text{priority}(P_i) + 1}$$
   - Pick $P_{\text{victim}} = \arg\min_{i \in \text{deadlocked}} \text{Cost}(P_i)$.
   - Abort $P_{\text{victim}}$, reclaim its resources, and re-run detection to verify if the deadlock is broken.
4. **Strategy C: Resource Preemption & Rollback (`ResourcePreemption`)**:
   - Select victim based on priority and preemption count (starvation guard).
   - Rollback the process state to a previous checkpoint or its initial state.
   - Reclaim allocated resources without deleting the process identity, allowing it to restart.

---

## Phase 4: Discrete-Event Simulator & Scenario Synthesizer

### Goal
Provide a tick-by-tick simulation of an Operating System scheduler handling concurrent process execution.

### Step-by-Step Procedure:
1. **Instruction Set Specification**:
   - Supported instructions: `REQUEST <resource> <count>`, `RELEASE <resource> <count>`, `WORK <ticks>`, `TERMINATE`.
2. **Simulator State Machine (`engine/simulator.py`)**:
   - Manage tick counter, active instructions pointer, blocked queue, and event logs.
   - At each `step()`:
     1. Unblock check: Iterate through blocked processes; grant requests if resources became available.
     2. Process active step: Execute current instruction for each unblocked process.
     3. Work decrement: For processes in `WORK` state, decrement remaining ticks and advance `work_completed`.
     4. Deadlock trigger: If configured trigger condition is met (e.g. on every block or every $N$ ticks), invoke `detect_deadlock()`.
     5. Automatic recovery: If recovery strategy is enabled and deadlock is found, execute recovery and log actions.
3. **Script Synthesizer (`engine/scenario.py`)**:
   - For scenarios defined purely with static matrices, auto-generate equivalent simulation scripts so every scenario can be simulated interactively.

---

## Phase 5: RESTful API Layer (FastAPI)

### Goal
Expose the engine over standard HTTP endpoints for client independence and web integration.

### Step-by-Step Procedure:
1. **Define Pydantic Request Models (`api/routes.py`)**:
   - `StatePayload`: Validates resource vectors, process metadata, and matrices.
   - `SimulateStartPayload`: Scenario name, recovery strategy, and trigger options.
   - `ManualRecoverPayload`: Process ID of selected victim and strategy type.
2. **Implement API Endpoints**:
   - `GET /api/scenarios`: List all pre-configured test scenarios.
   - `GET /api/scenarios/{name}`: Retrieve scenario JSON.
   - `POST /api/detect`: Run static deadlock detection and return trace + cycle data.
   - `POST /api/recover`: Run one-shot static recovery.
   - `POST /api/simulate/start`: Create an isolated simulator session with UUID.
   - `POST /api/simulate/step/{session_id}`: Advance simulation by 1 tick and return complete status.
   - `POST /api/simulate/manual_recover/{session_id}`: Abort/rollback user-specified victim process.
3. **Mount Static Assets (`api/server.py`)**:
   - Serve web client files (`index.html`, `style.css`, `app.js`, `graph.js`) on the root path `/`.

---

## Phase 6: High-Contrast Glassmorphic Web Dashboard

### Goal
Create a visual interface allowing users to view graphs, inspect matrices, step through simulations, and test manual recoveries.

### Step-by-Step Procedure:
1. **HTML Layout (`static/index.html`)**:
   - Top Navigation bar: Scenario switcher, Mode toggle (Static Analysis vs. Interactive Simulation), Engine status badge.
   - Main Grid:
     - Left Column: Resource Allocation Graph canvas / SVG visualizer.
     - Right Column: Dynamic matrix tables (Allocation, Request, Available).
     - Bottom Panel: Tick controls, auto-play speed slider, Manual Recovery victim selector, live event trace logs.
2. **Obsidian Glassmorphic Design (`static/style.css`)**:
   - Pitch-black backdrop (`#000000`) with subtle radial glow.
   - Semi-transparent glass containers (`rgba(14, 16, 22, 0.75)`) with `backdrop-filter: blur(20px)` and slim neon borders.
   - Bright white text (`#ffffff`), glowing process pill tags (`#60a5fa`), and yellow resource dots (`#fbbf24`).
3. **Graph Renderer (`static/graph.js`)**:
   - Draw bipartite or wait-for-graph with processes as circles and resources as squares.
   - Highlight deadlocked cycles with red glowing animated strokes.
   - Handle dragging and responsive layout adjustments.
4. **Frontend Controller (`static/app.js`)**:
   - Fetch scenario data, send detection requests, manage simulation timer for auto-play, render matrices, and dynamically stream event logs.

---

## Phase 7: Verification & Property-Based Testing

### Goal
Ensure 100% mathematical correctness and resilience against edge cases.

### Step-by-Step Procedure:
1. **Unit Tests**:
   - Test Tarjan SCC cycle detection on simple circular wait.
   - Test Matrix reduction algorithm on multi-instance safe and deadlocked states.
   - Test conservation invariant enforcement.
2. **Property-Based Equivalence Testing (`tests/test_random_equivalence.py`)**:
   - Generate **1,000 randomized single-instance states**.
   - Run both Tarjan's SCC algorithm and Matrix reduction algorithm on each.
   - Assert that both algorithms produce identical deadlock boolean flags and deadlocked process sets.
3. **API Integration & End-to-End Tests**:
   - Validate all endpoints using FastAPI `TestClient`.
   - Verify that all scenario files can be detected and simulated to completion.

---

## How to Execute the Completed Project

```bash
# 1. Initialize Python environment
python -m venv .venv
.venv\Scripts\activate       # Windows
# source .venv/bin/activate  # macOS / Linux

# 2. Install dependencies
pip install fastapi uvicorn pydantic pytest pytest-cov

# 3. Run all test suites
pytest

# 4. Start the interactive server
python run.py
# Open your browser at: http://127.0.0.1:8000
```
