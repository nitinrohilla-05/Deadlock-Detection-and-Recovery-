class GraphRenderer {
    constructor(svgId) {
        this.svg = document.getElementById(svgId);
        
        // Add arrow markers
        this.svg.innerHTML = `
            <defs>
                <marker id="arrowhead" markerWidth="10" markerHeight="7" refX="9" refY="3.5" orient="auto">
                    <polygon points="0 0, 10 3.5, 0 7" fill="var(--text-muted)" />
                </marker>
                <marker id="arrowhead-cycle" markerWidth="10" markerHeight="7" refX="9" refY="3.5" orient="auto">
                    <polygon points="0 0, 10 3.5, 0 7" fill="var(--danger)" />
                </marker>
            </defs>
            <g id="edges-layer"></g>
            <g id="nodes-layer"></g>
        `;
        this.edgesLayer = this.svg.querySelector('#edges-layer');
        this.nodesLayer = this.svg.querySelector('#nodes-layer');
    }

    render(state, isWFG = false, deadlockedPids = [], cycles = []) {
        // Dynamic resize
        this.width = this.svg.clientWidth || 600;
        this.height = this.svg.clientHeight || 400;
        
        this.edgesLayer.innerHTML = '';
        this.nodesLayer.innerHTML = '';
        
        const processes = state.processes;
        const resources = state.resources;
        
        // Circular layout
        const totalNodes = isWFG ? processes.length : processes.length + resources.length;
        const cx = this.width / 2;
        const cy = this.height / 2;
        const radius = Math.min(cx, cy) - 60; // Padding
        
        let angle = -Math.PI / 2; // Start from top
        const angleStep = (2 * Math.PI) / totalNodes;
        
        const nodePositions = {};
        
        processes.forEach(p => {
            nodePositions[`P_${p.id}`] = { 
                x: cx + radius * Math.cos(angle), 
                y: cy + radius * Math.sin(angle), 
                type: 'process', 
                data: p 
            };
            angle += angleStep;
        });
        
        if (!isWFG) {
            resources.forEach((r, i) => {
                nodePositions[`R_${r.name}`] = { 
                    x: cx + radius * Math.cos(angle), 
                    y: cy + radius * Math.sin(angle), 
                    type: 'resource', 
                    data: r, 
                    index: i 
                };
                angle += angleStep;
            });
        }
        
        // Determine Cycle Edges for highlighting
        const cycleEdges = new Set();
        if (cycles && cycles.length > 0) {
            const cycle = cycles[0];
            for (let i = 0; i < cycle.length; i++) {
                const u = cycle[i];
                const v = cycle[(i + 1) % cycle.length];
                cycleEdges.add(`P_${u}->P_${v}`);
            }
        }
        
        // Draw Edges
        if (isWFG) {
            for (let i = 0; i < processes.length; i++) {
                for (let r = 0; r < resources.length; r++) {
                    if (state.request[i][r] > 0) {
                        for (let j = 0; j < processes.length; j++) {
                            if (i !== j && state.allocation[j][r] > 0) {
                                const isCycle = cycleEdges.has(`P_${processes[i].id}->P_${processes[j].id}`);
                                this.drawEdge(nodePositions[`P_${processes[i].id}`], nodePositions[`P_${processes[j].id}`], true, isCycle);
                            }
                        }
                    }
                }
            }
        } else {
            // RAG edges
            for (let i = 0; i < processes.length; i++) {
                for (let r = 0; r < resources.length; r++) {
                    // Assignment: R -> P
                    if (state.allocation[i][r] > 0) {
                        this.drawEdge(nodePositions[`R_${resources[r].name}`], nodePositions[`P_${processes[i].id}`], false, false);
                    }
                    // Request: P -> R
                    if (state.request[i][r] > 0) {
                        let isCycle = false;
                        if (cycles.length > 0) {
                            const cycle = cycles[0];
                            if (cycle.includes(processes[i].id)) {
                                const nextPid = cycle[(cycle.indexOf(processes[i].id) + 1) % cycle.length];
                                const nextIdx = state.processes.findIndex(p => p.id === nextPid);
                                if (state.allocation[nextIdx][r] > 0) isCycle = true;
                            }
                        }
                        this.drawEdge(nodePositions[`P_${processes[i].id}`], nodePositions[`R_${resources[r].name}`], true, isCycle);
                    }
                }
            }
        }
        
        // Draw Nodes
        Object.keys(nodePositions).forEach(key => {
            const pos = nodePositions[key];
            const isDeadlocked = pos.type === 'process' && deadlockedPids.includes(pos.data.id);
            this.drawNode(pos, isDeadlocked);
        });
    }
    
    drawNode(pos, isDeadlocked) {
        const g = document.createElementNS("http://www.w3.org/2000/svg", "g");
        g.setAttribute("transform", `translate(${pos.x}, ${pos.y})`);
        
        if (pos.type === 'process') {
            const circle = document.createElementNS("http://www.w3.org/2000/svg", "circle");
            circle.setAttribute("r", 22);
            circle.setAttribute("class", `node-process ${isDeadlocked ? 'node-deadlocked' : ''}`);
            g.appendChild(circle);
            
            const text = document.createElementNS("http://www.w3.org/2000/svg", "text");
            text.textContent = pos.data.name;
            text.setAttribute("class", "node-text");
            g.appendChild(text);
        } else {
            const rect = document.createElementNS("http://www.w3.org/2000/svg", "rect");
            rect.setAttribute("width", 44);
            rect.setAttribute("height", 44);
            rect.setAttribute("x", -22);
            rect.setAttribute("y", -22);
            rect.setAttribute("rx", 6); // Rounded corners
            rect.setAttribute("class", "node-resource");
            g.appendChild(rect);
            
            const text = document.createElementNS("http://www.w3.org/2000/svg", "text");
            text.textContent = pos.data.name;
            text.setAttribute("class", "node-text");
            text.setAttribute("y", -30);
            g.appendChild(text);
            
            // Draw instance dots
            const total = pos.data.total;
            let dotX = -10;
            let dotY = -10;
            for (let k = 0; k < total && k < 4; k++) {
                const dot = document.createElementNS("http://www.w3.org/2000/svg", "circle");
                dot.setAttribute("r", 4);
                dot.setAttribute("cx", dotX + (k%2)*20);
                dot.setAttribute("cy", dotY + Math.floor(k/2)*20);
                dot.setAttribute("class", "res-dot");
                g.appendChild(dot);
            }
        }
        
        this.nodesLayer.appendChild(g);
    }
    
    drawEdge(n1, n2, isRequest, isCycle) {
        if (!n1 || !n2 || typeof n1.x !== 'number' || typeof n2.x !== 'number') return;
        const dx = n2.x - n1.x;
        const dy = n2.y - n1.y;
        const dist = Math.sqrt(dx*dx + dy*dy);
        if (dist === 0) return;
        
        const offset = 26; // Node radius + padding
        const ratio = (dist - offset) / dist;
        const ex = n1.x + dx * ratio;
        const ey = n1.y + dy * ratio;
        
        const sx = n1.x + dx * (offset/dist);
        const sy = n1.y + dy * (offset/dist);
        
        const line = document.createElementNS("http://www.w3.org/2000/svg", "line");
        line.setAttribute("x1", sx);
        line.setAttribute("y1", sy);
        line.setAttribute("x2", ex);
        line.setAttribute("y2", ey);
        
        let cls = "edge-line";
        if (isRequest) cls += " edge-request";
        if (isCycle) cls += " edge-cycle";
        line.setAttribute("class", cls);
        
        const marker = isCycle ? "url(#arrowhead-cycle)" : "url(#arrowhead)";
        line.setAttribute("marker-end", marker);
        
        this.edgesLayer.appendChild(line);
    }
}
