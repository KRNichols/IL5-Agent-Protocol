# Keys to the kingdom — scanner grading gate

The pack on GitHub is the grade gate. If the production FedRAMP High
questions are answered with **real cited evidence**, the GRADE must say
whether FedRAMP High / IL5 **scanner** level was hit.

This file is blunt on purpose. Speak this way to operators.

`READY` is **never** ATO, FedRAMP authorization, or DISA PA.

---

## What “all questions answered PASS with evidence” means

Default bank:

`il5-scanner/banks/production-high-53a-questions.jsonl`

That bank is **FedRAMP Rev 5 High / Class D** (official OSCAL profile,
**410** control IDs) × published NIST SP 800-53A Examine / Interview /
Test methods (**4238** questions on this freeze). See
`il5-scanner/banks/PROVENANCE.md`.

If **PATH is FedRAMP High** and every **in-scope** High-layer question
is `PASS` with a **cited evidence path** from what was handed:

- Scanner `GRADE` may be **READY**
- That means: ready for **human GRC / 3PAO prep review of this slice**
- The QUESTIONS tally must show `MISSING: 0` and no guessed PASS

PASS requires a real file you can point at. The answerer stub **never**
invents PASS. A human or Codex upgrades HOLD → PASS only after reading
the cited file.

Guessed answers are HOLD. Missing files are MISSING.

---

## What still fails IL5 even if High is READY

**Building only to FedRAMP High fails an IL5 assessment.**

The High bank cannot invent DoD overlays or architecture. These stay
`MISSING` (or HOLD) until you hand evidence — including the overlay
hooks in `question-bank/il5-overlay-hooks.json` when PATH is IL5:

| Still required for IL5 | Why the High bank cannot close it |
|---|---|
| DoD FedRAMP+ / SSP Addendum / Table D-1 DSPAV | Login-walled on cyber.mil. Do not guess parameter values. |
| US location, federal-community tenancy, dedicated hosts | SRG architecture, not a 53A High row by itself |
| Management plane isolated from commercial cloud | DISA architecture briefing item |
| CAC/PIV / Credential Strength D | Software TOTP is not Strength D |
| FIPS 140-3 CMVP certs **in FIPS mode** + Appendix Q | “AES-256” / “FIPS-compliant” fails |
| US-person / citizenship for privileged IL5 roles | CMMC is not a substitute |
| BCAP / SCCA / no direct internet mission path | Only if DoD-connected; collector cannot invent CAP tickets |
| STIG / SCAP / ACAS coverage matrix | Config collect is not the STIG of record |
| Authenticated scan program (§14) + inventory match | Unauthenticated-only is a hard hold |
| SSP appendices, CRM inheritance, POA&M, ConMon | Package artifacts. Scanner does not write an SSP. |
| CNSSI 1253 “+” if NSS | Official instruction on cnss.gov; ~170 is directional only |
| Shared responsibility written | IaaS vs customer-managed Neo4j: AWS PA does **not** cover Neo4j |

High-only claiming IL5 = **HOLD**.

---

## READY ≠ authorization

| Phrase | Meaning here |
|---|---|
| READY | Scanner grade: this slice is ready for a **human** GRC / 3PAO prep review |
| WARN | Soft gap that does not kill the claimed stack |
| HOLD | Hard gap, missing bank, guessed answers, or High sold as IL5 |
| ATO | Authority to Operate — **human AO only** |
| FedRAMP authorization / P-ATO | FedRAMP PMO / JAB / agency — **not this scanner** |
| DISA PA | DISA provisional authorization — **not this scanner** |

Never claim ATO. Never write exploits, PoCs, or attack playbooks.
Never put live GovCloud instance IDs, secrets, or real evidence packs
in git.

Trigger words stay: scan · grade · review this package · is this IL5
ready · hill-climb this solution. Three intake questions only (target
stack, what to scan, IaaS/PaaS/SaaS). No buyer-path quiz.

Operator steps: `RUN.md`. Contract: `AGENTS.md`.
