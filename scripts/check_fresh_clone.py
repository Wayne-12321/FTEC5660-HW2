"""Test a clean checkout with no .env, cache, audit, or preexisting results."""

import csv
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    parent = Path(tempfile.mkdtemp(prefix="hw2-clean-"))
    checkout = parent / "FTEC5660-HW2"
    subprocess.run(["git", "clone", "--quiet", "--no-hardlinks", str(root), str(checkout)], check=True)
    # Overlay the final submission onto the original starter's clean checkout.
    # Nothing from the working environment is copied into this checkout.
    for name in ("hw2.py", "requirements.txt", "requirements-lock.txt", "README.md", ".gitignore",
                 ".env.example", "reflection.md"):
        shutil.copyfile(root / name, checkout / name)
    shutil.copyfile(root / "task2/adversarial_cv.pdf", checkout / "task2/adversarial_cv.pdf")
    subprocess.run([sys.executable, "-m", "venv", str(checkout / ".venv")], check=True)
    python = checkout / ".venv/bin/python"
    start = time.monotonic()
    installation = subprocess.run([str(python), "-m", "pip", "install", "-r", "requirements.txt"],
                                  cwd=checkout, capture_output=True, text=True, timeout=1200)
    if installation.returncode:
        print("Fresh environment dependency installation failed.")
        return 1
    environment = os.environ.copy()
    # Supply a key through the environment, as a grader would; never copy .env.
    for line in (root / ".env").read_text().splitlines():
        if "=" in line and not line.lstrip().startswith("#"):
            key, value = line.split("=", 1)
            environment.setdefault(key.strip(), value.strip().strip("\"'"))
    environment.pop("HW2_AUDIT_DIR", None)
    run_start = time.monotonic()
    process = subprocess.run([str(python), "hw2.py", "--cv-folder", "public_test"],
                             cwd=checkout, env=environment, capture_output=True,
                             text=True, timeout=1800)
    elapsed = round(time.monotonic() - run_start, 2)
    rows = []
    if process.returncode == 0:
        with (checkout / "results.csv").open() as handle:
            rows = list(csv.DictReader(handle))
    record = {"exit_code": process.returncode, "run_seconds": elapsed,
              "install_and_run_seconds": round(time.monotonic() - start, 2),
              "env_file_present": (checkout / ".env").exists(),
              "initial_results_present": False, "rows": rows,
              "correct": sum(r["correctness"] == "correct" for r in rows), "total": len(rows)}
    output = root / "validation"
    (output / "fresh_clone.json").write_text(json.dumps(record, indent=2))
    (output / "fresh_clone.log").write_text(process.stdout + process.stderr)
    if process.returncode == 0:
        shutil.copyfile(checkout / "results.csv", output / "fresh_clone.csv")
    print(process.stdout.strip())
    print("Fresh clone check:", json.dumps({k: v for k, v in record.items() if k != "rows"}))
    print("Temporary checkout:", checkout)
    return process.returncode


if __name__ == "__main__":
    raise SystemExit(main())
