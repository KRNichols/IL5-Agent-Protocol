# IL5 Solution Scanner

Drop `AGENTS.md` and `FEDRAMP-HIGH-IL5-STANDARD.md` at a Codex/agent checkout root. The agent asks three intake questions once (target stack, what to scan, IaaS/PaaS/SaaS), waits, then grades `READY`, `HOLD`, or `WARN` in Plain English.

IL5 is FedRAMP High plus DoD overlays plus architecture. High alone fails an IL5 assessment. This scanner never claims ATO, FedRAMP authorization, or DISA PA.

The standard is the 4 Sep 2026 guide in `FEDRAMP-HIGH-IL5-STANDARD.md`. `AGENTS.perfect.md` is the twin of `AGENTS.md` — keep them identical. `SCANNER.md` is the playbook pointer.

## Question bank (production)

The production HIGH bank is `il5-scanner/banks/production-high-53a-questions.jsonl` (**4003** questions from official NIST SP 800-53A Rev 5 on the NIST HIGH-baseline-resolved-profile catalog). Interim baseline: `NIST-800-53B-HIGH` (not FedRAMP Appendix A). Rebuild with `tools/generate_production_banks.py`. See `QUESTION-BANK.md`. `fixtures/question-bank/` is a unit fixture only. Do not invent official control counts.

This repository has no application UI.
