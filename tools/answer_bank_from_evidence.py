#!/usr/bin/env python3
"""Answer the production HIGH 800-53A bank from collected evidence.

Stub rules (hard):
  - Default bank: il5-scanner/banks/production-high-53a-questions.jsonl
  - MISSING unless a mapped evidence file is present and non-empty
  - Never invent PASS
  - Never claim ATO, FedRAMP authorization, or DISA PA
  - High-alone still fails an IL5 assessment

Codex (or a human) may upgrade HOLD → PASS only after reading the cited
file and confirming the 53A objective is actually met. This script will
not do that upgrade.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_BANK = ROOT / "il5-scanner" / "banks" / "production-high-53a-questions.jsonl"
DEFAULT_MAP = ROOT / "il5-scanner" / "collectors" / "neo4j-ec2-govcloud-map.json"
OVERLAY = ROOT / "question-bank" / "il5-overlay-hooks.json"
FIXTURE_BANK = ROOT / "fixtures" / "question-bank" / "tiny-question-bank.jsonl"

PATH_ALIASES = {
    "high": "FedRAMP High",
    "fedramp-high": "FedRAMP High",
    "fedramp high only": "FedRAMP High",
    "fedramp high": "FedRAMP High",
    "il5-non-nss": "IL5 non-NSS",
    "il5 non-nss": "IL5 non-NSS",
    "il5-nss": "IL5 NSS",
    "il5 nss": "IL5 NSS",
    "unknown": "IL5 non-NSS",
}

VERDICTS = ("PASS", "HOLD", "WARN", "N/A", "MISSING")


def die(msg: str, code: int = 2) -> None:
    print(f"ERROR: {msg}", file=sys.stderr)
    raise SystemExit(code)


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open(encoding="utf-8") as fh:
        for line_no, line in enumerate(fh, 1):
            line = line.strip()
            if not line:
                continue
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError as exc:
                die(f"invalid JSONL in {path}:{line_no}: {exc}")
    return rows


def normalize_path(raw: str) -> str:
    key = (raw or "").strip().lower()
    return PATH_ALIASES.get(key, raw.strip() or "IL5 non-NSS")


def family_of(control: str) -> str:
    m = re.match(r"^([A-Za-z]+)", control or "")
    return (m.group(1) if m else "").upper()


def control_key(control: str, enhancement: str) -> str:
    base = (control or "").strip().upper()
    enh = (enhancement or "").strip()
    return f"{base}({enh})" if enh else base


def evidence_tree_files(evidence: Path) -> dict[str, Path]:
    files: dict[str, Path] = {}
    if not evidence.exists():
        return files
    for p in evidence.rglob("*"):
        if not p.is_file():
            continue
        rel = str(p.relative_to(evidence)).replace("\\", "/")
        if rel in {"MANIFEST.json", "FINDINGS-INDEX.json", "COLLECTOR.md"}:
            continue
        files[rel] = p
    return files


def is_present(path: Path) -> bool:
    if not path.exists() or path.stat().st_size == 0:
        return False
    try:
        head = path.read_text(encoding="utf-8", errors="replace")[:120]
    except OSError:
        return False
    if head.startswith("MISSING:"):
        return False
    return True


def build_presence(evidence: Path, mapping: dict[str, Any]) -> list[dict[str, Any]]:
    files = evidence_tree_files(evidence)
    present_rels = {rel for rel, p in files.items() if is_present(p)}
    collectors = []
    for c in mapping.get("collectors") or []:
        hits: list[str] = []
        for raw in c.get("paths") or []:
            raw_n = raw.rstrip("/")
            for rel in present_rels:
                if rel == raw_n or rel.startswith(raw_n + "/"):
                    hits.append(rel)
        collectors.append(
            {
                "id": c.get("id"),
                "families": [str(x).upper() for x in (c.get("families") or [])],
                "controls": [str(x).upper() for x in (c.get("controls") or [])],
                "methods": [str(x) for x in (c.get("methods") or [])],
                "evidence_present": sorted(set(hits)),
                "present": bool(hits),
            }
        )
    return collectors


def cite_for_question(
    question: dict[str, Any], collectors: list[dict[str, Any]]
) -> list[str]:
    fam = family_of(question.get("control") or "")
    ctl = control_key(question.get("control") or "", question.get("enhancement") or "")
    method = question.get("method") or ""
    hits: list[str] = []
    for c in collectors:
        if not c.get("present"):
            continue
        methods = c.get("methods") or []
        families = c.get("families") or []
        controls = c.get("controls") or []
        method_ok = (not methods) or method in methods
        if not method_ok:
            continue
        family_ok = "*" in families or fam in families
        control_ok = (not controls) or ctl in controls or (question.get("control") or "").upper() in controls
        # Interview collector is family-wildcard; still require method match.
        if c.get("id") == "interviews":
            if method == "Interview":
                hits.extend(c.get("evidence_present") or [])
            continue
        if family_ok or control_ok:
            hits.extend(c.get("evidence_present") or [])
    # Dedup, keep order
    seen: set[str] = set()
    out: list[str] = []
    for h in hits:
        if h not in seen:
            seen.add(h)
            out.append(h)
    return out


def load_overlay_questions() -> list[dict[str, Any]]:
    if not OVERLAY.exists():
        return []
    doc = load_json(OVERLAY)
    rows = []
    for raw in doc.get("rows") or []:
        base = raw.get("control") or ""
        enh = raw.get("enhancement") or ""
        oid = raw.get("objective_id") or ""
        method = raw.get("method") or "Examine"
        qid = f"{control_key(base, enh)}/{oid}/{method}"
        rows.append(
            {
                "id": qid,
                "control": base,
                "enhancement": enh,
                "objective_id": oid,
                "method": method,
                "question": raw.get("question") or "",
                "layer": raw.get("layer") or "FedRAMP+",
                "path_applicability": raw.get("path_applicability") or ["IL5 non-NSS", "IL5 NSS"],
                "source": "question-bank/il5-overlay-hooks.json",
            }
        )
    return rows


SETTING_RE = re.compile(
    r"^(?:#\s*)?([A-Za-z0-9_.]+)\s*=\s*(.*?)\s*$"
)


def parse_settings(text: str) -> dict[str, str]:
    out: dict[str, str] = {}
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("#") or line.startswith("MISSING:"):
            continue
        m = SETTING_RE.match(line)
        if m:
            out[m.group(1)] = m.group(2)
    return out


def first_setting(settings: dict[str, str], *keys: str) -> tuple[str, str] | None:
    for k in keys:
        if k in settings:
            return k, settings[k]
    return None


def add_change(
    changes: list[dict[str, str]],
    *,
    family: str,
    current: str,
    required: str,
    evidence: str,
    why: str,
) -> None:
    changes.append(
        {
            "family": family,
            "current": current,
            "required": required,
            "evidence": evidence,
            "why": why,
        }
    )


def inspect_config_changes(evidence: Path) -> list[dict[str, str]]:
    """Conservative current → required list. Never a PASS verdict."""
    changes: list[dict[str, str]] = []
    conf_path = None
    for name in ("neo4j/neo4j.conf.redacted", "neo4j/neo4j.conf", "neo4j/neo4j-settings-grep.txt"):
        p = evidence / name
        if is_present(p):
            conf_path = p
            break
    settings: dict[str, str] = {}
    if conf_path is not None:
        settings = parse_settings(conf_path.read_text(encoding="utf-8", errors="replace"))
        ev = str(conf_path.relative_to(evidence)).replace("\\", "/")

        auth = first_setting(settings, "dbms.security.auth_enabled", "server.security.auth_enabled")
        if auth and auth[1].lower() in {"false", "0", "no"}:
            add_change(
                changes,
                family="IA / AC",
                current=f"{auth[0]}={auth[1]}",
                required="dbms.security.auth_enabled=true (native and/or LDAP/SSO; no anonymous Bolt)",
                evidence=f"{ev} ; grep auth_enabled {ev}",
                why="Auth disabled is an IL5 / High access-control hold (IA-2, AC-3).",
            )

        bolt_tls = first_setting(
            settings,
            "dbms.connector.bolt.tls_level",
            "server.bolt.tls_level",
            "dbms.ssl.policy.bolt.enabled",
            "server.ssl.policy.bolt.enabled",
        )
        if bolt_tls and bolt_tls[1].lower() in {"disabled", "optional", "false", "0"}:
            add_change(
                changes,
                family="SC-8 / SC-13",
                current=f"{bolt_tls[0]}={bolt_tls[1]}",
                required="Bolt TLS required (dbms.ssl.policy.bolt.enabled=true or tls_level=REQUIRED); TLS 1.2+",
                evidence=f"{ev} ; grep -E 'tls|ssl.policy.bolt' {ev}",
                why="In-transit crypto must be a FIPS-validated module in FIPS mode (standard §9).",
            )

        http = first_setting(settings, "server.http.enabled", "dbms.connector.http.enabled")
        if http and http[1].lower() in {"true", "1", "yes"}:
            add_change(
                changes,
                family="SC-7 / SC-8",
                current=f"{http[0]}={http[1]}",
                required="Disable cleartext HTTP in production; HTTPS + Bolt TLS only, or bind HTTP to localhost for admin break-glass with compensating SG",
                evidence=f"{ev} ; grep http {ev}",
                why="Cleartext HTTP on an IL5 graph is a transit finding.",
            )

        listen = first_setting(
            settings,
            "server.default_listen_address",
            "dbms.default_listen_address",
            "server.bolt.listen_address",
            "dbms.connector.bolt.listen_address",
        )
        if listen and ("0.0.0.0" in listen[1] or listen[1].startswith(":")):
            add_change(
                changes,
                family="SC-7 / AC-17",
                current=f"{listen[0]}={listen[1]}",
                required="Listen on the private ENI / VPC address only; no public IP; SG limited to admin + app subnets",
                evidence=f"{ev} ; grep listen_address {ev}",
                why="0.0.0.0 plus a public SG is a direct-to-internet admin path (standard §28 #15).",
            )

        unrestr = first_setting(
            settings,
            "dbms.security.procedures.unrestricted",
            "server.security.procedures.unrestricted",
        )
        if unrestr and unrestr[1] in {"*", "apoc.*"}:
            add_change(
                changes,
                family="AC-6 / CM-7 / SI-7",
                current=f"{unrestr[0]}={unrestr[1]}",
                required="Allowlist only the APOC procedures the mission needs; deny unrestricted *",
                evidence=f"{ev} ; grep procedures.unrestricted {ev}",
                why="Unrestricted APOC is a privilege and plugin-surface hold.",
            )

        qlog = first_setting(
            settings,
            "db.logs.query.enabled",
            "dbms.logs.query.enabled",
            "server.logs.query.enabled",
        )
        if qlog and qlog[1].lower() in {"false", "off", "0"}:
            add_change(
                changes,
                family="AU-2 / AU-12",
                current=f"{qlog[0]}={qlog[1]}",
                required="Enable query logging (INFO or VERBOSE per AU policy) and ship to CloudWatch / SIEM",
                evidence=f"{ev} ; grep query {ev}",
                why="No query log means AU-2/AU-12 cannot be examined from the graph.",
            )

    apoc = evidence / "neo4j" / "apoc.conf.redacted"
    if not apoc.exists():
        apoc = evidence / "neo4j" / "apoc.conf"
    if is_present(apoc):
        apoc_s = parse_settings(apoc.read_text(encoding="utf-8", errors="replace"))
        ev = str(apoc.relative_to(evidence)).replace("\\", "/")
        import_ok = first_setting(apoc_s, "apoc.import.file.enabled", "apoc.export.file.enabled")
        if import_ok and import_ok[1].lower() in {"true", "1", "yes"}:
            add_change(
                changes,
                family="AC-6 / SI-7",
                current=f"{import_ok[0]}={import_ok[1]}",
                required="Disable APOC file import/export unless a documented mission need and path allowlist exist",
                evidence=f"{ev} ; grep import {ev}",
                why="APOC file import/export expands the host filesystem trust boundary.",
            )

    # AWS / EC2 shape
    inst = evidence / "ec2" / "instance.json"
    if is_present(inst):
        try:
            doc = json.loads(inst.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            doc = {}
        ev = "ec2/instance.json"
        reservations = doc.get("Reservations") or []
        insts = []
        for r in reservations:
            insts.extend(r.get("Instances") or [])
        if not insts and doc.get("InstanceId"):
            insts = [doc]
        for it in insts:
            pub = it.get("PublicIpAddress")
            if pub:
                add_change(
                    changes,
                    family="SC-7 / AC-17",
                    current=f"PublicIpAddress={pub}",
                    required="No public IPv4/IPv6 on the Neo4j instance; private subnet + SSM (or jump via VDMS)",
                    evidence=f"{ev} ; aws ec2 describe-instances --instance-ids <id>",
                    why="Public IP on an IL5 graph host is a classic §28 direct-to-internet path.",
                )
            meta = it.get("MetadataOptions") or {}
            tokens = (meta.get("HttpTokens") or "").lower()
            if tokens and tokens != "required":
                add_change(
                    changes,
                    family="CM-6 / AC-6",
                    current=f"MetadataOptions.HttpTokens={meta.get('HttpTokens')}",
                    required="IMDSv2 required (HttpTokens=required, hop limit 1 or 2 as designed)",
                    evidence="ec2/imds.json ; aws ec2 describe-instances",
                    why="IMDSv1 is not an IL5-ready instance metadata posture.",
                )
            az = ((it.get("Placement") or {}).get("AvailabilityZone") or "")
            if az and not az.startswith("us-gov-"):
                add_change(
                    changes,
                    family="SA-9(5) / PE-18",
                    current=f"AvailabilityZone={az}",
                    required="Place compute in AWS GovCloud (us-gov-west-1 or us-gov-east-1), not a commercial partition",
                    evidence=f"{ev} ; ec2/region.txt",
                    why="IL5 processing/storage/admin must be US federal-community (standard §8.1). Commercial ≠ GovCloud.",
                )

    imds = evidence / "ec2" / "imds.json"
    if is_present(imds):
        try:
            meta = json.loads(imds.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            meta = {}
        tokens = (meta.get("HttpTokens") or "").lower()
        if tokens and tokens != "required":
            add_change(
                changes,
                family="CM-6 / AC-6",
                current=f"HttpTokens={meta.get('HttpTokens')}",
                required="HttpTokens=required (IMDSv2)",
                evidence="ec2/imds.json",
                why="IMDSv2 required.",
            )

    ebs = evidence / "ec2" / "ebs-volumes.json"
    if is_present(ebs):
        try:
            doc = json.loads(ebs.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            doc = {}
        for vol in doc.get("Volumes") or []:
            if not vol.get("Encrypted"):
                add_change(
                    changes,
                    family="SC-28 / SC-13",
                    current=f"Volume {vol.get('VolumeId')} Encrypted=false",
                    required="EBS encryption on, customer-managed KMS in aws-us-gov, FIPS-validated CMK path",
                    evidence="ec2/ebs-volumes.json ; aws ec2 describe-volumes",
                    why="Unencrypted EBS holding a graph store fails SC-28. AWS-managed key vs CMK must be written in the CRM.",
                )
            kms = vol.get("KmsKeyId") or ""
            if vol.get("Encrypted") and kms and "arn:aws:" in kms and "arn:aws-us-gov:" not in kms:
                add_change(
                    changes,
                    family="SC-12 / SA-9",
                    current=f"KmsKeyId={kms}",
                    required="KMS key in the GovCloud partition (arn:aws-us-gov:kms:...)",
                    evidence="ec2/ebs-volumes.json",
                    why="Commercial-partition KMS is not GovCloud inheritance.",
                )

    sgs = evidence / "ec2" / "security-groups.json"
    if is_present(sgs):
        try:
            doc = json.loads(sgs.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            doc = {}
        for sg in doc.get("SecurityGroups") or []:
            for perm in sg.get("IpPermissions") or []:
                from_port = perm.get("FromPort")
                for rng in perm.get("IpRanges") or []:
                    cidr = rng.get("CidrIp") or ""
                    if cidr == "0.0.0.0/0" and from_port in {7473, 7474, 7687, 22, 443, None}:
                        add_change(
                            changes,
                            family="SC-7 / AC-4",
                            current=f"SG {sg.get('GroupId')} port {from_port} CidrIp=0.0.0.0/0",
                            required="Restrict Bolt/HTTPS/SSH to named admin/app CIDRs or prefix lists; no world-open 7687/7474/22",
                            evidence="ec2/security-groups.json ; aws ec2 describe-security-groups",
                            why="World-open graph ports fail SC-7 even if TLS is on.",
                        )

    region = evidence / "ec2" / "region.txt"
    if is_present(region):
        text = region.read_text(encoding="utf-8", errors="replace").strip()
        if text and not text.startswith("us-gov-"):
            add_change(
                changes,
                family="SA-9 / PE-18",
                current=f"region={text}",
                required="us-gov-west-1 or us-gov-east-1 (partition aws-us-gov)",
                evidence="ec2/region.txt",
                why="Commercial regions are not IL5 federal-community clouds (standard §8.3, §22).",
            )

    fips = evidence / "os" / "fips.txt"
    if is_present(fips):
        text = fips.read_text(encoding="utf-8", errors="replace")
        if "fips_enabled=0" in text or re.search(r"fips_enabled\s*[:=]\s*0", text):
            add_change(
                changes,
                family="SC-13 / IA-7",
                current="fips_enabled=0",
                required="OS FIPS mode on; Neo4j/JVM using a CMVP-validated module in FIPS mode; cite Appendix Q",
                evidence="os/fips.txt ; cat /proc/sys/crypto/fips_enabled",
                why="AES-256 or 'FIPS-compliant OpenSSL' without a CMVP cert fails SC-13 (standard §9, §28 #5).",
            )

    return changes


def write_config_changes(path: Path, changes: list[dict[str, str]]) -> None:
    lines = [
        "# Configuration change recommendations",
        "",
        "Format: **current → required → evidence**.",
        "This list is not an ATO, PA, or FedRAMP authorization.",
        "The answerer never marks PASS. A human / Codex must read the cited file.",
        "",
    ]
    if not changes:
        lines.append("No automated current→required rows were derived from the files that are present.")
        lines.append("Absence of a row is not a PASS. Most of the 4003-question bank remains MISSING until evidence exists.")
        lines.append("")
    for i, ch in enumerate(changes, 1):
        lines.append(f"## {i}. {ch['family']}")
        lines.append("")
        lines.append(f"- **current:** `{ch['current']}`")
        lines.append(f"- **required:** {ch['required']}")
        lines.append(f"- **evidence:** `{ch['evidence']}`")
        lines.append(f"- **why:** {ch['why']}")
        lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")


def grade_from_counts(
    *,
    path_label: str,
    tallies: Counter[str],
    in_scope: int,
    bank_ok: bool,
    high_only_claiming_il5: bool,
    changes: list[dict[str, str]],
) -> str:
    if not bank_ok:
        return "HOLD"
    if high_only_claiming_il5:
        return "HOLD"
    # Stub never PASSes, so it never reaches READY. READY is a human/Codex upgrade.
    if tallies["MISSING"] == in_scope:
        return "HOLD"
    if tallies["PASS"] == 0:
        return "HOLD"
    return "HOLD"


def render_report(
    *,
    grade: str,
    path_label: str,
    tallies: Counter[str],
    in_scope: int,
    answered: int,
    artifact: str,
    answers_path: str,
    changes_path: str,
    evidence: str,
    notes: list[str],
) -> str:
    def cov(name: str, verdict: str, text: str) -> str:
        return f"- {name}: {verdict} — {text}"

    missing_n = tallies["MISSING"]
    hold_n = tallies["HOLD"]
    lines = [
        f"GRADE: {grade}",
        "",
        f"PATH: {path_label}",
        "",
        "COVERAGE:",
        cov("Categorization", "HOLD" if path_label else "MISSING", "Scored from intake only; no FIPS 199 worksheet was invented."),
        cov("Control stack", "HOLD", "Production HIGH bank is NIST 800-53B HIGH (4003 53A rows), not FedRAMP Appendix A. Overlays are hooks, not a downloaded SSP Addendum."),
        cov("IL5 architecture", "HOLD" if "IL5" in path_label else "N/A", "GovCloud + citizenship + CAC/PIV + FIPS 140-3 + BCAP remain evidence-gated (standard §8–§12)."),
        cov("Scan program (§14)", "MISSING" if missing_n else "HOLD", "Authenticated OS/web/DB/STIG corpus must match inventory. Collector is config inspection, not a 3PAO scan of record."),
        cov("POA&M / ConMon", "MISSING", "No POA&M workbook was invented."),
        cov("Package artifacts", "MISSING", "SSP appendices / CRM were not generated."),
        cov("§28 failure modes", "HOLD", "See CONFIG-CHANGES.md and GAPS. High alone fails IL5."),
        "",
        "QUESTIONS:",
        f"- in_scope: {in_scope}",
        f"- answered: {answered}",
        f"- PASS: {tallies['PASS']}",
        f"- HOLD: {tallies['HOLD']}",
        f"- WARN: {tallies['WARN']}",
        f"- N/A: {tallies['N/A']}",
        f"- MISSING: {tallies['MISSING']}",
        f"- artifact: {artifact}",
        f"- answers: {answers_path}",
        "",
        "GAPS (ordered by assessment risk):",
    ]
    gaps = [
        "This stub never invents PASS. READY is not ATO. A human GRC / 3PAO prep review is still required.",
        "Building only to FedRAMP High fails an IL5 assessment (standard hard truth; §28 #18).",
        "Customer-managed Neo4j on EC2 is not covered by the AWS GovCloud PA (standard §22.2).",
    ]
    if hold_n:
        gaps.append(f"{hold_n} questions have cited evidence files but are HOLD until a human/Codex reads those files.")
    if missing_n:
        gaps.append(f"{missing_n} in-scope questions have no mapped evidence file (MISSING).")
    if changes_path:
        gaps.append(f"Configuration change list: {changes_path}")
    for i, g in enumerate(gaps, 1):
        lines.append(f"{i}. {g}")
    lines.extend(
        [
            "",
            "PLAIN ENGLISH:",
            "- What this solution is aiming for: evidence-backed answers on the production HIGH 800-53A bank for Neo4j on EC2 in US GovCloud, toward FedRAMP High plus DoD IL5 — not an authorization.",
            "- What already looks solid: the 4003-question production HIGH bank is in-tree; collectors write cited paths under evidence/<run-id>/.",
            "- What would bounce a 3PAO / DISA reviewer: guessed PASS marks, High-only sold as IL5, commercial-region hosts, unauthenticated scans, inventory that does not match the instance, missing FIPS module certificates, treating CMMC as an IL5 PA.",
            "- What to do next (top 3): (1) read CONFIG-CHANGES.md and close current→required rows, (2) fill MISSING evidence (SSP, CRM, STIG, authenticated scans, citizenship, CAC/PIV), (3) have a human upgrade HOLD→PASS only where the cited file actually meets the 53A objective.",
            "",
        ]
    )
    if notes:
        lines.append("NOTES:")
        for n in notes:
            lines.append(f"- {n}")
        lines.append("")
    lines.append(f"evidence: {evidence}")
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Answer the production HIGH bank from evidence. Never invents PASS. Never ATO."
    )
    parser.add_argument(
        "--bank",
        default=str(DEFAULT_BANK),
        help="Question JSONL (default: production HIGH 4003)",
    )
    parser.add_argument(
        "--map",
        default=str(DEFAULT_MAP),
        help="Collector → family map JSON",
    )
    parser.add_argument(
        "--evidence",
        required=True,
        help="evidence/<run-id> directory from collect_neo4j_ec2_evidence.sh",
    )
    parser.add_argument(
        "--path",
        default="IL5 non-NSS",
        help="Target stack: FedRAMP High | IL5 non-NSS | IL5 NSS",
    )
    parser.add_argument(
        "--shared-responsibility",
        default="IaaS",
        help="IaaS | PaaS | SaaS | unknown",
    )
    parser.add_argument(
        "--out-dir",
        default="",
        help="Where to write answers JSONL + GRADE.md (default: the evidence dir)",
    )
    parser.add_argument(
        "--include-overlay",
        action="store_true",
        help="Also answer IL5 overlay hooks (not an official addendum count)",
    )
    parser.add_argument(
        "--allow-fixture-bank",
        action="store_true",
        help="Permit fixtures/question-bank (unit tests only)",
    )
    args = parser.parse_args(argv)

    bank_path = Path(args.bank)
    evidence = Path(args.evidence)
    map_path = Path(args.map)
    out_dir = Path(args.out_dir) if args.out_dir else evidence
    out_dir.mkdir(parents=True, exist_ok=True)

    notes: list[str] = []
    if not bank_path.exists():
        die(f"production HIGH bank missing: {bank_path} — HOLD")
    try:
        bank_path.relative_to(FIXTURE_BANK.parent)
        fixtureish = True
    except ValueError:
        fixtureish = "fixtures/question-bank" in str(bank_path).replace("\\", "/")
    if fixtureish and not args.allow_fixture_bank:
        die("refusing fixtures/question-bank without --allow-fixture-bank (fixture-only, not production)")

    if not evidence.exists():
        die(f"evidence directory not found: {evidence}")
    if not map_path.exists():
        die(f"map not found: {map_path}")

    questions = load_jsonl(bank_path)
    mapping = load_json(map_path)
    path_label = normalize_path(args.path)
    if args.include_overlay or path_label in {"IL5 non-NSS", "IL5 NSS"}:
        questions = questions + load_overlay_questions()
        if path_label in {"IL5 non-NSS", "IL5 NSS"}:
            notes.append("IL5 overlay hooks appended. They are not a downloaded DoD SSP Addendum / CNSSI workbook.")

    collectors = build_presence(evidence, mapping)
    changes = inspect_config_changes(evidence)
    changes_path = out_dir / "CONFIG-CHANGES.md"
    write_config_changes(changes_path, changes)

    answers: list[dict[str, Any]] = []
    tallies: Counter[str] = Counter()
    in_scope = 0
    for q in questions:
        applicability = q.get("path_applicability") or [
            "FedRAMP High",
            "IL5 non-NSS",
            "IL5 NSS",
        ]
        row = {
            "id": q.get("id"),
            "control": q.get("control"),
            "enhancement": q.get("enhancement") or "",
            "objective_id": q.get("objective_id"),
            "method": q.get("method"),
            "layer": q.get("layer"),
            "question": q.get("question"),
            "verdict": "MISSING",
            "evidence_paths": [],
            "rationale": "",
        }
        if path_label not in applicability:
            row["verdict"] = "N/A"
            row["rationale"] = f"Out of path ({path_label} not in {applicability})."
            tallies["N/A"] += 1
            answers.append(row)
            continue
        in_scope += 1
        cites = cite_for_question(q, collectors)
        if cites:
            row["verdict"] = "HOLD"
            row["evidence_paths"] = cites
            row["rationale"] = (
                "Mapped evidence file(s) present. Stub will not invent PASS. "
                "Read the cited path(s) before upgrading."
            )
            tallies["HOLD"] += 1
        else:
            row["verdict"] = "MISSING"
            row["rationale"] = "No mapped evidence file present for this control/method."
            tallies["MISSING"] += 1
        if row["verdict"] == "PASS":
            die("internal error: stub emitted PASS")
        answers.append(row)

    if tallies["PASS"]:
        die("refusing to write answers: PASS count must be 0 in this stub")

    answered = tallies["HOLD"] + tallies["WARN"] + tallies["N/A"] + tallies["PASS"]
    high_only = path_label == "FedRAMP High"
    # If the operator asked for IL5 but only High evidence exists, still HOLD.
    grade = grade_from_counts(
        path_label=path_label,
        tallies=tallies,
        in_scope=in_scope,
        bank_ok=True,
        high_only_claiming_il5=False,
        changes=changes,
    )
    if high_only:
        notes.append("PATH is FedRAMP High only. High alone fails an IL5 assessment.")

    answers_path = out_dir / "answers.jsonl"
    with answers_path.open("w", encoding="utf-8") as fh:
        for row in answers:
            fh.write(json.dumps(row, ensure_ascii=False) + "\n")

    try:
        artifact = str(bank_path.resolve().relative_to(ROOT))
    except ValueError:
        artifact = str(bank_path)

    report = render_report(
        grade=grade,
        path_label=path_label,
        tallies=tallies,
        in_scope=in_scope,
        answered=answered,
        artifact=artifact,
        answers_path=str(answers_path),
        changes_path=str(changes_path),
        evidence=str(evidence),
        notes=notes,
    )
    grade_path = out_dir / "GRADE.md"
    grade_path.write_text(report, encoding="utf-8")

    summary = {
        "generated_at_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "grade": grade,
        "path": path_label,
        "shared_responsibility": args.shared_responsibility,
        "in_scope": in_scope,
        "answered": answered,
        "tallies": dict(tallies),
        "pass_emitted": 0,
        "never_invent_pass": True,
        "never_ato": True,
        "high_alone_fails_il5": True,
        "bank": artifact,
        "bank_question_rows": len(load_jsonl(bank_path)),
        "overlay_appended": bool(args.include_overlay or path_label in {"IL5 non-NSS", "IL5 NSS"}),
        "config_changes": len(changes),
        "answers": str(answers_path),
        "grade_md": str(grade_path),
        "config_changes_md": str(changes_path),
    }
    (out_dir / "SUMMARY.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")

    sys.stdout.write(report)
    print(f"wrote {answers_path}", file=sys.stderr)
    print(f"wrote {grade_path}", file=sys.stderr)
    print(f"wrote {changes_path}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
