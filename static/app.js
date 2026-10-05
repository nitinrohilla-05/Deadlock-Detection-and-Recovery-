const API_BASE = '/api';

let currentScenario = null;
let currentMode = 'static';
let simSessionId = null;
let simInterval = null;
let graph = null;

let currentState = null;
let currentMetrics = null;
let deadlockedPids = [];
let cycles = [];

document.addEventListener("DOMContentLoaded", async () => {
    graph = new GraphRenderer('rag-svg');
    
    const modeSelect = document.getElementById('mode-select');
    const scenarioSelect = document.getElementById('scenario-select');
    
    modeSelect.addEventListener('change', (e) => {
        currentMode = e.target.value;
        document.getElementById('sim-controls').style.display = currentMode === 'simulation' ? 'block' : 'none';
        document.getElementById('static-controls').style.display = currentMode === 'static' ? 'block' : 'none';
        if (simInterval) clearInterval(simInterval);
        loadScenario(scenarioSelect.value);
    });
    
    scenarioSelect.addEventListener('change', (e) => {
        loadScenario(e.target.value);
    });
    
    document.getElementById('btn-detect').addEventListener('click', () => {
        if (currentMode === 'static') detectStatic();
    });
    
    document.getElementById('btn-recover-auto').addEventListener('click', () => {
        if (currentMode === 'static') recoverStaticAuto();
    });
    
    document.getElementById('btn-recover-manual').addEventListener('click', () => {
        const victimId = parseInt(document.getElementById('victim-select').value);
        if (currentMode === 'static') recoverStaticManual(victimId);
        else recoverSimManual(victimId);
    });
    
    document.getElementById('btn-start').addEventListener('click', () => {
        startSimulation();
    });
    
    document.getElementById('btn-step').addEventListener('click', () => {
        stepSimulation();
    });
    
    document.getElementById('btn-auto').addEventListener('click', () => {
        if (simInterval) {
            clearInterval(simInterval);
            simInterval = null;
        } else {
            simInterval = setInterval(stepSimulation, 1000);
        }
    });
    
    // Load scenario list
    const res = await fetch(`${API_BASE}/scenarios`);
    const data = await res.json();
    data.scenarios.forEach(s => {
        const opt = document.createElement('option');
        opt.value = s;
        opt.textContent = s;
        scenarioSelect.appendChild(opt);
    });
    
    if (data.scenarios.length > 0) {
        loadScenario(data.scenarios[0]);
    }
});

async function loadScenario(name) {
    const res = await fetch(`${API_BASE}/scenarios/${name}`);
    currentScenario = await res.json();
    
    if (currentMode === 'static') {
        currentState = {
            processes: currentScenario.processes,
            resources: Object.keys(currentScenario.resources).map(k => ({name: k, total: currentScenario.resources[k]})),
            allocation: currentScenario.allocation || currentScenario.processes.map(() => Object.keys(currentScenario.resources).map(()=>0)),
            request: currentScenario.request || currentScenario.processes.map(() => Object.keys(currentScenario.resources).map(()=>0)),
            available: currentScenario.available || Object.values(currentScenario.resources)
        };
        deadlockedPids = [];
        cycles = [];
        updateUI();
    }
}

function updateUI() {
    renderTables();
    graph.render(currentState, false, deadlockedPids, cycles);
    
    const banner = document.getElementById('status-banner');
    if (deadlockedPids.length > 0) {
        banner.className = 'banner deadlock';
        banner.textContent = `DEADLOCK DETECTED among PIDs: ${deadlockedPids.join(', ')}`;
        
        // Update manual victim select
        const vs = document.getElementById('victim-select');
        vs.innerHTML = '';
        deadlockedPids.forEach(pid => {
            const opt = document.createElement('option');
            opt.value = pid;
            const p = currentState.processes.find(x => x.id === pid);
            opt.textContent = p ? p.name : `P${pid}`;
            vs.appendChild(opt);
        });
        document.getElementById('btn-recover-manual').disabled = false;
    } else {
        banner.className = 'banner safe';
        banner.textContent = 'SAFE';
        document.getElementById('btn-recover-manual').disabled = true;
    }
    
    if (currentMetrics) {
        document.getElementById('metrics-panel').innerHTML = `
            Tick: ${currentMetrics.tick || 0}<br>
            Deadlocks: ${currentMetrics.metrics.deadlocks_detected}<br>
            Victims: ${currentMetrics.metrics.victims}<br>
            Work Lost: ${currentMetrics.metrics.work_lost}<br>
            Completed: ${currentMetrics.metrics.completed_processes}<br>
            Aborted: ${currentMetrics.metrics.aborted_processes}
        `;
    }
}

