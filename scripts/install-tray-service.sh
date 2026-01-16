#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." >/dev/null 2>&1 && pwd)"
SERVICE_DIR="${HOME}/.config/systemd/user"
SERVICE_FILE="${SERVICE_DIR}/faster-whisper-tray.service"

mkdir -p "${SERVICE_DIR}"

cat > "${SERVICE_FILE}" <<EOF
[Unit]
Description=Faster Whisper tray indicator
After=graphical-session.target

[Service]
Type=simple
ExecStart=${ROOT_DIR}/scripts/faster_whisper_tray_wrapper.sh
Restart=on-failure

[Install]
WantedBy=default.target
EOF

systemctl --user daemon-reload
systemctl --user enable --now faster-whisper-tray.service

echo "Installed and started user service: faster-whisper-tray.service"
