# Playbook — Neo4j on EC2 in AWS US GovCloud

Read-only configuration inspection for **customer-managed Neo4j** on **EC2** in **AWS GovCloud (US)**. Target stack is **FedRAMP High plus DoD IL5** unless intake says High only.

This playbook does **not** authorize, PA, or ATO anything. `READY` is never ATO. High alone fails IL5. Do not write exploits, PoCs, payloads, or attack playbooks. Do not dump the graph.

Operator steps (Codex): [`RUN.md`](../RUN.md). Contract: [`AGENTS.md`](../AGENTS.md). Rubric: [`FEDRAMP-HIGH-IL5-STANDARD.md`](../FEDRAMP-HIGH-IL5-STANDARD.md) §§8–9, §14, §21–§22, §28.

Default bank after intake: `il5-scanner/banks/production-high-53a-questions.jsonl` (**4003** questions). Fixture tiny bank is fixture-only.

---

## 1. Shared responsibility (say this out loud)

| Layer | Who | What IL5 reviewers will ask |
|---|---|---|
| **IaaS — EC2 / VPC / EBS / KMS / IAM / CloudWatch / SSM** | AWS GovCloud **plus** the customer who configured the instance | Inherit only **in-scope** GovCloud services that are on the current FedRAMP Marketplace package **and** the DISA IL5 PA service list (standard §22). A platform PA does **not** cover Neo4j. |
| **Guest OS** | Customer (typical IaaS split) | STIG / SCAP, patching (SSM Patch), FIPS mode, time sync, EDR, inventory (Appendix M). |
| **Neo4j software** | Customer | `neo4j.conf`, auth (native / LDAP / SSO), Bolt/HTTP/HTTPS, TLS policies, plugins / APOC, query logs, backups of **graph** data, RBAC. **Not inherited.** |
| **Mission data in the graph** | Customer / mission | CUI / NSS categorization, encryption at rest (EBS + CMK), backup encryption (CP-9(8)), who can run Cypher. |

CRM row pattern (standard §21–§22): Implemented / Inherited / Shared / Customer / N/A — inherited-from package ID + date. Do not mark Neo4j AC/IA/AU/SC rows “inherited from AWS.”

