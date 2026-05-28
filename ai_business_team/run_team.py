#!/usr/bin/env python3
"""
Continuous runner — keeps the AI business team working around the clock.
Run as a background process or with PM2 / systemd / supervisor.

  python run_team.py
  pm2 start run_team.py --interpreter python3 --name ai-business-team
"""
import os
import sys
import time
import signal
import logging
from pathlib import Path
from datetime import datetime

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

logging.basicConfig(
    level=getattr(logging, os.getenv("LOG_LEVEL", "INFO")),
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler("team.log"),
        logging.StreamHandler()
    ]
)
log = logging.getLogger("ai_business_team")

CYCLE_HOURS = float(os.getenv("CYCLE_INTERVAL_HOURS", "1"))
CYCLE_SECONDS = int(CYCLE_HOURS * 3600)
_running = True


def _handle_signal(sig, frame):
    global _running
    log.info("Shutdown signal received — will stop after current cycle.")
    _running = False

signal.signal(signal.SIGINT, _handle_signal)
signal.signal(signal.SIGTERM, _handle_signal)


def main():
    sys.path.insert(0, str(Path(__file__).parent))
    from main import build_team

    log.info("=" * 60)
    log.info("AI Business Team starting")
    log.info(f"Cycle interval: {CYCLE_HOURS}h ({CYCLE_SECONDS}s)")
    log.info("=" * 60)

    orchestrator, agents, state, bus = build_team()
    cycle = 0

    while _running:
        cycle += 1
        log.info(f"--- Cycle #{cycle} start ---")
        try:
            result = orchestrator.run_cycle()
            log.info(f"Cycle #{cycle} complete.")
            log.info(result[:500])
        except Exception as exc:
            log.error(f"Cycle #{cycle} failed: {exc}", exc_info=True)

        if _running:
            wake_at = datetime.fromtimestamp(time.time() + CYCLE_SECONDS)
            log.info(f"Next cycle at {wake_at.strftime('%Y-%m-%d %H:%M:%S')}")
            # Sleep in small chunks so signals are handled promptly
            for _ in range(CYCLE_SECONDS):
                if not _running:
                    break
                time.sleep(1)

    log.info("AI Business Team shut down.")


if __name__ == "__main__":
    main()
