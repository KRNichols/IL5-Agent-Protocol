# Provenance — production question banks

Freeze: **2026-09-09**. Counts below are from official files fetched that
day. They are **not invented**. Question count is synthesized 53A rows.
It is **not** an official C/CE count. Re-download before you freeze an
assessment baseline.

Default grade path is **FedRAMP High / Class D**, not NIST SP 800-53B HIGH.

`READY` is never ATO, FedRAMP authorization, or DISA PA.
High alone fails IL5. See `KEYS.md`.

---

## Official sources (fetched)

| Role | Exact URL | What we took |
|---|---|---|
| NIST SP 800-53 Rev 5 + **SP 800-53A Rev 5** assessment procedures (OSCAL min catalog) | https://raw.githubusercontent.com/usnistgov/oscal-content/main/nist.gov/SP800-53/rev5/json/NIST_SP-800-53_rev5_catalog-min.json | Examine / Interview / Test methods and leaf objectives. CSRC: https://csrc.nist.gov/pubs/sp/800/53/a/r5/final |
| Same catalog, non-min | https://raw.githubusercontent.com/usnistgov/oscal-content/main/nist.gov/SP800-53/rev5/json/NIST_SP-800-53_rev5_catalog.json | Listed; min catalog used for synthesis |
| **FedRAMP Rev 5 High Baseline OSCAL profile** (Class D = High) | https://raw.githubusercontent.com/OSCAL-Foundation/fedramp-resources/main/baselines/rev5/json/FedRAMP_rev5_HIGH-baseline_profile.json | **410** `with-ids`. Title: *FedRAMP Rev 5 High Baseline*. Version: `fedramp-3.0.0rc1-oscal-1.1.2`. last-modified: `2025-02-28T00:00:00Z`. published: `2024-09-24T02:24:00Z` |
| FedRAMP High resolved catalog (listed, not required for ID filter) | https://raw.githubusercontent.com/OSCAL-Foundation/fedramp-resources/main/baselines/rev5/json/FedRAMP_rev5_HIGH-baseline-resolved-profile_catalog.json | Cross-check |
| FedRAMP certification / controls (human) | https://fedramp.gov/2026/reference/fedramp-certification/ · https://fedramp.gov/2026/reference/controls/ | Class D = High. SSP Appendix A High remains the workbook to re-download |
| NIST SP 800-53B HIGH profile (**comparison only**) | https://raw.githubusercontent.com/usnistgov/oscal-content/main/nist.gov/SP800-53/rev5/json/NIST_SP-800-53_rev5_HIGH-baseline_profile.json | **370** IDs. Title includes HIGH IMPACT BASELINE. **Not** FedRAMP High |
| NIST HIGH-baseline-resolved catalog | https://raw.githubusercontent.com/usnistgov/oscal-content/main/nist.gov/SP800-53/rev5/json/NIST_SP-800-53_rev5_HIGH-baseline-resolved-profile_catalog-min.json | Same 370 IDs / 4003 questions as 53B HIGH × 53A |
| GSA `fedramp-automation` High profile | https://raw.githubusercontent.com/GSA/fedramp-automation/master/dist/content/rev5/baselines/json/FedRAMP_rev5_HIGH-baseline_profile.json | **HTTP 404** on 2026-09-08 and 2026-09-09. Not used |
| DoD Rev 5 SSP Addendum + SRG Crosswalk | https://public.cyber.mil/dccs/dccs-documents/ | **Not fetched** (login wall). Overlay hooks only |
| CNSSI 1253 | https://www.cnss.gov/CNSS/issuances/Instructions.cfm | **Not fetched** as a catalog. NSS hooks only |

Machine copy of this table: `il5-scanner/banks/SOURCE.json` (also `question-bank/SOURCE.json`).

ID list extracted from the official profile (not invented):
`question-bank/fedramp-high-class-d.ids.txt`

---

## Counts on this freeze

| Bank | Path | Official IDs | 53A questions | Methods |
|---|---|---|---|---|
| **Default HIGH — FedRAMP High / Class D** | `production-high-53a-questions.jsonl` | **410** | **4238** | Examine 1542 · Interview 1542 · Test 1154 |
| NIST 800-53B HIGH (comparison) | `nist-800-53b-high-53a-questions.jsonl` | **370** | **4003** | Examine 1463 · Interview 1463 · Test 1077 |
| Full 800-53/53A catalog | `production-full-53a-questions.jsonl` | 1196 catalog controls (not a baseline) | **7772** | Examine 2775 · Interview 2772 · Test 2225 |
| IL5 overlay hooks | `question-bank/il5-overlay-hooks.json` | n/a (not a workbook extract) | **106** rows | Appended on IL5 paths only |

NIST 53B HIGH is a **subset** of FedRAMP High. IDs only in FedRAMP High
(40): AC-2(7)(9), AC-4(21), AC-6(8), AU-6(4)(7), CA-2(3), CA-8(2),
CM-5(5), CM-14, IA-2(6), IA-5(7)(8)(13), IR-4(2)(6), IR-9 + (2)(3)(4),
PE-14(2), PS-3(3), RA-5(3)(8), SA-9(1)(5), SA-11(1)(2), SC-7(10)(12)(20),
SC-45 + (1), SI-2(3), SI-4(1)(11)(16)(18)(19)(23).

Question delta (FedRAMP High − NIST 53B HIGH) = **235**.

The old default labeled “HIGH 4003” was NIST 53B HIGH. That is **not**
equivalent to FedRAMP High / Appendix A / Class D. Proof is the 40-ID
gap above, including CA-8(2) red team, SA-9(5) location, SC-45 time,
IA-5(7) static authenticators, IR-9 spillage, SA-11(1) SAST.

Rebuild:

```bash
python3 tools/generate_production_banks.py
```

---

## What this bank is not

- Not FedRAMP authorization, DISA PA, or ATO
- Not the DoD SSP Addendum / DSPAV table (not fetchable here)
- Not CNSSI 1253
- Not an official C/CE count — point at Appendix A High + the 410-ID profile
