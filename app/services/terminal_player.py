from __future__ import annotations
import sys
import time
import threading
from typing import Iterable, Tuple, Optional

CLEAR = "\x1b[2J"
HOME = "\x1b[H"
HIDE_CURSOR = "\x1b[?25l"
SHOW_CURSOR = "\x1b[?25h"

class TerminalPlayer:
    def __init__(self):
        self._stop = threading.Event()
        self._thread: Optional[threading.Thread] = None

    def play_frames(self, frames: Iterable[Tuple[str, float]], clear_each: bool = True):
        start = time.perf_counter()
        try:
            sys.stdout.write(HIDE_CURSOR)
            sys.stdout.flush()
            for i, (frame, spf) in enumerate(frames):
                if self._stop.is_set():
                    break
                if clear_each:
                    sys.stdout.write(HOME + CLEAR)
                else:
                    sys.stdout.write(HOME)
                sys.stdout.write(frame)
                sys.stdout.flush()

                next_due = start + (i + 1) * spf
                delay = max(0.0, next_due - time.perf_counter())
                time.sleep(delay)
        finally:
            sys.stdout.write("\n" + SHOW_CURSOR)
            sys.stdout.flush()

    def start_in_thread(self, frames: Iterable[Tuple[str, float]]):
        if self._thread and self._thread.is_alive():
            raise RuntimeError("A playback is already running")
        self._stop.clear()
        self._thread = threading.Thread(target=self.play_frames, args=(frames,), daemon=True)
        self._thread.start()

    def stop(self):
        self._stop.set()
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=1.0)
        self._thread = None

player = TerminalPlayer()
