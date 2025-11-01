#!/usr/bin/env bash
set -euo pipefail

DRY_RUN="${HARDENING_DRY_RUN:-0}"
ETC_DIR="${HARDENING_ETC_DIR:-/etc}"
UFW_ALLOW_PORTS=("22/tcp" "80/tcp" "443/tcp")
DISABLE_SERVICES=("avahi-daemon" "cups")

run_cmd() {
  if [[ "$DRY_RUN" == "1" ]]; then
    echo "RUN:$*"
  else
    "$@"
  fi
}

write_file() {
  local target="$1"
  local content="$2"
  if [[ "$DRY_RUN" == "1" ]]; then
    echo "WRITE:$target"
    return
  fi
  mkdir -p "$(dirname "$target")"
  if [[ -f "$target" ]]; then
    if printf '%s' "$content" | cmp -s - "$target"; then
      return
    fi
  fi
  printf '%s' "$content" > "$target"
}

if command -v apt-get >/dev/null 2>&1 || [[ "$DRY_RUN" == "1" ]]; then
  run_cmd apt-get update
  run_cmd apt-get install -y --no-install-recommends unattended-upgrades fail2ban
fi

if command -v ufw >/dev/null 2>&1 || [[ "$DRY_RUN" == "1" ]]; then
  run_cmd ufw --force enable
  for port in "${UFW_ALLOW_PORTS[@]}"; do
    run_cmd ufw allow "$port"
  done
  run_cmd ufw reload
fi

if command -v systemctl >/dev/null 2>&1 || [[ "$DRY_RUN" == "1" ]]; then
  for svc in "${DISABLE_SERVICES[@]}"; do
    if [[ "$DRY_RUN" == "1" ]]; then
      echo "SYSTEMCTL:disable:$svc"
    elif systemctl is-enabled "$svc" >/dev/null 2>&1; then
      systemctl disable "$svc"
      systemctl stop "$svc" || true
    fi
  done
fi

FAIL2BAN_DIR="$ETC_DIR/fail2ban/jail.d"
mkdir -p "$FAIL2BAN_DIR"
FAIL2BAN_CONF="$FAIL2BAN_DIR/ssh-hardening.local"
FAIL2BAN_CONTENT=$(cat <<'JAIL'
[sshd]
enabled = true
maxretry = 5
findtime = 600
bantime = 3600
JAIL
)
write_file "$FAIL2BAN_CONF" "$FAIL2BAN_CONTENT"

if command -v systemctl >/dev/null 2>&1 || [[ "$DRY_RUN" == "1" ]]; then
  run_cmd systemctl restart fail2ban
fi

echo "Hardening completed"
