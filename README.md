# Deadlock Lab

A comprehensive Deadlock Detection and Recovery Simulator for Operating Systems, featuring both Matrix and Wait-For-Graph (WFG) algorithms, advanced recovery strategies, and an interactive Web UI.

## Features
- **Dual Detection Engine**: Automatically uses WFG (Tarjan SCC) for single-instance resources and the general Matrix algorithm for multi-instance resources.
- **Tick-Based Simulation**: Step-by-step simulator to observe state transitions over time.
- **Recovery Strategies**: `TerminateAll`, `TerminateOneAtATime` (cost-based victim selection), and `ResourcePreemption`.
- **Interactive UI**: View graphs, matrices, and control simulation states interactively.

## Requirements
- OS: Windows, Linux, macOS
- Python 3.11+

## Quick Start (Run from scratch)

```bash
# 1. Create a virtual environment
python -m venv .venv

# 2. Activate the virtual environment
# Windows:
.venv\Scripts\activate
# Linux/Mac:
source .venv/bin/activate

# 3. Install requirements
pip install -r requirements.txt

# 4. Run the Web UI
python run.py
```
This will open the Deadlock Lab dashboard in your default browser at `http://127.0.0.1:8000`.

## CLI Usage

You can also run experiments directly from the command line:

```bash
python -m cli.main
```

## Running Tests

To verify the logic and coverage:
```bash
pytest --cov=engine --cov-fail-under=90 tests/
```

## Documentation
- [Design Report](docs/REPORT.md)
- [Viva Q&A](docs/VIVA.md)
- [Demo Script](docs/DEMO.md)

## Screenshots
![Cycle without deadlock](docs/screenshots/cycle_no_deadlock.png)
![Deadlock Detected](docs/screenshots/deadlock_detected.png)
![Recovered](docs/screenshots/recovered.png)
