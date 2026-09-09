#!/usr/bin/env python3
"""Synthesize transitional-scanner questions from a 800-53A catalog.

Production path: tools/build_production_bank.py fetches official NIST
800-53A + the FedRAMP Rev 5 High / Class D OSCAL profile and writes
question-bank/. It does not invent official control counts.

Inputs:
  - OSCAL catalog JSON (NIST SP 800-53 Rev 5 + 800-53A assessment
    procedures), or a flattened il5-question-catalog-v1 file
  - Optional baseline ID list / OSCAL profile (FedRAMP High / Class D)
  - Optional overlay row files (FedRAMP+ / CNSSI / SRG) when the path
    is IL5
  - fixtures/question-bank/ is a unit fixture only, not production

Official fetch / source path is printed by --print-sources.
See QUESTION-BANK.md.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import urllib.request
from pathlib import Path
from typing import Any, Iterable, Iterator

METHODS = ("Examine", "Interview", "Test")
LAYERS = ("High", "FedRAMP+", "CNSSI", "SRG")
PATHS = ("FedRAMP High", "IL5 non-NSS", "IL5 NSS")
PATH_ALIASES = {
    "high": "FedRAMP High",
    "fedramp-high": "FedRAMP High",
    "il5-non-nss": "IL5 non-NSS",
    "il5-nss": "IL5 NSS",
}
DEFAULT_PATHS = {
    "High": ("FedRAMP High", "IL5 non-NSS", "IL5 NSS"),
    "FedRAMP+": ("IL5 non-NSS", "IL5 NSS"),
    "CNSSI": ("IL5 NSS",),
    "SRG": ("IL5 non-NSS", "IL5 NSS"),
}

NIST_OSCAL_CATALOG_MIN = (
    "https://raw.githubusercontent.com/usnistgov/oscal-content/main/"
    "nist.gov/SP800-53/rev5/json/NIST_SP-800-53_rev5_catalog-min.json"
)
NIST_OSCAL_CATALOG = (
    "https://raw.githubusercontent.com/usnistgov/oscal-content/main/"
    "nist.gov/SP800-53/rev5/json/NIST_SP-800-53_rev5_catalog.json"
)
NIST_OSCAL_HIGH_PROFILE = (
    "https://raw.githubusercontent.com/usnistgov/oscal-content/main/"
    "nist.gov/SP800-53/rev5/json/NIST_SP-800-53_rev5_HIGH-baseline_profile.json"
)
NIST_OSCAL_HIGH_RESOLVED = (
    "https://raw.githubusercontent.com/usnistgov/oscal-content/main/"
    "nist.gov/SP800-53/rev5/json/NIST_SP-800-53_rev5_HIGH-baseline-resolved-profile_catalog-min.json"
)
FEDRAMP_HIGH_PROFILE = (
    "https://raw.githubusercontent.com/OSCAL-Foundation/fedramp-resources/main/"
    "baselines/rev5/json/FedRAMP_rev5_HIGH-baseline_profile.json"
)
FEDRAMP_HIGH_RESOLVED = (
    "https://raw.githubusercontent.com/OSCAL-Foundation/fedramp-resources/main/"
    "baselines/rev5/json/FedRAMP_rev5_HIGH-baseline-resolved-profile_catalog.json"
)

SOURCES_TEXT = """Official sources

NIST SP 800-53 Rev 5 + SP 800-53A Rev 5 assessment procedures (OSCAL):
  {catalog}
  {catalog_min}
  https://github.com/usnistgov/oscal-content/tree/main/nist.gov/SP800-53/rev5/json
  https://csrc.nist.gov/pubs/sp/800/53/a/r5/final

FedRAMP Rev 5 High / Class D OSCAL profile (preferred ID list):
  {fedramp_high}
  {fedramp_resolved}
  GSA/fedramp-automation returned 404 on 2026-09-08. This profile is the
  published FedRAMP Rev 5 High baseline (OSCAL Foundation). Class D = High.
  Also: https://fedramp.gov/2026/reference/fedramp-certification/
        https://fedramp.gov/2026/reference/controls/

