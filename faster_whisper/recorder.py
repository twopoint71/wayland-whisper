import argparse
import json
import os
import shlex
import signal
import subprocess
import sys
import time

from pathlib import Path

from faster_whisper import WhisperModel


DEFAULT_MODEL = "base"
DEFAULT_RECORD_CMD = "pw-record --rate 16000 --channels 1 --format s16"
DEFAULT_CLIPBOARD_CMD = "wl-copy"
DEFAULT_TYPE_CMD = "wtype -"
DEFAULT_PASTE_CMD = "wtype -M ctrl v"


def _xdg_dir(env_var, fallback_suffix):
    base = os.environ.get(env_var)
    if base:
        return Path(base)
    return Path.home() / fallback_suffix


def _cache_dir():
    return _xdg_dir("XDG_CACHE_HOME", ".cache") / "wayland-whisper"


def _config_dir():
    return _xdg_dir("XDG_CONFIG_HOME", ".config") / "wayland-whisper"


def _state_path():
    return _cache_dir() / "recording.json"


def _default_audio_path():
    return _cache_dir() / "recording.wav"


def _last_text_path():
    return _cache_dir() / "last.txt"


def _load_state():
    try:
        with _state_path().open("r", encoding="utf-8") as handle:
            return json.load(handle)
    except FileNotFoundError:
        return {}
    except json.JSONDecodeError:
        return {}


def _save_state(state):
    _cache_dir().mkdir(parents=True, exist_ok=True)
    with _state_path().open("w", encoding="utf-8") as handle:
        json.dump(state, handle)


def _is_alive(pid):
    if not pid:
        return False
    try:
        os.kill(pid, 0)
    except OSError:
        return False
    return True


def _parse_command(command, output_path):
    cmd_parts = shlex.split(command)
    if any("{output}" in part for part in cmd_parts):
        return [part.format(output=str(output_path)) for part in cmd_parts]
    return cmd_parts + [str(output_path)]


def _start_recording(args):
    state = _load_state()
    if state.get("recording") and _is_alive(state.get("pid")):
        print("Recording already active.", file=sys.stderr)
        return 0

    audio_path = Path(args.audio_path) if args.audio_path else _default_audio_path()
    audio_path.parent.mkdir(parents=True, exist_ok=True)
    if audio_path.exists():
        audio_path.unlink()

    record_cmd = (
        args.record_cmd
        or os.environ.get("FW_RECORD_CMD")
        or DEFAULT_RECORD_CMD
    )
    cmd = _parse_command(record_cmd, audio_path)

    process = subprocess.Popen(
        cmd,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        start_new_session=True,
    )

    state = {
        "recording": True,
        "pid": process.pid,
        "pgid": os.getpgid(process.pid),
        "audio_path": str(audio_path),
        "started_at": time.time(),
    }
    _save_state(state)
    return 0


def _stop_process(pid, pgid):
    if not pid:
        return
    target = pgid if pgid else pid
    try:
        if pgid:
            os.killpg(target, signal.SIGTERM)
        else:
            os.kill(target, signal.SIGTERM)
    except OSError:
        return

    for _ in range(30):
        if not _is_alive(pid):
            return
        time.sleep(0.1)

    try:
        if pgid:
            os.killpg(target, signal.SIGKILL)
        else:
            os.kill(target, signal.SIGKILL)
    except OSError:
        pass


def _run_command(command, text):
    cmd_parts = shlex.split(command)
    if any("{text}" in part for part in cmd_parts):
        cmd_parts = [part.format(text=text) for part in cmd_parts]
        return subprocess.run(cmd_parts, check=False)
    return subprocess.run(cmd_parts, input=text.encode("utf-8"), check=False)


def _transcribe(args, audio_path):
    model_name = args.model or os.environ.get("FW_MODEL") or DEFAULT_MODEL
    device = args.device or os.environ.get("FW_DEVICE") or "auto"
    compute_type = args.compute_type or os.environ.get("FW_COMPUTE_TYPE") or "default"
    language = args.language or os.environ.get("FW_LANGUAGE")
    task = args.task or os.environ.get("FW_TASK") or "transcribe"

    def run_transcribe(target_device):
        model = WhisperModel(
            model_name, device=target_device, compute_type=compute_type
        )
        segments, _info = model.transcribe(
            str(audio_path),
            language=language,
            task=task,
            log_progress=False,
        )
        return "".join(segment.text for segment in segments).strip()

    try:
        return run_transcribe(device)
    except RuntimeError as exc:
        if device == "auto" and (
            "cublas" in str(exc).lower() or "cuda" in str(exc).lower()
        ):
            return run_transcribe("cpu")
        raise


