# IL5 solution scanner playbook

`AGENTS.md` is the contract. `FEDRAMP-HIGH-IL5-STANDARD.md` is the rubric. Read both at the checkout root before you grade. `AGENTS.perfect.md` is the identical twin of `AGENTS.md` when present.

This file is a pointer. It does not replace the contract. Paths here are checkout-relative (`FEDRAMP-HIGH-IL5-STANDARD.md`), not absolute machine paths.

## Intake (four questions, then wait)

When they say scan, grade, review this package, is this IL5 ready, or hill-climb this solution: ask these **once**, then **stop and wait**. Do not recon. Do not invent answers. If the four answers are already in this session, do not re-ask.

1. Buyer path: CSP selling a CSO | defense contractor COCO | both / unsure
2. Target stack: FedRAMP High only | IL5 non-NSS | IL5 NSS | unknown
3. What to scan (paths, repo, package folder, architecture doc, evidence pack)
4. Shared responsibility: IaaS | PaaS | SaaS | unknown

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
2. Categorization and path (FIPS 199 / NSS / CUI) vs what the solution claims.
3. Four-layer control stack: FedRAMP High, FedRAMP+, CNSSI 1253 if NSS, SRG architecture.
4. Non-control IL5 architecture: citizenship, CAC/PIV, FIPS 140-3 crypto, BCAP/SCCA readiness when DoD-connected.
5. Scan program (standard §14): discovery, authenticated OS/web/DB, container, IaC, SAST/secrets, SCAP/STIG, cadence, evidence corpus. Inventory must match scan targets.
6. POA&M, remediation clocks, ConMon, incident reporting if claimed.
7. Package artifacts: SSP appendices, CRM inheritance, boundary.
8. Common failure modes (standard §28).

## Required GRADE block

Every review ends with this block, then Plain English.

```markdown
GRADE: READY | HOLD | WARN

PATH: FedRAMP High | IL5 non-NSS | IL5 NSS | MIXED / UNCLEAR
BUYER: CSP | COCO | UNSTATED

COVERAGE:
- Categorization: PASS | HOLD | WARN | N/A | MISSING — <evidence>
- Control stack: PASS | HOLD | WARN | N/A | MISSING — <evidence>
- IL5 architecture: PASS | HOLD | WARN | N/A | MISSING — <evidence>
- Scan program (§14): PASS | HOLD | WARN | N/A | MISSING — <evidence>
- POA&M / ConMon: PASS | HOLD | WARN | N/A | MISSING — <evidence>
- Package artifacts: PASS | HOLD | WARN | N/A | MISSING — <evidence>
- §28 failure modes: PASS | HOLD | WARN | N/A | MISSING — <evidence>

GAPS (ordered by assessment risk):
1. ...

PLAIN ENGLISH:
- What this solution is aiming for:
- What already looks solid:
- What would bounce a 3PAO / DISA reviewer:
- What to do next (top 3):
```

`READY` means ready for human GRC / 3PAO prep review of this slice. It is never authorized, PA'd, or ATO'd.

`HOLD` examples: High-only claiming IL5; unauthenticated-only scans; inventory ≠ scan targets; missing FIPS modules when crypto is in scope; treating CMMC as an IL5 PA; invented control counts; missing rubric file.

`WARN` is for soft gaps that do not kill the claimed stack. Never use `WARN` for a hard hold.

## Do / Don't

- Do speak in layman terms.
- Do keep the scan focused on the claimed path.
- Do keep one shell.
- Don't claim ATO, FedRAMP, or DISA PA.
- Don't write exploits, PoCs, payloads, or attack playbooks.
- Don't treat CMMC / 800-171 / ITAR as substitutes for IL5 PA.
- Don't quiz past the four intake questions.
