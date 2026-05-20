#!/usr/bin/env bash
# video-claw one-command installer.
#
# Usage:
#   curl -fsSL https://raw.githubusercontent.com/amirfish1/video-claw/main/install.sh | bash
#   curl -fsSL .../install.sh | VIDEO_CLAW_FROM=readme bash
#   ./install.sh                          # direct invocation after git clone
#
# Behaviour:
#   - Verifies python3 >= 3.10, pipx, and a Chromium-class browser.
#   - `pipx install --force git+https://github.com/amirfish1/video-claw` (idempotent).
#   - When stdin is a TTY (or /dev/tty is openable), runs `video-claw setup`
#     so the user pastes their API keys and learns the cost tradeoffs.
#   - Non-interactive runs print a "run `video-claw setup` next" hint and exit clean.

set -euo pipefail

REPO_URL="https://github.com/amirfish1/video-claw"
PIPX_TARGET="git+${REPO_URL}"
MIN_PY_MAJOR=3
MIN_PY_MINOR=10

err() {
  printf 'install: %s\n' "$*" >&2
}

note() {
  printf 'install: %s\n' "$*"
}

# ---------------------------------------------------------------------------
# Prereq checks
# ---------------------------------------------------------------------------

require_python3() {
  if ! command -v python3 >/dev/null 2>&1; then
    err "python3 not found on PATH."
    err "  macOS: xcode-select --install"
    err "  Linux: install python3 from your distro"
    exit 1
  fi
  # Version gate: >= 3.10
  if ! python3 - <<'PY' 2>/dev/null
import sys
sys.exit(0 if sys.version_info >= (3, 10) else 1)
PY
  then
    local v
    v="$(python3 -c 'import sys; print("%d.%d" % sys.version_info[:2])' 2>/dev/null || printf 'unknown')"
    err "python3 ${v} found; need >= ${MIN_PY_MAJOR}.${MIN_PY_MINOR}."
    exit 1
  fi
}

require_pipx() {
  if command -v pipx >/dev/null 2>&1; then
    return 0
  fi
  err "pipx not found on PATH."
  if [ "$(uname -s 2>/dev/null || printf unknown)" = "Darwin" ] && command -v brew >/dev/null 2>&1; then
    if prompt_yes_no "install pipx with 'brew install pipx' now?"; then
      brew install pipx
      pipx ensurepath >/dev/null 2>&1 || true
      # ensurepath edits the user's shell rc; current shell still lacks the new PATH.
      if ! command -v pipx >/dev/null 2>&1; then
        err "pipx installed but not on PATH in this shell."
        err "  Open a new terminal and re-run this installer, or run 'pipx ensurepath' and source your shell rc."
        exit 1
      fi
      return 0
    fi
  fi
  err "Install pipx and re-run. https://pipx.pypa.io/stable/installation/"
  exit 1
}

# Returns 0 if at least one Chromium-class browser exists.
# CHROME_BIN env var wins; otherwise we prefer stable Chrome over Beta/Dev/Canary,
# and Chrome family over Brave/Edge. Keep this order in sync with
# video_claw/renderer_html.py:_find_chrome_binary().
check_chrome() {
  if [ -n "${CHROME_BIN:-}" ] && [ -x "$CHROME_BIN" ]; then
    return 0
  fi
  # macOS app-bundle paths (stable channel first, dev/beta after, alternates last).
  local mac_candidates=(
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
    "/Applications/Google Chrome Beta.app/Contents/MacOS/Google Chrome Beta"
    "/Applications/Google Chrome Dev.app/Contents/MacOS/Google Chrome Dev"
    "/Applications/Google Chrome Canary.app/Contents/MacOS/Google Chrome Canary"
    "/Applications/Chromium.app/Contents/MacOS/Chromium"
    "/Applications/Brave Browser.app/Contents/MacOS/Brave Browser"
    "/Applications/Brave Browser Beta.app/Contents/MacOS/Brave Browser Beta"
    "/Applications/Brave Browser Nightly.app/Contents/MacOS/Brave Browser Nightly"
    "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge"
  )
  for p in "${mac_candidates[@]}"; do
    if [ -x "$p" ]; then
      return 0
    fi
  done
  # PATH-based fallbacks (Linux + dev shells).
  for cmd in google-chrome google-chrome-stable chromium chromium-browser brave-browser microsoft-edge chrome; do
    if command -v "$cmd" >/dev/null 2>&1; then
      return 0
    fi
  done
  return 1
}

