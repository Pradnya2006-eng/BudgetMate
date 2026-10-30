"""A tiny in-memory limiter to slow down password guessing.

It lives in the server's memory, so it resets on restart and isn't shared
between several server processes. That's fine for a single-server project;
a larger deployment would use something like Redis instead.
"""

import time
from collections import defaultdict, deque


class RateLimiter:
    def __init__(self, max_events, window_seconds):
        self.max_events = max_events
        self.window = window_seconds
        self._events = defaultdict(deque)

    def _prune(self, key):
        events = self._events[key]
        cutoff = time.monotonic() - self.window
        while events and events[0] < cutoff:
            events.popleft()
        if not events:
            del self._events[key]
        return self._events.get(key)

    def blocked(self, key):
        events = self._prune(key)
        return bool(events) and len(events) >= self.max_events

    def add(self, key):
        self._prune(key)
        self._events[key].append(time.monotonic())

    def reset(self, key):
        self._events.pop(key, None)
