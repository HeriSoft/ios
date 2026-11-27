"""Điểm vào: `python -m app_builder` (GUI) | `python -m app_builder doctor [--json]`."""
from __future__ import annotations

import argparse
import json
import sys


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    parser = argparse.ArgumentParser(prog="app_builder", description="App Builder AI")
    sub = parser.add_subparsers(dest="cmd")
    d = sub.add_parser("doctor", help="Kiểm tra công cụ trên máy")
    d.add_argument("--json", action="store_true")
    args, rest = parser.parse_known_args(argv)

    if args.cmd == "doctor":
        if hasattr(sys.stdout, "reconfigure"):
            sys.stdout.reconfigure(encoding="utf-8")
        from app_builder.core.config import load_settings
        from app_builder.services.doctor import format_report, run_doctor

        s = load_settings()
        checks = run_doctor(s.tool_paths, s.workspace_dir)
        if args.json:
            print(json.dumps([c.to_dict() for c in checks], ensure_ascii=False, indent=2))
        else:
            print(format_report(checks))
        return 0

    from app_builder.bootstrap import run_gui
    return run_gui([sys.argv[0], *rest])


if __name__ == "__main__":
    sys.exit(main())
