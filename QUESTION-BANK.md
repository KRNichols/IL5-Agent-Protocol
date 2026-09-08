# Question bank — transitional-scanner synthesis

Commercial / transitional GRC scanners ask **hundreds of questions**. This repo synthesizes the same style of questions from **NIST SP 800-53A Rev 5** assessment procedures (Examine / Interview / Test) against the **FedRAMP High / Class D** control set the operator supplies, plus overlay hooks when the buyer path is IL5.

This file is the operator guide. `AGENTS.md` / `SCANNER.md` are the answering contract. The synthesizer does **not** authorize, PA, or ATO anything. `READY` never means ATO.

## Hard rules

- Do **not** invent official control counts. Official C/CE lists live in the workbooks below, not in a generated question total.
- NIST SP 800-53B HIGH is **not** FedRAMP High / Class D. Do not substitute one for the other.
- Building only to FedRAMP High still **fails** an IL5 assessment. Overlay rows are required when the claimed path is IL5.
- No full ~410 (or ~600) bank is vendored here. A full bank is **generated-from-catalog** after the operator supplies official files.
- No exploits, PoCs, payloads, or attack playbooks.

## Official sources (fetch these)

| What | Where | What it is |
|---|---|---|
| NIST SP 800-53 Rev 5 + **800-53A Rev 5** assessment procedures (OSCAL JSON) | [usnistgov/oscal-content](https://github.com/usnistgov/oscal-content/tree/main/nist.gov/SP800-53/rev5/json) `NIST_SP-800-53_rev5_catalog.json` (or `-min.json`) | Machine-readable Examine / Interview / Test procedures. Combined catalog; **not** a FedRAMP baseline. |
| NIST SP 800-53A publication | [CSRC SP 800-53A Rev 5](https://csrc.nist.gov/pubs/sp/800/53/a/r5/final) | Human-readable assessment procedures. |
| FedRAMP High / **Class D** control set | [fedramp.gov/2026/reference/fedramp-certification](https://fedramp.gov/2026/reference/fedramp-certification/), [controls](https://fedramp.gov/2026/reference/controls/), [Rev 5 templates](https://www.fedramp.gov/rev5/documents-templates/) — SSP Appendix A High + Security Controls Baseline (Excel) | The High / Class D ID list the synthesizer should filter to. |
| NIST SP 800-53B HIGH profile | same oscal-content tree, `NIST_SP-800-53_rev5_HIGH-baseline_profile.json` | NIST High only. **Different set** from FedRAMP High. Safe as a filter only if you label it NIST High. |
| DoD FedRAMP+ / IL5 extras | [DoD Rev 5 SSP Addendum](https://public.cyber.mil/dccs/dccs-documents/) + SRG Control Crosswalk | Overlay rows (`layer: FedRAMP+`). |
| CNSSI 1253 | [cnss.gov instructions](https://www.cnss.gov/CNSS/issuances/Instructions.cfm) | Overlay rows (`layer: CNSSI`) when the path is IL5 NSS. |
| SRG non-control architecture | CSP SRG on cyber.mil (citizenship, CAC/PIV, BCAP/SCCA, FIPS, dedicated tenancy) | Overlay rows (`layer: SRG`). |

Print the same URLs from the tool:

```bash
python3 tools/synthesize_questions.py --print-sources
```

Optional fetch of the official NIST min catalog (not committed):

```bash
python3 tools/synthesize_questions.py --fetch-nist-catalog /tmp/NIST_SP-800-53_rev5_catalog-min.json
```

## How synthesis works

```
operator catalog (OSCAL 800-53/53A or flattened JSON)
        +
optional baseline IDs (FedRAMP Appendix A High / Class D workbook)
        +
optional overlay rows (FedRAMP+ / CNSSI / SRG) when path is IL5
        ↓
tools/synthesize_questions.py
        ↓
question objects (JSONL or JSON array)
```

1. Read every control and enhancement in the catalog.
2. Collect **leaf** `assessment-objective` parts (the Determine-if statements).
3. Collect `assessment-method` parts whose `method` prop is EXAMINE, INTERVIEW, or TEST.
4. Emit one question per (leaf objective × method).
5. If `--baseline` is set, keep only IDs in that list. IDs are normalized (`ac-2`, `AC-02`, `AC-2(1)`, `ac-2.1`).
6. Append overlay rows unchanged (except method / layer normalization).
7. If `--path` is set, drop questions whose `path_applicability` does not include that path.

If `--baseline` is omitted, the tool still emits, and **warns** that the result is not a FedRAMP High count.

### Question shape

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

| Field | Values |
|---|---|
| `method` | `Examine` \| `Interview` \| `Test` |
| `layer` | `High` \| `FedRAMP+` \| `CNSSI` \| `SRG` |
| `path_applicability` | `FedRAMP High`, `IL5 non-NSS`, `IL5 NSS` |
| `enhancement` | `""` or the enhancement number (`1`, `12`) |
| `source` | Catalog / overlay SOURCE string (required on snapshots) |

Default path applicability:

| Layer | Paths |
|---|---|
| High | FedRAMP High, IL5 non-NSS, IL5 NSS |
| FedRAMP+ | IL5 non-NSS, IL5 NSS |
| CNSSI | IL5 NSS |
| SRG | IL5 non-NSS, IL5 NSS |

JSON output wraps `{ "meta", "questions" }`. `meta.not_an_official_control_count` is always true. JSONL is one question object per line.

## Operator commands

Tiny example (checked in; **not** a full High bank):

```bash
python3 tools/synthesize_questions.py \
  --catalog examples/question-bank/tiny-53a-catalog.json \
  --baseline examples/question-bank/tiny-class-d-ids.txt \
  --overlay examples/question-bank/tiny-il5-overlay.json \
  --format jsonl \
  --out examples/question-bank/tiny-question-bank.jsonl
```

IL5 NSS path only (High + FedRAMP+ + CNSSI + SRG rows that list that path):

```bash
python3 tools/synthesize_questions.py \
  --catalog examples/question-bank/tiny-53a-catalog.json \
  --baseline examples/question-bank/tiny-class-d-ids.txt \
  --overlay examples/question-bank/tiny-il5-overlay.json \
  --path il5-nss \
  --format json \
  --out /tmp/il5-nss-questions.json
```

Full bank after the operator has official files (not committed):

```bash
python3 tools/synthesize_questions.py --fetch-nist-catalog /tmp/NIST_SP-800-53_rev5_catalog-min.json

# Convert official Appendix A High / Class D workbook → one ID per line
# (operator does this; this repo does not invent that list)

python3 tools/synthesize_questions.py \
  --catalog /tmp/NIST_SP-800-53_rev5_catalog-min.json \
  --baseline /tmp/fedramp-high-class-d-ids.txt \
  --overlay /tmp/dod-ssp-addendum-rows.json \
  --overlay /tmp/cnssi-1253-rows.json \
  --path il5-nss \
  --format jsonl \
  --out /tmp/il5-nss-question-bank.jsonl
```

Mark any generated full bank as **generated-from-catalog**. Do not check it in as “the 410.”

### Flattened catalog (if you are not using OSCAL)

```json
{
  "format": "il5-question-catalog-v1",
  "source": "SOURCE: extracted by operator from official 800-53A / Appendix A High",
  "controls": [
    {
      "id": "at-4",
      "title": "Training Records",
      "objectives": [{ "id": "at-4_obj.a", "prose": "…" }],
      "methods": [{ "method": "EXAMINE", "objects": "…" }]
    }
  ]
}
```

### Overlay file

```json
{
  "format": "il5-overlay-rows-v1",
  "source": "SOURCE: operator extract from DoD SSP Addendum / CNSSI 1253 / CSP SRG",
  "rows": [
    {
      "control": "AC-7",
      "enhancement": "",
      "objective_id": "ac-7_dspav",
      "method": "Examine",
      "layer": "FedRAMP+",
      "path_applicability": ["IL5 non-NSS", "IL5 NSS"],
      "question": "…"
    }
  ]
}
```

## Example snapshot (vendored)

`examples/question-bank/` holds a **tiny** shape snapshot: two High controls + one enhancement, plus four overlay hook rows.

| File | Role |
|---|---|
| `tiny-53a-catalog.json` | OSCAL-shaped catalog. SOURCE marked. Original short stems — **not** official 800-53A prose. |
| `tiny-class-d-ids.txt` | Three-ID demo filter. **Not** Appendix A High. |
| `tiny-il5-overlay.json` | FedRAMP+ / CNSSI / SRG hook shape. **Not** the SSP Addendum. |
| `tiny-question-bank.jsonl` | Generated from the files above. |

That bank is for contract tests and shape review. It is not a High or IL5 baseline.

## Answering protocol

Every in-scope synthesized question must be answered:

`PASS | HOLD | WARN | N/A | MISSING`

| Answer | When |
|---|---|
| PASS | Handed solution has **cited** evidence that meets the objective. No cite → not PASS. |
| HOLD | Evidence contradicts, is guessed, is wrong, or is High-only on an IL5 claim. Guessed answers are HOLD. |
| WARN | Soft gap that does not kill the claimed stack. Never use WARN for a hard hold. |
| N/A | Question’s `path_applicability` or shared-responsibility row does not apply. Say why. |
| MISSING | Nothing handed for this objective. Do not invent a story. |

- Never invent answers. Score only what was handed.
- `READY` on the GRADE block never means ATO, FedRAMP authorization, or DISA PA.
- High-alone still fails IL5.

Filled questionnaire artifact (optional): copy the JSONL and add:

```json
{
  "id": "AT-4/at-4_obj.a/Examine",
  "answer": "MISSING",
  "evidence": "",
  "notes": "No training-record sample in the handed pack."
}
```

## Report block

Keep the existing GRADE block from `AGENTS.md`, then add:

```markdown
QUESTIONS:
- in_scope: N
- answered: N
- PASS: N
- HOLD: N
- WARN: N
- N/A: N
- MISSING: N
- artifact: <path or none>
```

- `in_scope` — questions whose `path_applicability` includes the claimed path.
- `answered` — `PASS + HOLD + WARN + N/A` (a determination other than MISSING).
- `artifact` — path to the filled JSONL/JSON if one was written.

If no catalog-generated bank was in scope, set `in_scope: 0` and `artifact: none` — do not invent a fake 410.
