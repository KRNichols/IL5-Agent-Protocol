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
HIGH_META = ROOT / "il5-scanner" / "banks" / "production-high-53a-questions.meta.json"
SOURCE = ROOT / "il5-scanner" / "banks" / "SOURCE.json"
PROVENANCE = ROOT / "il5-scanner" / "banks" / "PROVENANCE.md"
OVERLAY = ROOT / "question-bank" / "il5-overlay-hooks.json"
IDS = ROOT / "question-bank" / "fedramp-high-class-d.ids.txt"
TWINS = (ROOT / "AGENTS.md", ROOT / "AGENTS.perfect.md")
KEYS = ROOT / "KEYS.md"
RUN = ROOT / "RUN.md"
NIST_CMP = ROOT / "il5-scanner" / "banks" / "nist-800-53b-high-53a-questions.jsonl"

FEDRAMP_ONLY = {
    "ac-2.7",
    "ca-8.2",
    "ia-5.7",
    "ir-9",
    "sa-9.5",
    "sa-11.1",
    "sc-45",
    "sc-45.1",
}


def run(argv: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(argv, cwd=ROOT, text=True, capture_output=True)


def _high_meta() -> dict:
    return json.loads(HIGH_META.read_text(encoding="utf-8"))


def _source() -> dict:
    return json.loads(SOURCE.read_text(encoding="utf-8"))


def test_twins_identical() -> None:
    a, b = TWINS
    assert a.read_text(encoding="utf-8") == b.read_text(encoding="utf-8"), "AGENTS twins drifted"


def test_three_intake_no_buyer() -> None:
    agents = (ROOT / "AGENTS.md").read_text(encoding="utf-8")
    assert "three answers" in agents
    assert "Don't quiz past the three intake questions." in agents
    assert "BUYER:" not in agents
    assert "1. Target stack:" in agents
    assert "Buyer path" not in agents


def test_keys_gate() -> None:
    text = KEYS.read_text(encoding="utf-8")
    assert "READY" in text
    assert "never" in text.lower()
    assert "ATO" in text
    assert "High alone" in text and "HOLD" in text
    assert "FedRAMP High slice only" in text
    assert "DISA PA" in text
    assert "FedRAMP High" in text


def test_run_md_on_main() -> None:
    text = RUN.read_text(encoding="utf-8")
    assert "until this PR lands" not in text.lower()
    assert "Until **this** PR" not in text
    assert "KEYS.md" in text
    assert "4238" in text


def test_high_bank_is_fedramp_high() -> None:
    meta = _high_meta()
    src = _source()
    n = sum(1 for line in HIGH_BANK.read_text(encoding="utf-8").splitlines() if line.strip())
    assert n == meta["question_count"], f"HIGH bank/meta mismatch: {n} vs {meta['question_count']}"
    assert n == 4238, f"FedRAMP High bank count unexpected: {n}"
    assert meta["catalog_controls_emitted"] == 410
    assert src["high_bank"]["baseline"] == "FedRAMP-HIGH-CLASS-D"
    assert src["high_bank"]["is_default_grade_path"] is True
    assert src["high_bank"]["not_fedramp_appendix_a"] is False
    assert src["nist_53b_high_comparison_bank"]["is_default_grade_path"] is False
    assert src["nist_53b_high_comparison_bank"]["not_fedramp_appendix_a"] is True
    assert src["nist_53b_high_is_not_fedramp_high"] is True
    assert src["high_alone_fails_il5"] is True
    assert "FedRAMP High" in (meta.get("baseline") or "")
    ids = [
        line.strip()
        for line in IDS.read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.startswith("#")
    ]
    assert len(ids) == 410, f"official ID list drifted: {len(ids)}"
    idset = set(ids)
    for cid in FEDRAMP_ONLY:
        assert cid in idset, f"FedRAMP-only ID missing from profile extract: {cid}"
    nist_n = sum(1 for line in NIST_CMP.read_text(encoding="utf-8").splitlines() if line.strip())
    assert nist_n == 4003
    assert src["baseline_diff"]["question_delta_fedramp_minus_nist53b"] == 235


def test_provenance_cites_official() -> None:
    text = PROVENANCE.read_text(encoding="utf-8")
    src = _source()
    assert "410" in text and "4238" in text
    assert "370" in text and "4003" in text
    assert "usnistgov/oscal-content" in text
    assert "OSCAL-Foundation/fedramp-resources" in text
    assert "fedramp.gov/2026/reference/fedramp-certification" in text
    assert "csrc.nist.gov/pubs/sp/800/53/a/r5/final" in text
    assert src["sources"][1]["id_count"] == 410
    assert src["sources"][1]["url"].endswith("FedRAMP_rev5_HIGH-baseline_profile.json")


def test_overlay_exhaustive_hooks() -> None:
    doc = json.loads(OVERLAY.read_text(encoding="utf-8"))
    rows = doc.get("rows") or []
    assert len(rows) >= 80, f"IL5 overlay still a stub: {len(rows)}"
    layers = {r.get("layer") for r in rows}
    assert {"FedRAMP+", "SRG", "CNSSI"} <= layers
    oids = {r.get("objective_id") for r in rows}
    assert "ac-7_dspav_cite" in oids
    assert "ia-2.12_cac_piv" in oids
    assert "sc-13_fips_140-3" in oids
    assert "sa-9.5_us_location" in oids
    assert "ia-2_cnssi_nss" in oids
    assert "pl-2_ssp_appendices" in oids
    assert doc.get("not_an_official_control_count") is True


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
        assert summary["bank_question_rows"] == 4238
        assert summary["tallies"].get("PASS", 0) == 0
        assert summary["in_scope"] >= 4238
        grade = (out / "GRADE.md").read_text(encoding="utf-8")
        assert grade.startswith("GRADE: HOLD")
        assert "QUESTIONS:" in grade
        assert "FedRAMP High / Class D" in grade
        assert "NIST 800-53B HIGH (4003" not in grade


def main() -> int:
    tests = [
        test_twins_identical,
        test_three_intake_no_buyer,
        test_keys_gate,
        test_run_md_on_main,
        test_high_bank_is_fedramp_high,
        test_provenance_cites_official,
        test_overlay_exhaustive_hooks,
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
