#!/usr/bin/env bash
# Read-only Neo4j-on-EC2 US GovCloud evidence collector.
# Copies configs and describe-output into evidence/<run-id>/.
# Never dumps graph data. Never writes exploits, PoCs, or attack playbooks.
# Never claims ATO, FedRAMP authorization, or DISA PA.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
RUN_ID=""
OUT_DIR=""
LOCAL_ROOT=""
SSH_TARGET=""
SSM_ID=""
AWS_REGION=""
AWS_PROFILE=""
INSTANCE_ID=""
NEO4J_HOME=""
NEO4J_CONF=""
SKIP_AWS=0

usage() {
  cat <<'EOF'
Usage: tools/collect_neo4j_ec2_evidence.sh [options]

Read-only collection of Neo4j + EC2 GovCloud configs into evidence/<run-id>/.
Does not dump the graph. Does not change configuration. Does not claim ATO.

Options:
  --out DIR              Destination (default: evidence/<utc-run-id>)
  --run-id ID            Run id used under evidence/ID
  --local-root DIR       Copy from a directory that already has neo4j.conf / AWS JSON
  --ssh user@host        Collect over SSH (read-only remote commands)
  --ssm INSTANCE_ID      Collect via AWS-RunShellScript (GovCloud region required)
  --region REGION        AWS region (us-gov-west-1 or us-gov-east-1)
  --profile NAME         AWS CLI profile
  --instance-id ID       EC2 instance id for describe-* (defaults to --ssm)
  --neo4j-home DIR       Remote or local NEO4J_HOME (default: autodetect)
  --neo4j-conf FILE      Path to neo4j.conf
  --skip-aws             Do not call AWS APIs
  -h, --help             This help

Examples:
  tools/collect_neo4j_ec2_evidence.sh --local-root /path/to/copied-configs
  tools/collect_neo4j_ec2_evidence.sh --ssh admin@10.0.1.20 --region us-gov-west-1 --instance-id i-0123
  tools/collect_neo4j_ec2_evidence.sh --ssm i-0123 --region us-gov-west-1 --profile gov

Do not put secrets in the repo. Redacted copies are written next to originals.
EOF
}

die() { echo "ERROR: $*" >&2; exit 2; }
note() { echo "$*" >&2; }

while [[ $# -gt 0 ]]; do
  case "$1" in
    --out) OUT_DIR="$2"; shift 2 ;;
    --run-id) RUN_ID="$2"; shift 2 ;;
    --local-root) LOCAL_ROOT="$2"; shift 2 ;;
    --ssh) SSH_TARGET="$2"; shift 2 ;;
    --ssm) SSM_ID="$2"; shift 2 ;;
    --region) AWS_REGION="$2"; shift 2 ;;
    --profile) AWS_PROFILE="$2"; shift 2 ;;
    --instance-id) INSTANCE_ID="$2"; shift 2 ;;
    --neo4j-home) NEO4J_HOME="$2"; shift 2 ;;
    --neo4j-conf) NEO4J_CONF="$2"; shift 2 ;;
    --skip-aws) SKIP_AWS=1; shift ;;
    -h|--help) usage; exit 0 ;;
    *) die "unknown argument: $1" ;;
  esac
done

if [[ -z "$RUN_ID" ]]; then
  RUN_ID="$(date -u +%Y%m%dT%H%M%SZ)-neo4j-ec2"
fi
if [[ -z "$OUT_DIR" ]]; then
  OUT_DIR="${ROOT}/evidence/${RUN_ID}"
fi
if [[ -z "$INSTANCE_ID" && -n "$SSM_ID" ]]; then
  INSTANCE_ID="$SSM_ID"
fi

mkdir -p "$OUT_DIR"/{neo4j,ec2,os,scans,interviews,notes}
ABS_OUT="$(cd "$OUT_DIR" && pwd)"

aws_cli() {
  local args=(aws)
  if [[ -n "$AWS_PROFILE" ]]; then
    args+=(--profile "$AWS_PROFILE")
  fi
  if [[ -n "$AWS_REGION" ]]; then
    args+=(--region "$AWS_REGION")
  fi
  "${args[@]}" "$@"
}

