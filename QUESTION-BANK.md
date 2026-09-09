# Question bank — production

The scanner asks every published NIST SP 800-53A Rev 5 Examine /
Interview / Test objective in the **production HIGH bank**.
That bank is the **default** after intake (`RUN.md` step 6).

This is not a demo. `READY` never means ATO. High-alone still fails IL5.
`fixtures/question-bank/` is a **unit fixture only** — never the grading bank.

## Production artifacts

| Path | What |
|---|---|
| `il5-scanner/banks/production-high-53a-questions.jsonl` | **Production HIGH bank — 4003 questions** |
| `il5-scanner/banks/production-high-53a-questions.meta.json` | HIGH meta |
| `il5-scanner/banks/production-full-53a-questions.jsonl` | Full 800-53/53A catalog — 7772 questions (max size) |
| `il5-scanner/banks/production-full-53a-questions.meta.json` | FULL meta |
| `il5-scanner/banks/SOURCE.json` | SOURCE URLs, dates, counts |
| `question-bank/fedramp-high-class-d.questions.jsonl` | Optional FedRAMP High / Class D ID filter (410 official profile IDs) |
| `question-bank/il5-overlay-hooks.json` | FedRAMP+ / CNSSI / SRG hooks (addendum not fetchable) |

`fixtures/question-bank/` is a **unit fixture only**. Do not grade from it.

Rebuild:

```bash
python3 tools/generate_production_banks.py
python3 tools/build_production_bank.py   # FedRAMP High / Class D ID filter
```

## Exact HIGH count

**4003 questions**

- 1463 leaf NIST SP 800-53A assessment objectives
- × Examine / Interview / Test **as published on each control** (54 HIGH controls have no Test method)
- Examine 1463 · Interview 1463 · Test 1077
- 370 controls from the official NIST HIGH-baseline-resolved-profile catalog

**Baseline label:** `NIST-800-53B-HIGH` — **not** FedRAMP Appendix A / Class D.
NIST SP 800-53B HIGH has 370 IDs. The FedRAMP Rev 5 High OSCAL profile has 410 IDs. They are different sets. Swap the ID list when Appendix A High is the freeze.

FULL catalog bank: **7772** questions from 1196 catalog controls (not a baseline).

Question count is synthesized 53A rows. It is **not** an official C/CE count.

## Official sources (fetched 2026-09-08)

| What | URL |
|---|---|
| NIST HIGH resolved catalog (800-53 + **800-53A**) | https://raw.githubusercontent.com/usnistgov/oscal-content/main/nist.gov/SP800-53/rev5/json/NIST_SP-800-53_rev5_HIGH-baseline-resolved-profile_catalog-min.json |
| NIST full 800-53/53A catalog | https://raw.githubusercontent.com/usnistgov/oscal-content/main/nist.gov/SP800-53/rev5/json/NIST_SP-800-53_rev5_catalog-min.json |
| NIST 800-53A publication | https://csrc.nist.gov/pubs/sp/800/53/a/r5/final |
| FedRAMP Rev 5 High / Class D OSCAL profile (410 IDs; GSA repo 404) | https://raw.githubusercontent.com/OSCAL-Foundation/fedramp-resources/main/baselines/rev5/json/FedRAMP_rev5_HIGH-baseline_profile.json |
| FedRAMP certification / controls | https://fedramp.gov/2026/reference/fedramp-certification/ · https://fedramp.gov/2026/reference/controls/ |
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
