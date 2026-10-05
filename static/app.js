const API_BASE = '/api';

let currentScenario = null;
let currentMode = 'static';
let simSessionId = null;
let simInterval = null;
let simSpeed = 700;
let graph = null;

let currentState = null;
let currentMetrics = null;
let deadlockedPids = [];
let cycles = [];

document.addEventListener("DOMContentLoaded", async () => {
    graph = new GraphRenderer('rag-svg');
    
    // Resize observer to auto-redraw graph on window resize
    const resizeObserver = new ResizeObserver(() => {
        if(currentState) updateUI();
    });
    const graphContainer = document.getElementById('graph-container');
    if (graphContainer) resizeObserver.observe(graphContainer);
    
    setupTabs();
    setupModals();
    
    const modeSelect = document.getElementById('mode-select');
    const scenarioSelect = document.getElementById('scenario-select');
    
    modeSelect.addEventListener('change', (e) => {
        currentMode = e.target.value;
        
        document.querySelectorAll('.mode-controls').forEach(el => el.classList.remove('active'));
        document.getElementById(currentMode === 'static' ? 'static-controls' : 'sim-controls').classList.add('active');
        
        document.getElementById('mode-help').textContent = currentMode === 'static' 
            ? "Analyze a static snapshot of the system." 
            : "Run a tick-based simulation of processes executing scripts.";
            
        if (simInterval) toggleAutoRun();

        // Switch to Metrics & Logs tab automatically when in simulation mode
        if (currentMode === 'simulation') {
            const metricsTabBtn = document.querySelector('.tab-btn[data-tab="metrics"]');
            if (metricsTabBtn) metricsTabBtn.click();
        } else {
            const matricesTabBtn = document.querySelector('.tab-btn[data-tab="matrices"]');
            if (matricesTabBtn) matricesTabBtn.click();
        }
        
        loadScenario(scenarioSelect.value);
    });
    
    scenarioSelect.addEventListener('change', (e) => {
        if (simInterval) toggleAutoRun();
        loadScenario(e.target.value);
    });
    
    // Bind Static buttons
    document.getElementById('btn-detect').addEventListener('click', detectStatic);
    document.getElementById('btn-recover-auto').addEventListener('click', recoverStaticAuto);
    document.getElementById('btn-recover-manual').addEventListener('click', () => {
        const victimId = parseInt(document.getElementById('victim-select').value);
        if (!isNaN(victimId)) {
            recoverManual(victimId);
        }
    });
    
    // Bind Sidebar Sim buttons
    document.getElementById('btn-start').addEventListener('click', startSimulation);
    document.getElementById('btn-step').addEventListener('click', stepSimulation);
    document.getElementById('btn-auto').addEventListener('click', toggleAutoRun);
    
    // Bind Tab Sim Toolbar buttons (in Metrics & Logs tab)
    const tabBtnStart = document.getElementById('tab-btn-start');
    if (tabBtnStart) tabBtnStart.addEventListener('click', startSimulation);
    
    const tabBtnStep = document.getElementById('tab-btn-step');
    if (tabBtnStep) tabBtnStep.addEventListener('click', stepSimulation);
    
    const tabBtnAuto = document.getElementById('tab-btn-auto');
    if (tabBtnAuto) tabBtnAuto.addEventListener('click', toggleAutoRun);
    
    const tabBtnReset = document.getElementById('tab-btn-reset');
    if (tabBtnReset) tabBtnReset.addEventListener('click', resetSimulation);
    
    const speedSelect = document.getElementById('speed-select');
    if (speedSelect) {
        speedSelect.addEventListener('change', (e) => {
            simSpeed = parseInt(e.target.value) || 700;
            if (simInterval) {
                clearInterval(simInterval);
                simInterval = setInterval(stepSimulation, simSpeed);
            }
        });
    }
    
    const btnClearLogs = document.getElementById('btn-clear-logs');
    if (btnClearLogs) {
        btnClearLogs.addEventListener('click', () => {
            const logBox = document.getElementById('event-log');
            if (logBox) logBox.innerHTML = '';
        });
    }
    
    // Fetch scenarios
    try {
        const res = await fetch(`${API_BASE}/scenarios`);
        const data = await res.json();
        
        scenarioSelect.innerHTML = '';
        
        const simGroup = document.createElement('optgroup');
        simGroup.label = '⚡ Interactive Simulation Scenarios';
        
        const staticGroup = document.createElement('optgroup');
        staticGroup.label = '📊 Classic Deadlock Benchmarks';
        
        const simScenarios = ['dining_philosophers_sim', 'two_process_sim', 'large_random'];
        
        data.scenarios.forEach(s => {
            const opt = document.createElement('option');
            opt.value = s;
            opt.textContent = s.replace(/_/g, ' ');
            if (simScenarios.includes(s)) {
                simGroup.appendChild(opt);
            } else {
                staticGroup.appendChild(opt);
            }
        });
        
        if (simGroup.children.length > 0) scenarioSelect.appendChild(simGroup);
        if (staticGroup.children.length > 0) scenarioSelect.appendChild(staticGroup);
        
        if (data.scenarios.length > 0) {
            loadScenario(scenarioSelect.value);
        }
    } catch(err) {
        showModal("Error", "Failed to connect to backend server.");
    }
});