redact_stream() {
  # Redact secret-bearing assignment lines. Keep key names for evidence.
  sed -E \
    -e 's/([Pp]assword|[Pp]asswd|[Ss]ecret|[Cc]lient_[Ss]ecret|[Bb]ind_[Pp]assword|[Kk]eystore[_-]?[Pp]assword|[Tt]ruststore[_-]?[Pp]assword|[Pp]rivate[_-]?[Kk]ey)([[:alnum:]._-]*)[[:space:]]*[=:][[:space:]]*.*/\1\2=***REDACTED***/g'
}

write_missing() {
  local dest="$1"
  local why="$2"
  mkdir -p "$(dirname "$dest")"
  printf 'MISSING: %s\n' "$why" >"$dest"
}

copy_if_exists() {
  local src="$1"
  local dest="$2"
  if [[ -f "$src" ]]; then
    mkdir -p "$(dirname "$dest")"
    redact_stream <"$src" >"$dest"
    return 0
  fi
  return 1
}

collect_from_local_root() {
  local src="$1"
  note "Copying local-root $src → $ABS_OUT"
  if [[ ! -d "$src" ]]; then
    die "--local-root is not a directory: $src"
  fi
  # Prefer a neo4j.conf wherever it sits.
  local found
  found="$(find "$src" -type f \( -name 'neo4j.conf' -o -name 'apoc.conf' -o -name '*.json' -o -name '*.txt' \) 2>/dev/null | head -n 200 || true)"
  local f
  for f in $found; do
    local rel="${f#"$src"/}"
    local dest="$ABS_OUT/$rel"
    mkdir -p "$(dirname "$dest")"
    if [[ "$f" == *.json ]]; then
      cp -p "$f" "$dest"
    else
      redact_stream <"$f" >"$dest"
    fi
  done
  # Also flatten common names into neo4j/ and ec2/ if the tree is flat.
  copy_if_exists "$src/neo4j.conf" "$ABS_OUT/neo4j/neo4j.conf.redacted" || true
  copy_if_exists "$src/apoc.conf" "$ABS_OUT/neo4j/apoc.conf.redacted" || true
}

collect_host_os_into() {
  local dest_root="$1"
  mkdir -p "$dest_root/os" "$dest_root/neo4j"
  {
    echo "date_utc=$(date -u +%Y-%m-%dT%H:%M:%SZ)"
    echo "uname=$(uname -a 2>/dev/null || true)"
    command -v timedatectl >/dev/null && timedatectl 2>/dev/null || true
  } >"$dest_root/os/uname.txt" || true

  if command -v ss >/dev/null 2>&1; then
    ss -lntup 2>/dev/null | redact_stream >"$dest_root/os/listening-ports.txt" || \
      ss -lnt 2>/dev/null >"$dest_root/os/listening-ports.txt" || true
  elif command -v netstat >/dev/null 2>&1; then
    netstat -lnt 2>/dev/null >"$dest_root/os/listening-ports.txt" || true
  else
    write_missing "$dest_root/os/listening-ports.txt" "ss/netstat not available"
  fi

  if [[ -f /proc/sys/crypto/fips_enabled ]]; then
    echo "fips_enabled=$(cat /proc/sys/crypto/fips_enabled)" >"$dest_root/os/fips.txt"
  else
    write_missing "$dest_root/os/fips.txt" "/proc/sys/crypto/fips_enabled not present"
  fi

  # IMDSv2 hop / token check — read-only metadata, no role-credential dump.
  local token=""
  token="$(curl -sS -X PUT "http://169.254.169.254/latest/api/token" \
    -H "X-aws-ec2-metadata-token-ttl-seconds: 60" --connect-timeout 2 --max-time 4 2>/dev/null || true)"
  if [[ -n "$token" ]]; then
    echo "imdsv2_token=obtained" >"$dest_root/os/imds-hop-limit.txt"
    curl -sS -H "X-aws-ec2-metadata-token: $token" \
      http://169.254.169.254/latest/dynamic/instance-identity/document \
      --connect-timeout 2 --max-time 4 \
      >"$dest_root/ec2/identity-document.json" 2>/dev/null || true
    local hops
    hops="$(curl -sS -H "X-aws-ec2-metadata-token: $token" \
      http://169.254.169.254/latest/meta-data/network/interfaces/macs/ \
      --connect-timeout 2 --max-time 4 2>/dev/null || true)"
    echo "macs=${hops}" >>"$dest_root/os/imds-hop-limit.txt"
  else
    write_missing "$dest_root/os/imds-hop-limit.txt" "IMDSv2 token not obtained (not on EC2 or IMDS blocked)"
  fi

  # STIG / SCAP placeholders — copy if the host already has results; do not scan.
  if [[ -d /var/log/oscap ]]; then
    ls -la /var/log/oscap >"$dest_root/os/stig-notes.txt" 2>/dev/null || true
  else
    write_missing "$dest_root/os/stig-notes.txt" "No /var/log/oscap results on host. Record the current quarterly STIG separately."
  fi
}

