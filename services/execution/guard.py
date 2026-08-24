"""Execution safety gate.

Live execution is fail-closed. This module does not submit transactions.
"""

import os


class ExecutionDisabled(RuntimeError):
    pass


def assert_execution_allowed() -> None:
    read_only = os.getenv("READ_ONLY_MODE", "true").lower() == "true"
    execution = os.getenv("EXECUTION_ENABLED", "false").lower() == "true"
    if read_only or not execution:
        raise ExecutionDisabled("Live execution is disabled; use paper trading until separately authorized.")