function setupTabs() {
    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
            document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
            
            btn.classList.add('active');
            const target = document.getElementById('tab-' + btn.dataset.tab);
            if (target) target.classList.add('active');
        });
    });
}

function setupModals() {
    const modal = document.getElementById('alert-modal');
    document.querySelectorAll('.close-btn, .close-btn-main').forEach(btn => {
        btn.addEventListener('click', () => modal.classList.remove('active'));
    });
}

function showModal(title, msg) {
    const titleEl = document.getElementById('modal-title');
    const msgEl = document.getElementById('modal-msg');
    const modal = document.getElementById('alert-modal');
    if (titleEl) titleEl.textContent = title;
    if (msgEl) msgEl.innerHTML = msg;
    if (modal) modal.classList.add('active');
}

async function loadScenario(name) {
    if (!name) return;
    try {
        const res = await fetch(`${API_BASE}/scenarios/${name}`);
        currentScenario = await res.json();
        
        // Reset simulation session
        simSessionId = null;
        if (simInterval) toggleAutoRun();
        
        const logBox = document.getElementById('event-log');
        if (logBox) logBox.innerHTML = '';
        currentMetrics = null;
        
        currentState = {
            processes: currentScenario.processes,
            resources: Object.keys(currentScenario.resources).map(k => ({name: k, total: currentScenario.resources[k]})),
            allocation: currentScenario.allocation || currentScenario.processes.map(() => Object.keys(currentScenario.resources).map(() => 0)),
            request: currentScenario.request || currentScenario.processes.map(() => Object.keys(currentScenario.resources).map(() => 0)),
            available: currentScenario.available || Object.values(currentScenario.resources)
        };
        deadlockedPids = [];
        cycles = [];
        updateUI();
    } catch(err) {
        showModal("Error", "Failed to load scenario.");
    }
}

function updateUI() {
    if(!currentState) return;
    renderTables();
    graph.render(currentState, currentMode === 'static' && isWFG(currentState), deadlockedPids, cycles);
    updateBanner();
    updateMetrics();
}

function isWFG(state) {
    // WFG is used when ALL resources have exactly 1 total instance
    return state.resources.every(r => r.total === 1);
}

function updateBanner() {
    const banner = document.getElementById('status-banner');
    const desc = document.getElementById('status-desc');
    const title = banner.querySelector('.status-title');
    const icon = banner.querySelector('.status-icon i');
    
    if (deadlockedPids.length > 0) {
        banner.className = 'status-banner deadlock';
        title.textContent = 'DEADLOCK DETECTED';
        const pNames = deadlockedPids.map(pid => {
            const p = currentState.processes.find(x => x.id === pid);
            return p ? p.name : `P${pid}`;
        });
        desc.textContent = `Deadlocked Processes: ${pNames.join(', ')}`;
        icon.className = 'fa-solid fa-triangle-exclamation';
        
        // Update manual victim select
        const vs = document.getElementById('victim-select');
        vs.innerHTML = '';
        vs.disabled = false;
        deadlockedPids.forEach(pid => {
            const opt = document.createElement('option');
            opt.value = pid;
            const p = currentState.processes.find(x => x.id === pid);
            opt.textContent = p ? p.name : `P${pid}`;
            vs.appendChild(opt);
        });
        document.getElementById('btn-recover-manual').disabled = false;
    } else {
        banner.className = 'status-banner safe';
        title.textContent = 'SYSTEM SAFE';
        desc.textContent = 'No deadlocks detected in current state.';
        icon.className = 'fa-solid fa-check-circle';
        
        const vs = document.getElementById('victim-select');
        vs.innerHTML = '<option value="">No deadlocked processes</option>';
        vs.disabled = true;
        document.getElementById('btn-recover-manual').disabled = true;
    }
}