NIST SP 800-53B HIGH baseline profile (NOT FedRAMP High / Class D):
  {high_profile}
  Different set. Do not substitute for FedRAMP High.

DoD FedRAMP+ / IL5 overlay:
  DoD Rev 5 SSP Addendum + SRG Control Crosswalk
  https://public.cyber.mil/dccs/dccs-documents/
  (login-walled as of 2026-09-08; production bank uses documented hooks)

CNSSI 1253 NSS overlays (IL5 NSS only):
  https://www.cnss.gov/CNSS/issuances/Instructions.cfm

Question count is synthesized 53A rows. It is not an official C/CE count.
Default grade path: FedRAMP High / Class D (not NIST 800-53B HIGH).
Production artifacts: il5-scanner/banks/  Rebuild: tools/generate_production_banks.py
Provenance: il5-scanner/banks/PROVENANCE.md
""".format(
    catalog=NIST_OSCAL_CATALOG,
    catalog_min=NIST_OSCAL_CATALOG_MIN,
    high_profile=NIST_OSCAL_HIGH_PROFILE,
    fedramp_high=FEDRAMP_HIGH_PROFILE,
    fedramp_resolved=FEDRAMP_HIGH_RESOLVED,
)

PARAM_RE = re.compile(r"\{\{\s*insert:\s*param,\s*([^}]+?)\s*\}\}")
WHITESPACE_RE = re.compile(r"\s+")


def warn(msg: str) -> None:
    print(f"WARN: {msg}", file=sys.stderr)


def die(msg: str, code: int = 2) -> None:
    print(f"ERROR: {msg}", file=sys.stderr)
    raise SystemExit(code)


def load_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        die(f"file not found: {path}")
    except json.JSONDecodeError as exc:
        die(f"invalid JSON in {path}: {exc}")


def collapse(text: str) -> str:
    return WHITESPACE_RE.sub(" ", (text or "").strip())


def clean_prose(text: str) -> str:
    text = PARAM_RE.sub(lambda m: f"[param:{m.group(1).strip()}]", text or "")
    return collapse(text).rstrip(" ;.")


def normalize_method(raw: str) -> str | None:
    if not raw:
        return None
    key = raw.strip().title()
    if key in METHODS:
        return key
    upper = raw.strip().upper()
    mapping = {"EXAMINE": "Examine", "INTERVIEW": "Interview", "TEST": "Test"}
    return mapping.get(upper)


def normalize_layer(raw: str) -> str:
    if raw in LAYERS:
        return raw
    key = (raw or "High").strip()
    aliases = {
        "high": "High",
        "fedramp high": "High",
        "class d": "High",
        "fedramp+": "FedRAMP+",
        "fedramp-plus": "FedRAMP+",
        "dod": "FedRAMP+",
        "cnssi": "CNSSI",
        "cnssi 1253": "CNSSI",
        "srg": "SRG",
    }
    return aliases.get(key.lower(), "High")


def normalize_id(raw: str) -> str:
    """Normalize ac-2, AC-02, AC-2(1), ac-2.1 to a compare key."""
    s = (raw or "").strip().lower().replace("_", "-")
    s = s.replace("(", ".").replace(")", "")
    s = re.sub(r"^([a-z]+)-0+(\d)", r"\1-\2", s)
    s = re.sub(r"\.0+(\d+)$", r".\1", s)
    return s


def split_control(cid: str) -> tuple[str, str]:
    """Return (base control label, enhancement label)."""
    key = normalize_id(cid)
    m = re.match(r"^([a-z]+)-(\d+)(?:\.(\d+))?$", key)
    if not m:
        return cid.upper(), ""
    base = f"{m.group(1).upper()}-{m.group(2)}"
    enh = m.group(3) or ""
    return base, enh


def display_control(base: str, enhancement: str) -> str:
    return f"{base}({enhancement})" if enhancement else base


def iter_oscal_controls(node: dict[str, Any]) -> Iterator[dict[str, Any]]:
    for control in node.get("controls") or []:
        yield control
        yield from iter_oscal_controls(control)


def catalog_controls(doc: dict[str, Any]) -> list[dict[str, Any]]:
    if doc.get("format") == "il5-question-catalog-v1":
        return list(doc.get("controls") or [])
    catalog = doc.get("catalog")
    if not isinstance(catalog, dict):
        die("catalog JSON must be an OSCAL catalog or il5-question-catalog-v1")
    out: list[dict[str, Any]] = []
    for group in catalog.get("groups") or []:
        out.extend(iter_oscal_controls(group))
    out.extend(iter_oscal_controls(catalog))
    return out


def catalog_source_label(doc: dict[str, Any], path: Path) -> str:
    if doc.get("format") == "il5-question-catalog-v1":
        return str(doc.get("source") or path)
    catalog = doc.get("catalog") or {}
    meta = catalog.get("metadata") or {}
    title = collapse(meta.get("title") or "")
    if title:
        return f"{path} — {title}"
    return str(path)


def prop_value(props: Iterable[dict[str, Any]] | None, name: str) -> str:
    for prop in props or []:
        if prop.get("name") == name and prop.get("value"):
            return str(prop["value"])
    return ""


def leaf_objectives(parts: list[dict[str, Any]] | None) -> list[tuple[str, str]]:
    """Collect leaf assessment-objective (id, prose) pairs."""
    found: list[tuple[str, str]] = []

    def walk(part: dict[str, Any]) -> None:
        if part.get("name") != "assessment-objective":
            for child in part.get("parts") or []:
                walk(child)
            return
        children = [
            c for c in (part.get("parts") or []) if c.get("name") == "assessment-objective"
        ]
        prose = clean_prose(part.get("prose") or "")
        if children:
            for child in children:
                walk(child)
            return
        oid = part.get("id") or prop_value(part.get("props"), "label") or "obj"
        if prose:
            found.append((str(oid), prose))

    for part in parts or []:
        walk(part)
    return found


def assessment_methods(parts: list[dict[str, Any]] | None) -> list[tuple[str, str]]:
    found: list[tuple[str, str]] = []
    for part in parts or []:
        if part.get("name") != "assessment-method":
            continue
        method = normalize_method(prop_value(part.get("props"), "method"))
        if not method:
            continue
        objects = []
        for child in part.get("parts") or []:
            if child.get("name") == "assessment-objects":
                objects.append(clean_prose(child.get("prose") or ""))
        found.append((method, "; ".join(o for o in objects if o)))
    return found


def flattened_objectives(control: dict[str, Any]) -> list[tuple[str, str]]:
    out: list[tuple[str, str]] = []
    for obj in control.get("objectives") or []:
        oid = str(obj.get("id") or "obj")
        prose = clean_prose(obj.get("prose") or obj.get("question") or "")
        if prose:
            out.append((oid, prose))
    return out


def flattened_methods(control: dict[str, Any]) -> list[tuple[str, str]]:
    out: list[tuple[str, str]] = []
    for item in control.get("methods") or []:
        if isinstance(item, str):
            method = normalize_method(item)
            if method:
                out.append((method, ""))
            continue
        method = normalize_method(str(item.get("method") or ""))
        if method:
            out.append((method, clean_prose(item.get("objects") or "")))
    return out


def make_question(
    *,
    control: str,
    enhancement: str,
    objective_id: str,
    method: str,
    question: str,
    layer: str,
    path_applicability: list[str],
    source: str,
) -> dict[str, Any]:
    qid = "/".join(
        [
            display_control(control, enhancement),
            objective_id,
            method,
        ]
    )
    return {
        "id": qid,
        "control": control,
        "enhancement": enhancement,
        "objective_id": objective_id,
        "method": method,
        "question": question,
        "layer": layer,
        "path_applicability": path_applicability,
        "source": source,
    }


def compose_question(method: str, label: str, objective_id: str, prose: str, objects: str) -> str:
    text = (
        f"{method}: Determine whether {label} objective {objective_id} is met — {prose}."
    )
    if objects:
        text += f" {method} objects: {objects}."
    return text


def questions_from_control(
    control: dict[str, Any],
    *,
    default_layer: str,
    source: str,
    published_only: bool = True,
) -> list[dict[str, Any]]:
    cid = str(control.get("id") or "")
    if not cid:
        return []
    base, enhancement = split_control(cid)
    label = display_control(base, enhancement)
    title = collapse(control.get("title") or "")
    layer = normalize_layer(str(control.get("layer") or default_layer))
    paths = list(control.get("path_applicability") or DEFAULT_PATHS[layer])

    objectives = flattened_objectives(control) or leaf_objectives(control.get("parts"))
    methods = flattened_methods(control) or assessment_methods(control.get("parts"))
    if not methods and not published_only:
        methods = [(m, "") for m in METHODS]
    if not objectives and not published_only:
        fallback = title or f"{label} assessment procedure"
        objectives = [(control.get("id") or "obj", f"{fallback} is implemented as required")]
    if not methods or not objectives:
        return []

    out: list[dict[str, Any]] = []
    for objective_id, prose in objectives:
        for method, objects in methods:
            out.append(
                make_question(
                    control=base,
                    enhancement=enhancement,
                    objective_id=objective_id,
                    method=method,
                    question=compose_question(method, label, objective_id, prose, objects),
                    layer=layer,
                    path_applicability=paths,
                    source=source,
                )
            )
    return out


def load_baseline_ids(path: Path) -> tuple[set[str], str]:
    text = path.read_text(encoding="utf-8").lstrip()
    if text.startswith("{") or text.startswith("["):
        doc = json.loads(text)
        ids = set(extract_profile_ids(doc))
        label = f"OSCAL profile/JSON IDs from {path}"
        if isinstance(doc, dict) and doc.get("profile"):
            title = (doc.get("profile") or {}).get("metadata", {}).get("title") or ""
            upper = title.upper()
            if "FEDRAMP" in upper and "HIGH" in upper:
                label = f"FedRAMP High / Class D OSCAL profile ({path})"
            elif "800-53B" in title or "HIGH IMPACT BASELINE" in upper:
                warn(
                    "baseline looks like NIST SP 800-53B HIGH, which is not "
                    "FedRAMP High / Class D. Production bank must use the "
                    "FedRAMP High profile."
                )
        return ids, label
    ids = set()
    for line in text.splitlines():
        raw = line.split("#", 1)[0].strip()
        if raw:
            ids.add(normalize_id(raw))
    return ids, f"ID list from {path}"


def extract_profile_ids(doc: Any) -> list[str]:
    if isinstance(doc, list):
        return [normalize_id(str(x)) for x in doc]
    if not isinstance(doc, dict):
        return []
    if doc.get("controls"):
        return [normalize_id(str(x)) for x in doc["controls"]]
    profile = doc.get("profile") or {}
    ids: list[str] = []
    for imp in profile.get("imports") or []:
        for block in imp.get("include-controls") or []:
            for item in block.get("with-ids") or []:
                ids.append(normalize_id(str(item)))
    return ids


def in_baseline(control_id: str, baseline: set[str]) -> bool:
    key = normalize_id(control_id)
    if key in baseline:
        return True
    # Allow a parent ID in the baseline to keep its enhancements only
    # when the enhancement itself is listed. No implicit include.
    return False


def load_overlay_rows(path: Path) -> list[dict[str, Any]]:
    doc = load_json(path)
    rows = doc.get("rows") if isinstance(doc, dict) else doc
    if not isinstance(rows, list):
        die(f"overlay {path} must be a JSON array or an object with rows[]")
    source = ""
    if isinstance(doc, dict):
        source = str(doc.get("source") or path)
    else:
        source = str(path)
    out: list[dict[str, Any]] = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        method = normalize_method(str(row.get("method") or ""))
        if not method:
            warn(f"skip overlay row without method in {path}")
            continue
        layer = normalize_layer(str(row.get("layer") or "FedRAMP+"))
        control = str(row.get("control") or "")
        enhancement = str(row.get("enhancement") or "")
        if not control:
            continue
        base, enh_from_id = split_control(control)
        enhancement = enhancement or enh_from_id
        paths = list(row.get("path_applicability") or DEFAULT_PATHS[layer])
        question = collapse(str(row.get("question") or ""))
        objective_id = str(row.get("objective_id") or "overlay")
        if not question:
            question = compose_question(
                method,
                display_control(base, enhancement),
                objective_id,
                "the overlay row from the operator-supplied official workbook is implemented",
                "",
            )
        out.append(
            make_question(
                control=base,
                enhancement=enhancement,
                objective_id=objective_id,
                method=method,
                question=question,
                layer=layer,
                path_applicability=paths,
                source=str(row.get("source") or source),
            )
        )
    return out


def filter_path(questions: list[dict[str, Any]], path: str | None) -> list[dict[str, Any]]:
    if not path:
        return questions
    wanted = PATH_ALIASES.get(path.lower(), path)
    return [q for q in questions if wanted in q.get("path_applicability", [])]


def emit(questions: list[dict[str, Any]], fmt: str, dest: Path | None, meta: dict[str, Any]) -> None:
    if fmt == "json":
        payload = {"meta": meta, "questions": questions}
        text = json.dumps(payload, indent=2, ensure_ascii=False) + "\n"
    else:
        text = "".join(json.dumps(q, ensure_ascii=False) + "\n" for q in questions)
    if dest:
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(text, encoding="utf-8")
        print(f"wrote {len(questions)} questions to {dest}", file=sys.stderr)
    else:
        sys.stdout.write(text)


def fetch_url(url: str, dest: Path) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    print(f"fetching {url}", file=sys.stderr)
    try:
        with urllib.request.urlopen(url, timeout=60) as resp:
            dest.write_bytes(resp.read())
    except Exception as exc:  # noqa: BLE001 — surface fetch failures plainly
        die(f"fetch failed: {exc}")
    print(f"wrote {dest} ({dest.stat().st_size} bytes)", file=sys.stderr)
    print(
        "SOURCE: NIST OSCAL from usnistgov/oscal-content. "
        "This is not FedRAMP High / Class D by itself.",
        file=sys.stderr,
    )


def build_meta(
    *,
    catalog: Path,
    source: str,
    baseline_label: str | None,
    overlay_paths: list[Path],
    path: str | None,
    control_ids: list[str],
    questions: list[dict[str, Any]],
) -> dict[str, Any]:
    layers: dict[str, int] = {}
    methods: dict[str, int] = {}
    for q in questions:
        layers[q["layer"]] = layers.get(q["layer"], 0) + 1
        methods[q["method"]] = methods.get(q["method"], 0) + 1
    return {
        "generated_from_catalog": True,
        "not_an_official_control_count": True,
        "catalog": str(catalog),
        "source": source,
        "baseline": baseline_label,
        "overlays": [str(p) for p in overlay_paths],
        "path_filter": path,
        "catalog_controls_emitted": len(control_ids),
        "question_count": len(questions),
        "by_layer": layers,
        "by_method": methods,
        "official_id_lists_live_in": [
            "FedRAMP Rev 5 High / Class D OSCAL profile (OSCAL-Foundation/fedramp-resources)",
            "FedRAMP SSP Appendix A High / Class D workbook on fedramp.gov",
            "DoD Rev 5 SSP Addendum + SRG Control Crosswalk on cyber.mil",
            "CNSSI 1253 if NSS",
        ],
        "question_count_is_not_a_control_count": True,
    }


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Synthesize IL5 scanner questions from 800-53A catalogs"
    )
    p.add_argument("--catalog", type=Path, help="OSCAL catalog or flattened catalog JSON")
    p.add_argument(
        "--baseline",
        type=Path,
        help="Optional control ID list (text) or OSCAL profile JSON. "
        "Use official FedRAMP High / Class D IDs, not a guessed 410.",
    )
    p.add_argument(
        "--overlay",
        type=Path,
        action="append",
        default=[],
        help="Overlay row JSON (repeatable). Use for FedRAMP+ / CNSSI / SRG.",
    )
    p.add_argument(
        "--path",
        choices=sorted(PATH_ALIASES),
        help="Keep questions applicable to this buyer path.",
    )
    p.add_argument(
        "--layer",
        default="High",
        help="Layer label for catalog-derived questions (default High).",
    )
    p.add_argument("--format", choices=("jsonl", "json"), default="jsonl")
    p.add_argument("--out", type=Path, help="Write here instead of stdout")
    p.add_argument("--meta-out", type=Path, help="Write generation meta JSON here")
    p.add_argument("--print-sources", action="store_true")
    p.add_argument(
        "--fetch-nist-catalog",
        type=Path,
        metavar="DEST",
        help="Download the official NIST 800-53/53A min catalog to DEST.",
    )
    p.add_argument(
        "--fetch-fedramp-high-profile",
        type=Path,
        metavar="DEST",
        help="Download the FedRAMP Rev 5 High / Class D OSCAL profile to DEST.",
    )
    p.add_argument(
        "--fill-missing-methods",
        action="store_true",
        help="If a control omits Examine/Interview/Test, invent all three. "
        "Default is published-methods-only (production).",
    )
    return p.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    if args.print_sources:
        sys.stdout.write(SOURCES_TEXT)
        if not args.catalog and not args.fetch_nist_catalog and not args.fetch_fedramp_high_profile:
            return 0
    if args.fetch_nist_catalog:
        fetch_url(NIST_OSCAL_CATALOG_MIN, args.fetch_nist_catalog)
        if not args.catalog and not args.fetch_fedramp_high_profile:
            return 0
    if args.fetch_fedramp_high_profile:
        fetch_url(FEDRAMP_HIGH_PROFILE, args.fetch_fedramp_high_profile)
        if not args.catalog:
            return 0

    if not args.catalog:
        die("provide --catalog, or use --print-sources / fetch flags")

    doc = load_json(args.catalog)
    source = catalog_source_label(doc, args.catalog)
    if "example" in source.lower() or "snapshot" in source.lower():
        warn(
            "catalog is a marked example snapshot, not the official "
            "NIST / FedRAMP workbook. Full banks must be generated-from-catalog."
        )

    baseline: set[str] | None = None
    baseline_label = None
    if args.baseline:
        baseline, baseline_label = load_baseline_ids(args.baseline)
        if not baseline:
            die(f"baseline file produced no IDs: {args.baseline}")
    else:
        warn(
            "no --baseline given; emitting every control in the catalog. "
            "That is not a FedRAMP High / Class D count. Pass official "
            "Appendix A High IDs to filter."
        )

    default_layer = normalize_layer(args.layer)
    questions: list[dict[str, Any]] = []
    emitted_ids: list[str] = []
    for control in catalog_controls(doc):
        cid = str(control.get("id") or "")
        if baseline is not None and not in_baseline(cid, baseline):
            continue
        emitted_ids.append(cid)
        questions.extend(
            questions_from_control(
                control,
                default_layer=default_layer,
                source=source,
                published_only=not args.fill_missing_methods,
            )
        )

    for overlay in args.overlay:
        questions.extend(load_overlay_rows(overlay))

    questions = filter_path(questions, args.path)
    meta = build_meta(
        catalog=args.catalog,
        source=source,
        baseline_label=baseline_label,
        overlay_paths=args.overlay,
        path=args.path,
        control_ids=emitted_ids,
        questions=questions,
    )
    print(
        "generated-from-catalog: "
        f"{meta['question_count']} questions from "
        f"{meta['catalog_controls_emitted']} catalog controls "
        "(question count is not an official C/CE count)",
        file=sys.stderr,
    )
    emit(questions, args.format, args.out, meta)
    if args.meta_out:
        args.meta_out.parent.mkdir(parents=True, exist_ok=True)
        args.meta_out.write_text(json.dumps(meta, indent=2) + "\n", encoding="utf-8")
    elif args.out:
        sidecar = args.out.with_suffix(args.out.suffix + ".meta.json")
        if args.format == "jsonl":
            sidecar = Path(str(args.out) + ".meta.json")
        sidecar.write_text(json.dumps(meta, indent=2) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
