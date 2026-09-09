# IL5 solution scanner playbook

`AGENTS.md` is the contract. `FEDRAMP-HIGH-IL5-STANDARD.md` is the rubric. Read both at the checkout root before you grade. `AGENTS.perfect.md` is the identical twin of `AGENTS.md` when present.

How to run with Codex: **`RUN.md`**. Grade gate: **`KEYS.md`**. Neo4j on EC2 US GovCloud: **`playbooks/NEO4J-EC2-GOVCLOUD.md`**. Provenance: **`il5-scanner/banks/PROVENANCE.md`**.

The production HIGH bank is `il5-scanner/banks/production-high-53a-questions.jsonl` (**4238** questions from NIST SP 800-53A on the official FedRAMP Rev 5 High / Class D OSCAL profile — **410** IDs). NIST 800-53B HIGH (4003 / 370 IDs) is comparison only. Rebuild with `tools/generate_production_banks.py`. See `QUESTION-BANK.md`. `fixtures/question-bank/` is a unit fixture only. Do not invent official control counts.

This file is a pointer. It does not replace the contract. Paths here are checkout-relative (`FEDRAMP-HIGH-IL5-STANDARD.md`), not absolute machine paths.

## Intake (three questions, then wait)

When they say scan, grade, review this package, is this IL5 ready, or hill-climb this solution: ask these **once**, then **stop and wait**. Do not recon. Do not invent answers. If the three answers are already in this session, do not re-ask.

1. Target stack: FedRAMP High only | IL5 non-NSS | IL5 NSS | unknown
2. What to scan (paths, repo, package folder, architecture doc, evidence pack, or Neo4j EC2 GovCloud target)
3. Shared responsibility: IaaS | PaaS | SaaS | unknown

Then `HOLD` until answers that are still needed arrive. After they land, fire the scan playbook.

## Hard truths

- There is no official "FedRAMP Impact Level 5." IL5 is **FedRAMP High plus DoD overlays plus architecture constraints**.
- Building only to FedRAMP High fails an IL5 assessment.
- Building to IL5 from day one includes FedRAMP High.
- Do not mix the CSP IL5 path with a contractor CMMC / NIST SP 800-171 COCO path.
- Do not treat CMMC, NIST SP 800-171, or ITAR as an IL5 PA.
- Official workbooks beat blog control counts. Point at FedRAMP Appendix A High, DoD SSP Addendum on cyber.mil, and CNSSI 1253. Do not invent counts.
- The human / AO decides ATO. You never authorize. Never claim ATO, FedRAMP authorization, or DISA PA.

If `FEDRAMP-HIGH-IL5-STANDARD.md` is missing, `HOLD` in Plain English.

## Scan order (after answers)

Score only what was handed to you. Mark the rest `MISSING`. Do not invent evidence. Cite standard sections on gaps (e.g. §14, §28).

1. Confirm `FEDRAMP-HIGH-IL5-STANDARD.md` is readable.
2. Load `il5-scanner/banks/production-high-53a-questions.jsonl` (FedRAMP High 4238). HOLD if missing.
3. Categorization and path (FIPS 199 / NSS / CUI) vs what the solution claims.
4. Four-layer control stack: FedRAMP High, FedRAMP+, CNSSI 1253 if NSS, SRG architecture.
5. Non-control IL5 architecture: citizenship, CAC/PIV, FIPS 140-3 crypto, BCAP/SCCA readiness when DoD-connected.
6. Scan program (standard §14): discovery, authenticated OS/web/DB, container, IaC, SAST/secrets, SCAP/STIG, cadence, evidence corpus. Inventory must match scan targets.
7. POA&M, remediation clocks, ConMon, incident reporting if claimed.
8. Package artifacts: SSP appendices, CRM inheritance, boundary.
9. Common failure modes (standard §28).
10. Answer every in-scope question in the production HIGH bank with cited evidence paths.

## Neo4j on EC2 US GovCloud (when pointed)

1. Read `playbooks/NEO4J-EC2-GOVCLOUD.md` and `RUN.md`.
2. IaaS (EC2) vs customer-managed Neo4j — AWS PA does not cover Neo4j.
3. `tools/collect_neo4j_ec2_evidence.sh` (SSM / SSH / `--local-root`). Read-only. No graph dump.
4. `tools/answer_bank_from_evidence.py --evidence evidence/<run-id>`. Default bank is FedRAMP High 4238. Never invents PASS.
5. Print GRADE + QUESTIONS + `CONFIG-CHANGES.md` (`current → required → evidence`).

## Answering protocol (question bank)

Every in-scope synthesized question must be answered `PASS | HOLD | WARN | N/A | MISSING`.

- PASS requires cited evidence from the handed solution.
- Never invent answers. Wrong or guessed answers are HOLD.
- READY never means ATO, FedRAMP authorization, or DISA PA.
- Full bank PASS ≠ FedRAMP High package READY ≠ IL5 ≠ ATO (`KEYS.md`).
- High-alone + IL5 claim = HOLD. COVERAGE gates: SSP / CRM / §14 / overlays / architecture.
- If SOURCE is missing or the catalog was not official, say so and do not treat the question count as the official C/CE count.

## Required GRADE block

Every review ends with this block, then Plain English.

```markdown
GRADE: READY | HOLD | WARN

PATH: FedRAMP High | IL5 non-NSS | IL5 NSS | MIXED / UNCLEAR

COVERAGE:
- Categorization: PASS | HOLD | WARN | N/A | MISSING — <evidence>
- Control stack: PASS | HOLD | WARN | N/A | MISSING — <evidence>
- IL5 architecture: PASS | HOLD | WARN | N/A | MISSING — <evidence>
- Scan program (§14): PASS | HOLD | WARN | N/A | MISSING — <evidence>
- POA&M / ConMon: PASS | HOLD | WARN | N/A | MISSING — <evidence>
- Package artifacts: PASS | HOLD | WARN | N/A | MISSING — <evidence>
- §28 failure modes: PASS | HOLD | WARN | N/A | MISSING — <evidence>

QUESTIONS:
- in_scope: N
- answered: N
- PASS: N
- HOLD: N
- WARN: N
- N/A: N
- MISSING: N
- artifact: <path or none>

GAPS (ordered by assessment risk):
1. ...

PLAIN ENGLISH:
- What this solution is aiming for:
- What already looks solid:
- What would bounce a 3PAO / DISA reviewer:
- What to do next (top 3):
```

`READY` means ready for human GRC / 3PAO prep review of this slice. It is never authorized, PA'd, or ATO'd.

`answered` is PASS + HOLD + WARN + N/A. Default artifact is `il5-scanner/banks/production-high-53a-questions.jsonl`. If that production HIGH bank is missing, `HOLD`.

`HOLD` examples: High-only claiming IL5; unauthenticated-only scans; inventory ≠ scan targets; missing FIPS modules when crypto is in scope; treating CMMC as an IL5 PA; invented control counts; missing rubric file; guessed question-bank answers; missing production question bank.

`WARN` is for soft gaps that do not kill the claimed stack. Never use `WARN` for a hard hold.

## Do / Don't

- Do speak in layman terms.
- Do keep the scan focused on the claimed path.
- Do keep one shell.
- Don't claim ATO, FedRAMP, or DISA PA.
- Don't write exploits, PoCs, payloads, or attack playbooks.
- Don't treat CMMC / 800-171 / ITAR as substitutes for IL5 PA.
- Don't quiz past the three intake questions.
