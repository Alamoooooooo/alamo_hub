#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import shutil
from dataclasses import dataclass
from pathlib import Path


REPO_SKILLS_DIR = Path(__file__).resolve().parents[1]
SYNC_SKILLS = ("github-sync-agent",)


@dataclass
class SyncItem:
    name: str
    source: Path
    destination: Path


def _codex_home() -> Path:
    return Path(os.environ.get("CODEX_HOME") or (Path.home() / ".codex"))


def _sync_plan(dest_root: Path) -> list[SyncItem]:
    items: list[SyncItem] = []
    for name in SYNC_SKILLS:
        items.append(
            SyncItem(
                name=name,
                source=REPO_SKILLS_DIR / name,
                destination=dest_root / name,
            )
        )
    return items


def _copy_skill(source: Path, destination: Path) -> None:
    if destination.exists():
        shutil.rmtree(destination)
    shutil.copytree(source, destination, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))


def main() -> int:
    parser = argparse.ArgumentParser(description="Sync repo-local GitHub sync skills into the Codex skills directory.")
    parser.add_argument("--dest", help="Destination skills directory. Defaults to $CODEX_HOME/skills.")
    parser.add_argument("--dry-run", action="store_true", help="Print the planned sync without copying files.")
    parser.add_argument("--json", action="store_true", help="Print the sync plan as JSON.")
    args = parser.parse_args()

    dest_root = Path(args.dest).expanduser().resolve() if args.dest else (_codex_home() / "skills").resolve()
    plan = _sync_plan(dest_root)

    missing = [item.name for item in plan if not item.source.exists()]
    if missing:
        raise SystemExit(f"Missing source skill directories: {', '.join(missing)}")

    if args.json:
        payload = {
            "destination_root": str(dest_root),
            "dry_run": args.dry_run,
            "skills": [
                {
                    "name": item.name,
                    "source": str(item.source),
                    "destination": str(item.destination),
                }
                for item in plan
            ],
        }
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return 0

    print(f"Destination root: {dest_root}")
    for item in plan:
        print(f"- {item.name}: {item.source} -> {item.destination}")

    if args.dry_run:
        return 0

    dest_root.mkdir(parents=True, exist_ok=True)
    for item in plan:
        _copy_skill(item.source, item.destination)

    print("Sync complete.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
