# Wayland Whisper (built on faster-whisper)

This project is a small Wayland-friendly voice input helper built on top of
`faster-whisper` by SYSTRAN. It records from your microphone, transcribes with Whisper,
and sends the result to your clipboard or the currently focused app.

It works on any Wayland compositor; the workflow below includes a KDE Plasma
example because that is the setup used to build and test it.

## Features

- Toggle recording with a single command (start/stop in one shortcut).
- Transcribe locally with faster-whisper.
- Output to clipboard, typed text, or clipboard + paste.
- Status tray indicator.
- Configurable via CLI flags or environment variables.

## Requirements

Python:
- Python 3.9+
- `pip install -r requirements.txt`
- `PyQt6` for the tray app (already in `requirements.txt`)

System tools:
- `pw-record` (PipeWire) for capture
- `wl-copy` for clipboard output
- `wtype` for typing or paste

GPU (optional):
- CUDA 12 runtime libs if you want `--device cuda`
- CPU works without CUDA

## Install

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Usage

Record + transcribe with a single toggle:

```bash
python -m faster_whisper.recorder toggle --device cpu --output clipboard
```

Or use the installed entry points:

```bash
faster-whisper-record toggle --device cpu --output clipboard
faster-whisper-tray
```

Output modes:
- `clipboard` (copy only)
- `type` (type into focused app)
- `paste` (copy + Ctrl+V)
- `both` (copy + type)

Tray indicator:

```bash
python -m faster_whisper.kde_tray
```

## Configuration

All CLI flags have matching env vars:

- `FW_MODEL`
- `FW_DEVICE` (`cpu`, `cuda`, `auto`)
- `FW_COMPUTE_TYPE` (CtrT compute type)
- `FW_LANGUAGE`
- `FW_TASK` (`transcribe`, `translate`)
- `FW_OUTPUT` (`clipboard`, `type`, `paste`, `both`)
- `FW_RECORD_CMD`
- `FW_CLIPBOARD_CMD`
- `FW_TYPE_CMD`
- `FW_PASTE_CMD`

Flag details and examples:

- `--model`: Whisper model name or local path.
  Example: `--model small` or `--model /path/to/whisper-ct2`.
- `--device`: Inference device.
  Example: `--device cpu` or `--device cuda`.
- `--compute-type`: CTranslate2 compute type.
  Example: `--compute-type int8` or `--compute-type float16`.
- `--language`: Force language code; omit for auto-detect.
  Example: `--language en`.
- `--task`: Task mode.
  Example: `--task transcribe` or `--task translate`.
- `--output`: Where the transcript goes.
  Example: `--output clipboard`, `--output paste`.
- `--record-cmd`: Recorder command; supports `{output}` placeholder.
  Example: `--record-cmd 'pw-record --rate 16000 --channels 1 --format s16 {output}'`.
- `--audio-path`: Recording output file.
  Example: `--audio-path /tmp/recording.wav`.
- `--clipboard-cmd`: Clipboard tool; reads stdin unless `{text}` is used.
  Example: `--clipboard-cmd wl-copy`.
- `--type-cmd`: Typing tool; reads stdin unless `{text}` is used.
  Example: `--type-cmd 'wtype -'`.
- `--paste-cmd`: Paste command (no stdin, sends key combo).
  Example: `--paste-cmd 'wtype -M ctrl v'`.

## KDE Plasma shortcut example

Create a small wrapper script and point your global shortcut to it. An example
is included at `scripts/faster_whisper_toggle_wrapper.sh` and can be customized.

In KDE:
- System Settings -> Shortcuts -> Custom Shortcuts -> Add Command
- Command: `/path/to/wayland-whisper/scripts/faster_whisper_toggle_wrapper.sh`

## Tray autostart

The tray icon only appears while the tray app is running. There are two simple
ways to start it on login:

Systemd user service (recommended):

```bash
bash scripts/install-tray-service.sh
```

KDE Autostart:

- System Settings -> Autostart -> Add Script
- Script: `/path/to/wayland-whisper/scripts/faster_whisper_tray_wrapper.sh`

## Wayland notes

- Some apps block simulated typing; if `type` fails, use `paste`.
- `paste` relies on `wtype -M ctrl v` by default; override with `FW_PASTE_CMD`
  if your app needs a different shortcut.

## Troubleshooting

- If you see `libcublas.so.12 not found`, your CUDA runtime is mismatched.
  Install CUDA 12 libs or use `--device cpu`.
- If you get a float16 warning on CPU, it is safe to ignore.

## Project layout

This is built on top of `faster-whisper` and adds a small Wayland helper layer:

- `faster_whisper/recorder.py` (record + transcribe + output)
- `faster_whisper/kde_tray.py` (tray indicator)
- `scripts/` (wrapper scripts and tray service installer)
