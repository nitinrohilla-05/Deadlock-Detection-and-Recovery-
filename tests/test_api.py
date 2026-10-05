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
