#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" >/dev/null 2>&1 && pwd)"
PROJECT_DIR="${PROJECT_DIR:-$(cd -- "${SCRIPT_DIR}/.." >/dev/null 2>&1 && pwd)}"
VENV_DIR="${VENV_DIR:-${PROJECT_DIR}/.venv}"

cd "${PROJECT_DIR}"
source "${VENV_DIR}/bin/activate"

# Path to nvidia runtimes
CUBLAS_PATH="$(pwd)/.venv/lib/python3.10/site-packages/nvidia/cublas/lib"
CUDNN_PATH="$(pwd)/.venv/lib/python3.10/site-packages/nvidia/cudnn/lib"

# Add cublas if missing
[[ ":$LD_LIBRARY_PATH:" != *":$CUBLAS_PATH:"* ]] && \
    export LD_LIBRARY_PATH="$CUBLAS_PATH${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"

# Add cudnn if missing
[[ ":$LD_LIBRARY_PATH:" != *":$CUDNN_PATH:"* ]] && \
    export LD_LIBRARY_PATH="$CUDNN_PATH${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"


# Defaults (override in this script, env vars, or CLI flags below).
FW_MODEL="${FW_MODEL:-small}"
FW_DEVICE="${FW_DEVICE:-cuda}" # cpu | cuda | auto
FW_COMPUTE_TYPE="${FW_COMPUTE_TYPE:-default}"
FW_LANGUAGE="${FW_LANGUAGE:-}"
FW_TASK="${FW_TASK:-transcribe}" # transcribe | translate
FW_OUTPUT="${FW_OUTPUT:-clipboard}" # clipboard | type | paste | both
FW_RECORD_CMD="${FW_RECORD_CMD:-}"
FW_CLIPBOARD_CMD="${FW_CLIPBOARD_CMD:-}"
FW_TYPE_CMD="${FW_TYPE_CMD:-}"
FW_PASTE_CMD="${FW_PASTE_CMD:-}"
FW_AUDIO_PATH="${FW_AUDIO_PATH:-}"

ARGS=(
  "--model" "${FW_MODEL}"
  "--device" "${FW_DEVICE}"
  "--compute-type" "${FW_COMPUTE_TYPE}"
  "--task" "${FW_TASK}"
  "--output" "${FW_OUTPUT}"
)

if [[ -n "${FW_LANGUAGE}" ]]; then ARGS+=("--language" "${FW_LANGUAGE}"); fi
if [[ -n "${FW_RECORD_CMD}" ]]; then ARGS+=("--record-cmd" "${FW_RECORD_CMD}"); fi
if [[ -n "${FW_AUDIO_PATH}" ]]; then ARGS+=("--audio-path" "${FW_AUDIO_PATH}"); fi
if [[ -n "${FW_CLIPBOARD_CMD}" ]]; then ARGS+=("--clipboard-cmd" "${FW_CLIPBOARD_CMD}"); fi
if [[ -n "${FW_TYPE_CMD}" ]]; then ARGS+=("--type-cmd" "${FW_TYPE_CMD}"); fi
if [[ -n "${FW_PASTE_CMD}" ]]; then ARGS+=("--paste-cmd" "${FW_PASTE_CMD}"); fi

python -m faster_whisper.recorder toggle "${ARGS[@]}" "$@"
