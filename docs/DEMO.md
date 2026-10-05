# Deadlock Lab: Presentation Walkthrough

## Setup
1. Launch the UI using `python run.py`.
2. Open `http://127.0.0.1:8000` in the browser.

## Step 1: The "Cycle Without Deadlock" Edge Case
1. Set Mode to **Static (Matrix)**.
2. Select **cycle_without_deadlock**.
3. Point out the cycle in the graph. Explain that structurally, there is a cycle.
4. Click **Detect Deadlock**.
5. Show the alert box: "Cycle found, but NO deadlock". Explain how the remaining instances outside the cycle save the system.
6. The banner remains green (SAFE).

## Step 2: Classic Deadlock Detection
1. Switch scenario to **textbook_deadlock**.
2. Click **Detect Deadlock**.
3. Notice the red DEADLOCK DETECTED banner.
4. Show how the specific deadlocked nodes (PIDs) are highlighted in the Graph, but other independent nodes are ignored.

## Step 3: Manual vs Auto Recovery
1. Use the **Manual Victim Selection** dropdown to show we can manually abort a process.
2. Click **Auto Recover**.
3. Show the event log and banner changing to SAFE, along with the UI matrix updating the Available resources.

## Step 4: Tick Simulator (Time Dynamics)
1. Change Mode to **Simulation (Tick)**.
2. Select **two_process_circular**.
3. Set Recovery Strategy to **Terminate One (Cost)**.
4. Click **Start Simulation**.
5. Click **Step Tick** manually 2-3 times to show requests being made and resources being granted.
6. Click **Auto-Run** and watch the system naturally encounter a deadlock.
7. Observe how the simulator pauses, the Auto-Recovery kicks in, a victim is rolled back, and the simulation completes successfully. Show the final metrics in the right panel (Work Lost).
