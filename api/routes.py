import os
import json
import uuid
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, Any
from engine.scenario import load_scenario, scenario_to_state, Scenario
from engine.simulator import Simulator
from engine.detection import detect_deadlock
from engine.recovery import TerminateAll, TerminateOneAtATime, ResourcePreemption
from engine.models import SystemState, Process, ResourceType

router = APIRouter()

class StatePayload(BaseModel):
    resources: dict[str, int]
    processes: list[dict]
    allocation: list[list[int]]
    request: list[list[int]]
    available: list[int]

class SimulateStartPayload(BaseModel):
    scenario: str
    strategy: str = "none" # none, terminate_all, terminate_one, preemption
    trigger_config: dict = {"type": "blocked"}

class ManualRecoverPayload(BaseModel):
    victim_id: int
    strategy: str = "terminate_one"

# In-memory session storage for simulations
sessions: dict[str, Simulator] = {}

def get_strategy(name: str):
    if name == "terminate_all": return TerminateAll()
    if name == "terminate_one": return TerminateOneAtATime()
    if name == "preemption": return ResourcePreemption()
    return None

def state_from_payload(payload: StatePayload) -> SystemState:
    state = SystemState()
    for p in payload.processes:
        state.add_process(Process(id=p["id"], name=p["name"], priority=p.get("priority", 0)))
    for r_name, total in payload.resources.items():
        state.add_resource(ResourceType(name=r_name, total=total))
    state.available = payload.available
    state.allocation = payload.allocation
    state.request = payload.request
    return state

@router.get("/scenarios")
def list_scenarios():
    files = [f for f in os.listdir("scenarios") if f.endswith(".json")]
    return {"scenarios": [f.replace(".json", "") for f in files]}

@router.get("/scenarios/{name}")
def get_scenario(name: str):
    try:
        sc = load_scenario(f"scenarios/{name}.json")
        return sc
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.post("/detect")
def detect_static(payload: StatePayload):
    state = state_from_payload(payload)
    result = detect_deadlock(state)
    return {
        "is_deadlocked": result.is_deadlocked,
        "deadlocked_pids": list(result.deadlocked_pids),
        "cycles": result.cycles,
        "cycle_without_deadlock": result.cycle_without_deadlock,
        "trace": [
            {"step": t.step, "work": t.work_vector, "process_finished": t.process_finished} 
            for t in result.trace
        ]
    }

@router.post("/recover")
def recover_static(payload: StatePayload, strategy: str = "terminate_one"):
    state = state_from_payload(payload)
    det = detect_deadlock(state)
    if not det.is_deadlocked:
        return {"message": "Not deadlocked", "state": payload.model_dump()}
        
    strat = get_strategy(strategy)
    if not strat:
        strat = TerminateOneAtATime()
        
    res = strat.recover(state, det.deadlocked_pids)
    
    return {
        "is_resolved": res.is_resolved,
        "actions": [{"type": a.action_type, "pid": a.process_id} for a in res.actions],
        "state": {
            "resources": payload.resources,
            "processes": payload.processes,
            "allocation": state.allocation,
            "request": state.request,
            "available": state.available
        }
    }

@router.post("/simulate/start")
def start_simulation(payload: SimulateStartPayload):
    try:
        sc = load_scenario(f"scenarios/{payload.scenario}.json")
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))
        
    state = scenario_to_state(sc)
    if not sc.scripts:
        raise HTTPException(status_code=400, detail="Scenario has no scripts")
        
    strat = get_strategy(payload.strategy)
    sim = Simulator(state, sc.scripts, trigger_config=payload.trigger_config, recovery_strategy=strat)
    
    session_id = str(uuid.uuid4())
    sessions[session_id] = sim
    
    return {"session_id": session_id}

def serialize_sim_status(sim: Simulator):
    return {
        "tick": sim.tick,
        "is_running": sim.is_running,
        "deadlocked_pids": list(sim.deadlocked_pids),
        "completed_pids": list(sim.completed),
        "blocked_pids": list(sim.blocked),
        "metrics": sim.metrics.__dict__,
        "logs": [
            {"tick": l.tick, "type": l.event_type, "message": l.message} 
            for l in sim.logs[-50:] # last 50 logs
        ],
        "state": {
            "available": sim.state.available,
            "allocation": sim.state.allocation,
            "request": sim.state.request,
            "processes": [{"id": p.id, "name": p.name, "priority": p.priority, "work": p.work_completed} for p in sim.state.processes],
            "resources": [{"name": r.name, "total": r.total} for r in sim.state.resources]
        }
    }

@router.post("/simulate/step/{session_id}")
def step_simulation(session_id: str):
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    sim = sessions[session_id]
    sim.step()
    return serialize_sim_status(sim)

@router.get("/simulate/status/{session_id}")
def get_simulation_status(session_id: str):
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    return serialize_sim_status(sessions[session_id])

@router.post("/simulate/manual_recover/{session_id}")
def manual_recover(session_id: str, payload: ManualRecoverPayload):
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    sim = sessions[session_id]
    
    if payload.victim_id not in sim.deadlocked_pids:
        raise HTTPException(status_code=400, detail="Victim is not deadlocked")
        
    strat = get_strategy(payload.strategy) or TerminateOneAtATime()
    # Manually execute abort/rollback on the selected victim
    # Actually strat.recover operates on the whole set, but manual implies we force it on a specific process.
    # So we call abort_process or rollback_process directly based on strategy type
    if isinstance(strat, TerminateAll) or isinstance(strat, TerminateOneAtATime):
        sim.log("MANUAL_ABORT", f"Process P{payload.victim_id} manually aborted.")
        strat.abort_process(sim.state, payload.victim_id)
        # reset script
        sim.active_scripts[payload.victim_id] = __import__('copy').deepcopy(sim.original_scripts[payload.victim_id])
        if payload.victim_id in sim.blocked: sim.blocked.remove(payload.victim_id)
        
    elif isinstance(strat, ResourcePreemption):
        sim.log("MANUAL_ROLLBACK", f"Process P{payload.victim_id} manually preempted.")
        is_partial = strat.rollback_process(sim.state, payload.victim_id)
        if is_partial:
            sim.active_scripts[payload.victim_id] = __import__('copy').deepcopy(sim.script_checkpoints[payload.victim_id])
        else:
            sim.active_scripts[payload.victim_id] = __import__('copy').deepcopy(sim.original_scripts[payload.victim_id])
        if payload.victim_id in sim.blocked: sim.blocked.remove(payload.victim_id)

    # Clear deadlocked state and redetect
    sim.deadlocked_pids.clear()
    sim.run_detection()
    
    return serialize_sim_status(sim)
