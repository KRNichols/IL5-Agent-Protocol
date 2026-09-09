# IL5 Solution Scanner

Drop `AGENTS.md` and `FEDRAMP-HIGH-IL5-STANDARD.md` at a Codex/agent checkout root. The agent asks three intake questions once (target stack, what to scan, IaaS/PaaS/SaaS), waits, then grades `READY`, `HOLD`, or `WARN` in Plain English.

**Grade gate:** [`KEYS.md`](KEYS.md) — what “all High questions PASS with evidence” means, and what still fails IL5. Never ATO.

**How to run with Codex:** [`RUN.md`](RUN.md) — trigger words, intake, Neo4j EC2 GovCloud collect, FedRAMP High answerer, GRADE + config-change list.

**Provenance:** [`il5-scanner/banks/PROVENANCE.md`](il5-scanner/banks/PROVENANCE.md) — official NIST / FedRAMP URLs and exact counts.

IL5 is FedRAMP High plus DoD overlays plus architecture. High alone fails an IL5 assessment. This scanner never claims ATO, FedRAMP authorization, or DISA PA.

The standard is the 4 Sep 2026 guide in `FEDRAMP-HIGH-IL5-STANDARD.md`. `AGENTS.perfect.md` is the twin of `AGENTS.md` — keep them identical. `SCANNER.md` is the playbook pointer.

## Question bank (production)

The **default** bank is FedRAMP High / Class D: `il5-scanner/banks/production-high-53a-questions.jsonl` (**410** official OSCAL profile IDs → **4238** NIST SP 800-53A questions). NIST 800-53B HIGH (**4003** / 370 IDs) is comparison only — it is not equivalent. Rebuild with `tools/generate_production_banks.py`. See `QUESTION-BANK.md`.

`fixtures/question-bank/` is a **unit fixture only**. Do not grade from it. Do not invent official control counts.

## Neo4j on EC2 US GovCloud

Customer-managed Neo4j on EC2 is **not** inherited from the AWS GovCloud PA. Collect read-only configs, then answer the FedRAMP High bank from evidence:

```bash
tools/collect_neo4j_ec2_evidence.sh --run-id my-run --local-root /path/to/configs --skip-aws
python3 tools/answer_bank_from_evidence.py --evidence evidence/my-run --path "IL5 non-NSS" --shared-responsibility IaaS
```

Playbook: `playbooks/NEO4J-EC2-GOVCLOUD.md`. Copy-paste operator steps: `RUN.md`.

This repository has no application UI. Do not commit secrets, live instance IDs, or real evidence packs.