function updateMetrics() {
    const valTick = document.getElementById('val-tick');
    const valStatus = document.getElementById('val-status');
    const valCompleted = document.getElementById('val-completed');
    const valDeadlocks = document.getElementById('val-deadlocks');
    
    if (!currentMetrics) {
        if (valTick) valTick.textContent = '0';
        if (valStatus) {
            valStatus.textContent = 'Ready';
            valStatus.style.color = '#ffffff';
        }
        if (valCompleted) valCompleted.textContent = currentState ? `0 / ${currentState.processes.length}` : '0 / 0';
        if (valDeadlocks) {
            valDeadlocks.textContent = '0';
            valDeadlocks.style.color = '#ffffff';
        }
        return;
    }
    
    const m = currentMetrics.metrics;
    if (valTick) valTick.textContent = currentMetrics.tick;
    
    if (valStatus) {
        if (deadlockedPids.length > 0) {
            valStatus.textContent = 'Deadlocked';
            valStatus.style.color = 'var(--danger)';
        } else if (!currentMetrics.is_running) {
            valStatus.textContent = 'Finished';
            valStatus.style.color = 'var(--success)';
        } else {
            valStatus.textContent = simInterval ? 'Running' : 'Paused';
            valStatus.style.color = simInterval ? 'var(--primary-hover)' : 'var(--warning)';
        }
    }
    
    if (valCompleted) {
        const total = currentState ? currentState.processes.length : m.completed_processes;
        valCompleted.textContent = `${m.completed_processes} / ${total}`;
    }
    
    if (valDeadlocks) {
        valDeadlocks.textContent = m.deadlocks_detected;
        valDeadlocks.style.color = m.deadlocks_detected > 0 ? 'var(--danger)' : '#ffffff';
    }
}

function renderTables() {
    const renderMatrix = (id, matrix, isAvailable = false) => {
        const table = document.getElementById(id);
        if (!table) return;
        table.innerHTML = '';
        
        // Header
        const trH = document.createElement('tr');
        if(!isAvailable) trH.appendChild(document.createElement('th'));
        
        currentState.resources.forEach(r => {
            const th = document.createElement('th');
            th.textContent = r.name;
            trH.appendChild(th);
        });
        table.appendChild(trH);
        
        if (isAvailable) {
            const trA = document.createElement('tr');
            currentState.available.forEach(a => {
                const td = document.createElement('td');
                td.textContent = a;
                trA.appendChild(td);
            });
            table.appendChild(trA);
            return;
        }
        
        currentState.processes.forEach((p, i) => {
            const tr = document.createElement('tr');
            const tdP = document.createElement('td');
            tdP.textContent = p.name;
            tr.appendChild(tdP);
            
            currentState.resources.forEach((r, j) => {
                const td = document.createElement('td');
                const val = (matrix && matrix[i] && typeof matrix[i][j] !== 'undefined') ? matrix[i][j] : 0;
                td.textContent = val;
                tr.appendChild(td);
            });
            table.appendChild(tr);
        });
    };
    
    renderMatrix('alloc-table', currentState.allocation);
    renderMatrix('req-table', currentState.request);
    renderMatrix('avail-table', null, true);
}

