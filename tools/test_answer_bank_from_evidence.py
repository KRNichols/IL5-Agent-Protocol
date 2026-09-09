#!/usr/bin/env python3
"""Unit checks for the evidence answerer. Never requires a live host."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ANSWERER = ROOT / "tools" / "answer_bank_from_evidence.py"
COLLECTOR = ROOT / "tools" / "collect_neo4j_ec2_evidence.sh"
FIXTURE_EV = ROOT / "fixtures" / "neo4j-ec2-evidence"
FIXTURE_BANK = ROOT / "fixtures" / "question-bank" / "tiny-question-bank.jsonl"
HIGH_BANK = ROOT / "il5-scanner" / "banks" / "production-high-53a-questions.jsonl"
TWINS = (ROOT / "AGENTS.md", ROOT / "AGENTS.perfect.md")


def run(argv: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(argv, cwd=ROOT, text=True, capture_output=True)


def test_twins_identical() -> None:
    a, b = TWINS
    assert a.read_text(encoding="utf-8") == b.read_text(encoding="utf-8"), "AGENTS twins drifted"


def test_high_bank_count() -> None:
    n = sum(1 for line in HIGH_BANK.read_text(encoding="utf-8").splitlines() if line.strip())
    assert n == 4003, f"HIGH bank shrank or grew: {n}"


def test_empty_evidence_all_missing_no_pass() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        ev = Path(tmp) / "empty"
        ev.mkdir()
        out = Path(tmp) / "out"
        proc = run(
            [
                sys.executable,
                str(ANSWERER),
                "--bank",
                str(FIXTURE_BANK),
                "--allow-fixture-bank",
                "--evidence",
                str(ev),
                "--path",
                "IL5 non-NSS",
                "--out-dir",
                str(out),
            ]
        )
        assert proc.returncode == 0, proc.stderr
        summary = json.loads((out / "SUMMARY.json").read_text(encoding="utf-8"))
        assert summary["tallies"].get("PASS", 0) == 0
        assert summary["pass_emitted"] == 0
        assert summary["grade"] == "HOLD"
        answers = [
            json.loads(line)
            for line in (out / "answers.jsonl").read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]
        in_scope = [r for r in answers if r["verdict"] != "N/A"]
        assert in_scope, "expected in-scope fixture questions"
        assert all(r["verdict"] == "MISSING" for r in in_scope)
        assert "GRADE:" in (out / "GRADE.md").read_text(encoding="utf-8")


def test_fixture_evidence_hold_never_pass() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp) / "out"
        proc = run(
            [
                sys.executable,
                str(ANSWERER),
                "--bank",
                str(FIXTURE_BANK),
                "--allow-fixture-bank",
                "--evidence",
                str(FIXTURE_EV),
                "--path",
                "IL5 non-NSS",
                "--out-dir",
                str(out),
            ]
        )
        assert proc.returncode == 0, proc.stderr
        summary = json.loads((out / "SUMMARY.json").read_text(encoding="utf-8"))
        assert summary["tallies"].get("PASS", 0) == 0
        assert summary["tallies"].get("HOLD", 0) >= 1
        changes = (out / "CONFIG-CHANGES.md").read_text(encoding="utf-8")
        assert "current:" in changes
        assert "required:" in changes
        assert "auth_enabled=false" in changes or "auth_enabled" in changes


def test_refuses_fixture_bank_without_flag() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        ev = Path(tmp) / "e"
        ev.mkdir()
        proc = run(
            [
                sys.executable,
                str(ANSWERER),
                "--bank",
                str(FIXTURE_BANK),
                "--evidence",
                str(ev),
                "--path",
                "FedRAMP High",
            ]
        )
        assert proc.returncode != 0
        assert "fixture" in (proc.stderr + proc.stdout).lower()


def test_collector_local_root() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        dest = Path(tmp) / "run"
        proc = run(
            [
                "bash",
                str(COLLECTOR),
                "--run-id",
                "unit",
                "--out",
                str(dest),
                "--local-root",
                str(FIXTURE_EV),
                "--skip-aws",
            ]
        )
        assert proc.returncode == 0, proc.stderr + proc.stdout
        assert (dest / "MANIFEST.json").exists()
        assert (dest / "neo4j" / "neo4j.conf").exists() or (dest / "neo4j" / "neo4j.conf.redacted").exists()
        manifest = json.loads((dest / "MANIFEST.json").read_text(encoding="utf-8"))
        assert manifest["graph_dump"] is False
        assert manifest["never_ato"] is True


def test_high_bank_answerer_no_pass() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp) / "out"
        proc = run(
            [
                sys.executable,
                str(ANSWERER),
                "--evidence",
                str(FIXTURE_EV),
                "--path",
                "IL5 non-NSS",
                "--out-dir",
                str(out),
            ]
        )
        assert proc.returncode == 0, proc.stderr
        summary = json.loads((out / "SUMMARY.json").read_text(encoding="utf-8"))
        assert summary["bank_question_rows"] == 4003
        assert summary["tallies"].get("PASS", 0) == 0
        assert summary["in_scope"] >= 4003
        grade = (out / "GRADE.md").read_text(encoding="utf-8")
        assert grade.startswith("GRADE: HOLD")
        assert "QUESTIONS:" in grade


def main() -> int:
    tests = [
        test_twins_identical,
        test_high_bank_count,
        test_empty_evidence_all_missing_no_pass,
        test_fixture_evidence_hold_never_pass,
        test_refuses_fixture_bank_without_flag,
        test_collector_local_root,
        test_high_bank_answerer_no_pass,
    ]
    failed = 0
    for fn in tests:
        try:
            fn()
            print(f"PASS {fn.__name__}")
        except Exception as exc:  # noqa: BLE001 — test runner
            failed += 1
            print(f"FAIL {fn.__name__}: {exc}")
    if failed:
        print(f"{failed} failed")
        return 1
    print("all passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
