#!/usr/bin/env python3
"""Generate production question banks.

Default HIGH bank = FedRAMP Rev 5 High / Class D (official OSCAL profile
IDs) × NIST SP 800-53A published Examine/Interview/Test methods.

Also writes:
  - NIST SP 800-53B HIGH comparison bank (NOT FedRAMP High)
  - Full NIST SP 800-53/53A catalog bank (not a baseline)

Does not invent official C/CE counts. Overlay hooks are separate.
"""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import synthesize_questions as syn  # noqa: E402

NIST_FULL = syn.NIST_OSCAL_CATALOG_MIN
NIST_53B_HIGH_PROFILE = syn.NIST_OSCAL_HIGH_PROFILE
NIST_HIGH_RESOLVED = syn.NIST_OSCAL_HIGH_RESOLVED
FEDRAMP_HIGH_PROFILE = syn.FEDRAMP_HIGH_PROFILE
FEDRAMP_HIGH_RESOLVED = syn.FEDRAMP_HIGH_RESOLVED
FEDRAMP_CERT = "https://fedramp.gov/2026/reference/fedramp-certification/"
FEDRAMP_CONTROLS = "https://fedramp.gov/2026/reference/controls/"
NIST_53A = "https://csrc.nist.gov/pubs/sp/800/53/a/r5/final"
CYBER_MIL = "https://public.cyber.mil/dccs/dccs-documents/"


def rel(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(ROOT))
    except ValueError:
        return str(path)


def rewrite_meta_paths(meta_dest: Path, catalog: Path, baseline_label: str | None) -> dict:
    meta = json.loads(meta_dest.read_text(encoding="utf-8"))
    meta["catalog"] = rel(catalog)
    src = str(meta.get("source") or "")
    abs_cat = str(catalog.resolve())
    if abs_cat in src:
        meta["source"] = src.replace(abs_cat, rel(catalog))
    if baseline_label:
        meta["baseline"] = baseline_label
    meta_dest.write_text(json.dumps(meta, indent=2) + "\n", encoding="utf-8")
    return meta


def generate(
    catalog: Path,
    dest: Path,
    meta_dest: Path,
    *,
    baseline: Path | None = None,
    overlay: Path | None = None,
    baseline_label: str | None = None,
) -> dict:
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
    if baseline is not None:
        argv.extend(["--baseline", str(baseline)])
    if overlay is not None and overlay.exists():
        argv.extend(["--overlay", str(overlay)])
    rc = syn.main(argv)
    if rc != 0:
        raise SystemExit(rc)
    return rewrite_meta_paths(meta_dest, catalog, baseline_label)


def write_id_list(profile_path: Path, dest: Path, fetched_at: str, url: str) -> dict:
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
        f"# url: {url}",
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
        "published": meta.get("published"),
        "path": rel(dest),
        "ids": [syn.normalize_id(x) for x in ordered],
    }


