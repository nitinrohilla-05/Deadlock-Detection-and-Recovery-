# Viva Q&A

**Q: What is the difference between Deadlock Detection and Deadlock Avoidance?**
A: Avoidance (e.g., Banker's Algorithm) requires a priori knowledge of maximum resource claims and checks safety *before* granting requests. Detection grants requests dynamically without prior knowledge and periodically scans the state graph/matrices to see if a deadlock *has already occurred*.

**Q: Why did you use two different algorithms (WFG and Matrix) for detection?**
A: A WFG (Wait-For-Graph) is efficient (O(V+E)) but is only sufficient for systems where every resource has exactly one instance. In a system with multiple instances of a single resource type, a cycle in the WFG is necessary but not sufficient for deadlock. Thus, for multi-instance resources, the Matrix algorithm (O(m * n^2)) must be used to simulate resource resolution.

**Q: How does your system select a victim during recovery?**
A: `TerminateOneAtATime` uses a cost-based selection. It minimizes `work_completed / (priority + 1)`. This ensures we don't abort high-priority processes or processes that have computed heavily, unless absolutely necessary.

**Q: Does your system suffer from starvation during recovery?**
A: No. The `ResourcePreemption` strategy tracks how many times a process has been preempted. If a process exceeds the max allowed preemptions, it is protected from being picked as a victim again, guaranteeing it will eventually progress.

**Q: How is 'Cycle without Deadlock' possible?**
A: If process A waits on resource R1 (held by B) and B waits on resource R2 (held by A), that's a cycle. But if R2 has *two* instances, and the second instance is held by C (who is not waiting on anything), C will eventually finish and release R2. B can then acquire R2, finish, and release R1, resolving A's request.
