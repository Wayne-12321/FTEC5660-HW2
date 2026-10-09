"""Run the unchanged assignment CLI and retain independently measured results."""

import argparse
import csv
import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--runs", type=int, default=3)
    parser.add_argument("--part", choices=["public", "attack", "both"], default="both")
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    output = root / "validation"
    output.mkdir(exist_ok=True)
    parts = ["public", "attack"] if args.part == "both" else [args.part]
    records = []
    for part in parts:
        for number in range(1, args.runs + 1):
            label = f"{part}_run_{number}"
            environment = os.environ.copy()
            environment["HW2_AUDIT_DIR"] = str(output / label)
            start = time.monotonic()
            process = subprocess.run(
                [sys.executable, "hw2.py", "--cv-folder",
                 "public_test" if part == "public" else "task2"],
                cwd=root, env=environment, capture_output=True, text=True, timeout=1800,
            )
            elapsed = round(time.monotonic() - start, 2)
            # The program only logs exception classes, never credentials.
            (output / f"{label}.log").write_text(process.stdout + process.stderr)
            print(label, "exit:", process.returncode, "seconds:", elapsed, flush=True)
            print(process.stdout.strip(), flush=True)
            if process.returncode:
                print("Run failed. See its validation log.", flush=True)
                return process.returncode
            shutil.copyfile(root / "results.csv", output / f"{label}.csv")
            with (root / "results.csv").open() as handle:
                rows = list(csv.DictReader(handle))
            record = {"run": label, "elapsed_seconds": elapsed, "rows": rows,
                      "correct": sum(r["correctness"] == "correct" for r in rows),
                      "total": len(rows)}
            records.append(record)
            (output / "summary.json").write_text(json.dumps(records, indent=2))
    # Keep the required top-level results.csv as the last public-test result.
    public_runs = sorted(output.glob("public_run_*.csv"))
    if public_runs:
        shutil.copyfile(public_runs[-1], root / "results.csv")
    print("Validation records saved under validation/.", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
