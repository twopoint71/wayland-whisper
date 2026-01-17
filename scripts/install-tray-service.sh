#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." >/dev/null 2>&1 && pwd)"
SERVICE_DIR="${HOME}/.config/systemd/user"
SERVICE_FILE="${SERVICE_DIR}/wayland-whisper-tray.service"

mkdir -p "${SERVICE_DIR}"

cat > "${SERVICE_FILE}" <<EOF
[Unit]
Description=Wayland Whisper tray indicator
After=graphical-session.target

[Service]
Type=simple
ExecStart=${ROOT_DIR}/scripts/wayland_whisper_tray_wrapper.sh
Restart=on-failure

[Install]
WantedBy=default.target
EOF

systemctl --user daemon-reload
systemctl --user enable --now wayland-whisper-tray.service

echo "Installed and started user service: wayland-whisper-tray.service"
