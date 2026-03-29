#!/usr/bin/env python3
"""Counting semaphore and mutex with deadlock detection."""
import sys, threading, time
from collections import defaultdict

class Semaphore:
    def __init__(self, value=1):
        self.value, self.waiters = value, 0
        self._lock = threading.Lock(); self._cond = threading.Condition(self._lock)
    def acquire(self, timeout=None):
        with self._cond:
            self.waiters += 1
            end = time.time() + timeout if timeout else None
            while self.value <= 0:
                remaining = (end - time.time()) if end else None
                if remaining is not None and remaining <= 0:
                    self.waiters -= 1; return False
                self._cond.wait(timeout=remaining)
            self.value -= 1; self.waiters -= 1; return True
    def release(self):
        with self._cond: self.value += 1; self._cond.notify()

class Mutex(Semaphore):
    def __init__(self): super().__init__(1); self.owner = None
    def acquire(self, timeout=None):
        ok = super().acquire(timeout)
        if ok: self.owner = threading.current_thread().ident
        return ok
    def release(self):
        self.owner = None; super().release()

class DeadlockDetector:
    def __init__(self): self.waits_for = defaultdict(set)  # thread -> set of threads
    def add_wait(self, waiter, holder):
        self.waits_for[waiter].add(holder)
    def remove_wait(self, waiter): self.waits_for.pop(waiter, None)
    def has_cycle(self):
        visited, stack = set(), set()
        def dfs(node):
            if node in stack: return True
            if node in visited: return False
            visited.add(node); stack.add(node)
            for n in self.waits_for.get(node, set()):
                if dfs(n): return True
            stack.discard(node); return False
        for node in list(self.waits_for): 
            if dfs(node): return True
        return False

def main():
    if len(sys.argv) < 2: print("Usage: semaphore.py <demo|test>"); return
    if sys.argv[1] == "test":
        s = Semaphore(2)
        assert s.acquire(); assert s.acquire()
        assert not s.acquire(timeout=0.01)  # would block
        s.release(); assert s.acquire()
        # Mutex
        m = Mutex(); assert m.acquire()
        assert not m.acquire(timeout=0.01)
        m.release(); assert m.acquire(); m.release()
        # Deadlock detection
        dd = DeadlockDetector()
        dd.add_wait("T1", "T2"); dd.add_wait("T2", "T3")
        assert not dd.has_cycle()
        dd.add_wait("T3", "T1"); assert dd.has_cycle()
        dd.remove_wait("T3"); assert not dd.has_cycle()
        # Threaded semaphore
        counter = [0]; sem = Semaphore(1)
        def inc():
            for _ in range(100):
                sem.acquire(); counter[0] += 1; sem.release()
        threads = [threading.Thread(target=inc) for _ in range(4)]
        for t in threads: t.start()
        for t in threads: t.join()
        assert counter[0] == 400
        print("All tests passed!")
    else:
        s = Semaphore(3); print(f"Semaphore(3), value={s.value}")
        s.acquire(); s.acquire(); print(f"After 2 acquires: value={s.value}")

if __name__ == "__main__": main()
