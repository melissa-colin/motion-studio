#!/usr/bin/env bash
# Install Motion Studio as a real `motion-studio` command (cross-distro, no apt).
#
# Uses pipx so the app and its dependencies live in their own isolated
# environment while exposing a single command on your PATH. Works on any Linux
# distribution (and macOS) without root.
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
EXTRAS="${MOTION_STUDIO_EXTRAS:-all}"   # core | smpl | video | all

echo ">> Motion Studio installer"

if ! command -v python3 >/dev/null 2>&1; then
  echo "!! python3 is required (>=3.9). Please install it first." >&2
  exit 1
fi

# Ensure pipx is available (user-level, no root).
if ! command -v pipx >/dev/null 2>&1; then
  echo ">> pipx not found; installing it for the current user..."
  python3 -m pip install --user pipx
  python3 -m pipx ensurepath
  export PATH="$HOME/.local/bin:$PATH"
fi

echo ">> Installing motion-studio[$EXTRAS] with pipx..."
pipx install --force "${HERE}[${EXTRAS}]"

# Optional desktop launcher (ignored on headless servers).
APPS_DIR="$HOME/.local/share/applications"
if [ -d "$(dirname "$APPS_DIR")" ]; then
  mkdir -p "$APPS_DIR"
  cat > "$APPS_DIR/motion-studio.desktop" <<DESKTOP
[Desktop Entry]
Type=Application
Name=Motion Studio
Comment=Multi-person SMPL motion editor
Exec=motion-studio
Terminal=true
Categories=Graphics;Science;
DESKTOP
  echo ">> Desktop launcher written to $APPS_DIR/motion-studio.desktop"
fi

echo ""
echo ">> Done. Start it with:"
echo "     motion-studio --smpl-dir ~/smpl/models --workspace ~/MotionStudio"
echo "   then open http://127.0.0.1:8815"
echo "   (set SMPL model path with --smpl-dir; it is not bundled.)"
