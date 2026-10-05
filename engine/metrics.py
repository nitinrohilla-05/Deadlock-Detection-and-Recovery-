from dataclasses import dataclass

@dataclass
class SimulationMetrics:
    deadlocks_detected: int = 0
    detection_runs: int = 0
    detection_time_ms: float = 0.0
    victims: int = 0
    work_lost: int = 0
    total_wait_time: int = 0
    makespan: int = 0
    starved_processes: int = 0
    completed_processes: int = 0
    aborted_processes: int = 0