collect_neo4j_into() {
  local dest_root="$1"
  local home="${2:-}"
  local conf="${3:-}"
  mkdir -p "$dest_root/neo4j"

  if [[ -z "$conf" ]]; then
    local candidates=()
    [[ -n "$home" ]] && candidates+=("$home/conf/neo4j.conf")
    candidates+=(
      /etc/neo4j/neo4j.conf
      /var/lib/neo4j/conf/neo4j.conf
      /opt/neo4j/conf/neo4j.conf
    )
    local c
    for c in "${candidates[@]}"; do
      if [[ -f "$c" ]]; then
        conf="$c"
        break
      fi
    done
  fi

  if [[ -n "$conf" && -f "$conf" ]]; then
    echo "neo4j_conf=$conf" >"$dest_root/neo4j/conf-path.txt"
    redact_stream <"$conf" >"$dest_root/neo4j/neo4j.conf.redacted"
    # Extract non-secret setting names for mapping (values redacted if they look like secrets).
    grep -E '^(server|dbms|initial|browser|metrics|logging)\.' "$conf" 2>/dev/null \
      | redact_stream >"$dest_root/neo4j/neo4j-settings-grep.txt" || true
    grep -E 'auth|ldap|oidc|saml|authentication_providers|authorization_providers' "$conf" 2>/dev/null \
      | redact_stream >"$dest_root/neo4j/auth-providers.txt" || true
    grep -E 'ssl|tls|bolt|http|https|listen_address' "$conf" 2>/dev/null \
      | redact_stream >"$dest_root/neo4j/tls-settings.txt" || true
    grep -E 'listen_address|advertised_address|bolt|http|https|backup' "$conf" 2>/dev/null \
      | redact_stream >"$dest_root/neo4j/listeners.txt" || true
    grep -E 'query\.log|logs\.query|db.logs.query' "$conf" 2>/dev/null \
      | redact_stream >"$dest_root/neo4j/query-log-settings.txt" || true
    grep -E 'backup|recovery|cluster' "$conf" 2>/dev/null \
      | redact_stream >"$dest_root/neo4j/backup-settings.txt" || true
    grep -E 'procedures\.(unrestricted|allowlist)|plugin' "$conf" 2>/dev/null \
      | redact_stream >"$dest_root/neo4j/plugins.txt" || true
  else
    write_missing "$dest_root/neo4j/neo4j.conf.redacted" "neo4j.conf not found. Pass --neo4j-conf or --neo4j-home."
  fi

  local apoc_candidates=()
  [[ -n "$home" ]] && apoc_candidates+=("$home/conf/apoc.conf")
  apoc_candidates+=(/etc/neo4j/apoc.conf /var/lib/neo4j/conf/apoc.conf)
  local a
  for a in "${apoc_candidates[@]}"; do
    if [[ -f "$a" ]]; then
      redact_stream <"$a" >"$dest_root/neo4j/apoc.conf.redacted"
      break
    fi
  done
  if [[ ! -f "$dest_root/neo4j/apoc.conf.redacted" ]]; then
    write_missing "$dest_root/neo4j/apoc.conf.redacted" "apoc.conf not found"
  fi

  if command -v neo4j-admin >/dev/null 2>&1; then
    # Settings dump only. Never `database dump` (that is graph data).
    if neo4j-admin server report --help >/dev/null 2>&1; then
      echo "neo4j-admin server report is available. Not invoked automatically (can include logs). Run only if the operator approved a settings-only report." \
        >"$dest_root/neo4j/server-report-note.txt"
    fi
    neo4j-admin server memory-recommendation >/dev/null 2>&1 || true
    if neo4j-admin help 2>/dev/null | grep -q 'setting'; then
      neo4j-admin setting 2>/dev/null | redact_stream >"$dest_root/neo4j/neo4j-admin-settings.txt" || \
        write_missing "$dest_root/neo4j/neo4j-admin-settings.txt" "neo4j-admin settings subcommand failed"
    else
      write_missing "$dest_root/neo4j/neo4j-admin-settings.txt" "neo4j-admin settings subcommand not in this version"
    fi
  else
    write_missing "$dest_root/neo4j/neo4j-admin-settings.txt" "neo4j-admin not on PATH"
  fi

  # Plugin directory listing — names only.
  local plug_dirs=()
  [[ -n "$home" ]] && plug_dirs+=("$home/plugins")
  plug_dirs+=(/var/lib/neo4j/plugins /opt/neo4j/plugins)
  local p
  for p in "${plug_dirs[@]}"; do
    if [[ -d "$p" ]]; then
      ls -la "$p" >"$dest_root/neo4j/plugins.txt" 2>/dev/null || true
      break
    fi
  done

  cat >"$dest_root/neo4j/encryption-at-rest.txt" <<'EOT'
Neo4j Community/Enterprise filesystem encryption is typically the volume
(EBS) plus optional enterprise features. This collector does not dump store
files. See ec2/ebs-volumes.json for volume encryption / KMS key ids.
EOT

  if command -v java >/dev/null 2>&1; then
    java -XshowSettings:security -version >"$dest_root/neo4j/java-security.txt" 2>&1 || true
  else
    write_missing "$dest_root/neo4j/java-security.txt" "java not on PATH"
  fi
}