function appendLog(tick, type, message) {
    const logBox = document.getElementById('event-log');
    if (!logBox) return;
    
    const div = document.createElement('div');
    div.className = 'log-entry';
    
    let badgeClass = 'badge-info';
    const t = type.toLowerCase();
    if (t.includes('grant')) badgeClass = 'badge-grant';
    else if (t.includes('request')) badgeClass = 'badge-request';
    else if (t.includes('block')) badgeClass = 'badge-block';
    else if (t.includes('deadlock')) badgeClass = 'badge-deadlock';
    else if (t.includes('abort')) badgeClass = 'badge-abort';
    else if (t.includes('rollback') || t.includes('recovery')) badgeClass = 'badge-recovery';
    else if (t.includes('end')) badgeClass = 'badge-end';
    else if (t.includes('checkpoint')) badgeClass = 'badge-checkpoint';
    else if (t.includes('pause')) badgeClass = 'badge-block';
    
    div.innerHTML = `<span class="log-tick">[Tick ${tick}]</span> <span class="log-badge ${badgeClass}">${type}</span> <span class="log-msg">${message}</span>`;
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
    
    try {
        const res = await fetch(`${API_BASE}/detect`, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(payload)
        });
        const data = await res.json();
        
        deadlockedPids = data.deadlocked_pids;
        cycles = data.cycles;
        
        if (data.cycle_without_deadlock) {
            showModal("Notice", "Cycle found in graph, but <strong>NO deadlock</strong>!<br><br>Other processes outside the cycle hold sufficient instances to eventually satisfy the requests, breaking the cycle.");
        }
        updateUI();
    } catch(err) {
        showModal("Error", "Deadlock detection request failed.");
    }
}

async function recoverStaticAuto() {
    const payload = {
        resources: currentScenario.resources,
        processes: currentState.processes,
        allocation: currentState.allocation,
        request: currentState.request,
        available: currentState.available
    };
    
    try {
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
            
            const actionsStr = data.actions.map(a => `<strong>${a.type}</strong> on P${a.pid}`).join('<br>');
            showModal("Recovery Success", `System is now safe. Actions taken:<br><br>${actionsStr}`);
        } else {
            showModal("Info", "No deadlock exists, or recovery failed.");
        }
    } catch(err) {
        showModal("Error", "Auto-recovery request failed.");
    }
}

async function recoverManual(victimId) {
    if (currentMode === 'static') {
        const idx = currentState.processes.findIndex(p => p.id === victimId);
        if (idx >= 0) {
            for (let r = 0; r < currentState.resources.length; r++) {
                currentState.available[r] += currentState.allocation[idx][r];
                currentState.allocation[idx][r] = 0;
                currentState.request[idx][r] = 0;
            }
            detectStatic(); 
        }
    } else {
        if (!simSessionId) return;
        const strategy = document.getElementById('strategy-select').value;
        try {
            const res = await fetch(`${API_BASE}/simulate/manual_recover/${simSessionId}`, {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({victim_id: victimId, strategy: strategy === 'none' ? 'terminate_one' : strategy})
            });
            const data = await res.json();
            applySimData(data);
            appendLog(data.tick, "MANUAL_RECOVERY", `Process P${victimId} manually aborted. Simulation can now proceed.`);
        } catch(err) {
            showModal("Error", "Manual recovery failed.");
        }
    }
}

// Sim Actions
async function startSimulation() {
    // If simulation is already auto-running, clicking "Pause" should pause it
    if (simInterval) {
        toggleAutoRun();
        return;
    }
    
    // If session already exists and is running, resume it!
    if (simSessionId && currentMetrics && currentMetrics.is_running && deadlockedPids.length === 0) {
        toggleAutoRun();
        return;
    }
    
    // Start fresh simulation session
    const scenarioName = document.getElementById('scenario-select').value;
    const strategy = document.getElementById('strategy-select').value;
    
    try {
        const res = await fetch(`${API_BASE}/simulate/start`, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({ scenario: scenarioName, strategy: strategy })
        });
        
        const data = await res.json();
        if (!res.ok) {
            showModal("Simulation Notice", `Cannot start simulation: ${data.detail || 'Unknown error'}`);
            return;
        }
        
        if (data.session_id) {
            simSessionId = data.session_id;
            const logBox = document.getElementById('event-log');
            if (logBox) logBox.innerHTML = '';
            appendLog(0, "START", `Simulation started for scenario "${scenarioName.replace(/_/g, ' ')}" [Strategy: ${strategy}].`);
            await fetchSimStatus();
            
            // Automatically begin auto-playing!
            if (!simInterval) {
                toggleAutoRun();
            }
        }
    } catch (err) {
        showModal("Connection Error", "Could not reach backend server to start simulation.");
    }
}

async function fetchSimStatus() {
    if (!simSessionId) return;
    try {
        const res = await fetch(`${API_BASE}/simulate/status/${simSessionId}`);
        applySimData(await res.json());
    } catch(err) {
        console.error("Failed to fetch sim status", err);
    }
}