require_chrome() {
  if check_chrome; then
    return 0
  fi
  err "no Chromium-class browser found (Google Chrome / Chromium / Brave)."
  err "  macOS: download Chrome from https://www.google.com/chrome/"
  err "  Or set CHROME_BIN=/path/to/chrome before running render."
  err "Continuing anyway; you can install Chrome later."
}

# ---------------------------------------------------------------------------
# pipx install
# ---------------------------------------------------------------------------

do_install() {
  # We always pass --force for idempotency (re-running the installer should
  # bring you up to head). Tone the user-facing message accordingly: if pipx
  # has no existing video-claw venv, this is a fresh install, not a "forced
  # reinstall"; if it does, frame it as a refresh rather than an override.
  local existing=""
  if command -v pipx >/dev/null 2>&1; then
    existing="$(pipx list --short 2>/dev/null | awk '$1 == "video-claw" { print $1 }')"
  fi
  if [ -n "$existing" ]; then
    note "found existing video-claw — refreshing to latest version..."
  else
    note "installing video-claw via pipx..."
  fi
  pipx install --force "$PIPX_TARGET"
}

# ---------------------------------------------------------------------------
# Interactive vs piped
# ---------------------------------------------------------------------------

# A `curl | bash` invocation has stdin connected to the script body, so
# `[ -t 0 ]` is false even though the user is sitting at a real terminal.
# Detection: if /dev/tty actually behaves like a tty (can be opened for read AND
# is a terminal device) we treat this as interactive. A bare `-r /dev/tty` test
# isn't enough — the device node may exist without a real terminal behind it
# (e.g. inside CI sandboxes), and a later read will fail with "Device not configured".
is_interactive() {
  if [ -t 0 ] && [ -t 1 ]; then
    return 0
  fi
  # Open /dev/tty as fd 3 and ask `test -t 3` — this is the real check.
  if { exec 3</dev/tty; } 2>/dev/null; then
    if [ -t 3 ]; then
      exec 3<&-
      return 0
    fi
    exec 3<&-
  fi
  return 1
}

prompt_yes_no() {
  local question="$1"
  if ! is_interactive; then
    return 1
  fi
  local choice=""
  if [ -t 0 ]; then
    printf 'install: %s [y/N] ' "$question"
    read -r choice
  else
    printf 'install: %s [y/N] ' "$question" > /dev/tty
    read -r choice < /dev/tty
  fi
  case "$choice" in
    [yY]|[yY][eE][sS]) return 0 ;;
    *) return 1 ;;
  esac
}

run_setup_wizard() {
  if ! is_interactive; then
    note "non-interactive shell detected; skipping the key wizard."
    note "Run \`video-claw setup\` in your terminal to configure keys."
    return 0
  fi
  note "launching interactive key wizard (video-claw setup)..."
  # If stdin isn't already a TTY (we're inside `curl | bash`), rewire stdin
  # from /dev/tty so input() in the wizard reads the user, not the script.
  if [ -t 0 ]; then
    video-claw setup || true
  else
    video-claw setup < /dev/tty || true
  fi
}

# ---------------------------------------------------------------------------
# Banner
# ---------------------------------------------------------------------------

success_banner() {
  cat <<EOF

video-claw is installed.

Next steps:
  1. video-claw setup            # configure keys (rerun anytime)
  2. video-claw init my-vid      # scaffold a project
  3. cd my-vid && video-claw render

Or, if you use Claude Code:
  video-claw install-skill       # ship the skill into ~/.claude/skills/
  Then say in any session: "make me a 30-second video about X".

Docs: ${REPO_URL}
EOF
}

# ---------------------------------------------------------------------------
# main
# ---------------------------------------------------------------------------

main() {
  # `channel` is internal telemetry — only useful when an outer wrapper sets
  # VIDEO_CLAW_FROM=readme / =skill / etc. so we can grep installs by source.
  # Stay quiet for everyone else; "channel: unknown" alarmed users on 0.3.0.
  if [ -n "${VIDEO_CLAW_FROM:-}" ]; then
    note "channel: ${VIDEO_CLAW_FROM}"
  fi
  require_python3
  require_pipx
  require_chrome

  do_install

  # PATH check: pipx default install location is ~/.local/bin
  if ! command -v video-claw >/dev/null 2>&1; then
    err "video-claw installed but not on PATH."
    err "  Run 'pipx ensurepath' and open a new terminal, then run 'video-claw setup'."
    exit 1
  fi

  run_setup_wizard
  success_banner
}

if [ "${BASH_SOURCE[0]:-$0}" = "${0}" ]; then
  main "$@"
fi