collect_via_ssh() {
  local target="$1"
  note "SSH collect from $target (read-only)"
  local remote_tmp="/tmp/il5-neo4j-ec2-$$"
  ssh -o BatchMode=yes -o StrictHostKeyChecking=accept-new "$target" \
    "NEO4J_HOME='${NEO4J_HOME}' NEO4J_CONF='${NEO4J_CONF}' bash -s" <<'REMOTE'
set -euo pipefail
tmp=$(mktemp -d)
mkdir -p "$tmp"/{neo4j,ec2,os}
# Host OS
{
  echo "date_utc=$(date -u +%Y-%m-%dT%H:%M:%SZ)"
  echo "uname=$(uname -a 2>/dev/null || true)"
} >"$tmp/os/uname.txt"
if command -v ss >/dev/null 2>&1; then
  ss -lnt 2>/dev/null >"$tmp/os/listening-ports.txt" || true
fi
if [[ -f /proc/sys/crypto/fips_enabled ]]; then
  echo "fips_enabled=$(cat /proc/sys/crypto/fips_enabled)" >"$tmp/os/fips.txt"
fi
token=$(curl -sS -X PUT "http://169.254.169.254/latest/api/token" \
  -H "X-aws-ec2-metadata-token-ttl-seconds: 60" --connect-timeout 2 --max-time 4 2>/dev/null || true)
if [[ -n "$token" ]]; then
  echo "imdsv2_token=obtained" >"$tmp/os/imds-hop-limit.txt"
  curl -sS -H "X-aws-ec2-metadata-token: $token" \
    http://169.254.169.254/latest/dynamic/instance-identity/document \
    --connect-timeout 2 --max-time 4 >"$tmp/ec2/identity-document.json" 2>/dev/null || true
fi
conf=""
if [[ -n "${NEO4J_CONF:-}" && -f "${NEO4J_CONF}" ]]; then
  conf="$NEO4J_CONF"
else
  for c in ${NEO4J_HOME:+$NEO4J_HOME/conf/neo4j.conf} /etc/neo4j/neo4j.conf /var/lib/neo4j/conf/neo4j.conf /opt/neo4j/conf/neo4j.conf; do
    [[ -f "$c" ]] && conf="$c" && break
  done
fi
if [[ -n "$conf" ]]; then
  echo "neo4j_conf=$conf" >"$tmp/neo4j/conf-path.txt"
  # Redact on the remote before the tarball leaves the host.
  sed -E 's/([Pp]assword|[Pp]asswd|[Ss]ecret|[Bb]ind_[Pp]assword|[Kk]eystore[_-]?[Pp]assword|[Tt]ruststore[_-]?[Pp]assword|[Pp]rivate[_-]?[Kk]ey)([[:alnum:]._-]*)[[:space:]]*[=:][[:space:]]*.*/\1\2=***REDACTED***/g' \
    <"$conf" >"$tmp/neo4j/neo4j.conf.redacted"
fi
for a in ${NEO4J_HOME:+$NEO4J_HOME/conf/apoc.conf} /etc/neo4j/apoc.conf; do
  if [[ -f "$a" ]]; then
    sed -E 's/([Pp]assword|[Ss]ecret)([[:alnum:]._-]*)[[:space:]]*[=:][[:space:]]*.*/\1\2=***REDACTED***/g' \
      <"$a" >"$tmp/neo4j/apoc.conf.redacted"
    break
  fi
done
if command -v neo4j-admin >/dev/null 2>&1; then
  echo "neo4j-admin=$(command -v neo4j-admin)" >"$tmp/neo4j/neo4j-admin-settings.txt"
  neo4j-admin version >>"$tmp/neo4j/neo4j-admin-settings.txt" 2>&1 || true
fi
tar -C "$tmp" -czf /tmp/il5-neo4j-ec2-evidence.tgz .
echo /tmp/il5-neo4j-ec2-evidence.tgz
REMOTE
  scp -o BatchMode=yes "$target:/tmp/il5-neo4j-ec2-evidence.tgz" "$ABS_OUT/remote.tgz"
  tar -C "$ABS_OUT" -xzf "$ABS_OUT/remote.tgz"
  rm -f "$ABS_OUT/remote.tgz"
  ssh -o BatchMode=yes "$target" "rm -f /tmp/il5-neo4j-ec2-evidence.tgz" || true
}

