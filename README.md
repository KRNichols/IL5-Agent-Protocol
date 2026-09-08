# IL5 Solution Scanner

Drop `AGENTS.md` and `FEDRAMP-HIGH-IL5-STANDARD.md` at a Codex/agent checkout root. The agent asks four intake questions once (buyer path, target stack, what to scan, IaaS/PaaS/SaaS), waits, then grades `READY`, `HOLD`, or `WARN` in Plain English.

IL5 is FedRAMP High plus DoD overlays plus architecture. High alone fails an IL5 assessment. This scanner never claims ATO, FedRAMP authorization, or DISA PA.

The standard is the 4 Sep 2026 guide in `FEDRAMP-HIGH-IL5-STANDARD.md`. `AGENTS.perfect.md` is the twin of `AGENTS.md` — keep them identical. `SCANNER.md` is the playbook pointer.

## Question bank

Transitional-scanner questions are synthesized from NIST SP 800-53A Rev 5 (Examine / Interview / Test) against the operator-supplied FedRAMP High / Class D set, plus overlay hooks when the path is IL5. See `QUESTION-BANK.md` and `tools/synthesize_questions.py`. Official catalogs are not vendored. A tiny shape snapshot is in `examples/question-bank/`. Do not invent official control counts.

This repository has no application UI.