async function stepSimulation() {
    if (!simSessionId) {
        await startSimulation();
        return;
    }
    try {
        const res = await fetch(`${API_BASE}/simulate/step/${simSessionId}`, { method: 'POST' });
        if (!res.ok) {
            showModal("Simulation Error", "Failed to step simulation.");
            if (simInterval) toggleAutoRun();
            return;
        }
        applySimData(await res.json());
    } catch(err) {
        if (simInterval) toggleAutoRun();
    }
}

async function toggleAutoRun() {
    if (!simSessionId) {
        await startSimulation();
        return;
    }
    
    if (simInterval) {
        clearInterval(simInterval);
        simInterval = null;
        updateAutoRunButtons(false);
    } else {
        simInterval = setInterval(stepSimulation, simSpeed);
        updateAutoRunButtons(true);
    }
    updateMetrics();
}

function updateAutoRunButtons(isRunning) {
    const sideStartBtn = document.getElementById('btn-start');
    const tabStartBtn = document.getElementById('tab-btn-start');
    const sideAutoBtn = document.getElementById('btn-auto');
    const tabAutoBtn = document.getElementById('tab-btn-auto');
    
    if (isRunning) {
        if (sideStartBtn) sideStartBtn.innerHTML = '<i class="fa-solid fa-pause"></i> Pause';
        if (tabStartBtn) tabStartBtn.innerHTML = '<i class="fa-solid fa-pause"></i> Pause';
        if (sideAutoBtn) sideAutoBtn.innerHTML = '<i class="fa-solid fa-pause"></i> Pause';
        if (tabAutoBtn) tabAutoBtn.innerHTML = '<i class="fa-solid fa-pause"></i> Pause';
        
        [sideStartBtn, tabStartBtn, sideAutoBtn, tabAutoBtn].forEach(b => {
            if (b) {
                b.classList.add('btn-warning');
                b.classList.remove('btn-primary', 'btn-secondary');
            }
        });
    } else {
        if (sideStartBtn) sideStartBtn.innerHTML = '<i class="fa-solid fa-play"></i> Start Simulation';
        if (tabStartBtn) tabStartBtn.innerHTML = '<i class="fa-solid fa-play"></i> Start';
        if (sideAutoBtn) sideAutoBtn.innerHTML = '<i class="fa-solid fa-forward"></i> Auto-Play';
        if (tabAutoBtn) tabAutoBtn.innerHTML = '<i class="fa-solid fa-forward"></i> Auto-Play';
        
        if (sideStartBtn) { sideStartBtn.classList.add('btn-primary'); sideStartBtn.classList.remove('btn-warning'); }
        if (tabStartBtn) { tabStartBtn.classList.add('btn-primary'); tabStartBtn.classList.remove('btn-warning'); }
        if (sideAutoBtn) { sideAutoBtn.classList.add('btn-warning'); sideAutoBtn.classList.remove('btn-primary'); }
        if (tabAutoBtn) { tabAutoBtn.classList.add('btn-warning'); tabAutoBtn.classList.remove('btn-primary'); }
    }
}

function resetSimulation() {
    if (simInterval) toggleAutoRun();
    simSessionId = null;
    const scenarioName = document.getElementById('scenario-select').value;
    loadScenario(scenarioName);
    const logBox = document.getElementById('event-log');
    if (logBox) logBox.innerHTML = '';
    appendLog(0, "INFO", "Simulation reset to initial state.");
}

function applySimData(data) {
    currentState = data.state;
    currentMetrics = data;
    deadlockedPids = data.deadlocked_pids;
    cycles = []; 
    
    const logBox = document.getElementById('event-log');
    if (logBox) {
        logBox.innerHTML = '';
        data.logs.forEach(l => appendLog(l.tick, l.type, l.message));
    }
    
    updateUI();
    
    const strategy = document.getElementById('strategy-select').value;
    
    // If deadlocked and manual recovery is selected, pause auto-play so user can select a victim
    if (deadlockedPids.length > 0 && strategy === 'none') {
        if (simInterval) {
            clearInterval(simInterval);
            simInterval = null;
            updateAutoRunButtons(false);
        }
        appendLog(data.tick, "PAUSE", "Simulation paused for Manual Recovery. Choose a victim below and click Abort Victim.");
    }
    
    if (!data.is_running) {
        if (simInterval) {
            clearInterval(simInterval);
            simInterval = null;
            updateAutoRunButtons(false);
        }
        appendLog(data.tick, "SYSTEM", "Simulation finished all processes.");
    }
}