def _output_text(args, text):
    if not text:
        return

    output_mode = args.output or os.environ.get("FW_OUTPUT") or "clipboard"
    if output_mode in ("clipboard", "both", "paste"):
        clipboard_cmd = (
            args.clipboard_cmd
            or os.environ.get("FW_CLIPBOARD_CMD")
            or DEFAULT_CLIPBOARD_CMD
        )
        _run_command(clipboard_cmd, text)

    if output_mode in ("type", "both"):
        type_cmd = (
            args.type_cmd
            or os.environ.get("FW_TYPE_CMD")
            or DEFAULT_TYPE_CMD
        )
        _run_command(type_cmd, text)

    if output_mode in ("paste",):
        paste_cmd = (
            args.paste_cmd
            or os.environ.get("FW_PASTE_CMD")
            or DEFAULT_PASTE_CMD
        )
        subprocess.run(shlex.split(paste_cmd), check=False)


def _stop_recording(args):
    state = _load_state()
    if not state.get("recording"):
        print("Recording not active.", file=sys.stderr)
        return 1

    pid = state.get("pid")
    pgid = state.get("pgid")
    audio_path = Path(state.get("audio_path") or _default_audio_path())

    _stop_process(pid, pgid)
    state["recording"] = False
    state["stopped_at"] = time.time()
    _save_state(state)

    if not audio_path.exists():
        print("No recording found to transcribe.", file=sys.stderr)
        return 1

    text = _transcribe(args, audio_path)
    _cache_dir().mkdir(parents=True, exist_ok=True)
    with _last_text_path().open("w", encoding="utf-8") as handle:
        handle.write(text)

    _output_text(args, text)
    return 0


def _toggle(args):
    state = _load_state()
    if state.get("recording") and _is_alive(state.get("pid")):
        return _stop_recording(args)
    return _start_recording(args)


def _status(_args):
    state = _load_state()
    recording = state.get("recording") and _is_alive(state.get("pid"))
    print("recording" if recording else "idle")
    return 0


def _build_parser():
    parser = argparse.ArgumentParser(
        description="Record audio and transcribe with wayland-whisper."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    def add_common(cmd):
        cmd.add_argument("--model", help="Model name or path.")
        cmd.add_argument("--device", help="Device override, e.g. cpu/cuda/auto.")
        cmd.add_argument("--compute-type", help="CTranslate2 compute type.")
        cmd.add_argument("--language", help="Language code override.")
        cmd.add_argument("--task", help="transcribe or translate.")
        cmd.add_argument(
            "--output",
            choices=["clipboard", "type", "paste", "both"],
            help="Where to send the transcript.",
        )
        cmd.add_argument(
            "--clipboard-cmd",
            help="Command for clipboard copy (reads stdin unless {text} is used).",
        )
        cmd.add_argument(
            "--type-cmd",
            help="Command to type into focused app (reads stdin unless {text} is used).",
        )
        cmd.add_argument(
            "--paste-cmd",
            help="Command to paste into focused app (no stdin; default sends Ctrl+V).",
        )

    start = subparsers.add_parser("start", help="Start recording.")
    start.add_argument(
        "--record-cmd",
        help="Recorder command, supports {output} placeholder.",
    )
    start.add_argument(
        "--audio-path",
        help="Path to store the recording.",
    )
    add_common(start)
    start.set_defaults(func=_start_recording)

    stop = subparsers.add_parser("stop", help="Stop recording and transcribe.")
    add_common(stop)
    stop.set_defaults(func=_stop_recording)

    toggle = subparsers.add_parser("toggle", help="Toggle recording on/off.")
    toggle.add_argument(
        "--record-cmd",
        help="Recorder command, supports {output} placeholder.",
    )
    toggle.add_argument(
        "--audio-path",
        help="Path to store the recording.",
    )
    add_common(toggle)
    toggle.set_defaults(func=_toggle)

    status = subparsers.add_parser("status", help="Show recording status.")
    status.set_defaults(func=_status)

    return parser


def main(argv=None):
    parser = _build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
