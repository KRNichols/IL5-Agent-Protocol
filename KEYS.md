# Keys to the kingdom — scanner grading gate

The pack on GitHub is the grade gate. Speak this way to operators.

```
full bank PASS
  ≠ FedRAMP High package READY
  ≠ IL5
  ≠ ATO
```

Answering every in-scope FedRAMP High 53A question `PASS` with cited
evidence is a **control-tally**. It is **not** a FedRAMP High package
grade, **not** IL5, and **not** authorization.

`READY` is **never** ATO, FedRAMP authorization, or DISA PA.

---

## Default bank

`il5-scanner/banks/production-high-53a-questions.jsonl`

**FedRAMP Rev 5 High / Class D** — official OSCAL profile **410** IDs ×
published NIST SP 800-53A Examine / Interview / Test (**4238** questions
on this freeze). Official `modify.set-parameters` are baked into each
matching row as `fedramp_constraint` (and into the question text).

See `il5-scanner/banks/SOURCE.json` and `QUESTION-BANK.md`.

Named alternate (not the default): NIST SP 800-53B HIGH **4003** at
`il5-scanner/banks/nist-800-53b-high-53a-questions.jsonl`. Do not grade
FedRAMP High from that file.

---

## What full-bank PASS is, and is not

If every **in-scope** FedRAMP High question is `PASS` with a **cited
evidence path**:

- The QUESTIONS tally may show `MISSING: 0`
- That is **not** FedRAMP High **package** READY
- That is **not** IL5
- That is **not** ATO / FedRAMP authorization / DISA PA

Scanner `GRADE` for a **FedRAMP High package** slice stays **HOLD**
until the COVERAGE gates below are also evidenced. Guessed PASS is HOLD.
Missing files are MISSING. The answerer stub never invents PASS.

---

## COVERAGE gates (required for High package READY)

All of these must be scored from handed evidence. The 53A bank cannot
invent them:

| Gate | HOLD unless |
|---|---|
| SSP / package artifacts | Starred FedRAMP SSP appendices (A, J CRM, M inventory, O POA&M, Q crypto, …) are present or explicitly cited as missing |
| CRM / shared responsibility | Appendix J names Implemented / Inherited / Shared / Customer per control; no false inherit of customer apps (Neo4j ≠ AWS PA) |
| §14 scan program | Authenticated OS/web/DB/container + inventory match; unauthenticated-only is a hard hold |
| IL5 overlays | Only if PATH is IL5 — SSP Addendum / DSPAV / CNSSI cited, not guessed |
| IL5 architecture | Only if PATH is IL5 — US location, tenancy, CAC/PIV Strength D, FIPS 140-3 in FIPS mode, citizenship, BCAP/SCCA if DoD-connected |

**High-alone + IL5 claim = HOLD.**
IL5 needs FedRAMP High **plus** overlays **plus** architecture.

---

## READY ≠ authorization

| Phrase | Meaning here |
|---|---|
| full bank PASS | Every in-scope 53A row has cited PASS — still not a package grade |
| READY | Scanner grade: this **slice** is ready for **human** GRC / 3PAO prep — only after bank **and** COVERAGE gates |
| WARN | Soft gap that does not kill the claimed stack |
| HOLD | Hard gap, missing bank, guessed answers, High sold as IL5, or COVERAGE gate missing |
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
