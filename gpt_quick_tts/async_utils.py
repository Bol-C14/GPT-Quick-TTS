from __future__ import annotations

"""Run asyncio coroutines on a dedicated background thread."""

import asyncio
import threading
from typing import Optional


class AsyncLoopThread:
    """Dedicated event loop running on its own thread.

    Reusing a single loop avoids creating/closing loops per call and reduces
    shutdown noise from background transports.
    """

    def __init__(self):
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._loop: Optional[asyncio.AbstractEventLoop] = None
        self._started = threading.Event()
        self._stop_requested = threading.Event()
        self._thread.start()
        self._started.wait()

    def _run(self):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        self._loop = loop
        self._started.set()
        try:
            loop.run_until_complete(self._main())
        finally:
            try:
                loop.close()
            except Exception:
                pass

    async def _main(self):
        while not self._stop_requested.is_set():
            await asyncio.sleep(0.1)

    def run_coroutine(self, coro, timeout: Optional[float] = None):
        """Submit a coroutine to the background loop and wait for the result."""
        if not self._loop:
            raise RuntimeError("Async loop not started")
        future = asyncio.run_coroutine_threadsafe(coro, self._loop)
        return future.result(timeout=timeout)

    def stop(self, timeout: float = 2.0):
        """Request loop shutdown and join the thread."""
        self._stop_requested.set()
        if self._loop:
            try:
                self._loop.call_soon_threadsafe(lambda: None)
            except Exception:
                pass
        self._thread.join(timeout=timeout)