collect_via_ssm() {
  local iid="$1"
  [[ -n "$AWS_REGION" ]] || die "--ssm requires --region (us-gov-west-1 or us-gov-east-1)"
  command -v aws >/dev/null 2>&1 || die "aws CLI not found"
  note "SSM collect from $iid in $AWS_REGION (read-only AWS-RunShellScript)"
  local commands
  commands=$(cat <<'SSM'
set -euo pipefail
echo "=== uname ==="
uname -a
echo "=== fips ==="
if [ -f /proc/sys/crypto/fips_enabled ]; then cat /proc/sys/crypto/fips_enabled; else echo MISSING; fi
echo "=== listening ==="
ss -lnt 2>/dev/null || netstat -lnt 2>/dev/null || echo MISSING
echo "=== neo4j.conf ==="
for c in /etc/neo4j/neo4j.conf /var/lib/neo4j/conf/neo4j.conf /opt/neo4j/conf/neo4j.conf; do
  if [ -f "$c" ]; then
    echo "PATH=$c"
    sed -E 's/([Pp]assword|[Ss]ecret|[Bb]ind_[Pp]assword)([[:alnum:]._-]*)[[:space:]]*[=:][[:space:]]*.*/\1\2=***REDACTED***/g' "$c"
    break
  fi
done
echo "=== apoc.conf ==="
for a in /etc/neo4j/apoc.conf /var/lib/neo4j/conf/apoc.conf; do
  if [ -f "$a" ]; then
    echo "PATH=$a"
    sed -E 's/([Pp]assword|[Ss]ecret)([[:alnum:]._-]*)[[:space:]]*[=:][[:space:]]*.*/\1\2=***REDACTED***/g' "$a"
    break
  fi
done
echo "=== neo4j-admin ==="
command -v neo4j-admin && neo4j-admin version || echo MISSING
echo "=== plugins ==="
ls -la /var/lib/neo4j/plugins /opt/neo4j/plugins /etc/neo4j/plugins 2>/dev/null || echo MISSING
SSM
)
  local cmd_id
  cmd_id="$(aws_cli ssm send-command \
    --instance-ids "$iid" \
    --document-name AWS-RunShellScript \
    --comment "IL5 read-only Neo4j/EC2 evidence collect — no dump, no ATO" \
    --parameters "commands=[$(python3 -c 'import json,sys; print(json.dumps(sys.stdin.read()))' <<<"$commands")]" \
    --query 'Command.CommandId' --output text)"
  echo "ssm_command_id=$cmd_id" >"$ABS_OUT/ec2/ssm-command-id.txt"
  note "Waiting for SSM command $cmd_id"
  local i
  for i in 1 2 3 4 5 6 7 8 9 10 11 12; do
    local status
    status="$(aws_cli ssm get-command-invocation --command-id "$cmd_id" --instance-id "$iid" --query 'Status' --output text 2>/dev/null || echo Pending)"
    case "$status" in
      Success|Failed|Cancelled|TimedOut) break ;;
    esac
    sleep 5
  done
  aws_cli ssm get-command-invocation --command-id "$cmd_id" --instance-id "$iid" \
    --output json >"$ABS_OUT/os/ssm-invocation.json"
  python3 - "$ABS_OUT/os/ssm-invocation.json" "$ABS_OUT" <<'PY'
