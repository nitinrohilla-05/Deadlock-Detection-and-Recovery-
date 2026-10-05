# Deadlock Lab: Comprehensive File Purpose Directory

This document provides a complete reference guide explaining the **exact purpose, responsibility, and interactions of every file** in the Deadlock Lab codebase.

---

## 1. Quick Reference File Map

| File Path | Component | Primary Purpose |
| :--- | :--- | :--- |
| [`run.py`](file:///c:/Users/HP/OneDrive/Desktop/Deadlock/run.py) | Root Runner | Launches the Uvicorn FastAPI server and opens the browser. |
| [`requirements.txt`](file:///c:/Users/HP/OneDrive/Desktop/Deadlock/requirements.txt) | Dependencies | Lists runtime and testing dependencies (`fastapi`, `uvicorn`, `pytest`). |
| [`generate_scenarios.py`](file:///c:/Users/HP/OneDrive/Desktop/Deadlock/generate_scenarios.py) | Utility | Script used to generate complex and edge-case benchmark scenario JSON files. |
| [`PROCEDURE.md`](file:///c:/Users/HP/OneDrive/Desktop/Deadlock/PROCEDURE.md) | Documentation | Step-by-step procedure guide to recreate the entire project from scratch. |
| [`FILE_PURPOSE.md`](file:///c:/Users/HP/OneDrive/Desktop/Deadlock/FILE_PURPOSE.md) | Documentation | This file; comprehensive file-by-file purpose directory. |
| [`engine/models.py`](file:///c:/Users/HP/OneDrive/Desktop/Deadlock/engine/models.py) | Engine Core | Data structures (`Process`, `ResourceType`, `SystemState`, `DetectionResult`). |
| [`engine/validation.py`](file:///c:/Users/HP/OneDrive/Desktop/Deadlock/engine/validation.py) | Engine Core | Enforces the system resource conservation invariant ($\text{Total} = \text{Available} + \sum \text{Alloc}$). |
| [`engine/detection.py`](file:///c:/Users/HP/OneDrive/Desktop/Deadlock/engine/detection.py) | Engine Core | Dual detection algorithm: Tarjan WFG (single-instance) & Matrix Reduction (multi-instance). |
| [`engine/recovery.py`](file:///c:/Users/HP/OneDrive/Desktop/Deadlock/engine/recovery.py) | Engine Core | Deadlock breaking strategies (`TerminateAll`, cost-based `TerminateOne`, and `ResourcePreemption`). |
| [`engine/simulator.py`](file:///c:/Users/HP/OneDrive/Desktop/Deadlock/engine/simulator.py) | Engine Core | Tick-based discrete event OS simulator managing queues, scripts, and recoveries. |
| [`engine/scenario.py`](file:///c:/Users/HP/OneDrive/Desktop/Deadlock/engine/scenario.py) | Engine Core | Scenario JSON deserializer and procedural simulation script synthesizer. |
| [`engine/metrics.py`](file:///c:/Users/HP/OneDrive/Desktop/Deadlock/engine/metrics.py) | Engine Core | Telemetry tracker recording ticks, blocked counts, victims aborted, and throughput. |
| [`api/server.py`](file:///c:/Users/HP/OneDrive/Desktop/Deadlock/api/server.py) | REST API | FastAPI application entrypoint, router mounting, and static file hosting. |
| [`api/routes.py`](file:///c:/Users/HP/OneDrive/Desktop/Deadlock/api/routes.py) | REST API | HTTP endpoints for static detection, recovery, scenario queries, and simulation sessions. |
| [`cli/main.py`](file:///c:/Users/HP/OneDrive/Desktop/Deadlock/cli/main.py) | CLI | Terminal interface for headless testing, scenario running, and ASCII table viewing. |
| [`static/index.html`](file:///c:/Users/HP/OneDrive/Desktop/Deadlock/static/index.html) | Frontend | Single Page Application dashboard layout with graph canvas, controls, and matrix tables. |
| [`static/style.css`](file:///c:/Users/HP/OneDrive/Desktop/Deadlock/static/style.css) | Frontend | Pitch-black obsidian glassmorphic styling, high-contrast typography, and responsive grid. |
| [`static/app.js`](file:///c:/Users/HP/OneDrive/Desktop/Deadlock/static/app.js) | Frontend | Frontend state machine, API fetch client, simulation ticker, and matrix table renderer. |
| [`static/graph.js`](file:///c:/Users/HP/OneDrive/Desktop/Deadlock/static/graph.js) | Frontend | Canvas/SVG graph engine rendering processes, resources, directed edges, and deadlock cycles. |
| [`static/theme.js`](file:///c:/Users/HP/OneDrive/Desktop/Deadlock/static/theme.js) | Frontend | Persistent dark/light theme switcher and local storage helper. |

---

## 2. Root Files

### [`run.py`](file:///c:/Users/HP/OneDrive/Desktop/Deadlock/run.py)
* **Purpose:** Single command entrypoint to start the entire web application.
* **Responsibilities:**
  - Starts the `uvicorn` ASGI web server on host `127.0.0.1` and port `8000`.
  - Automatically launches the user's default browser pointing to `http://127.0.0.1:8000`.
  - Provides a clean Ctrl+C shutdown signal.

### [`requirements.txt`](file:///c:/Users/HP/OneDrive/Desktop/Deadlock/requirements.txt)
* **Purpose:** Defines the Python package requirements.
* **Dependencies Included:**
  - `fastapi`: High-performance asynchronous web framework for REST endpoints.
  - `uvicorn`: ASGI server implementation for FastAPI.
  - `pydantic`: Strong schema validation for API payloads.
  - `pytest` & `pytest-cov`: Testing framework and code coverage analyzer.

### [`generate_scenarios.py`](file:///c:/Users/HP/OneDrive/Desktop/Deadlock/generate_scenarios.py)
* **Purpose:** Offline utility generator script.
* **Responsibilities:** Procedurally produces valid, balanced JSON scenarios (such as random graphs and multi-cycle topologies) ensuring all generated matrices satisfy mathematical invariants.

---

## 3. Core Engine (`engine/`)

### [`engine/models.py`](file:///c:/Users/HP/OneDrive/Desktop/Deadlock/engine/models.py)
* **Purpose:** Defines the object-oriented abstractions and data structures representing the OS state.
* **Classes:**
  - `Process`: Represents a task with `id`, `name`, `priority`, and accumulated `work_completed`.
  - `ResourceType`: Represents a resource with `name` and total capacity `total`.
  - `SystemState`: Encapsulates the complete snapshot of the system:
    - Lists of processes and resources.
    - $P \times R$ `allocation` matrix.
    - $P \times R$ `request` matrix.
    - Vector of `available` resources.
  - `DetectionResult`: Carries the output of deadlock detection (`is_deadlocked`, `deadlocked_pids`, `cycles`, `trace`, and `cycle_without_deadlock`).
  - `Action` & `RecoveryResult`: Encapsulate recovery operations (`ABORT`, `PREEMPT`, `ROLLBACK`).

### [`engine/validation.py`](file:///c:/Users/HP/OneDrive/Desktop/Deadlock/engine/validation.py)
* **Purpose:** Enforces physical and mathematical validity of the OS state before detection or simulation.
* **Responsibilities:**
  - Verifies matrix dimensions match $P \times R$.
  - Asserts non-negativity of all matrix entries.
  - Validates the fundamental resource conservation invariant:
    $$\text{Available}_j + \sum_{i} \text{Allocation}_{i,j} == \text{Total}_j \quad \forall j$$
  - Raises `StateValidationError` if any check fails.

### [`engine/detection.py`](file:///c:/Users/HP/OneDrive/Desktop/Deadlock/engine/detection.py)
* **Purpose:** Implements the dual deadlock detection algorithms.
* **Key Components:**
  - `detect_deadlock(state)`: Smart dispatcher. Evaluates whether the system consists solely of single-instance resources or multi-instance resources and invokes the appropriate algorithm.
  - **Tarjan's SCC Wait-For-Graph (WFG) Algorithm**: Converts process-resource allocations into a directed wait-for-graph between processes and locates strongly connected components containing cycles.
  - **Matrix Reduction Algorithm (Silberschatz / Banker's Variant)**: Simulates hypothetical process completion by progressively granting requests if $Request_i \le Work$, returning the set of processes that can never complete.
  - **Disambiguation of "Cycle Without Deadlock"**: Properly verifies whether a cycle of requests is non-fatal because available capacity or non-cycle processes can unblock the system.

### [`engine/recovery.py`](file:///c:/Users/HP/OneDrive/Desktop/Deadlock/engine/recovery.py)
* **Purpose:** Implements automated deadlock resolution mechanisms.
* **Strategies:**
  - `TerminateAll`: Aborts every deadlocked process simultaneously, freeing all their held resources back to the pool.
  - `TerminateOneAtATime`: Iteratively selects a single victim using a cost function:
    $$\text{Cost} = \frac{\text{work\_completed}}{\text{priority} + 1}$$
    Aborts the lowest cost victim, reclaims resources, re-runs detection, and repeats only if deadlocks remain.
  - `ResourcePreemption`: Temporarily strips allocated resources from a victim process, rolling its execution back to a previous checkpoint without terminating it. Includes a starvation counter.

### [`engine/simulator.py`](file:///c:/Users/HP/OneDrive/Desktop/Deadlock/engine/simulator.py)
* **Purpose:** Discrete-event execution engine modeling time progression in discrete "ticks".
* **Responsibilities:**
  - Maintains process instruction pointers, blocked queues, and historical checkpoints.
  - Supports script instructions: `REQUEST`, `RELEASE`, `WORK`, and `TERMINATE`.
  - In each `step()` tick:
    1. Attempts to unblock waiting processes.
    2. Executes active process instructions.
    3. Decrements active work counters and credits completed work.
    4. Triggers detection based on configured policy (e.g. on every block).
    5. Applies configured recovery strategy if a deadlock occurs.
  - Stores a chronological event log of all state transitions.

### [`engine/scenario.py`](file:///c:/Users/HP/OneDrive/Desktop/Deadlock/engine/scenario.py)
* **Purpose:** File loader and script synthesizer for scenario definitions.
* **Responsibilities:**
  - Loads and deserializes scenario `.json` files into `Scenario` dataclasses.
  - Converts scenario definitions into live `SystemState` objects.
  - `synthesize_scripts(scenario)`: Automatically generates valid step-by-step simulation scripts for scenarios defined purely as static matrices, enabling interactive simulation across all test cases.

### [`engine/metrics.py`](file:///c:/Users/HP/OneDrive/Desktop/Deadlock/engine/metrics.py)
* **Purpose:** Real-time telemetry tracker for simulations.
* **Metrics Recorded:** Total ticks elapsed, deadlocks detected, recovery routines invoked, victim processes aborted/preempted, and process completion throughput.

---

## 4. API Layer (`api/`)

### [`api/server.py`](file:///c:/Users/HP/OneDrive/Desktop/Deadlock/api/server.py)
* **Purpose:** Configures and launches the FastAPI application.
* **Responsibilities:**
  - Instantiates the `FastAPI` app.
  - Mounts the REST router under the `/api` prefix.
  - Mounts the `/static` folder and serves `index.html` as the root route (`/`).

### [`api/routes.py`](file:///c:/Users/HP/OneDrive/Desktop/Deadlock/api/routes.py)
* **Purpose:** Exposes HTTP endpoints for frontend and external client interaction.
* **Endpoints:**
  - `GET /api/scenarios`: Returns list of available scenario files.
  - `GET /api/scenarios/{name}`: Returns the JSON configuration of a specific scenario.
  - `POST /api/detect`: Analyzes a given `SystemState` and returns detection results, cycles, and execution trace.
  - `POST /api/recover`: Executes one-shot recovery on a static state.
  - `POST /api/simulate/start`: Initializes a stateful simulation session, returning a `session_id`.
  - `POST /api/simulate/step/{session_id}`: Advances simulation by 1 tick and returns updated state, logs, and metrics.
  - `GET /api/simulate/status/{session_id}`: Polls the current state of a running simulation session.
  - `POST /api/simulate/manual_recover/{session_id}`: Allows the user to select and abort/preempt a specific victim process manually.

---

## 5. Command-Line Interface (`cli/`)

### [`cli/main.py`](file:///c:/Users/HP/OneDrive/Desktop/Deadlock/cli/main.py)
* **Purpose:** Interactive terminal interface for headless environments or terminal users.
* **Responsibilities:**
  - Allows selecting and loading any scenario directly from the console.
  - Prints formatted ASCII tables of Allocation, Request, and Available vectors.
  - Runs detection and displays step-by-step reduction traces or detected cycles in terminal color.
  - Provides step-by-step CLI simulation execution.

---

## 6. Frontend Web Dashboard (`static/`)

### [`static/index.html`](file:///c:/Users/HP/OneDrive/Desktop/Deadlock/static/index.html)
* **Purpose:** The structure and markup of the Deadlock Lab dashboard.
* **Sections:**
  - Navigation bar with scenario selector, mode toggles, and status badges.
  - Visual graph canvas container with legend (processes, resources, request edges, allocation edges).
  - Matrix tables view: Live rendered Allocation, Request, and Available matrices.
  - Simulation controller: Start/Pause button, Step Forward, Auto-play speed slider, Recovery strategy selector.
  - Manual recovery drawer: Victim process dropdown and abort button.
  - Metrics cards and real-time scrolling event log stream.

### [`static/style.css`](file:///c:/Users/HP/OneDrive/Desktop/Deadlock/static/style.css)
* **Purpose:** Comprehensive styling and responsive UI design system.
* **Key Aesthetic Elements:**
  - Pitch-black obsidian theme (`#000000`) with subtle deep violet radial glows.
  - Translucent glassmorphism panels (`rgba(14, 16, 22, 0.75)`) with backdrop blur.
  - 100% high-contrast typography: pure white text (`#ffffff`) on dark backgrounds.
  - Color-coded badges for processes (blue `#60a5fa`), resources (amber `#fbbf24`), safe states (emerald `#10b981`), and deadlocks (red `#ef4444`).

### [`static/app.js`](file:///c:/Users/HP/OneDrive/Desktop/Deadlock/static/app.js)
* **Purpose:** Primary client-side controller and application logic.
* **Responsibilities:**
  - Fetches scenario catalog and manages active scenario state.
  - Switches between Static Analysis Mode and Simulation Mode.
  - Sends detection requests to `/api/detect` and formats reduction traces.
  - Manages simulation session lifecycle (`startSimulation`, `stepSimulation`, `toggleAutoRun`).
  - Implements the auto-play timer loop with dynamic speed control.
  - Handles manual victim selection and executes manual recovery calls.
  - Re-renders matrix tables and streams event log entries.

### [`static/graph.js`](file:///c:/Users/HP/OneDrive/Desktop/Deadlock/static/graph.js)
* **Purpose:** Graph visualization engine.
* **Responsibilities:**
  - Renders processes as circular nodes and resources as rounded square nodes.
  - Draws directed allocation edges (Resource $\to$ Process) and request edges (Process $\to$ Resource).
  - Highlights deadlocked cycles with red glowing borders and animated indicators.
  - Supports node dragging and responsive coordinate recalculation.

### [`static/theme.js`](file:///c:/Users/HP/OneDrive/Desktop/Deadlock/static/theme.js)
* **Purpose:** Theme management script for persisting UI preferences in browser `localStorage`.

---

## 7. Scenario Test Cases (`scenarios/`)

* [`scenarios/two_process_circular.json`](file:///c:/Users/HP/OneDrive/Desktop/Deadlock/scenarios/two_process_circular.json): Minimal 2-process, 2-resource classic circular wait deadlock ($P_0 \to R_1 \to P_1 \to R_0 \to P_0$).
* [`scenarios/dining_philosophers.json`](file:///c:/Users/HP/OneDrive/Desktop/Deadlock/scenarios/dining_philosophers.json): Classic 5-philosopher single-instance circular deadlock.
* [`scenarios/dining_philosophers_sim.json`](file:///c:/Users/HP/OneDrive/Desktop/Deadlock/scenarios/dining_philosophers_sim.json): Variant of dining philosophers with asymmetric ordering that simulates to completion safely without deadlock.
* [`scenarios/large_random.json`](file:///c:/Users/HP/OneDrive/Desktop/Deadlock/scenarios/large_random.json): Stress-test scenario with 15 processes, 8 resource types, containing a 5-process deadlock sub-graph ($P_0 \dots P_4$) alongside active unblocked processes.
* [`scenarios/cycle_without_deadlock.json`](file:///c:/Users/HP/OneDrive/Desktop/Deadlock/scenarios/cycle_without_deadlock.json): Classic edge case containing a structural cycle in the graph, but sufficient multi-instance resources exist so the system does not deadlock.
* [`scenarios/two_independent_deadlocks.json`](file:///c:/Users/HP/OneDrive/Desktop/Deadlock/scenarios/two_independent_deadlocks.json): Two completely disconnected deadlock cycles existing concurrently in the same system ($P_0 \leftrightarrow P_1$ and $P_2 \leftrightarrow P_3$).
* [`scenarios/textbook_deadlock.json`](file:///c:/Users/HP/OneDrive/Desktop/Deadlock/scenarios/textbook_deadlock.json): Standard multi-instance deadlock example from Silberschatz & Galvin Operating Systems textbook.
* [`scenarios/textbook_safe.json`](file:///c:/Users/HP/OneDrive/Desktop/Deadlock/scenarios/textbook_safe.json): Benchmark safe state from the Silberschatz textbook demonstrating a successful Banker's reduction trace.
* [`scenarios/two_process_sim.json`](file:///c:/Users/HP/OneDrive/Desktop/Deadlock/scenarios/two_process_sim.json): Two-process sequence demonstrating safe interleaved execution.

---

## 8. Automated Test Suite (`tests/`)

* [`tests/test_models.py`](file:///c:/Users/HP/OneDrive/Desktop/Deadlock/tests/test_models.py): Verifies constructors, serialization, and immutability of core data models.
* [`tests/test_validation.py`](file:///c:/Users/HP/OneDrive/Desktop/Deadlock/tests/test_validation.py): Validates invariant checking, dimension validations, and negative count assertions.
* [`tests/test_detection.py`](file:///c:/Users/HP/OneDrive/Desktop/Deadlock/tests/test_detection.py): Unit tests for Tarjan's SCC cycle detector, Matrix reduction, and the cycle-without-deadlock edge case.
* [`tests/test_random_equivalence.py`](file:///c:/Users/HP/OneDrive/Desktop/Deadlock/tests/test_random_equivalence.py): **1,000 property-based randomized tests** asserting that Tarjan's WFG algorithm and the Matrix reduction algorithm produce identical results on any single-instance resource state.
* [`tests/test_recovery.py`](file:///c:/Users/HP/OneDrive/Desktop/Deadlock/tests/test_recovery.py): Tests `TerminateAll`, `TerminateOneAtATime` cost calculation, victim selection, and preemption rollback.
* [`tests/test_scenarios.py`](file:///c:/Users/HP/OneDrive/Desktop/Deadlock/tests/test_scenarios.py): Automated schema validation of all 9 JSON scenario files in `scenarios/`.
* [`tests/test_simulator.py`](file:///c:/Users/HP/OneDrive/Desktop/Deadlock/tests/test_simulator.py): Tests simulator tick transitions, blocked queue ordering, and auto-recovery triggers.
* [`tests/test_api.py`](file:///c:/Users/HP/OneDrive/Desktop/Deadlock/tests/test_api.py): FastAPI `TestClient` integration tests for detection, recovery, scenario endpoints, and simulation sessions.

---

## 9. Academic & Demo Documentation (`docs/`)

* [`docs/REPORT.md`](file:///c:/Users/HP/OneDrive/Desktop/Deadlock/docs/REPORT.md): Technical engineering report detailing the mathematical formulation, algorithmic choices, and architecture.
* [`docs/VIVA.md`](file:///c:/Users/HP/OneDrive/Desktop/Deadlock/docs/VIVA.md): Comprehensive Viva Voce / oral examination preparation document containing questions and in-depth theoretical answers on deadlock theory.
* [`docs/DEMO.md`](file:///c:/Users/HP/OneDrive/Desktop/Deadlock/docs/DEMO.md): Step-by-step demonstration walkthrough for presentations or lab evaluations.
