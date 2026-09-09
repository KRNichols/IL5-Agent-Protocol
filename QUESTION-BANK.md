# Question bank — production

The scanner asks every published NIST SP 800-53A Rev 5 Examine /
Interview / Test objective on the **official FedRAMP Rev 5 High /
Class D** control ID list. That bank is the **default** after intake
(`RUN.md` step 6). Grade-gate wording: `KEYS.md`.

This is not a demo. `READY` never means ATO. High-alone still fails IL5.
`fixtures/question-bank/` is a **unit fixture only** — never the grading bank.

NIST SP 800-53B HIGH (**4003** questions / **370** IDs) is **not**
FedRAMP High. It is a **named alternate** only
(`il5-scanner/banks/nist-800-53b-high-53a-questions.jsonl`).
`AGENTS.md` / `RUN.md` / `SCANNER.md` default to the FedRAMP High bank.

## Production artifacts

| Path | What |
|---|---|
| `il5-scanner/banks/production-high-53a-questions.jsonl` | **Default grade path — FedRAMP High / Class D — 4238 questions** |
| `il5-scanner/banks/production-high-53a-questions.meta.json` | HIGH meta |
| `il5-scanner/banks/PROVENANCE.md` | Official URLs + exact counts |
| `il5-scanner/banks/SOURCE.json` | Machine provenance |
| `il5-scanner/banks/nist-800-53b-high-53a-questions.jsonl` | NIST 800-53B HIGH comparison — 4003 questions (not the grade path) |
| `il5-scanner/banks/production-full-53a-questions.jsonl` | Full 800-53/53A catalog — 7772 questions (max size) |
| `question-bank/fedramp-high-class-d.ids.txt` | 410 official profile `with-ids` |
| `question-bank/fedramp-high-class-d.questions.jsonl` | Mirror of the default HIGH bank |
| `question-bank/il5-overlay-hooks.json` | FedRAMP+ / CNSSI / SRG hooks (addendum not fetchable) |

`fixtures/question-bank/` is a **unit fixture only**. Do not grade from it.

Rebuild:

```bash
python3 tools/generate_production_banks.py
```

## Exact default HIGH count (this freeze)

**4238 questions** from **410** official FedRAMP High / Class D IDs

- Published 53A methods only (no invented Test/Interview)
- Examine 1542 · Interview 1542 · Test 1154
- Profile: OSCAL Foundation *FedRAMP Rev 5 High Baseline*
  `fedramp-3.0.0rc1-oscal-1.1.2` (last-modified 2025-02-28)

**Baseline label:** `FedRAMP-HIGH-CLASS-D`.

NIST SP 800-53B HIGH has **370** IDs / **4003** questions. FedRAMP High
adds **40** IDs and **235** 53A questions. They are different sets.
See `il5-scanner/banks/PROVENANCE.md` for the ID list.

Question count is synthesized 53A rows. It is **not** an official C/CE count.

## Official sources (fetched 2026-09-09)

| What | URL |
|---|---|
| NIST 800-53 + **800-53A** OSCAL catalog | https://raw.githubusercontent.com/usnistgov/oscal-content/main/nist.gov/SP800-53/rev5/json/NIST_SP-800-53_rev5_catalog-min.json |
| NIST 800-53A publication | https://csrc.nist.gov/pubs/sp/800/53/a/r5/final |
| FedRAMP Rev 5 High / Class D OSCAL profile (**410** IDs; GSA repo 404) | https://raw.githubusercontent.com/OSCAL-Foundation/fedramp-resources/main/baselines/rev5/json/FedRAMP_rev5_HIGH-baseline_profile.json |
| FedRAMP certification / controls | https://fedramp.gov/2026/reference/fedramp-certification/ · https://fedramp.gov/2026/reference/controls/ |
| NIST 800-53B HIGH (comparison) | https://raw.githubusercontent.com/usnistgov/oscal-content/main/nist.gov/SP800-53/rev5/json/NIST_SP-800-53_rev5_HIGH-baseline_profile.json |
| DoD SSP Addendum (login-walled) | https://public.cyber.mil/dccs/dccs-documents/ |
| CNSSI 1253 | https://www.cnss.gov/CNSS/issuances/Instructions.cfm |

```bash
python3 tools/synthesize_questions.py --print-sources
```

## Question shape

```json
{
  "id": "AT-4/at-4_obj.a/Examine",
  "control": "AT-4",
  "enhancement": "",
  "objective_id": "at-4_obj.a",
  "method": "Examine",
  "question": "Examine: Determine whether AT-4 objective at-4_obj.a is met — …",
  "layer": "High",
  "path_applicability": ["FedRAMP High", "IL5 non-NSS", "IL5 NSS"],
  "source": "…SOURCE attribution…"
}
```

## Answering protocol

Every in-scope question: `PASS | HOLD | WARN | N/A | MISSING`

- PASS requires cited evidence from the handed solution.
- Never invent answers. Guessed answers are HOLD.
- READY never means ATO.
- All High PASS + cited evidence can make PATH FedRAMP High scanner-READY.
  IL5 still fails until overlays / architecture / package evidence exists
  (`KEYS.md`).

## Report block

Keep the GRADE block from `AGENTS.md` (no BUYER line). Then:

```markdown
QUESTIONS:
- in_scope: N
- answered: N
- PASS: N
- HOLD: N
- WARN: N
- N/A: N
- MISSING: N
- artifact: il5-scanner/banks/production-high-53a-questions.jsonl
```

If the production HIGH bank is missing, `HOLD`.

## Neo4j EC2 GovCloud answering

`tools/answer_bank_from_evidence.py` loads this HIGH bank by default,
maps `evidence/<run-id>/` through
`il5-scanner/collectors/neo4j-ec2-govcloud-map.json`, and writes
`answers.jsonl` + GRADE + QUESTIONS. It marks **MISSING** unless a
mapped evidence file is present. It **never invents PASS**. See
`playbooks/NEO4J-EC2-GOVCLOUD.md` and `RUN.md`.
