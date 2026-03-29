#!/usr/bin/env python3
"""Counting semaphore implementation."""
import threading, time

class Semaphore:
    def __init__(self, count: int = 1):
        self._count = count
        self._lock = threading.Lock()
        self._cond = threading.Condition(self._lock)

    def acquire(self, timeout: float = None) -> bool:
        with self._cond:
            end = time.monotonic() + timeout if timeout else None
            while self._count <= 0:
                remaining = (end - time.monotonic()) if end else None
                if remaining is not None and remaining <= 0:
                    return False
                self._cond.wait(timeout=remaining)
            self._count -= 1
            return True

    def release(self):
        with self._cond:
            self._count += 1
            self._cond.notify()

    @property
    def value(self):
        return self._count

    def __enter__(self):
        self.acquire()
        return self

    def __exit__(self, *args):
        self.release()

if __name__ == "__main__":
    sem = Semaphore(2)
    print(f"Initial: {sem.value}")
    sem.acquire(); print(f"After acquire: {sem.value}")
    sem.release(); print(f"After release: {sem.value}")

def test():
    s = Semaphore(2)
    assert s.value == 2
    s.acquire(); assert s.value == 1
    s.acquire(); assert s.value == 0
    # Timeout
    assert not s.acquire(timeout=0.01)
    s.release(); assert s.value == 1
    # Context manager
    with s:
        assert s.value == 0
    assert s.value == 1
    # Threading
    results = []
    sem = Semaphore(1)
    def worker(n):
        with sem:
            results.append(n)
            time.sleep(0.01)
    threads = [threading.Thread(target=worker, args=(i,)) for i in range(3)]
    for t in threads: t.start()
    for t in threads: t.join()
    assert len(results) == 3
    print("  semaphore: ALL TESTS PASSED")
