# How to run this with Codex

Production scanner. Default bank is **HIGH 4003** (`il5-scanner/banks/production-high-53a-questions.jsonl`). `READY` is **never** ATO, FedRAMP authorization, or DISA PA. High alone fails IL5. No exploits, PoCs, or attack playbooks. Do not put secrets in the repo.

`fixtures/question-bank/` is a **unit fixture only**. Do not grade from it.

---

## 1. Point Codex at this pack

**Option A — this checkout**

Drop or clone the pack at the Codex workspace root so these files sit together:

- `AGENTS.md` (contract; twin `AGENTS.perfect.md` must stay identical)
- `SCANNER.md`
- `FEDRAMP-HIGH-IL5-STANDARD.md`
- `RUN.md` (this file)
- `playbooks/NEO4J-EC2-GOVCLOUD.md`
- `il5-scanner/banks/production-high-53a-questions.jsonl`

**Option B — GitHub**

Point Codex at `https://github.com/KRNichols/IL5-Agent-Protocol` on **`main`** after this PR lands. Until then, use this branch / PR checkout.

Linux:

```bash
git clone https://github.com/KRNichols/IL5-Agent-Protocol.git
cd IL5-Agent-Protocol
```

Windows (PowerShell):

```powershell
git clone https://github.com/KRNichols/IL5-Agent-Protocol.git
cd IL5-Agent-Protocol
```

Tell Codex: *Follow `AGENTS.md`. Operator steps are `RUN.md`.*

---

## 2. Trigger words (unchanged)

Say one of these **once**:

- scan
- grade
- review this package
- is this IL5 ready
- hill-climb this solution

Codex asks **three** intake questions, then **stops and waits**. It must not recon and must not invent answers.

---

## 3. Answer the three intake questions

1. **Target stack:** `FedRAMP High only` | `IL5 non-NSS` | `IL5 NSS` | `unknown`
2. **What to scan:** Neo4j on EC2 in AWS GovCloud — plus instance id, region, and/or local paths (see step 4)
3. **Shared responsibility:** `IaaS` (EC2 + customer-managed Neo4j). Not PaaS. AWS PA does not cover Neo4j.

Example reply you can paste:

```text
1. IL5 non-NSS
2. Neo4j on EC2 in AWS GovCloud; instance i-0123456789abcdef0; region us-gov-west-1; collect via SSM. Evidence dest: evidence/neo4j-govcloud-1
3. IaaS
```

If any of the three is still missing, Codex HOLDs and waits. Do not add a buyer-path question.

---

## 4. Point at the Neo4j EC2 GovCloud target

Give **one** transport. **No secrets in the repo** (no PEM files, no SSO tokens, no passwords).

| Transport | What you hand Codex |
|---|---|
| SSM | Instance id + GovCloud region + AWS profile name (profile lives in *your* `~/.aws`, not git) |
| SSH | `user@private-ip` or host from your SSH config (keys stay local) |
| Paths | Directory you already copied (`neo4j.conf`, AWS JSON). Use `--local-root` |

GovCloud regions: `us-gov-west-1`, `us-gov-east-1` (partition `aws-us-gov`). Commercial regions are the wrong cloud.

---

## 5. Run the evidence collector

Linux / macOS / WSL / Git Bash:

```bash
chmod +x tools/collect_neo4j_ec2_evidence.sh

# Already-copied configs (safest first run)
tools/collect_neo4j_ec2_evidence.sh \
  --run-id neo4j-govcloud-1 \
  --local-root /path/to/copied-configs \
  --region us-gov-west-1 \
  --skip-aws

# SSH + AWS describe (read-only)
tools/collect_neo4j_ec2_evidence.sh \
  --run-id neo4j-govcloud-1 \
  --ssh admin@10.0.1.20 \
  --region us-gov-west-1 \
  --instance-id i-0123456789abcdef0 \
  --profile gov

# SSM + AWS describe (read-only)
tools/collect_neo4j_ec2_evidence.sh \
  --run-id neo4j-govcloud-1 \
  --ssm i-0123456789abcdef0 \
  --region us-gov-west-1 \
  --profile gov
```

Windows PowerShell (collector is bash — use Git Bash, WSL, or the same commands inside WSL):

```powershell
wsl -e bash -lc 'cd /mnt/c/src/IL5-Agent-Protocol && tools/collect_neo4j_ec2_evidence.sh --run-id neo4j-govcloud-1 --local-root /mnt/c/tmp/copied-configs --region us-gov-west-1 --skip-aws'
```

Writes `evidence/<run-id>/` (`MANIFEST.json`, `neo4j/`, `ec2/`, `os/`). Redacts password lines. **Does not dump the graph.**

Smoke the collector on the in-repo fixture (no live host):

```bash
tools/collect_neo4j_ec2_evidence.sh \
  --run-id fixture-smoke \
  --local-root fixtures/neo4j-ec2-evidence \
  --skip-aws
```

---

## 6. Run the bank answerer (HIGH 4003)

Linux / macOS / WSL:

```bash
python3 tools/answer_bank_from_evidence.py \
  --evidence evidence/neo4j-govcloud-1 \
  --path "IL5 non-NSS" \
  --shared-responsibility IaaS
```

Windows PowerShell:

```powershell
python tools\answer_bank_from_evidence.py `
  --evidence evidence\neo4j-govcloud-1 `
  --path "IL5 non-NSS" `
  --shared-responsibility IaaS
```

Defaults:

- Bank: `il5-scanner/banks/production-high-53a-questions.jsonl` (**4003**)
- Map: `il5-scanner/collectors/neo4j-ec2-govcloud-map.json`
- IL5 paths also append overlay **hooks** (not a downloaded SSP Addendum)

The stub marks **MISSING** unless a mapped evidence file is present. It **never invents PASS**. Codex may upgrade HOLD→PASS only after reading the cited file.

Writes (under the evidence dir unless `--out-dir` is set):

- `GRADE.md` — GRADE + QUESTIONS tally
- `answers.jsonl` — one verdict per in-scope question
- `CONFIG-CHANGES.md` — current → required → evidence
- `SUMMARY.json`

---

## 7. Read the report

Open, in order:

1. `evidence/<run-id>/GRADE.md` — `GRADE`, `PATH`, `COVERAGE`, **QUESTIONS** tally
2. `evidence/<run-id>/CONFIG-CHANGES.md` — concrete config changes
3. `evidence/<run-id>/answers.jsonl` — per-question `PASS|HOLD|WARN|N/A|MISSING` + cited paths
4. `playbooks/NEO4J-EC2-GOVCLOUD.md` — what still needs a human package (SSP, CRM, STIG, CAC/PIV)

`answered` = PASS + HOLD + WARN + N/A. This stub’s PASS count is **0** until a human/Codex upgrades from evidence.

If PATH is FedRAMP High only and the mission needed IL5: **HOLD**. High alone fails IL5.

---

## What Codex does after intake (no extra quiz)

1. Confirm `FEDRAMP-HIGH-IL5-STANDARD.md` is readable.
2. Load the production HIGH bank (4003). HOLD if it is missing.
3. If the target is Neo4j + EC2 + GovCloud: run the collector, then the answerer.
4. Map findings to in-scope questions with cited paths.
5. Print the GRADE block + QUESTIONS tally + config-change list.
6. Speak in layman terms. Stop. Do not claim ATO.
