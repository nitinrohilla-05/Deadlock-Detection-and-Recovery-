# Deadlock Lab: Deadlock Detection, Simulation & Recovery Engine

**Python 3.10+** • **FastAPI** • **1,024 Passing Pytests** • **90%+ Coverage** • **Pitch-Black Glassmorphic UI** • **MIT License**

An academic and industrial-grade **Deadlock Detection, Discrete-Event Simulation, and Automated Recovery System** for Operating Systems. Features a dual-engine algorithmic core (Wait-For-Graph with Tarjan's SCC & General Matrix Reduction), multi-mode tick-based concurrency simulator, cost-based automated recovery strategies, and an interactive **pitch-black obsidian glassmorphic** web dashboard.

---

## Table of Contents
1. [Key Features & Innovations](#1-key-features--innovations)
2. [Algorithmic & Mathematical Architecture](#2-algorithmic--mathematical-architecture)
3. [System Architecture](#3-system-architecture)
4. [Quick Start & Portability Guide](#4-quick-start--portability-guide)
5. [Interactive Web Dashboard Tour](#5-interactive-web-dashboard-tour)
6. [Pre-Configured Benchmark Scenarios](#6-pre-configured-benchmark-scenarios)
7. [Automated Recovery Strategies](#7-automated-recovery-strategies)
8. [CLI Terminal Tool](#8-cli-terminal-tool)
9. [RESTful API Reference](#9-restful-api-reference)
10. [Test Suite & Property-Based Verification](#10-test-suite--property-based-verification)
11. [Project Documentation Links](#11-project-documentation-links)

---

## 1. Key Features & Innovations

* **Dual Detection Engine**:
  * **Wait-For-Graph (WFG)**: Operates on single-instance resource systems using **Tarjan's Strongly Connected Components (SCC)** algorithm ($\mathcal{O}(V + E)$).
  * **Matrix Reduction (Silberschatz / Banker's Variant)**: Operates on general multi-instance resource systems ($\mathcal{O}(P^2 \times R)$).
  * **Cycle-Without-Deadlock Disambiguation**: Correctly identifies non-fatal dependency cycles where available capacities or unblocked threads can resolve the loop.
* **Tick-Based Concurrency Simulator**:
  * Models real OS time progression in discrete ticks.
  * Supports concurrent instruction streams: `REQUEST`, `RELEASE`, `WORK`, and `TERMINATE`.
  * Manages active instruction pointers, blocked queues, checkpoints, and real-time state transitions.
  * One-click **Auto-Play** with dynamic speed slider (100ms - 2000ms per tick).
* **Automated & Manual Recovery Strategies**:
  * **Terminate All**: Immediate abort of all deadlocked processes.
  * **Terminate One (Cost-Based Victim Selection)**: Iterative abortion minimizing lost CPU time while preserving high-priority tasks.
  * **Resource Preemption & Rollback**: Reclaims allocated resources without destroying the task identity, complete with a **starvation prevention guard**.
  * **Interactive Manual Recovery Drawer**: Allows the user to select specific victim processes and abort/preempt them on the fly.
* **Pitch-Black Obsidian Glassmorphism UI**:
  * Deep `#000000` pitch-black foundation with subtle radial accents.
  * Semi-transparent glass containers (`rgba(14, 16, 22, 0.75)`) with `backdrop-filter: blur(20px)`.
  * High-contrast typography (pure white `#ffffff`, slate `#94a3b8`, glowing blue processes, and yellow resource markers).
  * Interactive SVG/Canvas force-directed Resource Allocation Graph (RAG) with animated red glow for deadlocked cycles.
* **100% Self-Contained & Portable**:
  * Zero Node.js or npm dependencies; all frontend logic is pure native ES6 JavaScript, HTML5, and CSS3.
  * Runs seamlessly on any Windows, macOS, or Linux machine with standard Python.

---

## 2. Algorithmic & Mathematical Architecture

### 2.1 State Representation & Invariant
A system state is formally defined as a tuple:
$$\mathcal{S} = (\mathcal{P}, \mathcal{R}, \mathbf{A}, \mathbf{Q}, \mathbf{V})$$
Where:
* $\mathcal{P} = \{P_0, P_1, \dots, P_{n-1}\}$ is the set of $n$ processes. Each process has priority $w_i \ge 0$ and accumulated work $c_i \ge 0$.
* $\mathcal{R} = \{R_0, R_1, \dots, R_{m-1}\}$ is the set of $m$ resource types with total capacity vector $\mathbf{T} \in \mathbb{N}^m$.
* $\mathbf{A} \in \mathbb{N}^{n \times m}$: Allocation matrix where $A_{i,j}$ is instances of resource $j$ held by process $i$.
* $\mathbf{Q} \in \mathbb{N}^{n \times m}$: Request matrix where $Q_{i,j}$ is instances of resource $j$ actively requested by process $i$.
* $\mathbf{V} \in \mathbb{N}^m$: Available vector where $V_j$ is unallocated instances of resource $j$.

#### Fundamental Conservation Invariant
Every valid state must satisfy:
$$T_j = V_j + \sum_{i=0}^{n-1} A_{i,j} \quad \forall j \in \{0, \dots, m-1\}$$
Any violation raises a `StateValidationError` during validation.

---

### 2.2 Algorithm 1: Wait-For-Graph (Single-Instance Resources)
When $\forall j, T_j = 1$, the system maps to a directed Wait-For-Graph $\mathcal{G} = (\mathcal{V}, \mathcal{E})$:
* Vertices $\mathcal{V} = \mathcal{P}$.
* Directed edge $P_i \to P_k$ exists if $P_i$ is waiting for resource $R_m$ currently allocated to $P_k$.

**Detection Theorem**: A deadlock exists if and only if $\mathcal{G}$ contains a directed cycle.
We implement **Tarjan's Strongly Connected Components (SCC)** algorithm using a single depth-first search (DFS) pass maintaining discovery times and lowest reachable indices (`lowlink`). Any SCC with $|C| > 1$ or a self-loop is marked as deadlocked.

$$\text{Time Complexity: } \mathcal{O}(|\mathcal{V}| + |\mathcal{E}|) \equiv \mathcal{O}(n + m)$$

---

### 2.3 Algorithm 2: General Matrix Reduction (Multi-Instance Resources)
When $\exists j, T_j > 1$, cycles in the allocation graph do not necessarily imply deadlock. The general reduction algorithm is used:

```python
Work = Available.copy()
Finish = [False] * n

# Step 1: Processes with zero allocation cannot cause deadlocks
for i in range(n):
    if Allocation[i] == 0:
        Finish[i] = True

# Step 2: Iteratively find a process whose requests can be satisfied
while True:
    found = False
    for i in range(n):
        if not Finish[i] and Request[i] <= Work:
            Work += Allocation[i]
            Finish[i] = True
            found = True
            break
    if not found:
        break

# Step 3: Any process that cannot finish is deadlocked
Deadlocked = {P_i for i in range(n) if not Finish[i]}
```

$$\text{Time Complexity: } \mathcal{O}(n^2 \times m)$$

---

### 2.4 Cost-Based Victim Selection
When resolving deadlocks iteratively, the optimal victim $P^*$ minimizes total lost computation while respecting process priority:
$$\text{Cost}(P_i) = \frac{\text{work\_completed}(P_i) + 1}{\text{priority}(P_i) + 1}$$
$$P^* = \arg\min_{P_i \in \text{Deadlocked}} \text{Cost}(P_i)$$
* Low-priority tasks that have barely started execution are terminated first.
* High-priority tasks near completion are protected.

---

## 3. System Architecture

```
┌────────────────────────────────────────────────────────────────────────┐
│                   Browser Dashboard (HTML5 / CSS3 / Vanilla ES6)      │
│     ┌─────────────────────┐   ┌──────────────────┐   ┌───────────────┐ │
│     │ SVG / Canvas Graph  │   │ Live Matrices    │   │ Simulation    │ │
│     │ Interactive RAG/WFG │   │ Alloc/Req/Avail  │   │ Auto-Play/Step│ │
│     └─────────────────────┘   └──────────────────┘   └───────────────┘ │
└────────────────────────────────────▲───────────────────────────────────┘
                                     │ HTTP / JSON REST APIs
┌────────────────────────────────────▼───────────────────────────────────┐
│                     FastAPI Application Layer (api/)                  │
│   • /api/detect         • /api/simulate/start    • /api/scenarios      │
│   • /api/recover        • /api/simulate/step     • /api/simulate/status│
└────────────────────────────────────▲───────────────────────────────────┘
                                     │ In-Memory Sessions & Direct Calls
┌────────────────────────────────────▼───────────────────────────────────┐
│                       Core Algorithmic Engine (engine/)                │
│  ┌────────────────────┐ ┌────────────────────┐ ┌────────────────────┐  │
│  │   models.py        │ │   detection.py     │ │   recovery.py      │  │
│  │ State, Process, Res│ │ Tarjan SCC, Matrix │ │ Terminate, Preempt │  │
│  └────────────────────┘ └────────────────────┘ └────────────────────┘  │
│  ┌────────────────────┐ ┌────────────────────┐ ┌────────────────────┐  │
│  │   simulator.py     │ │   scenario.py      │ │   metrics.py       │  │
│  │ Tick State Machine │ │ Loader & Synthesizer│ │ Telemetry Tracker  │  │
│  └────────────────────┘ └────────────────────┘ └────────────────────┘  │
└────────────────────────────────────────────────────────────────────────┘
```

---

## 4. Quick Start & Portability Guide

The project is completely self-contained and works on **Windows, macOS, and Linux**.

### Prerequisites
* **Python 3.10 or higher** installed ([python.org](https://www.python.org/downloads/)).
* Git (optional — you can also click **Code $\to$ Download ZIP**).

### Installation & Execution (3 Commands)

```bash
# 1. Clone or extract the repository
git clone https://github.com/nitinrohilla-05/Deadlock-Detection-and-Recovery-.git
cd Deadlock-Detection-and-Recovery-

# 2. Install dependencies (FastAPI, Uvicorn, Pytest)
pip install -r requirements.txt

# 3. Launch the Web UI
python run.py
```

`run.py` boots the server at `http://127.0.0.1:8000` and **automatically opens your default browser**.

---

## 5. Interactive Web Dashboard Tour

The Web UI provides two comprehensive operating modes:

### Mode 1: Static Analysis Mode
* **Resource Allocation Graph (RAG)**: Visualizes processes as circles and resources as squares. Directed green edges denote resource assignments; yellow dashed edges denote pending requests.
* **Deadlock Detection**: Clicking **"Detect Deadlock"** computes the state. If a deadlock exists:
  * The status banner glows red: `⚠ DEADLOCK DETECTED`.
  * Deadlocked cycles in the graph animate with a glowing crimson pulse.
  * An execution trace table illustrates the step-by-step matrix reduction or SCC decomposition.
* **Static One-Shot Recovery**: Test immediate automated resolution using Terminate All, Terminate One, or Resource Preemption.

### Mode 2: Interactive Simulation Mode
* **One-Click Instant Run**: Clicking **"Start Simulation"** begins execution immediately, ticking through process scripts.
* **Live Speed Slider**: Adjust simulation playback speed from 100ms (fast) to 2000ms (slow).
* **Dynamic Pause/Resume**: Pause simulation at any tick to inspect live allocation matrices.
* **Manual Recovery Drawer**: When simulation encounters a deadlock under manual mode, it cleanly pauses, activates the victim dropdown, and lets you select and abort any process manually.
* **Live Event Stream**: Real-time console showing requests, grants, blocks, releases, and recovery logs.

---

## 6. Pre-Configured Benchmark Scenarios

The repository includes 9 verified scenarios located in [`scenarios/`](scenarios/):

| Scenario Name | Processes | Resources | Topology / Characteristics | Expected Result |
| :--- | :---: | :---: | :--- | :--- |
| `two_process_circular.json` | 2 | 2 | Classic 2-thread mutex circular wait ($P_0 \to R_1 \to P_1 \to R_0$). | **Deadlock** ($P_0, P_1$) |
| `dining_philosophers.json` | 5 | 5 | 5 philosophers each holding one fork and requesting the next. | **Deadlock** ($P_0 \dots P_4$) |
| `dining_philosophers_sim.json`| 5 | 5 | Resource hierarchy solution to dining philosophers. | **Safe** (Simulates to completion) |
| `large_random.json` | 15 | 8 | 15 processes, 8 multi-instance resources with embedded 5-cycle. | **Deadlock** ($P_0 \dots P_4$) |
| `cycle_without_deadlock.json` | 4 | 2 | Multi-instance graph with a cycle where extra units unblock tasks. | **Safe** (`cycle_without_deadlock=True`)|
| `two_independent_deadlocks.json`| 4 | 4 | Two completely disjoint deadlock cycles ($P_0 \leftrightarrow P_1$ and $P_2 \leftrightarrow P_3$). | **Deadlock** ($P_0, P_1, P_2, P_3$) |
| `textbook_deadlock.json` | 5 | 3 | Silberschatz Operating Systems textbook multi-instance deadlock. | **Deadlock** ($P_1, P_2, P_3, P_4$) |
| `textbook_safe.json` | 5 | 3 | Silberschatz textbook safe state benchmark. | **Safe** (Full reduction trace) |
| `two_process_sim.json` | 2 | 2 | Non-conflicting interleaved process scripts. | **Safe** (Completes cleanly) |

---

## 7. Automated Recovery Strategies

```
                     ┌─────────────────────────┐
                     │   Deadlock Detected     │
                     └────────────┬────────────┘
                                  │
         ┌────────────────────────┼────────────────────────┐
         ▼                        ▼                        ▼
┌──────────────────┐    ┌──────────────────┐    ┌──────────────────┐
│  Terminate All   │    │  Terminate One   │    │Resource Preempt  │
│  (Aggressive)    │    │   (Cost-Based)   │    │   (Rollback)     │
├──────────────────┤    ├──────────────────┤    ├──────────────────┤
│ Abort all tasks  │    │ Calculate cost:  │    │ Preempt resource │
│ in deadlock set; │    │ C = work/(prio+1)│    │ from victim;     │
│ reclaim all units│    │ Abort lowest task│    │ rollback script  │
│ at once.         │    │ Re-check cycle.  │    │ to checkpoint.   │
└──────────────────┘    └──────────────────┘    └──────────────────┘
```

1. **`TerminateAll`**: Drastic recovery. Frees all allocations immediately.
2. **`TerminateOneAtATime`**: Graceful recovery. Aborts one task, returns its resources, and re-invokes detection. If the cycle is broken, no further processes are terminated.
3. **`ResourcePreemption`**: Non-fatal recovery. Takes resources away from a process and rewinds its instruction pointer to a saved checkpoint. Includes a counter preventing the same process from being preempted more than 3 times (starvation guard).

---

## 8. CLI Terminal Tool

You can run experiments, analyze custom JSON files, and simulate executions directly in your terminal without a browser:

```bash
python -m cli.main
```

### Features of the CLI:
* Interactive scenario picker.
* Colorized terminal ASCII matrix tables (Allocation, Request, Available).
* Direct step-by-step reduction traces and detected cycle paths.
* Step-by-step simulation debugger.

---

## 9. RESTful API Reference

The FastAPI backend exposes standard HTTP endpoints under the `/api` prefix:

### Detection & Recovery
* `POST /api/detect`: Analyzes a state and returns detection status, cycles, and traces.
* `POST /api/recover`: Executes one-shot static recovery on a given state payload.

### Scenarios
* `GET /api/scenarios`: Returns catalog of all available scenario JSON files.
* `GET /api/scenarios/{name}`: Fetches complete configuration and scripts for a scenario.

### Simulation Sessions
* `POST /api/simulate/start`: Creates a stateful simulator session.
  ```json
  {
    "scenario": "large_random",
    "strategy": "terminate_one",
    "trigger_config": {"type": "blocked"}
  }
  ```
  *Response:* `{"session_id": "4b684346-a4c3-4d45-926b-d0a06fa34958"}`
* `POST /api/simulate/step/{session_id}`: Advances the session by 1 tick and returns updated matrices, event logs, blocked lists, and metrics.
* `GET /api/simulate/status/{session_id}`: Polls the current state of a running session.
* `POST /api/simulate/manual_recover/{session_id}`: Aborts or preempts a specific victim process:
  ```json
  {
    "victim_id": 0,
    "strategy": "terminate_one"
  }
  ```

---

## 10. Test Suite & Property-Based Verification

The project includes an exhaustive automated test suite with **1,024 test cases**:

```bash
# Run complete test suite with coverage report
pytest --cov=engine --cov-fail-under=90 tests/
```

### Test Coverage Highlights:
* **Property-Based Randomized Equivalence (`tests/test_random_equivalence.py`)**: Generates **1,000 randomized state topologies** and mathematically proves that Tarjan's SCC Wait-For-Graph algorithm and the Matrix Reduction algorithm yield identical results for all single-instance configurations.
* **Edge Case Verification (`tests/test_detection.py`)**: Tests cycles without deadlocks, disconnected sub-graphs, and multi-component deadlocks.
* **Invariant Defense (`tests/test_validation.py`)**: Verifies that dimension mismatches, negative allocations, and conservation violations are rejected.
* **Recovery Logic (`tests/test_recovery.py`)**: Verifies victim selection rankings and rollback integrity.

---

## 11. Project Documentation Links

* [**`PROCEDURE.md`**](PROCEDURE.md): Complete engineering procedure to recreate this project from scratch.
* [**`FILE_PURPOSE.md`**](FILE_PURPOSE.md): Comprehensive directory explaining every file, class, and method in the codebase.
* [**`docs/REPORT.md`**](docs/REPORT.md): Academic design report detailing theoretical foundations.
* [**`docs/VIVA.md`**](docs/VIVA.md): Oral examination (Viva Voce) questions and detailed answers.
* [**`docs/DEMO.md`**](docs/DEMO.md): Guided demonstration script for presentations and evaluations.

---

## License
This project is open-source and licensed under the [MIT License](LICENSE).