import json, sys
from pathlib import Path
inv = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
out = inv.get("StandardOutputContent") or ""
Path(sys.argv[2], "os", "ssm-stdout.txt").write_text(out, encoding="utf-8")
err = inv.get("StandardErrorContent") or ""
if err:
    Path(sys.argv[2], "os", "ssm-stderr.txt").write_text(err, encoding="utf-8")
# Split neo4j.conf block if present.
if "=== neo4j.conf ===" in out:
    block = out.split("=== neo4j.conf ===", 1)[1]
    if "=== " in block:
        block = block.split("=== ", 1)[0]
    Path(sys.argv[2], "neo4j", "neo4j.conf.redacted").write_text(block.strip() + "\n", encoding="utf-8")
if "=== apoc.conf ===" in out:
    block = out.split("=== apoc.conf ===", 1)[1]
    if "=== " in block:
        block = block.split("=== ", 1)[0]
    Path(sys.argv[2], "neo4j", "apoc.conf.redacted").write_text(block.strip() + "\n", encoding="utf-8")
PY
}

collect_aws_apis() {
  local iid="$1"
  if [[ "$SKIP_AWS" -eq 1 ]]; then
    write_missing "$ABS_OUT/ec2/instance.json" "--skip-aws"
    return
  fi
  if ! command -v aws >/dev/null 2>&1; then
    write_missing "$ABS_OUT/ec2/instance.json" "aws CLI not installed"
    return
  fi
  if [[ -z "$AWS_REGION" ]]; then
    write_missing "$ABS_OUT/ec2/region.txt" "--region not set. For GovCloud use us-gov-west-1 or us-gov-east-1."
    return
  fi
  echo "$AWS_REGION" >"$ABS_OUT/ec2/region.txt"
  if [[ "$AWS_REGION" != us-gov-* ]]; then
    echo "WARN: region $AWS_REGION is not a US GovCloud region (us-gov-west-1 / us-gov-east-1). IL5 location rules are standard §8.1." \
      >"$ABS_OUT/ec2/region-warning.txt"
  fi
  if [[ -z "$iid" ]]; then
    write_missing "$ABS_OUT/ec2/instance.json" "No --instance-id / --ssm. AWS describe skipped."
    return
  fi
  note "AWS describe-* for $iid in $AWS_REGION (read-only)"
  aws_cli ec2 describe-instances --instance-ids "$iid" >"$ABS_OUT/ec2/instance.json" || \
    write_missing "$ABS_OUT/ec2/instance.json" "describe-instances failed"
  aws_cli ec2 describe-instance-attribute --instance-id "$iid" --attribute disableApiTermination \
    >"$ABS_OUT/ec2/disable-api-termination.json" 2>/dev/null || true
  python3 - "$ABS_OUT/ec2/instance.json" "$ABS_OUT" <<'PY' || true
import json, sys
from pathlib import Path
p = Path(sys.argv[1])
out = Path(sys.argv[2])
try:
    doc = json.loads(p.read_text(encoding="utf-8"))
except Exception:
    sys.exit(0)
res = (doc.get("Reservations") or [{}])[0]
inst = (res.get("Instances") or [{}])[0]
meta = inst.get("MetadataOptions") or {}
(out / "ec2" / "imds.json").write_text(json.dumps(meta, indent=2) + "\n", encoding="utf-8")
enis = inst.get("NetworkInterfaces") or []
(out / "ec2" / "network-interfaces.json").write_text(json.dumps(enis, indent=2) + "\n", encoding="utf-8")
sg_ids = [g.get("GroupId") for g in inst.get("SecurityGroups") or [] if g.get("GroupId")]
(out / "ec2" / "sg-ids.txt").write_text("\n".join(sg_ids) + ("\n" if sg_ids else ""), encoding="utf-8")
vol_ids = [m.get("Ebs", {}).get("VolumeId") for m in inst.get("BlockDeviceMappings") or [] if m.get("Ebs", {}).get("VolumeId")]
(out / "ec2" / "volume-ids.txt").write_text("\n".join(vol_ids) + ("\n" if vol_ids else ""), encoding="utf-8")
profile = inst.get("IamInstanceProfile") or {}
(out / "ec2" / "iam-instance-profile.json").write_text(json.dumps(profile, indent=2) + "\n", encoding="utf-8")
vpc = {"VpcId": inst.get("VpcId"), "SubnetId": inst.get("SubnetId"), "Placement": inst.get("Placement"),
       "PublicIpAddress": inst.get("PublicIpAddress"), "PrivateIpAddress": inst.get("PrivateIpAddress"),
       "RegionHint": inst.get("Placement", {}).get("AvailabilityZone")}
(out / "ec2" / "vpc.json").write_text(json.dumps(vpc, indent=2) + "\n", encoding="utf-8")
PY
  if [[ -f "$ABS_OUT/ec2/sg-ids.txt" && -s "$ABS_OUT/ec2/sg-ids.txt" ]]; then
    # shellcheck disable=SC2046
    aws_cli ec2 describe-security-groups --group-ids $(tr '\n' ' ' <"$ABS_OUT/ec2/sg-ids.txt") \
      >"$ABS_OUT/ec2/security-groups.json" || true
  fi
  if [[ -f "$ABS_OUT/ec2/volume-ids.txt" && -s "$ABS_OUT/ec2/volume-ids.txt" ]]; then
    # shellcheck disable=SC2046
    aws_cli ec2 describe-volumes --volume-ids $(tr '\n' ' ' <"$ABS_OUT/ec2/volume-ids.txt") \
      >"$ABS_OUT/ec2/ebs-volumes.json" || true
  fi
  if [[ -f "$ABS_OUT/ec2/vpc.json" ]]; then
    local subnet
    subnet="$(python3 -c 'import json,sys; print(json.load(open(sys.argv[1])).get("SubnetId") or "")' "$ABS_OUT/ec2/vpc.json" 2>/dev/null || true)"
    if [[ -n "$subnet" ]]; then
      aws_cli ec2 describe-subnets --subnet-ids "$subnet" >"$ABS_OUT/ec2/subnets.json" || true
    fi
  fi
  aws_cli ssm describe-instance-information --filters "Key=InstanceIds,Values=$iid" \
    >"$ABS_OUT/ec2/ssm-instance.json" 2>/dev/null || \
    write_missing "$ABS_OUT/ec2/ssm-instance.json" "describe-instance-information failed"
  aws_cli ssm describe-instance-patch-states --instance-ids "$iid" \
    >"$ABS_OUT/ec2/ssm-patch-state.json" 2>/dev/null || \
    write_missing "$ABS_OUT/ec2/ssm-patch-state.json" "describe-instance-patch-states failed"
  aws_cli logs describe-log-groups --limit 50 \
    >"$ABS_OUT/ec2/cloudwatch-log-groups.json" 2>/dev/null || \
    write_missing "$ABS_OUT/ec2/cloudwatch-log-groups.json" "describe-log-groups failed"
  # Role policy names only — no secret material.
  local role_arn
  role_arn="$(python3 -c 'import json,sys; print((json.load(open(sys.argv[1])).get("Arn") or ""))' "$ABS_OUT/ec2/iam-instance-profile.json" 2>/dev/null || true)"
  if [[ -n "$role_arn" ]]; then
    echo "instance_profile_arn=$role_arn" >"$ABS_OUT/ec2/iam-role-policies.json"
    echo "NOTE: list attached role policies with iam get-instance-profile / list-attached-role-policies if the operator role allows. Do not paste long-term keys." \
      >>"$ABS_OUT/ec2/iam-role-policies.json"
  fi
}

