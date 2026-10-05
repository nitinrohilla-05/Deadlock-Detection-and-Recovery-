class GraphRenderer {
    constructor(svgId) {
        this.svg = document.getElementById(svgId);
        this.width = this.svg.clientWidth;
        this.height = this.svg.clientHeight;
        this.nodes = [];
        this.edges = [];
        
        // Add arrow marker
        this.svg.innerHTML = `
            <defs>
                <marker id="arrowhead" markerWidth="10" markerHeight="7" refX="9" refY="3.5" orient="auto">
                    <polygon points="0 0, 10 3.5, 0 7" fill="var(--text-muted)" />
                </marker>
                <marker id="arrowhead-cycle" markerWidth="10" markerHeight="7" refX="9" refY="3.5" orient="auto">
                    <polygon points="0 0, 10 3.5, 0 7" fill="#ff4444" />
                </marker>
            </defs>
            <g id="edges-layer"></g>
            <g id="nodes-layer"></g>
        `;
        this.edgesLayer = this.svg.querySelector('#edges-layer');
        this.nodesLayer = this.svg.querySelector('#nodes-layer');
    }

    render(state, isWFG = false, deadlockedPids = [], cycles = []) {
        this.edgesLayer.innerHTML = '';
        this.nodesLayer.innerHTML = '';
        this.nodes = [];
        
        const processes = state.processes;
        const resources = state.resources;
        
        // Circular layout
        const totalNodes = isWFG ? processes.length : processes.length + resources.length;
        const cx = this.width / 2;
        const cy = this.height / 2;
        const radius = Math.min(cx, cy) - 50;
        
        let angle = 0;
        const angleStep = (2 * Math.PI) / totalNodes;
        
        const nodePositions = {};
        
        processes.forEach((p, i) => {
            const x = cx + radius * Math.cos(angle);
            const y = cy + radius * Math.sin(angle);
            nodePositions[`P_${p.id}`] = { x, y, type: 'process', data: p };
            angle += angleStep;
        });
        
        if (!isWFG) {
            resources.forEach((r, i) => {
                const x = cx + radius * Math.cos(angle);
                const y = cy + radius * Math.sin(angle);
                nodePositions[`R_${r.name}`] = { x, y, type: 'resource', data: r, index: i };
                angle += angleStep;
            });
        }
        
        // Draw Edges
        const cycleEdges = new Set();
        if (cycles && cycles.length > 0) {
            // Highlight the first cycle
            const cycle = cycles[0];
            for (let i = 0; i < cycle.length; i++) {
                const u = cycle[i];
                const v = cycle[(i + 1) % cycle.length];
                cycleEdges.add(`P_${u}->P_${v}`);
            }
        }
        
        if (isWFG) {
            // WFG edges
            for (let i = 0; i < processes.length; i++) {
                for (let r = 0; r < resources.length; r++) {
                    if (state.request[i][r] > 0) {
                        for (let j = 0; j < processes.length; j++) {
                            if (i !== j && state.allocation[j][r] > 0) {
                                this.drawEdge(nodePositions[`P_${processes[i].id}`], nodePositions[`P_${processes[j].id}`], true, cycleEdges.has(`P_${processes[i].id}->P_${processes[j].id}`));
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
                        // Check if this request is part of a cycle (P_i requests R which is held by P_j in cycle)
                        let isCycle = false;
                        if (cycles.length > 0) {
                            const cycle = cycles[0];
                            if (cycle.includes(processes[i].id)) {
                                const nextPidInCycle = cycle[(cycle.indexOf(processes[i].id) + 1) % cycle.length];
                                const nextPidx = state.processes.findIndex(p => p.id === nextPidInCycle);
                                if (state.allocation[nextPidx][r] > 0) {
                                    isCycle = true;
                                }
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
            circle.setAttribute("r", 20);
            circle.setAttribute("fill", "var(--bg-panel)");
            circle.setAttribute("class", `graph-node ${isDeadlocked ? 'deadlocked' : ''}`);
            // Provide hook for UI selection
            circle.setAttribute("data-pid", pos.data.id);
            g.appendChild(circle);
            
            const text = document.createElementNS("http://www.w3.org/2000/svg", "text");
            text.textContent = pos.data.name;
            text.setAttribute("class", "graph-text");
            g.appendChild(text);
        } else {
            const rect = document.createElementNS("http://www.w3.org/2000/svg", "rect");
            rect.setAttribute("width", 40);
            rect.setAttribute("height", 40);
            rect.setAttribute("x", -20);
            rect.setAttribute("y", -20);
            rect.setAttribute("fill", "var(--bg-panel)");
            rect.setAttribute("class", "graph-node");
            g.appendChild(rect);
            
            const text = document.createElementNS("http://www.w3.org/2000/svg", "text");
            text.textContent = pos.data.name;
            text.setAttribute("class", "graph-text");
            text.setAttribute("y", -25);
            g.appendChild(text);
            
            // Draw instance dots (simple grid)
            const total = pos.data.total;
            let dotX = -10;
            let dotY = -10;
            for (let k = 0; k < total && k < 4; k++) {
                const dot = document.createElementNS("http://www.w3.org/2000/svg", "circle");
                dot.setAttribute("r", 4);
                dot.setAttribute("cx", dotX + (k%2)*20);
                dot.setAttribute("cy", dotY + Math.floor(k/2)*20);
                dot.setAttribute("class", "resource-dot");
                g.appendChild(dot);
            }
        }
        
        this.nodesLayer.appendChild(g);
    }
    
    drawEdge(n1, n2, isRequest, isCycle) {
        const dx = n2.x - n1.x;
        const dy = n2.y - n1.y;
        const dist = Math.sqrt(dx*dx + dy*dy);
        
        // shorten the line so arrow doesn't hide behind node
        const offset = 22;
        const ratio = (dist - offset) / dist;
        const ex = n1.x + dx * ratio;
        const ey = n1.y + dy * ratio;
        
        const line = document.createElementNS("http://www.w3.org/2000/svg", "line");
        line.setAttribute("x1", n1.x);
        line.setAttribute("y1", n1.y);
        line.setAttribute("x2", ex);
        line.setAttribute("y2", ey);
        
        let cls = "graph-edge";
        if (isRequest) cls += " request";
        if (isCycle) cls += " cycle";
        line.setAttribute("class", cls);
        
        const marker = isCycle ? "url(#arrowhead-cycle)" : "url(#arrowhead)";
        line.setAttribute("marker-end", marker);
        
        this.edgesLayer.appendChild(line);
    }
}