function renderTables() {
    const renderMatrix = (id, matrix) => {
        const table = document.getElementById(id);
        table.innerHTML = '';
        
        // Header
        const trH = document.createElement('tr');
        trH.appendChild(document.createElement('th'));
        currentState.resources.forEach(r => {
            const th = document.createElement('th');
            th.textContent = r.name;
            trH.appendChild(th);
        });
        table.appendChild(trH);
        
        currentState.processes.forEach((p, i) => {
            const tr = document.createElement('tr');
            const tdP = document.createElement('td');
            tdP.textContent = p.name;
            tr.appendChild(tdP);
            
            currentState.resources.forEach((r, j) => {
                const td = document.createElement('td');
                td.textContent = matrix[i][j];
                tr.appendChild(td);
            });
            table.appendChild(tr);
        });
    };
    
    renderMatrix('alloc-table', currentState.allocation);
    renderMatrix('req-table', currentState.request);
    
    // Available
    const tableA = document.getElementById('avail-table');
    tableA.innerHTML = '';
    const trH = document.createElement('tr');
    currentState.resources.forEach(r => {
        const th = document.createElement('th');
        th.textContent = r.name;
        trH.appendChild(th);
    });
    tableA.appendChild(trH);
    
    const trA = document.createElement('tr');
    currentState.available.forEach(a => {
        const td = document.createElement('td');
        td.textContent = a;
        trA.appendChild(td);
    });
    tableA.appendChild(trA);
}

function appendLog(tick, type, message) {
    const logBox = document.getElementById('event-log');
    const div = document.createElement('div');
    div.textContent = `[Tick ${tick}] ${type}: ${message}`;
    logBox.appendChild(div);
    logBox.scrollTop = logBox.scrollHeight;
}

// Static Actions
async function detectStatic() {
    const payload = {
        resources: currentScenario.resources,
        processes: currentState.processes,
        allocation: currentState.allocation,
        request: currentState.request,
        available: currentState.available
    };
    
    const res = await fetch(`${API_BASE}/detect`, {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify(payload)
    });
    const data = await res.json();
    
    deadlockedPids = data.deadlocked_pids;
    cycles = data.cycles;
    
    if (data.cycle_without_deadlock) {
        alert("Cycle found, but NO deadlock: other processes can still release instances");
    }
    updateUI();
}

async function recoverStaticAuto() {
    const payload = {
        resources: currentScenario.resources,
        processes: currentState.processes,
        allocation: currentState.allocation,
        request: currentState.request,
        available: currentState.available
    };
    
    const res = await fetch(`${API_BASE}/recover`, {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify(payload)
    });
    const data = await res.json();
    
    if (data.is_resolved) {
        currentState.allocation = data.state.allocation;
        currentState.request = data.state.request;
        currentState.available = data.state.available;
        deadlockedPids = [];
        cycles = [];
        updateUI();
        alert(`Recovered. Actions taken: ${data.actions.map(a => a.type + " " + a.pid).join(', ')}`);
    } else {
        alert("Recovery failed or not deadlocked.");
    }
}

async function recoverStaticManual(victimId) {
    // In static mode, manual recovery is just aborting the victim locally.
    const idx = currentState.processes.findIndex(p => p.id === victimId);
    if (idx >= 0) {
        for (let r = 0; r < currentState.resources.length; r++) {
            currentState.available[r] += currentState.allocation[idx][r];
            currentState.allocation[idx][r] = 0;
            currentState.request[idx][r] = 0;
        }
        detectStatic(); // re-detect
    }
}

// Sim Actions
async function startSimulation() {
    const scenarioName = document.getElementById('scenario-select').value;
    const strategy = document.getElementById('strategy-select').value;
    
    const res = await fetch(`${API_BASE}/simulate/start`, {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({
            scenario: scenarioName,
            strategy: strategy
        })
    });
    const data = await res.json();
    if (data.session_id) {
        simSessionId = data.session_id;
        document.getElementById('btn-step').disabled = false;
        document.getElementById('btn-auto').disabled = false;
        document.getElementById('event-log').innerHTML = '';
        fetchSimStatus();
    } else {
        alert("Error starting simulation");
    }
}

async function fetchSimStatus() {
    if (!simSessionId) return;
    const res = await fetch(`${API_BASE}/simulate/status/${simSessionId}`);
    const data = await res.json();
    applySimData(data);
}

async function stepSimulation() {
    if (!simSessionId) return;
    const res = await fetch(`${API_BASE}/simulate/step/${simSessionId}`, { method: 'POST' });
    const data = await res.json();
    applySimData(data);
}

async function recoverSimManual(victimId) {
    if (!simSessionId) return;
    const strategy = document.getElementById('strategy-select').value;
    const res = await fetch(`${API_BASE}/simulate/manual_recover/${simSessionId}`, {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({victim_id: victimId, strategy: strategy})
    });
    const data = await res.json();
    applySimData(data);
}

function applySimData(data) {
    currentState = data.state;
    currentMetrics = data;
    deadlockedPids = data.deadlocked_pids;
    cycles = []; // Simulator API doesn't return cycles currently, but deadlocked nodes highlight
    
    document.getElementById('event-log').innerHTML = '';
    data.logs.forEach(l => appendLog(l.tick, l.type, l.message));
    
    updateUI();
    
    if (!data.is_running) {
        if (simInterval) { clearInterval(simInterval); simInterval = null; }
        document.getElementById('btn-step').disabled = true;
        document.getElementById('btn-auto').disabled = true;
        alert("Simulation ended.");
    }
}
