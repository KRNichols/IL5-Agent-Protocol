#!/usr/bin/env python3
"""Fetch official catalogs and build the production FedRAMP High / Class D bank.

Preferred one-command rebuild (HIGH + NIST-53B comparison + FULL + overlay):
  python3 tools/generate_production_banks.py

This script remains the FedRAMP High / Class D ID-filter builder used by
that command and by operators who only want question-bank/ Class D artifacts.

Uses:
  - NIST SP 800-53 Rev 5 + 800-53A Rev 5 OSCAL catalog (assessment procedures)
  - FedRAMP Rev 5 High Baseline OSCAL profile (Class D ID list)

Does not invent C/CE counts. The High ID count is whatever the official
profile contains. Question count is synthesized 53A rows, not a control count.

DoD SSP Addendum / CNSSI files are attached as overlay hooks when present;
cyber.mil is login-walled and is recorded as not-fetched.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def _rel(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(ROOT))
    except ValueError:
        return str(path)
if str(ROOT / "tools") not in sys.path:
    sys.path.insert(0, str(ROOT / "tools"))

import synthesize_questions as syn  # noqa: E402

NIST_CATALOG = syn.NIST_OSCAL_CATALOG_MIN
FEDRAMP_HIGH_PROFILE = (
    "https://raw.githubusercontent.com/OSCAL-Foundation/fedramp-resources/main/"
    "baselines/rev5/json/FedRAMP_rev5_HIGH-baseline_profile.json"
)
FEDRAMP_HIGH_RESOLVED = (
    "https://raw.githubusercontent.com/OSCAL-Foundation/fedramp-resources/main/"
    "baselines/rev5/json/FedRAMP_rev5_HIGH-baseline-resolved-profile_catalog.json"
)
NIST_53B_HIGH_PROFILE = syn.NIST_OSCAL_HIGH_PROFILE
FEDRAMP_CERT = "https://fedramp.gov/2026/reference/fedramp-certification/"
FEDRAMP_CONTROLS = "https://fedramp.gov/2026/reference/controls/"
CYBER_MIL = "https://public.cyber.mil/dccs/dccs-documents/"


def write_id_list(profile_path: Path, dest: Path, fetched_at: str) -> dict:
    ids, label = syn.load_baseline_ids(profile_path)
    doc = syn.load_json(profile_path)
    meta = (doc.get("profile") or {}).get("metadata") or {}
    ordered = []
    for imp in (doc.get("profile") or {}).get("imports") or []:
        for block in imp.get("include-controls") or []:
            ordered.extend(block.get("with-ids") or [])
    if not ordered:
        ordered = sorted(ids)
    lines = [
        "# SOURCE: extracted from official FedRAMP Rev 5 High Baseline OSCAL profile",
        f"# url: {FEDRAMP_HIGH_PROFILE}",
        f"# title: {meta.get('title')}",
        f"# version: {meta.get('version')}",
        f"# last-modified: {meta.get('last-modified')}",
        f"# published: {meta.get('published')}",
        f"# fetched_at: {fetched_at}",
        f"# id_count: {len(ordered)}  (count of with-ids in this official profile; not invented)",
        "# Class D = FedRAMP High (FedRAMP Consolidated Rules 2026).",
        "# This is NOT NIST SP 800-53B HIGH.",
        "# Re-download SSP Appendix A High / this profile before freezing a baseline.",
        "",
    ]
    lines.extend(ordered)
    dest.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return {
        "label": label,
        "id_count": len(ordered),
        "title": meta.get("title"),
        "version": meta.get("version"),
        "last_modified": meta.get("last-modified"),
        "path": str(dest),
    }


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Build the production FedRAMP High / Class D question bank")
    p.add_argument(
        "--out-dir",
        type=Path,
        default=ROOT / "question-bank",
        help="Directory for production artifacts (default: question-bank/)",
    )
    p.add_argument(
        "--work-dir",
        type=Path,
        default=ROOT / "question-bank" / "raw",
        help="Where to store fetched official catalogs (gitignored).",
    )
    p.add_argument(
        "--skip-fetch",
        action="store_true",
        help="Reuse files already in --work-dir.",
    )
    args = p.parse_args(argv)

    fetched_at = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    out_dir: Path = args.out_dir
    work: Path = args.work_dir
    out_dir.mkdir(parents=True, exist_ok=True)
    work.mkdir(parents=True, exist_ok=True)

    catalog_path = work / "NIST_SP-800-53_rev5_catalog-min.json"
    profile_path = work / "FedRAMP_rev5_HIGH-baseline_profile.json"
    nist_high_path = work / "NIST_SP-800-53_rev5_HIGH-baseline_profile.json"
    overlay_path = out_dir / "il5-overlay-hooks.json"

    if not args.skip_fetch or not catalog_path.exists():
        syn.fetch_url(NIST_CATALOG, catalog_path)
    if not args.skip_fetch or not profile_path.exists():
        syn.fetch_url(FEDRAMP_HIGH_PROFILE, profile_path)
    if not args.skip_fetch or not nist_high_path.exists():
        try:
            syn.fetch_url(NIST_53B_HIGH_PROFILE, nist_high_path)
        except SystemExit:
            syn.warn("NIST 800-53B HIGH profile fetch failed; comparison omitted")

    id_info = write_id_list(profile_path, out_dir / "fedramp-high-class-d.ids.txt", fetched_at)

    nist_high_count = None
    if nist_high_path.exists():
        nist_ids, _ = syn.load_baseline_ids(nist_high_path)
        nist_high_count = len(nist_ids)
        if nist_high_count != id_info["id_count"]:
            syn.warn(
                f"NIST SP 800-53B HIGH has {nist_high_count} IDs; "
                f"FedRAMP High / Class D profile has {id_info['id_count']} IDs. "
                "They are different sets. Production bank uses FedRAMP High."
            )

    bank_path = out_dir / "fedramp-high-class-d.questions.jsonl"
    meta_path = out_dir / "fedramp-high-class-d.meta.json"
    overlays = [overlay_path] if overlay_path.exists() else []

    argv_syn = [
        "--catalog",
        str(catalog_path),
        "--baseline",
        str(profile_path),
        "--format",
        "jsonl",
        "--out",
        str(bank_path),
        "--meta-out",
        str(meta_path),
    ]
    for ov in overlays:
        argv_syn.extend(["--overlay", str(ov)])
    rc = syn.main(argv_syn)
    if rc != 0:
        return rc

    meta = json.loads(meta_path.read_text(encoding="utf-8")) if meta_path.exists() else {}
    source = {
        "generated_from_catalog": True,
        "production": True,
        "fetched_at": fetched_at,
        "question_count": meta.get("question_count"),
        "fedramp_high_class_d_ids_from_official_profile": id_info["id_count"],
        "nist_sp_800_53b_high_ids": nist_high_count,
        "nist_53b_high_is_not_fedramp_high": True,
        "question_count_is_not_a_control_count": True,
        "class_d_equals_fedramp_high": True,
        "high_alone_fails_il5": True,
        "sources": [
            {
                "role": "NIST SP 800-53 Rev 5 + SP 800-53A Rev 5 assessment procedures",
                "url": NIST_CATALOG,
                "also": syn.NIST_OSCAL_CATALOG,
                "csrc": "https://csrc.nist.gov/pubs/sp/800/53/a/r5/final",
                "local": _rel(catalog_path),
            },
            {
                "role": "FedRAMP Rev 5 High / Class D ID list (OSCAL profile)",
                "url": FEDRAMP_HIGH_PROFILE,
                "resolved_catalog": FEDRAMP_HIGH_RESOLVED,
                "fedramp_certification": FEDRAMP_CERT,
                "fedramp_controls": FEDRAMP_CONTROLS,
                "title": id_info["title"],
                "version": id_info["version"],
                "last_modified": id_info["last_modified"],
                "id_count": id_info["id_count"],
                "local_ids": _rel(Path(id_info["path"])),
            },
            {
                "role": "NIST SP 800-53B HIGH profile (comparison only; NOT FedRAMP High)",
                "url": NIST_53B_HIGH_PROFILE,
                "id_count": nist_high_count,
            },
            {
                "role": "DoD FedRAMP+ / SSP Addendum / SRG (not fetched — login wall)",
                "url": CYBER_MIL,
                "fetched": False,
                "overlay_hooks": _rel(overlay_path) if overlay_path.exists() else None,
            },
            {
                "role": "CNSSI 1253 NSS overlays (not fetched as a catalog)",
                "url": "https://www.cnss.gov/CNSS/issuances/Instructions.cfm",
                "fetched": False,
            },
        ],
        "artifacts": {
            "questions": _rel(bank_path),
            "meta": _rel(meta_path),
            "ids": _rel(Path(id_info["path"])),
            "overlay_hooks": _rel(overlay_path) if overlay_path.exists() else None,
        },
    }
    source_path = out_dir / "SOURCE.json"
    source_path.write_text(json.dumps(source, indent=2) + "\n", encoding="utf-8")
    print(
        f"PRODUCTION bank: {meta.get('question_count')} questions "
        f"from {id_info['id_count']} FedRAMP High / Class D IDs "
        f"(official profile) + overlay hooks. See {source_path}",
        file=sys.stderr,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
