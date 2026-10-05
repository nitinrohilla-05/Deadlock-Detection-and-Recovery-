import argparse
import sys
import csv
from engine.scenario import load_scenario, scenario_to_state
from engine.simulator import Simulator
from engine.recovery import TerminateAll, TerminateOneAtATime, ResourcePreemption

def get_strategy(name: str):
    if name == "terminate_all":
        return TerminateAll()
    elif name == "terminate_one":
        return TerminateOneAtATime()
    elif name == "preemption":
        return ResourcePreemption()
    return None

def run_command(args):
    scenario = load_scenario(args.scenario)
    state = scenario_to_state(scenario)
    
    if not scenario.scripts:
        print("Scenario has no scripts. Cannot simulate.")
        return
        
    strategy = get_strategy(args.strategy)
    sim = Simulator(state, scenario.scripts, recovery_strategy=strategy)
    
    while sim.is_running:
        sim.step()
        
    print(f"Simulation finished at tick {sim.tick}")
    print(f"Deadlocks detected: {sim.metrics.deadlocks_detected}")
    print(f"Victims: {sim.metrics.victims}")
    print(f"Work lost: {sim.metrics.work_lost}")
    print(f"Makespan: {sim.metrics.makespan}")

def compare_command(args):
    scenario = load_scenario(args.scenario)
    
    if not scenario.scripts:
        print("Scenario has no scripts. Cannot simulate.")
        return
        
    strategies = ["terminate_all", "terminate_one", "preemption"]
    results = []
    
    for s_name in strategies:
        state = scenario_to_state(scenario)
        strategy = get_strategy(s_name)
        sim = Simulator(state, scenario.scripts, recovery_strategy=strategy)
        
        while sim.is_running:
            sim.step()
            
        results.append({
            "strategy": s_name,
            "deadlocks": sim.metrics.deadlocks_detected,
            "victims": sim.metrics.victims,
            "work_lost": sim.metrics.work_lost,
            "makespan": sim.metrics.makespan,
            "wait_time": sim.metrics.total_wait_time,
            "completed": sim.metrics.completed_processes,
            "aborted": sim.metrics.aborted_processes
        })
        
    print(f"{'Strategy':<15} | {'Deadlocks':<10} | {'Victims':<8} | {'Work Lost':<10} | {'Makespan':<10} | {'Completed':<10} | {'Aborted':<8}")
    print("-" * 85)
    for r in results:
        print(f"{r['strategy']:<15} | {r['deadlocks']:<10} | {r['victims']:<8} | {r['work_lost']:<10} | {r['makespan']:<10} | {r['completed']:<10} | {r['aborted']:<8}")

    if args.csv:
        with open(args.csv, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=results[0].keys())
            writer.writeheader()
            writer.writerows(results)
        print(f"Exported to {args.csv}")

def main():
    parser = argparse.ArgumentParser(description="Deadlock Detection and Recovery Simulator")
    subparsers = parser.add_subparsers(dest="command", required=True)
    
    run_parser = subparsers.add_parser("run")
    run_parser.add_argument("scenario", help="Path to scenario JSON")
    run_parser.add_argument("--strategy", choices=["terminate_all", "terminate_one", "preemption"], default="terminate_one")
    
    compare_parser = subparsers.add_parser("compare")
    compare_parser.add_argument("scenario", help="Path to scenario JSON")
    compare_parser.add_argument("--csv", help="Export to CSV file")
    
    args = parser.parse_args()
    
    if args.command == "run":
        run_command(args)
    elif args.command == "compare":
        compare_command(args)

if __name__ == "__main__":
    main()
