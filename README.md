# IL5 Solution Scanner

Drop `AGENTS.md` and `FEDRAMP-HIGH-IL5-STANDARD.md` at a Codex/agent checkout root. The agent asks three intake questions once (target stack, what to scan, IaaS/PaaS/SaaS), waits, then grades `READY`, `HOLD`, or `WARN` in Plain English.

**How to run with Codex:** [`RUN.md`](RUN.md) — trigger words, intake, Neo4j EC2 GovCloud collect, HIGH 4003 answerer, GRADE + config-change list.

IL5 is FedRAMP High plus DoD overlays plus architecture. High alone fails an IL5 assessment. This scanner never claims ATO, FedRAMP authorization, or DISA PA.

The standard is the 4 Sep 2026 guide in `FEDRAMP-HIGH-IL5-STANDARD.md`. `AGENTS.perfect.md` is the twin of `AGENTS.md` — keep them identical. `SCANNER.md` is the playbook pointer.

## Question bank (production)

The production HIGH bank is the **default**: `il5-scanner/banks/production-high-53a-questions.jsonl` (**4003** questions from official NIST SP 800-53A Rev 5 on the NIST HIGH-baseline-resolved-profile catalog). Interim baseline: `NIST-800-53B-HIGH` (not FedRAMP Appendix A). Rebuild with `tools/generate_production_banks.py`. See `QUESTION-BANK.md`.

`fixtures/question-bank/` is a **unit fixture only**. Do not grade from it. Do not invent official control counts.

## Neo4j on EC2 US GovCloud

Customer-managed Neo4j on EC2 is **not** inherited from the AWS GovCloud PA. Collect read-only configs, then answer the HIGH bank from evidence:

```bash
tools/collect_neo4j_ec2_evidence.sh --run-id my-run --local-root /path/to/configs --skip-aws
python3 tools/answer_bank_from_evidence.py --evidence evidence/my-run --path "IL5 non-NSS" --shared-responsibility IaaS
```

Playbook: `playbooks/NEO4J-EC2-GOVCLOUD.md`. Copy-paste operator steps: `RUN.md`.

This repository has no application UI.
