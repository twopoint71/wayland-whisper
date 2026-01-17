# AGENTS.md

Notes for working on the Wayland Whisper repo.

## Project summary
- Wayland-friendly wrapper around `faster-whisper` for push-to-talk style dictation.
- Core logic lives in `faster_whisper/recorder.py` (record, transcribe, output).
- Tray indicator lives in `faster_whisper/kde_tray.py` (PyQt6, reads state file).
- Most other files in `faster_whisper/` are upstream faster-whisper library code.

## Entry points and usage
- CLI module: `python -m faster_whisper.recorder <start|stop|toggle|status>`.
- Tray: `python -m faster_whisper.kde_tray`.
- README shows optional console scripts if installed via editable install.

## Wrapper scripts
- `scripts/wayland_whisper_toggle_wrapper.sh`: activates venv and runs the recorder
  with env/CLI overrides (FW_* variables).
- `scripts/wayland_whisper_tray_wrapper.sh`: activates venv and starts tray app.
- `scripts/install-tray-service.sh`: installs a systemd user service for tray.

## Runtime data and state
- Cache dir: `~/.cache/wayland-whisper/`.
- Files:
  - `recording.json`: current state (recording flag, pid, audio path).
  - `recording.wav`: default capture output.
  - `last.txt`: last transcript text.

## Config and defaults
- Defaults in `faster_whisper/recorder.py`:
  - Record: `pw-record --rate 16000 --channels 1 --format s16`
  - Clipboard: `wl-copy`
  - Type: `wtype -`
  - Paste: `wtype -M ctrl v`
- Env var overrides (same as CLI flags):
  `FW_MODEL`, `FW_DEVICE`, `FW_COMPUTE_TYPE`, `FW_LANGUAGE`, `FW_TASK`,
  `FW_OUTPUT`, `FW_RECORD_CMD`, `FW_CLIPBOARD_CMD`, `FW_TYPE_CMD`,
  `FW_PASTE_CMD`, `FW_AUDIO_PATH`.

## Dependencies and assumptions
- PipeWire (`pw-record`) for audio capture.
- Wayland clipboard tool (`wl-copy`).
- `wtype` for simulated typing/paste (requires compositor support for virtual keyboard).
- Optional CUDA 12 runtime for GPU inference; CPU works without CUDA.

## Troubleshooting
- Empty `recording.wav`: check input device/profile and verify `pw-record` works.
- No typing/paste: compositor may not support `virtual-keyboard`; use `FW_OUTPUT=clipboard`.
- Clipboard empty: confirm `wl-copy` is installed and `FW_OUTPUT` includes clipboard.
