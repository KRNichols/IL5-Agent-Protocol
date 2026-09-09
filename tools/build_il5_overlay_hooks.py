#!/usr/bin/env python3
"""Write exhaustive IL5 overlay / architecture hooks.

These are documented cite-hooks from FEDRAMP-HIGH-IL5-STANDARD.md.
They are NOT a downloaded DoD SSP Addendum or CNSSI catalog.
They do not invent official extra-control counts or DSPAV values.
Default verdict is MISSING until the operator hands evidence.
"""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEST = ROOT / "question-bank" / "il5-overlay-hooks.json"

IL5 = ["IL5 non-NSS", "IL5 NSS"]
NSS = ["IL5 NSS"]
ALL = ["FedRAMP High", "IL5 non-NSS", "IL5 NSS"]

SRC = (
    "IL5 overlay HOOKS — not a substitute for the official DoD Rev 5 SSP "
    "Addendum, SRG Control Crosswalk, or CNSSI 1253. public.cyber.mil / "
    "www.cyber.mil/dccs/dccs-documents/ is a login-walled LWC community; "
    "no machine-readable addendum was retrieved. CNSSI 1253 remains on "
    "cnss.gov. Rows cite FEDRAMP-HIGH-IL5-STANDARD.md §§6–28. They are "
    "not an invented extra-control count. Replace with official workbook "
    "extracts when the operator can download them. Default grade is "
    "MISSING until cited evidence is handed. Do not guess DSPAV values."
)


def r(
    control: str,
    enhancement: str,
    oid: str,
    method: str,
    layer: str,
    paths: list[str],
    question: str,
) -> dict:
    return {
        "control": control,
        "enhancement": enhancement,
        "objective_id": oid,
        "method": method,
        "layer": layer,
        "path_applicability": paths,
        "question": question,
    }


def dspav(control: str, enhancement: str, oid: str, label: str) -> list[dict]:
    cell = f"{control}({enhancement})" if enhancement else control
    return [
        r(
            control,
            enhancement,
            oid,
            "Examine",
            "FedRAMP+",
            IL5,
            f"Examine: Does the handed DoD Rev 5 SSP Addendum / Table D-1 / "
            f"DSPAV record the current DoD parameter for {label} ({cell})? "
            f"Cite the official addendum cell. Do not guess the value. "
            f"Official file was not fetchable from cyber.mil (standard §6).",
        ),
        r(
            control,
            enhancement,
            oid,
            "Interview",
            "FedRAMP+",
            IL5,
            f"Interview: Who applies the DoD {label} ({cell}) parameter, and "
            f"is it written in the SSP Addendum rather than silently edited "
            f"into the FedRAMP SSP? (standard §6.3)",
        ),
    ]


