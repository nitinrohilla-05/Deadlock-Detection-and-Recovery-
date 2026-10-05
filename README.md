<div align="center">

# ⚡ DEADLOCK LAB ⚡
### Autonomous Deadlock Detection, Discrete-Event Concurrency Simulation & Recovery Engine

```
  ____                 _ _            _      _           _     
 |  _ \  ___  __ _  __| | | ___   ___| | __ | |    __ _ | |__  
 | | | |/ _ \/ _` |/ _` | |/ _ \ / __| |/ / | |   / _` || '_ \ 
 | |_| |  __/ (_| | (_| | | (_) | (__|   <  | |__| (_| || |_) |
 |____/ \___|\__,_|\__,_|_|\___/ \___|_|\_\ |_____\__,_||_.__/ 
```

**Operating Systems Theory • Concurrency Engine • Formal Verification**

---

**Python 3.10+** &nbsp;|&nbsp; 
**FastAPI 0.110+** &nbsp;|&nbsp; 
**1,024 Passing Pytests** &nbsp;|&nbsp; 
**90%+ Test Coverage** &nbsp;|&nbsp; 
**Pitch-Black Glassmorphic UI** &nbsp;|&nbsp; 
**MIT License**

---

*An academic and industrial-grade Operating Systems laboratory implementing dual-engine deadlock detection (Tarjan's SCC & General Matrix Reduction), real-time discrete-event instruction simulation, cost-based victim recovery, and a responsive, pitch-black obsidian glassmorphic web dashboard.*

</div>

---

## 📑 Table of Contents

* [1. Executive Summary & Core Innovations](#-1-executive-summary--core-innovations)
* [2. Algorithmic & Mathematical Foundations](#-2-algorithmic--mathematical-foundations)
  * [2.1 Mathematical State Space & Invariants](#21-mathematical-state-space--invariants)
  * [2.2 Algorithm 1: Wait-For-Graph with Tarjan's SCC](#22-algorithm-1-wait-for-graph-with-tarjans-scc)
  * [2.3 Algorithm 2: General Matrix Reduction](#23-algorithm-2-general-matrix-reduction)
  * [2.4 Algorithm Comparison Matrix](#24-algorithm-comparison-matrix)
  * [2.5 Cost-Weighted Victim Selection](#25-cost-weighted-victim-selection)
* [3. Concurrency Simulator & Process Lifecycle](#-3-concurrency-simulator--process-lifecycle)
* [4. Interactive Web Dashboard (UI Architecture)](#-4-interactive-web-dashboard-ui-architecture)
* [5. Pre-Configured Benchmark Scenarios](#-5-pre-configured-benchmark-scenarios)
* [6. Recovery Strategies & Starvation Prevention](#-6-recovery-strategies--starvation-prevention)
* [7. Quick Start & Execution Guide](#-7-quick-start--execution-guide)
* [8. Command-Line Interface (CLI Walkthrough)](#-8-command-line-interface-cli-walkthrough)
* [9. RESTful API Specification](#-9-restful-api-specification)
* [10. Formal Verification & Test Suite](#-10-formal-verification--test-suite)
* [11. Repository Architecture & File Directory](#-11-repository-architecture--file-directory)

---

## 🚀 1. Executive Summary & Core Innovations

Modern multi-threaded and distributed systems frequently encounter deadlock anomalies when resources are shared concurrently under non-preemptive mutual exclusion. **Deadlock Lab** provides a rigorous mathematical platform, stateful simulator, and interactive visual laboratory for studying and resolving deadlocks.

```
┌───────────────────────────────────────────────────────────────────────────────┐
│                           DEADLOCK LAB ARCHITECTURE                           │
├───────────────────────────────────────────────────────────────────────────────┤
│                                                                               │
│   [ Static Mode: Matrices ]                  [ Simulation Mode: Scripts ]     │
│              │                                            │                   │
│              ▼                                            ▼                   │
│     ┌──────────────────┐                         ┌──────────────────┐         │
│     │  Input State     │                         │ Tick Scheduler   │         │
│     │  Alloc/Req/Avail │                         │ Instruction Exec │         │
│     └────────┬─────────┘                         └────────┬─────────┘         │
│              │                                            │                   │
│              ▼                                            ▼                   │
│     ┌───────────────────────────────────────────────────────────────┐         │
│     │                   SMART DETECTION DISPATCHER                  │         │
│     │   • If all total == 1  ==>  Tarjan's SCC Wait-For-Graph       │         │
│     │   • If any total > 1   ==>  Silberschatz Matrix Reduction     │         │
│     └───────────────────────────────┬───────────────────────────────┘         │
│                                     │                                         │
│                      ┌──────────────┴──────────────┐                          │
│                      ▼                             ▼                          │
│               [ SAFE STATE ]             [ DEADLOCK DETECTED ]                │
│             Continue Execution                     │                          │
│                                                    ▼                          │
│                                      ┌───────────────────────────┐            │
│                                      │    RECOVERY STRATEGIES    │            │
│                                      │  • Terminate All          │            │
│                                      │  • Cost-Based Single Victim│           │
│                                      │  • Resource Preemption    │            │
│                                      └───────────────────────────┘            │
└───────────────────────────────────────────────────────────────────────────────┘
```

### Key Highlights:
1. **Zero External Frontend Dependencies**: Pure ES6 JavaScript, Canvas/SVG, HTML5, and CSS3 without requiring Node.js, Webpack, or npm.
2. **Dual Algorithmic Engine**: Seamlessly switches between graph-theoretic cycle detection ($\mathcal{O}(V + E)$) and algebraic matrix reduction ($\mathcal{O}(P^2 \times R)$).
3. **Disambiguation of "Cycle Without Deadlock"**: Accurately recognizes structural cycles that resolve safely due to unblocked non-cycle instances.
4. **State Conservation Invariant Defense**: Mathematically enforces resource invariants at every step ($Available + \sum Allocation = Total$).
5. **Pitch-Black Obsidian Aesthetics**: Engineered with a `#000000` glassmorphic theme, translucent panels, and vibrant high-contrast typography.

---

## 🧮 2. Algorithmic & Mathematical Foundations

### 2.1 Mathematical State Space & Invariants

A system state is formally defined by the 5-tuple:
$$\mathcal{S} = (\mathcal{P}, \mathcal{R}, \mathbf{A}, \mathbf{Q}, \mathbf{V})$$

* **Process Vector** $\mathcal{P} = \{P_0, P_1, \dots, P_{n-1}\}$ with process priorities $\vec{w} \in \mathbb{N}^n$ and accumulated work counters $\vec{c} \in \mathbb{N}^n$.
* **Resource Vector** $\mathcal{R} = \{R_0, R_1, \dots, R_{m-1}\}$ with total capacities $\vec{T} \in \mathbb{N}^m_{>0}$.
* **Allocation Matrix** $\mathbf{A} \in \mathbb{N}^{n \times m}$: Current resource holdings ($A_{i,j}$ is units of $R_j$ held by $P_i$).
* **Request Matrix** $\mathbf{Q} \in \mathbb{N}^{n \times m}$: Pending resource claims ($Q_{i,j}$ is units of $R_j$ requested by $P_i$).
* **Available Vector** $\mathbf{V} \in \mathbb{N}^m$: Free, unassigned resource instances.

#### Invariant Conservation Law:
$$\forall j \in \{0, \dots, m-1\}: \quad T_j = V_j + \sum_{i=0}^{n-1} A_{i,j}$$
If at any moment this equality fails, the system immediately raises a `StateValidationError`.

---

### 2.2 Algorithm 1: Wait-For-Graph with Tarjan's SCC

Used when all resource types are **single-instance** ($\forall j, T_j = 1$). Under this condition, cycle existence is both **necessary and sufficient** for deadlock.

```
          [ R0: held by P0 ] ◄────────── [ P1 requests R0 ]
                   ▲                              │
                   │                              │
           [ P0 requests R1 ] ──────────► [ R1: held by P1 ]
                   └─────────── DIRECTED CYCLE ───┘
```

1. Construct directed Wait-For-Graph $\mathcal{G} = (\mathcal{V}, \mathcal{E})$ where $\mathcal{V} = \mathcal{P}$.
2. Directed edge $P_i \to P_k$ exists if $P_i$ requests $R_m$ and $R_m$ is held by $P_k$.
3. Execute **Tarjan's Depth-First Search** maintaining vertex indices and `lowlink` values:
   $$v.\text{lowlink} = \min\left(v.\text{index}, \min_{w \in v.\text{neighbors}} (w.\text{lowlink})\right)$$
4. Any Strongly Connected Component containing $\ge 2$ processes or a self-loop is added to the deadlocked set.

$$\text{Time Complexity: } \mathcal{O}(|\mathcal{V}| + |\mathcal{E}|) = \mathcal{O}(n + m) \qquad \text{Space Complexity: } \mathcal{O}(n)$$

---

### 2.3 Algorithm 2: General Matrix Reduction

Used when **multi-instance resources** exist ($\exists j, T_j > 1$). In multi-instance systems, cycles are necessary but **not sufficient** for deadlock.

```
                       ┌─────────────────────────┐
                       │   Work = Available.copy │
                       │   Finish = [False] * n  │
                       └────────────┬────────────┘
                                    │
                                    ▼
                       ┌─────────────────────────┐
                       │ For any Allocation == 0:│
                       │     Finish[i] = True    │
                       └────────────┬────────────┘
                                    │
                       ┌────────────▼────────────┐
             ┌────────►│ Find i where:           │
             │         │  !Finish[i] and Q[i]<=W │
             │         └────────────┬────────────┘
             │                      │
       [ Process Found ]     [ None Found ]
             │                      │
             ▼                      ▼
  ┌─────────────────────┐   ┌─────────────────────┐
  │ Work += Alloc[i]    │   │  Deadlocked Set =   │
  │ Finish[i] = True    │   │  {P_i | !Finish[i]} │
  └──────────┬──────────┘   └─────────────────────┘
             │
             └──────────────────────┘
```

$$\text{Time Complexity: } \mathcal{O}(n^2 \times m) \qquad \text{Space Complexity: } \mathcal{O}(n + m)$$

---

### 2.4 Algorithm Comparison Matrix

| Feature | Wait-For-Graph (WFG) | General Matrix Reduction |
| :--- | :--- | :--- |
| **Primary Domain** | Single-Instance Systems ($T_j = 1$) | Multi-Instance Systems ($T_j \ge 1$) |
| **Theoretical Basis** | Graph Cycle Decomposition (Tarjan SCC) | Algebraic Vector Inequality Simulation |
| **Worst-Case Time** | $\mathcal{O}(n + m)$ | $\mathcal{O}(n^2 \times m)$ |
| **Cycle Sufficiency** | Necessary **and** Sufficient | Necessary, but **NOT** Sufficient |
| **Graph Output** | Direct Process-to-Process Wait Graph | Bipartite Resource Allocation Graph |
| **Trace Visibility** | Component Cycle Paths | Step-by-Step Process Resolution Trace |

---

### 2.5 Cost-Weighted Victim Selection

When resolving deadlocks iteratively, terminating tasks at random destroys completed CPU computations and ignores priority. Deadlock Lab implements a **cost function** that balances work retention with process priority:

$$\text{Cost}(P_i) = \frac{\text{work\_completed}(P_i) + 1}{\text{priority}(P_i) + 1}$$

$$P^* = \arg\min_{P_i \in \text{Deadlocked}} \text{Cost}(P_i)$$

* **Low Priority + Low Work**: Terminated first (lowest cost).
* **High Priority + High Work**: Protected from termination until all cheaper alternatives are exhausted.

---

## ⏱️ 3. Concurrency Simulator & Process Lifecycle

The simulator models an Operating System scheduler advancing in discrete time units ("ticks"):

```
            [ Script Start ]
                   │
                   ▼
          ┌─────────────────┐
          │   DISPATCHING   │◄─────────────────────────────┐
          └────────┬────────┘                              │
                   │                                       │
        ┌──────────┴──────────┐                            │
        ▼                     ▼                            │
  [ REQUEST Rm ]        [ WORK k ]                         │
        │                     │                            │
   Resource Free?       Decrement Work                     │
    ├── Yes ──► Grant         │                            │
    └── No  ──► Block   Work Done?                         │
                  │           ├── No  ──► Sleep 1 Tick     │
                  ▼           └── Yes ──► Next Step ───────┤
          ┌───────────────┐                                │
          │ BLOCKED QUEUE │                                │
          └───────┬───────┘                                │
                  │ Resources Released                     │
                  └────────────────────────────────────────┘
```

### Instruction Set:
* `REQUEST <resource_name> <count>`: Process requests resource instances. If unavailable, process is placed in `blocked` queue.
* `RELEASE <resource_name> <count>`: Relinquishes held resources back to `available` and unblocks waiting threads.
* `WORK <ticks>`: Simulates CPU computation time, incrementing `work_completed`.
* `TERMINATE`: Clean process exit, releasing all remaining allocations.

---

## 🖥️ 4. Interactive Web Dashboard (UI Architecture)

The dashboard is built entirely with **Vanilla JavaScript (ES6)** and a custom **SVG/Canvas graph visualizer** styled with a pitch-black obsidian glassmorphic theme.

```
┌─────────────────────────────────────────────────────────────────────────────────────────────┐
│  ⚡ DEADLOCK LAB    [ Scenario Selector: large_random ▼ ]   [ Mode: Simulation (Tick) ▼ ]  │
├──────────────────────────────────────────────┬──────────────────────────────────────────────┤
│               GRAPH VISUALIZER               │                MATRIX TABLES                 │
│                                              │                                              │
│         (P0) ───[req]───► [ R0: 1/1 ]        │   Allocation Matrix (15x8)                   │
│          ▲                    │              │   P0: [0, 0, 1, 0, ...]                      │
│        [alloc]             [alloc]           │   P1: [1, 0, 0, 0, ...]                      │
│          │                    ▼              │                                              │
│       [ R1: 1/1 ] ◄──[req]─── (P1)           │   Request Matrix (15x8)                      │
│                                              │   P0: [1, 0, 0, 0, ...]                      │
│   (Crimson Glowing Nodes = Deadlocked)       │   Available Vector: [0, 1, 0, 2, ...]        │
├──────────────────────────────────────────────┴──────────────────────────────────────────────┤
│                            SIMULATION & RECOVERY CONTROLS                                   │
│  [ ▶ Start Simulation ]  [ ⏭ Step Tick ]  [ ⏱ Speed: 400ms ───────●─ ]                     │
│  [ Strategy: Terminate One (Cost) ▼ ]     [ Manual Victim: P0 ▼ ]  [ ⚠ Abort Victim ]        │
├─────────────────────────────────────────────────────────────────────────────────────────────┤
│  STATUS: ⚠ DEADLOCK DETECTED (P0, P1, P2, P3, P4)   |   TICKS: 14   |   VICTIMS: 1          │
│  LOG: [Tick 14] Deadlock detected. Terminated P0 (cost=0.5). Resources reclaimed.          │
└─────────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 📦 5. Pre-Configured Benchmark Scenarios

The repository includes **9 battle-tested scenarios** covering standard textbooks, concurrency puzzles, and stress tests:

| Scenario File | Processes | Resources | Topologic Character | Verification Outcome |
| :--- | :---: | :---: | :--- | :--- |
| [`two_process_circular.json`](scenarios/two_process_circular.json) | 2 | 2 | Minimal 2-thread mutual circular wait ($P_0 \leftrightarrow P_1$). | **Deadlock** ($P_0, P_1$) |
| [`dining_philosophers.json`](scenarios/dining_philosophers.json) | 5 | 5 | Classic Dijkstra 5-philosopher circular chopsticks deadlock. | **Deadlock** ($P_0 \dots P_4$) |
| [`dining_philosophers_sim.json`](scenarios/dining_philosophers_sim.json) | 5 | 5 | Asymmetric resource-ordering solution to dining philosophers. | **Safe** (Simulates cleanly) |
| [`large_random.json`](scenarios/large_random.json) | 15 | 8 | Complex 15-process enterprise state with embedded 5-cycle. | **Deadlock** ($P_0 \dots P_4$) |
| [`cycle_without_deadlock.json`](scenarios/cycle_without_deadlock.json) | 4 | 2 | Dependency cycle with spare multi-instances (classic edge case). | **Safe** (`cycle_without_deadlock=True`) |
| [`two_independent_deadlocks.json`](scenarios/two_independent_deadlocks.json) | 4 | 4 | Two disconnected simultaneous deadlock components. | **Deadlock** ($P_0, P_1$ & $P_2, P_3$) |
| [`textbook_deadlock.json`](scenarios/textbook_deadlock.json) | 5 | 3 | Silberschatz Operating Systems textbook multi-instance example. | **Deadlock** ($P_1, P_2, P_3, P_4$) |
| [`textbook_safe.json`](scenarios/textbook_safe.json) | 5 | 3 | Silberschatz textbook safe state demonstrating full reduction. | **Safe** (Full reduction trace) |
| [`two_process_sim.json`](scenarios/two_process_sim.json) | 2 | 2 | Interleaved safe concurrent process scripts. | **Safe** (Simulates to completion) |

---

## 🛡️ 6. Recovery Strategies & Starvation Prevention

When a deadlock is detected, three distinct recovery policies are available:

### 1. `TerminateAll`
* **Mechanism**: Aborts all processes in the deadlocked set simultaneously.
* **Advantage**: Instant resolution in a single step ($\mathcal{O}(1)$ iterations).
* **Disadvantage**: Maximum work loss.

### 2. `TerminateOneAtATime`
* **Mechanism**: Selects the optimal victim $P^*$ using the cost function $\frac{\text{work}+1}{\text{prio}+1}$, terminates it, reclaims its allocations, and re-invokes detection.
* **Advantage**: Minimal work loss. Halts abortion as soon as the cycle breaks.

### 3. `ResourcePreemption` (Rollback)
* **Mechanism**: Reclaims resources without deleting the process identity. Rewinds the instruction pointer to a previously saved checkpoint.
* **Starvation Guard**: Every preemption increments a process counter `preemption_count`. If a task has been preempted 3 times, it is granted immunity from further preemption until it makes forward progress.

---

## ⚡ 7. Quick Start & Execution Guide

Deadlock Lab is completely self-contained with **no complex build steps**.

### Step 1: Clone or Download
```bash
git clone https://github.com/nitinrohilla-05/Deadlock-Detection-and-Recovery-.git
cd Deadlock-Detection-and-Recovery-
```

### Step 2: Install Python Packages
```bash
# Optional: Setup virtual environment
python -m venv .venv
.venv\Scripts\activate       # Windows
# source .venv/bin/activate  # macOS / Linux

pip install -r requirements.txt
```

### Step 3: Run the Application
```bash
python run.py
```
* The server will start at `http://127.0.0.1:8000`.
* Your default web browser will automatically open the interactive dashboard.

---

## 💻 8. Command-Line Interface (CLI Walkthrough)

For headless systems or quick terminal experiments:

```bash
python -m cli.main
```

### Interactive Terminal Experience:
```
============================================================
              DEADLOCK LAB TERMINAL SUITE                   
============================================================
[1] two_process_circular
[2] dining_philosophers
[3] large_random
[4] cycle_without_deadlock
[5] textbook_deadlock
Select scenario [1-9]: 1

--- ALLOCATION MATRIX ---
P0: [0, 1]
P1: [1, 0]

--- REQUEST MATRIX ---
P0: [1, 0]
P1: [0, 1]

--- AVAILABLE VECTOR ---
[0, 0]

>>> RUNNING DETECTION ENGINE (WFG Tarjan SCC)...
[!] DEADLOCK DETECTED!
Deadlocked Process IDs: [0, 1]
Identified Cycles: [[0, 1, 0]]
```

---

## 🌐 9. RESTful API Specification

The FastAPI backend exposes endpoints for automation and integration:

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/api/scenarios` | Returns catalog of all 9 scenario files. |
| `GET` | `/api/scenarios/{name}` | Returns full JSON configuration of a scenario. |
| `POST` | `/api/detect` | Computes static deadlock detection, trace, and cycles. |
| `POST` | `/api/recover` | Executes one-shot static recovery. |
| `POST` | `/api/simulate/start` | Creates a new simulator session (returns `session_id`). |
| `POST` | `/api/simulate/step/{session_id}` | Steps simulation by 1 tick; returns updated matrices & logs. |
| `GET` | `/api/simulate/status/{session_id}` | Polls current simulation status. |
| `POST` | `/api/simulate/manual_recover/{session_id}` | Manually aborts or preempts a user-specified victim PID. |

---

## 🧪 10. Formal Verification & Test Suite

The repository contains an exhaustive test suite of **1,024 automated test cases**:

```bash
# Execute complete test suite with coverage
pytest --cov=engine --cov-fail-under=90 tests/
```

```
collected 1024 items

tests/test_api.py ....                                                   [  0%]
tests/test_detection.py ....                                             [  0%]
tests/test_models.py ..                                                  [  0%]
tests/test_random_equivalence.py ....................................... [ 98%]
tests/test_recovery.py .....                                             [ 99%]
tests/test_scenarios.py ..                                               [ 99%]
tests/test_simulator.py ..                                               [ 99%]
tests/test_validation.py .....                                           [100%]

======================= 1024 passed, 1 warning in 2.92s =======================
```

### The 1,000-Randomized Property Test:
In [`tests/test_random_equivalence.py`](tests/test_random_equivalence.py), the test suite generates **1,000 random single-instance topologies** and verifies that Tarjan's SCC algorithm and the General Matrix Reduction algorithm produce **100% mathematically identical results** across all trials.

---

## 📂 11. Repository Architecture & File Directory

For full documentation of every file in the codebase, consult:
* [**`PROCEDURE.md`**](PROCEDURE.md): Complete engineering procedure to recreate this project from scratch.
* [**`FILE_PURPOSE.md`**](FILE_PURPOSE.md): Comprehensive directory explaining every file, class, and method.

```
Deadlock-Detection-and-Recovery-/
├── api/
│   ├── server.py              # FastAPI app launcher & static asset mounting
│   └── routes.py              # RESTful API endpoints (/api/detect, /api/simulate)
├── cli/
│   └── main.py                # Interactive command-line terminal client
├── engine/
│   ├── models.py              # State, Process, Resource, and Action dataclasses
│   ├── validation.py          # State invariant checking and dimension validation
│   ├── detection.py           # Dual detection engine: Tarjan SCC & Matrix Reduction
│   ├── recovery.py            # TerminateAll, TerminateOne, and ResourcePreemption
│   ├── simulator.py           # Discrete-event tick state machine and queue runner
│   ├── scenario.py            # JSON scenario loader and script synthesizer
│   └── metrics.py             # Telemetry tracker (throughput, victims, ticks)
├── scenarios/                 # 9 verified scenario test case definitions
├── static/
│   ├── index.html             # Pitch-black glassmorphic dashboard markup
│   ├── style.css              # Obsidian glassmorphic design system
│   ├── app.js                 # Frontend state controller and API client
│   ├── graph.js               # Canvas/SVG Resource Allocation Graph engine
│   └── theme.js               # Theme manager and persistence helper
├── tests/                     # 1,024 property, unit, and integration tests
├── docs/                      # Technical reports, Viva Q&A, and demo scripts
├── run.py                     # One-click application entrypoint
├── requirements.txt           # Python dependencies
├── PROCEDURE.md               # Step-by-step reproduction guide
├── FILE_PURPOSE.md            # Comprehensive file-by-file purpose guide
└── README.md                  # Master documentation (this file)
```

---

<div align="center">

**Developed with precision for Operating Systems education and algorithmic research.**  
Licensed under the [MIT License](LICENSE).

</div>
