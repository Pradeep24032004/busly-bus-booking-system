import threading
from typing import Dict, Tuple, List, Optional

# Key: (bus_id, seat_number)
class SeatLockManager:
    def __init__(self):
        self._locks: Dict[Tuple[str, str], threading.Lock] = {}
        self._owners: Dict[Tuple[str, str], str] = {}  # maps to reservation_id
        self._map_lock = threading.RLock()

    def _get_lock(self, bus_id: str, seat: str) -> threading.Lock:
        key = (bus_id, seat)
        with self._map_lock:
            if key not in self._locks:
                self._locks[key] = threading.Lock()
            return self._locks[key]

    def try_acquire_many(self, bus_id: str, seats: List[str], reservation_id: str) -> Tuple[bool, List[str]]:
        """
        Attempt to acquire locks for all seats non-blockingly.
        Returns (success, conflicting_seats)
        """
        keys = sorted([(bus_id, s) for s in seats], key=lambda x: x[1])
        acquired = []
        conflicting = []
        for (b, s) in keys:
            lock = self._get_lock(b, s)
            got = lock.acquire(blocking=False)
            if got:
                acquired.append((b, s))
            else:
                conflicting.append(s)
                # immediate failure; release any acquired
                break

        if conflicting:
            # release acquired
            for (b, s) in acquired:
                self._get_lock(b, s).release()
            return False, conflicting

        # mark owners
        with self._map_lock:
            for (b, s) in acquired:
                self._owners[(b, s)] = reservation_id
        return True, []

    def release_many(self, bus_id: str, seats: List[str], reservation_id: Optional[str] = None):
        keys = [(bus_id, s) for s in seats]
        with self._map_lock:
            for (b, s) in keys:
                owner = self._owners.get((b, s))
                if reservation_id is None or owner == reservation_id:
                    if (b, s) in self._owners:
                        del self._owners[(b, s)]
                    try:
                        lock = self._locks.get((b, s))
                        if lock and lock.locked():
                            lock.release()
                    except RuntimeError:
                        # already released or not acquired - ignore
                        pass

    def owner_of(self, bus_id: str, seat: str) -> Optional[str]:
        return self._owners.get((bus_id, seat))
