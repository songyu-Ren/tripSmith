from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
from pathlib import Path


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def _setup_path() -> None:
    api_dir = _repo_root() / "apps" / "api"
    sys.path.insert(0, str(api_dir))


def _checksum(obj: object) -> str:
    raw = json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("run_id")
    args = parser.parse_args()

    _setup_path()

    from tripsmith.core.db import SessionLocal
    from tripsmith.models.agent_run import AgentRun

    db = SessionLocal()
    try:
        run = db.query(AgentRun).filter(AgentRun.id == args.run_id).first()
        if not run:
            print("run not found", file=sys.stderr)
            return 2

        tool_calls = run.tool_calls_json or []
        output = run.output_json or {}

        print(json.dumps({"run_id": run.id, "trip_id": run.trip_id, "phase": run.phase, "created_at": run.created_at.isoformat()}, ensure_ascii=False))
        print(json.dumps({"tool_calls_checksum": _checksum(tool_calls), "output_checksum": _checksum(output)}, ensure_ascii=False))
        if os.getenv("PRINT_TOOL_CALLS", "0") == "1":
            print(json.dumps({"tool_calls": tool_calls}, ensure_ascii=False))
        return 0
    finally:
        db.close()


if __name__ == "__main__":
    raise SystemExit(main())

