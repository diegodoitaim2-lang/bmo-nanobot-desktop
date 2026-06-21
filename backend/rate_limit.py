from __future__ import annotations

import time
from collections import defaultdict, deque
from threading import Lock


_counters: dict[str, deque[float]] = defaultdict(deque)
_counters_lock = Lock()


def check_rate_limit(ip: str, path: str, *, now: float | None = None) -> tuple[bool, int]:
    """Return (allowed, retry_after_seconds)."""
    current = now if now is not None else time.time()
    window = 60.0
    status_paths = {
        "/api/health",
        "/api/system",
        "/api/settings",
        "/api/reminders",
        "/api/subagents",
        "/api/tasks",
    }
    limit = 240 if path in status_paths or ip.startswith("127.") else 30
    with _counters_lock:
        queue = _counters[ip]
        while queue and current - queue[0] > window:
            queue.popleft()
        if len(queue) >= limit:
            retry_after = max(1, int(window - (current - queue[0])))
            return False, retry_after
        queue.append(current)
    return True, 0
