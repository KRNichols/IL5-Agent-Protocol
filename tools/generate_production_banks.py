#!/usr/bin/env python3
"""Generate production HIGH + FULL 800-53A question banks.

HIGH bank: NIST SP 800-53 HIGH-baseline-resolved-profile catalog
(NIST SP 800-53B HIGH — not FedRAMP Appendix A / Class D).
FULL bank: entire NIST SP 800-53/53A catalog (max size).

Methods are only those published on each control (no invented Test/Interview).
"""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import synthesize_questions as syn  # noqa: E402

NIST_HIGH_RESOLVED = syn.NIST_OSCAL_HIGH_RESOLVED
NIST_FULL = syn.NIST_OSCAL_CATALOG_MIN


def rel(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(ROOT))
    except ValueError:
        return str(path)


def generate(catalog: Path, dest: Path, meta_dest: Path, overlay: Path | None) -> dict:
    argv = [
        "--catalog",
        str(catalog),
        "--format",
        "jsonl",
        "--out",
        str(dest),
        "--meta-out",
        str(meta_dest),
    ]
    if overlay and overlay.exists():
        argv.extend(["--overlay", str(overlay)])
    rc = syn.main(argv)
    if rc != 0:
        raise SystemExit(rc)
    return json.loads(meta_dest.read_text(encoding="utf-8"))


def main() -> int:
    fetched_at = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    raw = ROOT / "question-bank" / "raw"
    banks = ROOT / "il5-scanner" / "banks"
    raw.mkdir(parents=True, exist_ok=True)
    banks.mkdir(parents=True, exist_ok=True)

    high_cat = raw / "NIST_SP-800-53_rev5_HIGH-baseline-resolved-profile_catalog-min.json"
    full_cat = raw / "NIST_SP-800-53_rev5_catalog-min.json"
    if not high_cat.exists():
        syn.fetch_url(NIST_HIGH_RESOLVED, high_cat)
    if not full_cat.exists():
        syn.fetch_url(NIST_FULL, full_cat)

    overlay = ROOT / "question-bank" / "il5-overlay-hooks.json"

    high_q = banks / "production-high-53a-questions.jsonl"
    high_m = banks / "production-high-53a-questions.meta.json"
    # HIGH bank is the 53A objectives only (orchestrator 4003). Overlay is separate.
    high_meta = generate(high_cat, high_q, high_m, overlay=None)

    full_q = banks / "production-full-53a-questions.jsonl"
    full_m = banks / "production-full-53a-questions.meta.json"
    full_meta = generate(full_cat, full_q, full_m, overlay=None)

    # Also copy HIGH into question-bank/ as the production High path
    prod_high = ROOT / "question-bank" / "nist-800-53b-high.questions.jsonl"
    prod_high.write_bytes(high_q.read_bytes())
    (ROOT / "question-bank" / "nist-800-53b-high.meta.json").write_text(
        json.dumps(high_meta, indent=2) + "\n", encoding="utf-8"
    )

    source = {
        "generated_from_catalog": True,
        "production": True,
        "fetched_at": fetched_at,
        "high_bank": {
            "path": rel(high_q),
            "question_count": high_meta.get("question_count"),
            "catalog_controls_emitted": high_meta.get("catalog_controls_emitted"),
            "baseline": "NIST-800-53B-HIGH",
            "not_fedramp_appendix_a": True,
            "catalog": NIST_HIGH_RESOLVED,
            "label": "NIST SP 800-53 HIGH-baseline-resolved-profile catalog (includes 800-53A). Not FedRAMP High / Class D.",
        },
        "full_bank": {
            "path": rel(full_q),
            "question_count": full_meta.get("question_count"),
            "catalog_controls_emitted": full_meta.get("catalog_controls_emitted"),
            "baseline": "NIST-SP-800-53-REV5-FULL-CATALOG",
            "catalog": NIST_FULL,
            "label": "Entire NIST SP 800-53/53A catalog. Not a baseline. Max-size bank.",
        },
        "question_count_is_not_a_control_count": True,
        "high_alone_fails_il5": True,
        "overlay_hooks": rel(overlay) if overlay.exists() else None,
    }
    (banks / "SOURCE.json").write_text(json.dumps(source, indent=2) + "\n", encoding="utf-8")
    (ROOT / "question-bank" / "NIST-HIGH-SOURCE.json").write_text(
        json.dumps(source, indent=2) + "\n", encoding="utf-8"
    )
    print(
        f"HIGH {high_meta.get('question_count')} questions from "
        f"{high_meta.get('catalog_controls_emitted')} controls — {high_q}",
        file=sys.stderr,
    )
    print(
        f"FULL {full_meta.get('question_count')} questions from "
        f"{full_meta.get('catalog_controls_emitted')} controls — {full_q}",
        file=sys.stderr,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