write_manifest() {
  python3 - "$ABS_OUT" "$RUN_ID" "$ROOT" <<'PY'
import json, os, sys
from datetime import datetime, timezone
from pathlib import Path
out = Path(sys.argv[1])
run_id = sys.argv[2]
root = Path(sys.argv[3])
files = []
for p in sorted(out.rglob("*")):
    if p.is_file():
        rel = str(p.relative_to(out)).replace("\\", "/")
        if rel in {"MANIFEST.json", "FINDINGS-INDEX.json"}:
            continue
        files.append({"path": rel, "bytes": p.stat().st_size, "missing": p.read_text(encoding="utf-8", errors="replace")[:80].startswith("MISSING:")})
manifest = {
    "format": "il5-neo4j-ec2-evidence-v1",
    "run_id": run_id,
    "collected_at_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    "playbook": "playbooks/NEO4J-EC2-GOVCLOUD.md",
    "map": "il5-scanner/collectors/neo4j-ec2-govcloud-map.json",
    "read_only": True,
    "graph_dump": False,
    "never_ato": True,
    "files": files,
}
(out / "MANIFEST.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
# Findings index: which mapped collectors have non-MISSING files.
mapp = root / "il5-scanner" / "collectors" / "neo4j-ec2-govcloud-map.json"
index = {"format": "il5-findings-index-v1", "collectors": []}
if mapp.exists():
    doc = json.loads(mapp.read_text(encoding="utf-8"))
    present = {f["path"] for f in files if not f["missing"]}
    for c in doc.get("collectors") or []:
        hits = []
        for raw in c.get("paths") or []:
            raw = raw.rstrip("/")
            for p in present:
                if p == raw or p.startswith(raw + "/"):
                    hits.append(p)
        index["collectors"].append({
            "id": c.get("id"),
            "families": c.get("families"),
            "controls": c.get("controls"),
            "evidence_present": sorted(set(hits)),
            "present": bool(hits),
        })
(out / "FINDINGS-INDEX.json").write_text(json.dumps(index, indent=2) + "\n", encoding="utf-8")
print(str(out))
PY
}

# --- run ---
note "IL5 Neo4j/EC2 collector → $ABS_OUT"
echo "This collector is read-only. It does not authorize, PA, or ATO anything." >"$ABS_OUT/COLLECTOR.md"
cat >>"$ABS_OUT/COLLECTOR.md" <<EOF

run_id: $RUN_ID
playbook: playbooks/NEO4J-EC2-GOVCLOUD.md
operator: RUN.md

Do not commit secrets. Redacted copies use ***REDACTED***.
EOF

if [[ -n "$LOCAL_ROOT" ]]; then
  collect_from_local_root "$LOCAL_ROOT"
fi

# Local-host collection when no remote transport was given (or in addition).
if [[ -z "$SSH_TARGET" && -z "$SSM_ID" && -z "$LOCAL_ROOT" ]]; then
  collect_host_os_into "$ABS_OUT"
  collect_neo4j_into "$ABS_OUT" "$NEO4J_HOME" "$NEO4J_CONF"
elif [[ -z "$SSH_TARGET" && -z "$SSM_ID" && -n "$LOCAL_ROOT" ]]; then
  # Local-root already copied; still try host OS if we are on the box.
  collect_host_os_into "$ABS_OUT"
  collect_neo4j_into "$ABS_OUT" "$NEO4J_HOME" "$NEO4J_CONF"
fi

if [[ -n "$SSH_TARGET" ]]; then
  collect_via_ssh "$SSH_TARGET"
fi
if [[ -n "$SSM_ID" ]]; then
  collect_via_ssm "$SSM_ID"
fi

collect_aws_apis "$INSTANCE_ID"
write_manifest

note "Evidence written to $ABS_OUT"
note "Next: python3 tools/answer_bank_from_evidence.py --evidence $ABS_OUT"
note "READY is never ATO. High alone fails IL5."
