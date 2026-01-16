#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" >/dev/null 2>&1 && pwd)"
PROJECT_DIR="${PROJECT_DIR:-$(cd -- "${SCRIPT_DIR}/.." >/dev/null 2>&1 && pwd)}"
VENV_DIR="${VENV_DIR:-${PROJECT_DIR}/.venv}"

cd "${PROJECT_DIR}"
source "${VENV_DIR}/bin/activate"

python -m faster_whisper.kde_tray
