from fastapi.testclient import TestClient
from api.server import app

client = TestClient(app)

def test_list_scenarios():
    response = client.get("/api/scenarios")
    assert response.status_code == 200
    data = response.json()
    assert "scenarios" in data
    assert "textbook_safe" in data["scenarios"]

def test_get_scenario():
    response = client.get("/api/scenarios/textbook_safe")
    assert response.status_code == 200
    data = response.json()
    assert "resources" in data
    assert "processes" in data

def test_detect_static():
    sc_res = client.get("/api/scenarios/textbook_deadlock")
    sc = sc_res.json()
    
    payload = {
        "resources": sc["resources"],
        "processes": sc["processes"],
        "allocation": sc["allocation"],
        "request": sc["request"],
        "available": sc["available"]
    }
    
    response = client.post("/api/detect", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["is_deadlocked"] is True
    assert len(data["deadlocked_pids"]) > 0

def test_simulate_start_and_step():
    # Test starting simulation on scenario without explicit scripts (synthesized)
    res1 = client.post("/api/simulate/start", json={"scenario": "cycle_without_deadlock", "strategy": "none"})
    assert res1.status_code == 200
    data1 = res1.json()
    assert "session_id" in data1
    sid1 = data1["session_id"]
    
    # Step simulation
    step_res = client.post(f"/api/simulate/step/{sid1}")
    assert step_res.status_code == 200
    step_data = step_res.json()
    assert step_data["tick"] == 1
    assert "metrics" in step_data
    assert "logs" in step_data

    # Test starting simulation on scenario with explicit scripts
    res2 = client.post("/api/simulate/start", json={"scenario": "two_process_sim", "strategy": "terminate_one"})
    assert res2.status_code == 200
    assert "session_id" in res2.json()

