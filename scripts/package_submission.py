"""Create a secret-free, portable English submission archive."""

import hashlib
import json
import subprocess
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    marker = "# Everything below is provided runner/scoring code. No edits are needed."
    original = subprocess.check_output(["git", "show", "HEAD:hw2.py"], cwd=ROOT, text=True)
    current = (ROOT / "hw2.py").read_text()
    assert original.split(marker, 1)[1] == current.split(marker, 1)[1], "Starter runner was modified"
    records = json.loads((ROOT / "validation/summary.json").read_text())
    assert len([r for r in records if r["run"].startswith("public")]) == 3
    assert len([r for r in records if r["run"].startswith("attack")]) == 3
    for record in records:
        assert record["elapsed_seconds"] < 1800
        assert all(0 <= float(row["score"]) <= 1 for row in record["rows"])
    fresh = json.loads((ROOT / "validation/fresh_clone.json").read_text())
    assert fresh["exit_code"] == 0 and fresh["total"] == 7 and not fresh["env_file_present"]

    tests = subprocess.run([str(ROOT / ".venv/bin/python"), "-m", "unittest", "discover",
                            "-s", "tests", "-v"], cwd=ROOT, capture_output=True, text=True, check=True)
    (ROOT / "validation/unit_tests.log").write_text(tests.stdout + tests.stderr)
    tracked = ["hw2.py", "requirements.txt", "requirements-lock.txt", "README.md",
               "reflection.md", ".env.example", ".gitignore", "results.csv"]
    files = [ROOT / name for name in tracked]
    for folder in ("public_test", "task2", "output/pdf", "scripts", "tests", "validation"):
        files.extend(p for p in (ROOT / folder).rglob("*")
                     if p.is_file() and "__pycache__" not in p.parts
                     and p.suffix != ".pyc" and p.name not in {".DS_Store", "submission_manifest.json"})
    files = sorted(set(files))
    key = None
    for line in (ROOT / ".env").read_text().splitlines():
        if line.startswith("DEEPSEEK_API_KEY="):
            key = line.split("=", 1)[1].strip().strip("\"'").encode()
    assert key, "Local secret-scan reference missing"
    for path in files:
        assert key not in path.read_bytes(), f"Credential found in deliverable: {path.name}"
    manifest = {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in files}
    (ROOT / "validation/submission_manifest.json").write_text(json.dumps(manifest, indent=2))
    files.append(ROOT / "validation/submission_manifest.json")
    output = ROOT.parent / "FTEC5660-HW2_English_Submission.zip"
    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for path in files:
            archive.write(path, str(Path("FTEC5660-HW2") / path.relative_to(ROOT)))
    with zipfile.ZipFile(output) as archive:
        assert archive.testzip() is None
        assert not any(Path(name).name == ".env" or ".venv" in Path(name).parts
                       or ".git" in Path(name).parts for name in archive.namelist())
        assert all(key not in archive.read(name) for name in archive.namelist())
    print("Submission archive:", output)
    print("Files:", len(files))
    print("Archive bytes:", output.stat().st_size)
    print("Credential scan: passed; starter runner unchanged; ZIP integrity passed.")


if __name__ == "__main__":
    main()