Commercial AWS (`aws` partition, `us-east-1`, …) is **not** GovCloud (`aws-us-gov`, `us-gov-west-1`, `us-gov-east-1`). Encrypting harder in a commercial region does not become IL5 (standard §8, §28 #1).

---

## 2. What to collect when pointed (read-only)

Point Codex at **SSM**, **SSH**, or **already-copied paths**. No long-term keys in the repo. Redact passwords in place.

Collector: `tools/collect_neo4j_ec2_evidence.sh` → `evidence/<run-id>/`.

| Collector id | What to gather (inspection only) | Typical command / file | Families | Bank use |
|---|---|---|---|---|
| `neo4j.conf` | Full settings file, redacted | `/etc/neo4j/neo4j.conf` or `$NEO4J_HOME/conf/neo4j.conf` | AC AU CM IA SC | Examine AC-2/3/17, IA-2/5, SC-7/8/13, CM-6/7, AU-2/12 |
| `neo4j-admin-settings` | Settings listing — **not** `database dump` | `neo4j-admin version`; settings subcommand if present | CM SC | Examine CM-6 |
| `auth-providers` | native / LDAP / OIDC / SSO lines | `grep -E 'auth\|ldap\|oidc\|saml' neo4j.conf` | AC IA | Examine IA-2, IA-5, IA-8, AC-2 |
| `tls` | Bolt/HTTPS SSL policy, cert paths (not private keys) | `grep -E 'ssl\|tls' neo4j.conf`; `dbms.ssl.policy.*` | SC AC | Examine SC-8, SC-8(1), SC-13, AC-17(2) |
| `listeners-ports` | listen/advertised addresses; host listeners | `ss -lnt` (or `netstat -lnt`); Bolt 7687, HTTP 7474, HTTPS 7473 | SC AC CM | Examine/Test SC-7, CM-7, AC-17 |
| `encryption-at-rest` | Store encryption feature + **EBS** | Neo4j notes + `describe-volumes` | SC | Examine SC-28, SC-12, SC-13 |
| `backups` | backup schedule, dest, encryption | `grep backup neo4j.conf`; systemd/cron **names** only | CP SC | Examine CP-9, CP-9(8) |
| `plugins-apoc` | plugin JARs + `apoc.conf` | `ls $NEO4J_HOME/plugins`; `apoc.conf` | AC CM SI | Examine AC-6, CM-7, SI-7 |
| `query-logging` | query log enablement + dest | `db.logs.query.enabled` / `dbms.logs.query.enabled` | AU | Examine AU-2, AU-3, AU-12 |
| `security-groups` | inbound/outbound rules | `aws ec2 describe-security-groups` | SC AC | Examine SC-7, AC-4, AC-17 |
| `imdsv2` | `HttpTokens`, hop limit; IMDS token **without** role-cred dump | `describe-instances` → `MetadataOptions`; `PUT /latest/api/token` | AC SC CM | Examine/Test CM-6, AC-6 |
| `ebs-kms` | volume encrypted + `KmsKeyId` partition | `aws ec2 describe-volumes` | SC MP | Examine SC-12, SC-13, SC-28 |
| `vpc-subnet` | VPC, subnet, public IP, AZ | `describe-instances`, `describe-subnets` | SC AC | Examine SC-7, SA-9(5) |
| `ssm` | managed instance, inventory | `ssm describe-instance-information` | AC CM MA | Examine AC-17, CM-8 |
| `cloudwatch` | log groups / alarms (names) | `logs describe-log-groups` | AU SI | Examine AU-6, AU-12, SI-4 |
| `ssm-patch` | patch state | `ssm describe-instance-patch-states` | SI CM RA | Examine SI-2, RA-5 |
| `stig` | existing SCAP/STIG results only — do not invent a scan | `/var/log/oscap` listing if present | CM | Examine/Test CM-6 |
| `iam-instance-profile` | profile ARN + attached policy **names** | `IamInstanceProfile` on the instance | AC IA | Examine AC-6 |
| `public-ip` | `PublicIpAddress` / ENI associations | `describe-instances`, `network-interfaces.json` | SC AC | Examine SC-7, AC-17 |
| `fips` | OS FIPS flag; JVM security settings | `/proc/sys/crypto/fips_enabled`; `java -XshowSettings:security` | SC IA | Examine/Test SC-13, IA-7 |
| `partition-region` | identity document / region | IMDS identity document; `--region` | SA PE SC | Examine SA-9, SA-9(5), PE-18 |
| `interviews` | operator notes (optional) | `evidence/<run-id>/interviews/` | * | Interview methods only |
| `scans` | existing authenticated scan exports (optional) | `evidence/<run-id>/scans/` | RA CM SI | Test methods |

Map file Codex loads: `il5-scanner/collectors/neo4j-ec2-govcloud-map.json`.

**Never collect:** graph `database dump`, store copies, unredacted keystores, IAM secret keys, customer Cypher result sets, exploit/PoC output.

---

## 3. US GovCloud specifics

| Topic | Required posture | Evidence |
|---|---|---|
| Regions | `us-gov-west-1` and/or `us-gov-east-1` | `ec2/region.txt`, IMDS identity document |
| Partition | `aws-us-gov` ARNs (`arn:aws-us-gov:…`) | KMS key ARN, instance profile ARN |
| vs commercial | Different accounts, different IAM, no “stretch” of commercial admin into GovCloud | Management-plane statement (standard §8.4) |
| FedRAMP inheritance | AWS GovCloud has FedRAMP High and DoD IL2/4/5 PAs **for listed services** | Marketplace + DISA PA service list — not assumed |
| Customer Neo4j | **Not** on the AWS PA boundary | CRM: Customer for Neo4j AC/IA/AU/SC/CM |
| FIPS | In-transit and at-rest modules on the **active** CMVP list, **in FIPS mode** (standard §9). FIPS 140-2 historical **21 Sep 2026** | Appendix Q + `os/fips.txt` + JVM/module certs |
| CAC/PIV | Privileged DoD users at Credential Strength D (standard §10) | IdP / Neo4j SSO / bastion — not software TOTP alone |
| No public IP | Private subnet; admin via SSM or VDMS jump; Bolt not on `0.0.0.0/0` | `instance.json`, SG JSON |
| BCAP / SCCA | If DoD-connected: no direct IL5 path across the open internet (standard §11) | Architecture doc — collector cannot invent this |

---

## 4. Answering the 4003-question HIGH bank

After collection:

```text
python3 tools/answer_bank_from_evidence.py \
  --evidence evidence/<run-id> \
  --path "IL5 non-NSS" \
  --shared-responsibility IaaS
```

Stub rules:

- Load **production HIGH** by default (4003). Do not grade from `fixtures/question-bank/`.
- Every in-scope question: `PASS | HOLD | WARN | N/A | MISSING`.
- **MISSING** if no mapped evidence file is present.
- **HOLD** if a mapped file is present — cited path, **not** PASS.
- **N/A** if `path_applicability` excludes the intake stack (overlay hooks on a High-only path).
- The stub **never invents PASS**. Codex may upgrade HOLD→PASS only after reading the cited file.
- IL5 paths also load `question-bank/il5-overlay-hooks.json` (hooks, not a cyber.mil workbook).
- Emit GRADE + QUESTIONS tally. `READY` ≠ ATO.

Interview questions stay MISSING until `interviews/` notes exist. Test questions stay MISSING until `scans/` or mapped test files (e.g. `os/listening-ports.txt`, `os/fips.txt`) exist.

---

## 5. Configuration change recommendations

Every automated finding uses this format (also `evidence/<run-id>/CONFIG-CHANGES.md`):

```markdown
- **current:** `dbms.connector.bolt.tls_level=DISABLED`
- **required:** Bolt TLS required (`dbms.ssl.policy.bolt.enabled=true` or `tls_level=REQUIRED`); TLS 1.2+
- **evidence:** `neo4j/neo4j.conf.redacted` ; grep -E 'tls|ssl.policy.bolt' neo4j.conf
```

Typical current → required rows (inspect, do not exploit):

| current | required | evidence command/file | Families |
|---|---|---|---|
| `dbms.security.auth_enabled=false` | `true`; LDAP/SSO or native + MFA at the bastion/IdP | `grep auth_enabled neo4j.conf` | IA AC |
| Bolt `tls_level=DISABLED` / `OPTIONAL` | TLS required; FIPS module in FIPS mode | `grep -E 'tls\|ssl.policy.bolt' neo4j.conf` | SC-8 SC-13 |
| `server.http.enabled=true` on ENI | HTTPS/Bolt only, or localhost + SG | `grep http neo4j.conf` | SC-7 SC-8 |
| listen `0.0.0.0` | Private ENI; no public IP | `grep listen_address neo4j.conf` | SC-7 AC-17 |
| `procedures.unrestricted=*` | Allowlist needed APOC only | `grep procedures.unrestricted neo4j.conf` | AC-6 CM-7 |
| `apoc.import.file.enabled=true` | Off unless documented allowlist | `apoc.conf` | AC-6 SI-7 |
| query log `false` | On; ship to CloudWatch/SIEM | `grep query neo4j.conf` | AU-2 AU-12 |
| `HttpTokens=optional` | `required` (IMDSv2) | `ec2/imds.json` | CM-6 AC-6 |
| `PublicIpAddress` set | None; private subnet + SSM | `describe-instances` | SC-7 |
| EBS `Encrypted=false` | Encrypted + GovCloud CMK | `describe-volumes` | SC-28 SC-12 |
| SG `7687/7474/22 = 0.0.0.0/0` | Named CIDRs / prefix lists | `describe-security-groups` | SC-7 AC-4 |
| region `us-east-1` | `us-gov-west-1` or `us-gov-east-1` | `--region` / identity document | SA-9 PE-18 |
| `fips_enabled=0` | OS FIPS + CMVP certs in Appendix Q | `cat /proc/sys/crypto/fips_enabled` | SC-13 |
| IAM profile `*:*` on Neo4j role | Least privilege: SSM, CW logs, KMS decrypt for **this** volume | `iam-instance-profile.json` | AC-6 |

Do not apply changes from this scanner unless the operator separately asked for a change window. The collector is read-only.

---

## 6. How Codex should run this slice

1. Intake **three** questions only (target stack, what to scan, IaaS/PaaS/SaaS). Stop and wait.
2. Load the production HIGH bank. Confirm 4003 rows and `il5-scanner/banks/SOURCE.json`.
3. If what-to-scan is Neo4j on EC2 GovCloud, read this playbook and `RUN.md`.
4. Run the collector (SSM / SSH / `--local-root`). Do not recon beyond what was pointed.
5. Run the answerer. Cite evidence paths on every HOLD.
6. Print GRADE + QUESTIONS + CONFIG-CHANGES. Speak in layman terms.
7. Never claim ATO. If PATH is High only and the user wanted IL5, HOLD.

---

## 7. §14 scan program (this collector is not the scan of record)

Config collection is **Examine** evidence. A 3PAO still expects authenticated OS + DB + STIG/SCAP, inventory match, monthly cadence, machine-readable corpus (standard §14). Mark scan-program coverage MISSING until those files are in `scans/` and Appendix M matches the instance id / private IP / hostname.
