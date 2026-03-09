from __future__ import annotations
import threading, time, logging, sqlite3
from app.ingestor import refresh

log = logging.getLogger("news.scheduler")

class Refresher(threading.Thread):
    daemon = True
    def __init__(self, conn: sqlite3.Connection, interval_minutes: int, enable_google: bool, enable_gdelt: bool):
        super().__init__()
        self.conn = conn
        self.interval_s = max(60, interval_minutes * 60)
        self.enable_google = enable_google
        self.enable_gdelt = enable_gdelt
        self._stop = threading.Event()

    def stop(self):
        self._stop.set()

    def run(self):
        log.info("Refresher started interval_s=%s", self.interval_s)
        try:
            info = refresh(self.conn, enable_google=self.enable_google, enable_gdelt=self.enable_gdelt)
            log.info("Refresh complete %s", info)
        except Exception as e:
            log.exception("Initial refresh failed: %s", e)

        while not self._stop.is_set():
            time.sleep(self.interval_s)
            if self._stop.is_set():
                break
            try:
                info = refresh(self.conn, enable_google=self.enable_google, enable_gdelt=self.enable_gdelt)
                log.info("Refresh complete %s", info)
            except Exception as e:
                log.exception("Refresh failed: %s", e)