def main() -> int:
    fetched_at = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    raw = ROOT / "question-bank" / "raw"
    banks = ROOT / "il5-scanner" / "banks"
    qdir = ROOT / "question-bank"
    raw.mkdir(parents=True, exist_ok=True)
    banks.mkdir(parents=True, exist_ok=True)
    qdir.mkdir(parents=True, exist_ok=True)

    import build_il5_overlay_hooks as ov  # noqa: E402

    ov.main()

    catalog_path = raw / "NIST_SP-800-53_rev5_catalog-min.json"
    fedramp_profile = raw / "FedRAMP_rev5_HIGH-baseline_profile.json"
    nist_53b_profile = raw / "NIST_SP-800-53_rev5_HIGH-baseline_profile.json"
    nist_high_resolved = raw / "NIST_SP-800-53_rev5_HIGH-baseline-resolved-profile_catalog-min.json"

    syn.fetch_url(NIST_FULL, catalog_path)
    syn.fetch_url(FEDRAMP_HIGH_PROFILE, fedramp_profile)
    syn.fetch_url(NIST_53B_HIGH_PROFILE, nist_53b_profile)
    try:
        syn.fetch_url(NIST_HIGH_RESOLVED, nist_high_resolved)
    except SystemExit:
        syn.warn("NIST HIGH resolved catalog fetch failed; comparison omitted")

    id_info = write_id_list(
        fedramp_profile, qdir / "fedramp-high-class-d.ids.txt", fetched_at, FEDRAMP_HIGH_PROFILE
    )
    nist_ids, _ = syn.load_baseline_ids(nist_53b_profile)
    nist_high_count = len(nist_ids)
    fedramp_ids = set(id_info["ids"])
    only_fedramp = sorted(fedramp_ids - nist_ids)
    only_nist = sorted(nist_ids - fedramp_ids)
    if nist_high_count != id_info["id_count"]:
        syn.warn(
            f"NIST SP 800-53B HIGH has {nist_high_count} IDs; "
            f"FedRAMP High / Class D profile has {id_info['id_count']} IDs. "
            "They are different sets. Default grade path uses FedRAMP High."
        )

    overlay = qdir / "il5-overlay-hooks.json"

    high_q = banks / "production-high-53a-questions.jsonl"
    high_m = banks / "production-high-53a-questions.meta.json"
    high_label = (
        f"FedRAMP High / Class D OSCAL profile ({rel(fedramp_profile)}; "
        f"{id_info['id_count']} official with-ids)"
    )
    high_meta = generate(
        catalog_path,
        high_q,
        high_m,
        baseline=fedramp_profile,
        overlay=None,
        baseline_label=high_label,
    )

    nist_q = banks / "nist-800-53b-high-53a-questions.jsonl"
    nist_m = banks / "nist-800-53b-high-53a-questions.meta.json"
    nist_meta = generate(
        catalog_path,
        nist_q,
        nist_m,
        baseline=nist_53b_profile,
        overlay=None,
        baseline_label="NIST-800-53B-HIGH (comparison only; NOT FedRAMP High / Class D)",
    )

    full_q = banks / "production-full-53a-questions.jsonl"
    full_m = banks / "production-full-53a-questions.meta.json"
    full_meta = generate(
        catalog_path,
        full_q,
        full_m,
        baseline=None,
        overlay=None,
        baseline_label="NIST-SP-800-53-REV5-FULL-CATALOG (not a baseline)",
    )

    # Mirror FedRAMP High into question-bank/ as the Class D filter bank.
    class_d_q = qdir / "fedramp-high-class-d.questions.jsonl"
    class_d_m = qdir / "fedramp-high-class-d.meta.json"
    class_d_q.write_bytes(high_q.read_bytes())
    class_d_m.write_text(json.dumps(high_meta, indent=2) + "\n", encoding="utf-8")

    (qdir / "nist-800-53b-high.meta.json").write_text(
        json.dumps(nist_meta, indent=2) + "\n", encoding="utf-8"
    )

    overlay_count = 0
    if overlay.exists():
        overlay_count = len(json.loads(overlay.read_text(encoding="utf-8")).get("rows") or [])

    source = {
        "generated_from_catalog": True,
        "production": True,
        "fetched_at": fetched_at,
        "default_grade_path": "FedRAMP High / Class D",
        "nist_53b_high_is_not_fedramp_high": True,
        "high_alone_fails_il5": True,
        "question_count_is_not_a_control_count": True,
        "gsa_fedramp_automation_profile_url_404_as_of": "2026-09-08 and rechecked this build",
        "high_bank": {
            "path": rel(high_q),
            "question_count": high_meta.get("question_count"),
            "catalog_controls_emitted": high_meta.get("catalog_controls_emitted"),
            "baseline": "FedRAMP-HIGH-CLASS-D",
            "official_profile_id_count": id_info["id_count"],
            "not_nist_800_53b_high": True,
            "profile": FEDRAMP_HIGH_PROFILE,
            "profile_title": id_info["title"],
            "profile_version": id_info["version"],
            "profile_last_modified": id_info["last_modified"],
            "profile_published": id_info["published"],
            "catalog": NIST_FULL,
            "catalog_csrc": NIST_53A,
            "label": (
                "FedRAMP Rev 5 High / Class D OSCAL profile IDs × NIST SP 800-53A "
                "published Examine/Interview/Test. Default scanner grade path."
            ),
        },
        "nist_53b_high_comparison_bank": {
            "path": rel(nist_q),
            "question_count": nist_meta.get("question_count"),
            "catalog_controls_emitted": nist_meta.get("catalog_controls_emitted"),
            "baseline": "NIST-800-53B-HIGH",
            "official_profile_id_count": nist_high_count,
            "not_fedramp_appendix_a": True,
            "profile": NIST_53B_HIGH_PROFILE,
            "catalog": NIST_FULL,
            "label": (
                "NIST SP 800-53B HIGH only. Kept for diff against FedRAMP High. "
                "Not the default grade path."
            ),
        },
        "full_bank": {
            "path": rel(full_q),
            "question_count": full_meta.get("question_count"),
            "catalog_controls_emitted": full_meta.get("catalog_controls_emitted"),
            "baseline": "NIST-SP-800-53-REV5-FULL-CATALOG",
            "catalog": NIST_FULL,
            "label": "Entire NIST SP 800-53/53A catalog. Not a baseline. Max-size bank.",
        },
        "baseline_diff": {
            "fedramp_high_ids": id_info["id_count"],
            "nist_800_53b_high_ids": nist_high_count,
            "ids_only_in_fedramp_high": only_fedramp,
            "ids_only_in_nist_53b_high": only_nist,
            "question_delta_fedramp_minus_nist53b": (
                (high_meta.get("question_count") or 0) - (nist_meta.get("question_count") or 0)
            ),
        },
        "overlay_hooks": {
            "path": rel(overlay) if overlay.exists() else None,
            "row_count": overlay_count,
            "appended_on_il5_paths": True,
            "not_a_downloaded_ssp_addendum": True,
        },
        "sources": [
            {
                "role": "NIST SP 800-53 Rev 5 + SP 800-53A Rev 5 assessment procedures",
                "url": NIST_FULL,
                "also": syn.NIST_OSCAL_CATALOG,
                "csrc": NIST_53A,
                "local": rel(catalog_path),
            },
            {
                "role": "FedRAMP Rev 5 High / Class D ID list (OSCAL profile) — default grade path",
                "url": FEDRAMP_HIGH_PROFILE,
                "resolved_catalog": FEDRAMP_HIGH_RESOLVED,
                "fedramp_certification": FEDRAMP_CERT,
                "fedramp_controls": FEDRAMP_CONTROLS,
                "title": id_info["title"],
                "version": id_info["version"],
                "last_modified": id_info["last_modified"],
                "published": id_info["published"],
                "id_count": id_info["id_count"],
                "local_ids": id_info["path"],
                "gsa_fedramp_automation": (
                    "https://raw.githubusercontent.com/GSA/fedramp-automation/master/"
                    "dist/content/rev5/baselines/json/FedRAMP_rev5_HIGH-baseline_profile.json"
                ),
                "gsa_status": "HTTP 404 as of 2026-09-08 and this rebuild; OSCAL Foundation profile used",
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
                "overlay_hooks": rel(overlay) if overlay.exists() else None,
            },
            {
                "role": "CNSSI 1253 NSS overlays (not fetched as a catalog)",
                "url": "https://www.cnss.gov/CNSS/issuances/Instructions.cfm",
                "fetched": False,
            },
        ],
    }
    id_info.pop("ids", None)
    (banks / "SOURCE.json").write_text(json.dumps(source, indent=2) + "\n", encoding="utf-8")
    (qdir / "SOURCE.json").write_text(json.dumps(source, indent=2) + "\n", encoding="utf-8")

    print(
        f"DEFAULT HIGH (FedRAMP High / Class D) {high_meta.get('question_count')} "
        f"questions from {high_meta.get('catalog_controls_emitted')} of "
        f"{id_info['id_count']} official profile IDs — {high_q}",
        file=sys.stderr,
    )
    print(
        f"NIST 53B HIGH comparison {nist_meta.get('question_count')} questions "
        f"from {nist_meta.get('catalog_controls_emitted')} controls — {nist_q}",
        file=sys.stderr,
    )
    print(
        f"FULL {full_meta.get('question_count')} questions from "
        f"{full_meta.get('catalog_controls_emitted')} controls — {full_q}",
        file=sys.stderr,
    )
    print(f"IL5 overlay hooks: {overlay_count} — {overlay}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