def rows() -> list[dict]:
    out: list[dict] = []

    # --- FedRAMP+ / Table D-1 cite hooks (illustrative IDs from standard §6.2) ---
    out += dspav("AC-7", "", "ac-7_dspav_cite", "privileged lockout")
    out += dspav("AU-5", "1", "au-5.1_dspav_cite", "audit-failure / capacity warning")
    out += dspav("CM-7", "5", "cm-7.5_dspav_cite", "least-functionality DSPAV")
    out += dspav("IA-5", "1", "ia-5.1_dspav_cite", "password-based authenticator DSPAV")
    out += dspav("PE-15", "", "pe-15_dspav_cite", "water-damage DSPAV")
    out += dspav("PS-3", "4", "ps-3.4_dspav_cite", "personnel citizenship / US-person")
    out += dspav("SA-4", "5", "sa-4.5_dspav_cite", "system/component/service configurations")
    out += dspav("SA-9", "1", "sa-9.1_dspav_cite", "external-service risk assessment")
    out += dspav("SA-9", "6", "sa-9.6_dspav_cite", "external-service DSPAV listed for IL4/5/6")
    out += dspav("SA-9", "7", "sa-9.7_dspav_cite", "external-service DSPAV listed for IL4/5/6")
    out += dspav("SA-9", "8", "sa-9.8_dspav_cite", "external-service DSPAV listed for IL4/5/6")
    out += dspav("SC-12", "6", "sc-12.6_dspav_cite", "PKI / key-establishment DSPAV")
    out += dspav("SC-17", "", "sc-17_dspav_cite", "PKI certificates per DoDI 8520.02 / 8520.03")
    out += dspav("SC-18", "", "sc-18_dspav_cite", "mobile-code DSPAV")
    out += dspav("SC-18", "2", "sc-18.2_dspav_cite", "mobile-code restrictions")

    out += [
        r(
            "PL-10",
            "",
            "pl-10_addendum_join",
            "Examine",
            "FedRAMP+",
            IL5,
            "Examine: Was FedRAMP High Appendix A joined to the current DoD "
            "Rev 5 SSP Addendum on Control ID, with every 'DoD added' / "
            "'parameter changed' / 'DSPAV required' row flagged? Do not use "
            "a blog extra-control count (standard §6.3, §28 #20).",
        ),
        r(
            "PL-11",
            "",
            "pl-11_high_alone",
            "Examine",
            "SRG",
            IL5,
            "Examine: Does the handed package admit that FedRAMP High alone "
            "fails an IL5 assessment, and show the FedRAMP+ / SRG / (if NSS) "
            "CNSSI layers as in-scope? High Marketplace listing is not a "
            "DISA PA (standard hard truth; §25; §28 #18).",
        ),
        r(
            "CA-2",
            "",
            "ca-2_delta_test",
            "Examine",
            "FedRAMP+",
            IL5,
            "Examine: Is each extra / changed FedRAMP+ row mapped to a test "
            "case a 3PAO or DISA SCA will run? Cite the SAP / addendum. "
            "Missing addendum = MISSING, not PASS (standard §6.3).",
        ),
    ]

    # --- Location / tenancy / management plane / data placement (§8) ---
    out += [
        r(
            "SA-9",
            "5",
            "sa-9.5_us_location",
            "Examine",
            "SRG",
            IL5,
            "Examine: Do SA-09(05) and PE-18 name United States / US "
            "outlying / DoD on-premises regions, facilities, and every "
            "replication target for IL5 processing, storage, and "
            "administration? Commercial-region hosts fail (standard §8.1).",
        ),
        r(
            "PE-18",
            "",
            "pe-18_us_location",
            "Examine",
            "SRG",
            IL5,
            "Examine: Does PE-18 document US-location of system components "
            "that process or store IL5 data, including backups and support "
            "staff reachability? Offshore admin of IL5 data fails "
            "(standard §8.1, §12.3).",
        ),
        r(
            "SA-9",
            "5",
            "sa-9.5_us_location",
            "Interview",
            "SRG",
            IL5,
            "Interview: Who can reach IL5 data from outside the United "
            "States, and is that path forbidden in the handed architecture?",
        ),
        r(
            "SC-7",
            "21",
            "sc-7.21_physical_separation",
            "Examine",
            "SRG",
            IL5,
            "Examine: Does the handed architecture show physical separation "
            "from non-DoD / non-federal tenants (no shared physical hosts, "
            "storage arrays, or switches with public/commercial tenants)? "
            "Virtual isolation among federal tenants is not enough to waive "
            "this (standard §8.2).",
        ),
        r(
            "SC-4",
            "",
            "sc-4_logical_separation",
            "Examine",
            "SRG",
            IL5,
            "Examine: Is virtual/logical separation among DoD and federal "
            "tenants documented, and is dedicated-host / isolated-VM / "
            "dedicated-tenancy the compute construct actually used? Do not "
            "assume cryptographic isolation unless the current PA says so "
            "(standard §8.2).",
        ),
        r(
            "SC-7",
            "20",
            "sc-7.20_federal_community",
            "Examine",
            "SRG",
            IL5,
            "Examine: Is the CSO a US federal-government community cloud "
            "(GovCloud / Azure Government / equivalent), not a public "
            "commercial stack with commercial neighbors (standard §8.3)?",
        ),
        r(
            "SA-9",
            "",
            "sa-9_mgmt_plane",
            "Examine",
            "SRG",
            IL5,
            "Examine: Is the CSO management plane isolated from the "
            "vendor's commercial cloud? Can a commercial-region admin reach "
            "IL5 hosts? Where do break-glass and hypervisor admins sit "
            "(standard §8.4)? A shared commercial management plane is a "
            "classic IL5 finding (§28 #2).",
        ),
        r(
            "SA-9",
            "",
            "sa-9_mgmt_plane",
            "Interview",
            "SRG",
            IL5,
            "Interview: How does the vendor corporate network touch the "
            "CSO, and can commercial-region staff administer IL5 hosts?",
        ),
        r(
            "SC-28",
            "",
            "sc-28_data_placement",
            "Examine",
            "SRG",
            IL5,
            "Examine: Is IL5 data (including backups, snapshots, logs, "
            "crash dumps, and support bundles) kept off non-federal "
            "physical media? Encryption does not waive physical-separation "
            "rules unless the current SRG/PA explicitly allows it "
            "(standard §8.5).",
        ),
        r(
            "CP-9",
            "8",
            "cp-9.8_backup_placement",
            "Examine",
            "SRG",
            IL5,
            "Examine: Are IL5 backups encrypted with a validated module "
            "and stored only in the federal-community / US-location "
            "boundary named in SA-09(05) (standard §8.5, §9.2)?",
        ),
    ]

    # --- SCCA / BCAP / network (§8.6, §11) ---
    out += [
        r(
            "AC-17",
            "3",
            "ac-17.3_bcap_scca",
            "Examine",
            "SRG",
            IL5,
            "Examine: If the CSO will connect to DoD networks, does the "
            "handed package show BCAP/SCCA-ready managed access points "
            "(AC-17(3)) rather than a High-only commercial edge? PA is not "
            "permission to connect (standard §8.6, §11).",
        ),
        r(
            "AC-17",
            "3",
            "ac-17.3_no_internet_path",
            "Examine",
            "SRG",
            IL5,
            "Examine: Is there a documented statement that there is no "
            "direct IL5 mission path across the open internet except "
            "through NIPRNet IAPs and a mission/DoD/DISA DMZ "
            "(standard §11.1)?",
        ),
        r(
            "SC-7",
            "3",
            "sc-7.3_cap",
            "Examine",
            "SRG",
            IL5,
            "Examine: Is the CAP (BCAP off-prem or ICAP on-prem) named, "
            "and is the circuit/path from the hosting enclave to that CAP "
            "in the architecture (standard §8.6, §11.2)? Collector configs "
            "cannot invent this — MISSING until the package shows it.",
        ),
        r(
            "SC-7",
            "",
            "sc-7_vdss",
            "Examine",
            "SRG",
            IL5,
            "Examine: Does the package show a Virtual Datacenter Security "
            "Stack (VDSS) — firewall, IDS/IPS, WAF facing the CAP — or a "
            "written mission-owner split that the CSO supports "
            "(standard §8.6)?",
        ),
        r(
            "AC-17",
            "",
            "ac-17_vdms",
            "Examine",
            "SRG",
            IL5,
            "Examine: Does the privileged path go through a Virtual "
            "Datacenter Management Stack (VDMS) / jump, not a coffee-shop "
            "split-tunnel laptop into IL5 (standard §8.6, §11.4, SC-07(07))?",
        ),
        r(
            "IA-5",
            "",
            "ia-5_tccm",
            "Examine",
            "SRG",
            IL5,
            "Examine: Is a Trusted Cloud Credential Manager (TCCM) or "
            "equivalent vault/issuance path documented for cloud-admin "
            "credentials (standard §8.6)?",
        ),
        r(
            "CM-7",
            "",
            "cm-7_ppsm",
            "Examine",
            "SRG",
            IL5,
            "Examine: Are ports, protocols, and services registered under "
            "DoDI 8551.01 PPSM for any DoD-connected path? Unregistered PPS "
            "is a connection-approval finding (standard §11.3).",
        ),
        r(
            "SC-20",
            "",
            "sc-20_dod_dns",
            "Examine",
            "SRG",
            IL5,
            "Examine: If DoD-connected, does DNS go through DoD-approved "
            "DNS as the SRG requires (standard §11.3)?",
        ),
        r(
            "CA-3",
            "",
            "ca-3_snap_catc_cptc",
            "Examine",
            "SRG",
            IL5,
            "Examine: For a DoD-connected CSO, are SNAP / CATC / CPTC / "
            "SCCA activation artifacts present or explicitly not-yet "
            "(standard §11.5–§11.6)? A FedRAMP High listing does not skip "
            "these. Do not invent connection tickets.",
        ),
        r(
            "IR-4",
            "",
            "ir-4_cssp",
            "Examine",
            "SRG",
            IL5,
            "Examine: Is the CSSP named and is sensor-insertion / "
            "monitoring live-before-traffic addressed (standard §11.6, "
            "§18.3)?",
        ),
    ]

    # --- Crypto (§9) ---
    out += [
        r(
            "SC-13",
            "",
            "sc-13_fips_140-3",
            "Examine",
            "SRG",
            IL5,
            "Examine: When crypto is in scope, does the handed package "
            "cite active FIPS 140-3 CMVP module certificates (not "
            "historical, not revoked) for the modules actually used, "
            "operated in FIPS mode (standard §9.1, §28 #5)? "
            "'FIPS-compliant' or 'AES-256' without a CMVP cert fails.",
        ),
        r(
            "SC-13",
            "",
            "sc-13_fips_140-3",
            "Test",
            "SRG",
            IL5,
            "Test: Does the handed evidence show FIPS mode enabled on "
            "in-scope modules, not merely licensed (standard §9.1, §24.5)?",
        ),
        r(
            "SC-13",
            "",
            "sc-13_140-2_sunset",
            "Examine",
            "SRG",
            IL5,
            "Examine: If any FIPS 140-2 module remains, is there a "
            "documented transition off the CMVP historical list "
            "(140-2 goes historical 21 Sep 2026) (standard §9.3, §28 #6)?",
        ),
        r(
            "SC-12",
            "",
            "sc-12_cmk_hsm",
            "Examine",
            "SRG",
            IL5,
            "Examine: Are customer-managed keys for IL5 mission data "
            "HSM-backed, stored separately from ciphertext, with SC-12(01) "
            "availability documented (standard §9.4)?",
        ),
        r(
            "SC-8",
            "1",
            "sc-8.1_tls",
            "Examine",
            "SRG",
            IL5,
            "Examine: Is in-transit crypto TLS 1.2 minimum / 1.3 preferred "
            "using a validated module in FIPS mode? SSL / TLS 1.0 / 1.1 "
            "are forbidden (NIST SP 800-52 Rev 2; standard §9.2).",
        ),
        r(
            "SC-17",
            "",
            "sc-17_dod_pki",
            "Examine",
            "SRG",
            IL5,
            "Examine: Do DoD-facing endpoints use DoD PKI (or an "
            "AO-approved commercial-PKI path per DoDI 8520.02)? Let's "
            "Encrypt / public CA is not a default for IL5 DoD-facing "
            "endpoints (standard §9.5).",
        ),
        r(
            "AU-9",
            "3",
            "au-9.3_log_crypto",
            "Examine",
            "SRG",
            IL5,
            "Examine: Are audit logs cryptographically protected with a "
            "validated module (AU-09(03); standard §9.2, §19)?",
        ),
        r(
            "PL-2",
            "",
            "pl-2_appendix_q",
            "Examine",
            "SRG",
            IL5,
            "Examine: Does SSP Appendix Q list every cryptographic module, "
            "version, CMVP certificate number, and FIPS-mode evidence "
            "(standard §9.3, §23.1, §28 #16)? Missing cert numbers = HOLD.",
        ),
    ]

    # --- Identity / CAC/PIV (§10) ---
    out += [
        r(
            "IA-2",
            "12",
            "ia-2.12_cac_piv",
            "Examine",
            "SRG",
            IL5,
            "Examine: Does the handed package show CAC/PIV (or approved "
            "PKI) for privileged DoD users at Credential Strength D, with "
            "the implementation cited from the package — not inferred "
            "(standard §10.2)? Software TOTP alone is not Strength D "
            "(§28 #4).",
        ),
        r(
            "IA-2",
            "1",
            "ia-2.1_privileged_mfa",
            "Examine",
            "SRG",
            IL5,
            "Examine: Do CSP privileged admins use a hardware token or "
            "PKI, US persons, no shared accounts (standard §10.2, §12)?",
        ),
        r(
            "IA-5",
            "7",
            "ia-5.7_no_static_secrets",
            "Examine",
            "SRG",
            IL5,
            "Examine: Are service accounts / NPEs PKI or hardware-backed "
            "with no embedded unencrypted static authenticators "
            "(IA-05(07); standard §10.2)?",
        ),
        r(
            "IA-8",
            "",
            "ia-8_federation",
            "Examine",
            "SRG",
            IL5,
            "Examine: If federated to DoD ICAM / mission IdP, are IA-08 "
            "profiles, assertion protection, and IdP-down behavior "
            "documented without a local password fallback below Strength D "
            "(standard §10.3)?",
        ),
        r(
            "IA-2",
            "12",
            "ia-2.12_cac_piv",
            "Interview",
            "SRG",
            IL5,
            "Interview: How do privileged DoD users authenticate to the "
            "CSO and to customer-managed apps (including Neo4j if in "
            "scope) — CAC/PIV/PKI or software TOTP?",
        ),
    ]

    # --- Personnel / citizenship (§12) ---
    out += [
        r(
            "PS-3",
            "4",
            "ps-3.4_srg_citizenship",
            "Examine",
            "SRG",
            IL5,
            "Examine: Does the handed package show US-citizen privileged "
            "access to IL5 CSO infrastructure, and US citizens / nationals "
            "/ US persons for broader IL4/5 users per the current SRG / "
            "PS-03(04), with foreign persons only by AO approval? Cite the "
            "official row. CMMC is not a substitute (standard §12.1, §27).",
        ),
        r(
            "PS-3",
            "",
            "ps-3_screening",
            "Examine",
            "SRG",
            IL5,
            "Examine: Is privileged screening (typical public bar: ADP-2 / "
            "IT-2 / Tier 3 plus NDA, or the AO's written tier) evidenced "
            "for people who can reach IL5 hosts or keys (standard §12.2)?",
        ),
        r(
            "PS-4",
            "2",
            "ps-4.2_leaver",
            "Examine",
            "SRG",
            IL5,
            "Examine: Can a leaver's cloud-admin tokens be disabled fast "
            "enough (PS-04 automated actions) that they cannot retain IL5 "
            "admin (standard §12.3)?",
        ),
        r(
            "PS-3",
            "4",
            "ps-3.4_srg_citizenship",
            "Interview",
            "SRG",
            IL5,
            "Interview: Where does 24x7 ops sit, and can break-glass route "
            "through an offshore NOC (standard §12.3, §28 #3)?",
        ),
        r(
            "MA-5",
            "",
            "ma-5_nonlocal",
            "Examine",
            "SRG",
            IL5,
            "Examine: Does nonlocal / vendor maintenance of IL5 systems "
            "originate only from US / eligible staff — not non-US / "
            "non-cleared staff over the open internet (standard §5.9)?",
        ),
    ]

    # --- STIG / SCAP / ACAS (§13) ---
    out += [
        r(
            "CM-6",
            "",
            "cm-6_stig_matrix",
            "Examine",
            "SRG",
            IL5,
            "Examine: Is there a STIG/SRG coverage matrix for every "
            "in-scope product class (guest OS, Neo4j/app, jump host, "
            "logging, backup, admin workstations) with STIG ID, scan tool, "
            "last result date, and CAT I count (standard §13.3)?",
        ),
        r(
            "CM-6",
            "",
            "cm-6_stig_cat1",
            "Examine",
            "SRG",
            IL5,
            "Examine: Are open STIG CAT I findings zero at the claimed "
            "authorization posture? CAT I is High/severe — none open at "
            "ATO/PA (standard §13.2). STIG-once-never-again fails (§28 #11).",
        ),
        r(
            "CM-6",
            "",
            "cm-6_stig_cat1",
            "Test",
            "SRG",
            IL5,
            "Test: Do handed SCAP / Evaluate-STIG / ACAS compliance "
            "results exist and map to Vuln IDs for the scanned inventory "
            "(standard §13.4)? Config collection is not a STIG of record.",
        ),
        r(
            "RA-5",
            "",
            "ra-5_acas",
            "Examine",
            "SRG",
            IL5,
            "Examine: For DISN-connected IaaS/PaaS, is ACAS (or a DISA-"
            "accepted equivalent feeding the CSSP) identified? SaaS may "
            "N/A ACAS but still owes FedRAMP authenticated scans "
            "(standard §13.5, §21).",
        ),
    ]

    # --- Scan program (§14) ---
    out += [
        r(
            "RA-5",
            "5",
            "ra-5.5_authenticated",
            "Examine",
            "SRG",
            ALL,
            "Examine: Are Moderate/High scans authenticated wherever "
            "possible (RA-05(05))? Unauthenticated ≥10% of a submission "
            "triggers DFR (standard §14.3, §28 #7).",
        ),
        r(
            "CM-8",
            "",
            "cm-8_inventory_match",
            "Examine",
            "SRG",
            ALL,
            "Examine: Does Appendix M inventory match scan targets and "
            "running systems (hostnames / IPs / image IDs)? Inventory ≠ "
            "scan targets is a hard hold (standard §14.6, §28 #8).",
        ),
        r(
            "RA-5",
            "",
            "ra-5_monthly_types",
            "Examine",
            "SRG",
            ALL,
            "Examine: Does the handed scan corpus include discovery, "
            "authenticated OS, web/API, database, container, IaC, "
            "SAST/secrets, and SCAP/STIG as applicable — not a single "
            "unauthenticated export (standard §14.1)?",
        ),
        r(
            "RA-5",
            "",
            "ra-5_cadence",
            "Examine",
            "SRG",
            ALL,
            "Examine: Is there a monthly-minimum authenticated OS+web+DB+"
            "container of 100% inventory (or AO-approved unique-class "
            "sample), with no sampling of internet-reachable assets "
            "(standard §14.2)?",
        ),
        r(
            "RA-5",
            "2",
            "ra-5.2_signatures",
            "Examine",
            "SRG",
            ALL,
            "Examine: Are scanner plugin/signature dates and config "
            "checksums attested, matching the last 3PAO-validated config "
            "(standard §14.3)?",
        ),
        r(
            "SA-11",
            "1",
            "sa-11.1_sast",
            "Examine",
            "SRG",
            ALL,
            "Examine: Is SAST / secret scan a pipeline gate on every "
            "release (SA-11(01); standard §14.1)?",
        ),
        r(
            "CA-8",
            "",
            "ca-8_pentest",
            "Examine",
            "SRG",
            ALL,
            "Examine: Is there a 3PAO (or rehearsal) pentest covering the "
            "six FedRAMP attack vectors, including tenant→tenant isolation "
            "(standard §15)? Automated scanning is not a pentest.",
        ),
        r(
            "CA-8",
            "2",
            "ca-8.2_red_team",
            "Examine",
            "SRG",
            ALL,
            "Examine: For High / Class D, are CA-08(02) red-team exercises "
            "scoped and scheduled separately from the annual pentest "
            "(standard §15.1)? This ID is FedRAMP High, not NIST 53B HIGH.",
        ),
    ]

    # --- POA&M / ConMon / incidents (§16–§18) ---
    out += [
        r(
            "CA-5",
            "",
            "ca-5_poam_template",
            "Examine",
            "SRG",
            ALL,
            "Examine: Is the official FedRAMP POA&M Excel used, one unique "
            "scanner ID per item (no bundled rows) (standard §16.1, §28 #9)?",
        ),
        r(
            "SI-2",
            "",
            "si-2_clocks",
            "Examine",
            "SRG",
            ALL,
            "Examine: Do remediation clocks start correctly (Critical/High "
            "30 days from detection; vendor patches 30 days from vendor "
            "release; KEV date if shorter) (standard §16.3)?",
        ),
        r(
            "CA-7",
            "",
            "ca-7_conmon_monthly",
            "Examine",
            "SRG",
            ALL,
            "Examine: Is a monthly ConMon package present or scheduled "
            "(raw scans, Appendix M, POA&M, deviations, exec summary, "
            "scanner attestation, incident list) (standard §17.1)?",
        ),
        r(
            "IR-6",
            "",
            "ir-6_clocks",
            "Examine",
            "SRG",
            ALL,
            "Examine: Does the IRP quote the live CR26 Incident Evaluation "
            "clocks for Class D (not a Moderate copy; confirm on freeze "
            "day) (standard §18.1, §28 #17)?",
        ),
        r(
            "IR-6",
            "",
            "ir-6_dod",
            "Examine",
            "SRG",
            IL5,
            "Examine: Are CSSP / CJCSM 6510.01 / (if CUI on a contractor "
            "enclave) DFARS 72-hour DIBNet paths written (standard §18.3)? "
            "DFARS/CMMC is not an IL5 PA.",
        ),
        r(
            "CM-3",
            "",
            "cm-3_significant_change",
            "Examine",
            "SRG",
            ALL,
            "Examine: Are boundary / tenancy / crypto / identity / data-flow "
            "moves typed as significant or transformative, with FedRAMP SCN "
            "and (for IL5) DISA RE2 / SCCA notice (standard §20)?",
        ),
    ]

    # --- Shared responsibility / inheritance / package (§21–§23) ---
    out += [
        r(
            "SA-9",
            "",
            "sa-9_crm",
            "Examine",
            "SRG",
            ALL,
            "Examine: Does the CRM / Appendix J name Implemented / "
            "Inherited / Shared / Customer / N/A per control, with "
            "inherited-from package ID + date (standard §21–§22)?",
        ),
        r(
            "SA-9",
            "",
            "sa-9_no_false_inherit",
            "Examine",
            "SRG",
            ALL,
            "Examine: Are customer-managed applications (including Neo4j "
            "on EC2) marked Customer for AC/IA/AU/SC/CM — not 'inherited "
            "from the AWS GovCloud PA'? A platform PA is service-by-service "
            "(standard §22.2, §28 #12, §28 #14).",
        ),
        r(
            "PL-2",
            "",
            "pl-2_ssp_appendices",
            "Examine",
            "SRG",
            ALL,
            "Examine: Are starred FedRAMP SSP appendices present or "
            "explicitly missing: A (High controls), F RoB, G ISCP, J CRM, "
            "M inventory, O POA&M, Q crypto modules — plus K FIPS 199, "
            "E identity, N ConMon, P SCRM (standard §23.1)? The scanner "
            "cannot invent these.",
        ),
        r(
            "RA-2",
            "",
            "ra-2_fips199",
            "Examine",
            "SRG",
            ALL,
            "Examine: Is there a written FIPS 199 / AO categorization "
            "(CIA + IL + NSS yes/no + overlays)? Skipping this and "
            "discovering NSS later is §28 #19 (standard §3, §23.1 App K).",
        ),
        r(
            "CA-2",
            "",
            "ca-2_sar_sap",
            "Examine",
            "SRG",
            ALL,
            "Examine: Are SAP, test-case workbook, SAR, RET, High SRTM, "
            "and 3PAO independence statement present if an assessment is "
            "claimed — or marked MISSING if not handed (standard §23.2)?",
        ),
        r(
            "CA-6",
            "",
            "ca-6_dod_delta",
            "Examine",
            "SRG",
            IL5,
            "Examine: Is the DoD delta package present or listed as not-"
            "yet: filled SSP Addendum, architecture briefing, onboarding "
            "questionnaire, eMASS import plan, SCCA/BCAP design, CSSP "
            "CONOPS, citizenship evidence (standard §23.3)?",
        ),
    ]

    # --- CNSSI / NSS / privacy (§7) ---
    out += [
        r(
            "IA-2",
            "",
            "ia-2_cnssi_nss",
            "Examine",
            "CNSSI",
            NSS,
            "Examine: If the path is IL5 NSS, does the handed package show "
            "the AO-selected CNSSI 1253 Table D-1 '+' rows from the "
            "official instruction (cnss.gov), not a blog count "
            "(standard §7, §28 #20)? ~170 extras is directional only.",
        ),
        r(
            "PL-10",
            "",
            "pl-10_cnssi_overlays",
            "Examine",
            "CNSSI",
            NSS,
            "Examine: Are applicable CNSSI attachments named (Privacy, "
            "ICS, CDS, Space) and is the Classified System Overlay "
            "explicitly not grabbed for IL5 (standard §7.2)?",
        ),
        r(
            "PT-2",
            "",
            "pt-2_privacy_overlay",
            "Examine",
            "CNSSI",
            IL5,
            "Examine: If DoD PII/PHI is in scope, is the current CNSSI "
            "Privacy Overlay plus SRG PII/PHI parameter tables applied "
            "(standard §7.3)? If PII is out of scope, say so with a cited "
            "boundary statement — do not invent N/A.",
        ),
        r(
            "RA-2",
            "",
            "ra-2_nss_memo",
            "Examine",
            "CNSSI",
            NSS,
            "Examine: Is the NSS determination under NIST SP 800-59 in "
            "writing from the sponsoring AO (standard §3.2, §7.1)?",
        ),
    ]

    # --- Related regimes / hard truths (§27, §28) ---
    out += [
        r(
            "CA-6",
            "",
            "ca-6_not_cmmc",
            "Examine",
            "SRG",
            IL5,
            "Examine: Does the package treat CMMC / NIST SP 800-171 / "
            "ITAR / SOC 2 as non-substitutes for a DISA IL5 PA "
            "(standard §27, §28 #18)?",
        ),
        r(
            "CA-6",
            "",
            "ca-6_not_cmmc",
            "Interview",
            "SRG",
            IL5,
            "Interview: Is anyone selling this slice as 'CMMC so we are "
            "IL5-ready'? That claim is a HOLD.",
        ),
        r(
            "CA-6",
            "",
            "ca-6_ready_not_ato",
            "Examine",
            "SRG",
            ALL,
            "Examine: Does any handed claim equate scanner READY / High "
            "Marketplace listing with ATO, FedRAMP authorization, or DISA "
            "PA? READY means ready for human GRC / 3PAO prep review of "
            "this slice only (AGENTS.md; KEYS.md; standard §25).",
        ),
        r(
            "SC-7",
            "",
            "sc-7_no_public_admin",
            "Examine",
            "SRG",
            IL5,
            "Examine: Are admin / Bolt / graph ports free of 0.0.0.0/0 and "
            "public IPs on IL5 hosts (standard §28 #15)? Config evidence "
            "may HOLD this; the stub still will not invent PASS.",
        ),
        r(
            "PL-8",
            "",
            "pl-8_architecture_narrative",
            "Examine",
            "SRG",
            IL5,
            "Examine: Does PL-08 describe tenant isolation, key "
            "management, and BCAP paths in enough detail that a 3PAO can "
            "pentest them (standard §5.12, §8)?",
        ),
        r(
            "AU-8",
            "",
            "au-8_time_cssp",
            "Examine",
            "SRG",
            IL5,
            "Examine: Are clocks UTC from an authoritative source "
            "(SC-45(01) / AU-08) and are logs queryable by CSP IR and CSSP "
            "without a days-long ticket (standard §19)?",
        ),
        r(
            "SC-45",
            "1",
            "sc-45.1_authoritative",
            "Examine",
            "SRG",
            ALL,
            "Examine: Is SC-45 / SC-45(01) implemented (authoritative time "
            "source)? These IDs are in FedRAMP High / Class D and are "
            "absent from NIST SP 800-53B HIGH (standard §5.16, §19).",
        ),
    ]

    return out


def main() -> int:
    payload = {
        "format": "il5-overlay-rows-v1",
        "source": SRC,
        "official_workbooks_not_fetched": [
            "https://public.cyber.mil/dccs/dccs-documents/",
            "https://www.cyber.mil/dccs/dccs-documents/",
            "DoD Rev 5 SSP Addendum Controls v1.2",
            "DoD SRG Control Crosswalk",
            "https://www.cnss.gov/CNSS/issuances/Instructions.cfm",
        ],
        "not_an_official_control_count": True,
        "high_alone_fails_il5": True,
        "never_invent_pass": True,
        "default_verdict_until_evidence": "MISSING",
        "rows": rows(),
    }
    DEST.parent.mkdir(parents=True, exist_ok=True)
    DEST.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {len(payload['rows'])} overlay hooks to {DEST}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
