#!/usr/bin/env bash
# install.sh — ExistenZ Installer
# Copies scripts, installs dependencies, wires Claude Code Stop Hook.
#
# Usage:
#   bash install.sh           # Standard install
#   bash install.sh --upgrade # Re-install (overwrite existing)
#   bash install.sh --uninstall

set -euo pipefail

SCRIPTS_DIR="$HOME/.claude/scripts"
SETTINGS_FILE="$HOME/.claude/settings.json"
SCRIPT_NAME="existenz"
READ_SESSION_DEST="/usr/local/bin/read-session"
UPGRADE=false
UNINSTALL=false

# --- Colors ---
RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; BLUE='\033[0;34m'; NC='\033[0m'
info()    { echo -e "${BLUE}[sss]${NC} $*"; }
success() { echo -e "${GREEN}[sss]${NC} $*"; }
warn()    { echo -e "${YELLOW}[sss]${NC} $*"; }
error()   { echo -e "${RED}[sss]${NC} $*" >&2; exit 1; }

for arg in "$@"; do
  case $arg in
    --upgrade)   UPGRADE=true ;;
    --uninstall) UNINSTALL=true ;;
  esac
done

# --- Uninstall ---
if $UNINSTALL; then
  info "Removing sss..."
  rm -f "$SCRIPTS_DIR/$SCRIPT_NAME"
  rm -f "$READ_SESSION_DEST"
  # Remove Stop Hook entry from settings.json
  if command -v python3 &>/dev/null && [ -f "$SETTINGS_FILE" ]; then
    python3 - "$SETTINGS_FILE" <<'EOF'
import json, sys
f = sys.argv[1]
with open(f) as fh:
    d = json.load(fh)
hooks = d.get("hooks", {})
stops = hooks.get("Stop", [])
hooks["Stop"] = [h for h in stops if "sss" not in str(h)]
if not hooks["Stop"]:
    hooks.pop("Stop", None)
d["hooks"] = hooks
with open(f, "w") as fh:
    json.dump(d, fh, indent=2)
print("Hook removed from settings.json")
EOF
  fi
  success "Uninstalled."
  exit 0
fi

# --- Check Python ---
PYTHON=$(command -v python3 || true)
[ -z "$PYTHON" ] && error "python3 not found. Install Python 3.10+."
PY_VERSION=$($PYTHON -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
info "Python $PY_VERSION found."
[[ "$PY_VERSION" < "3.10" ]] && error "Python 3.10+ required (found $PY_VERSION)."

# --- Check Claude Code ---
[ ! -d "$HOME/.claude" ] && error "~/.claude not found. Install Claude Code first: https://claude.ai/code"

# --- Check existing install ---
if [ -f "$SCRIPTS_DIR/$SCRIPT_NAME" ] && ! $UPGRADE; then
  warn "ExistenZ already installed at $SCRIPTS_DIR/$SCRIPT_NAME"
  warn "Run with --upgrade to overwrite."
  exit 0
fi

# --- Install dependencies ---
info "Installing Python dependencies..."
if command -v uv &>/dev/null; then
  info "Using uv (fast)..."
  uv pip install "fastembed>=0.4.0" "numpy>=1.24.0" --system 2>/dev/null || \
  uv pip install "fastembed>=0.4.0" "numpy>=1.24.0"
elif $PYTHON -m pip install --help &>/dev/null 2>&1; then
  $PYTHON -m pip install "fastembed>=0.4.0" "numpy>=1.24.0" --break-system-packages 2>/dev/null || \
  $PYTHON -m pip install "fastembed>=0.4.0" "numpy>=1.24.0"
else
  error "No pip or uv found. Install uv: curl -LsSf https://astral.sh/uv/install.sh | sh"
fi

# --- Copy scripts ---
info "Installing sss to $SCRIPTS_DIR..."
mkdir -p "$SCRIPTS_DIR"
cp "src/sss" "$SCRIPTS_DIR/sss"
chmod +x "$SCRIPTS_DIR/sss"

if [ -f "src/read-session" ]; then
  info "Installing read-session to $READ_SESSION_DEST..."
  if [ -w "/usr/local/bin" ] || sudo -n true 2>/dev/null; then
    sudo cp "src/read-session" "$READ_SESSION_DEST"
    sudo chmod +x "$READ_SESSION_DEST"
  else
    # Fallback: install to ~/.local/bin
    mkdir -p "$HOME/.local/bin"
    cp "src/read-session" "$HOME/.local/bin/read-session"
    chmod +x "$HOME/.local/bin/read-session"
    warn "read-session installed to ~/.local/bin — make sure it's in your PATH."
    warn "Add to ~/.zshrc:  export PATH=\"\$HOME/.local/bin:\$PATH\""
  fi
fi

# --- Add to PATH if needed ---
if ! echo "$PATH" | grep -q "$SCRIPTS_DIR"; then
  warn "$SCRIPTS_DIR not in PATH."
  warn "Add to ~/.zshrc:  export PATH=\"$SCRIPTS_DIR:\$PATH\""
fi

# --- Wire Stop Hook in settings.json ---
if [ ! -f "$SETTINGS_FILE" ]; then
  warn "$SETTINGS_FILE not found — skipping hook setup."
  warn "Create it manually or start Claude Code once to generate it."
else
  info "Wiring Stop Hook in $SETTINGS_FILE..."
  $PYTHON - "$SETTINGS_FILE" "$SCRIPTS_DIR/$SCRIPT_NAME" <<'EOF'
import json, sys
settings_path, sss_path = sys.argv[1], sys.argv[2]

with open(settings_path) as f:
    settings = json.load(f)

hook_cmd = {
    "type": "command",
    "command": f"{sss_path} --index",
    "run_in_background": True
}

hooks = settings.setdefault("hooks", {})
stop_hooks = hooks.setdefault("Stop", [])

# Check if already registered
already = any("sss" in str(h) for h in stop_hooks)
if not already:
    stop_hooks.append(hook_cmd)
    with open(settings_path, "w") as f:
        json.dump(settings, f, indent=2)
    print(f"Stop Hook added: {sss_path} --index")
else:
    print("Stop Hook already registered — skipping.")
EOF
fi

# --- Build initial index ---
echo ""
info "Building initial search index (first run downloads ~33MB embedding model)..."
"$SCRIPTS_DIR/$SCRIPT_NAME" --index

echo ""
success "Installation complete!"
echo ""
echo "  Search your sessions:"
echo "    sss \"your query\"              # Fast BM25 search"
echo "    sss \"your query\" --hybrid     # BM25 + Semantic (best quality)"
echo "    sss --continuation \"project\"  # Resume recent work"
echo "    sss --stats                    # Index statistics"
echo ""
echo "  Multilingual mode (optional, downloads 117MB model):"
echo "    SSS_EMBED_MODEL=intfloat/multilingual-e5-small sss --index --force"
echo ""
echo "  More: https://github.com/YOUR_USERNAME/claude-session-search"
