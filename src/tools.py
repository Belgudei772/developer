from __future__ import annotations

import os
import shlex
import subprocess
from pathlib import Path

WORKSPACE_ROOT = Path.cwd().resolve()
BLOCKED_COMMANDS = {
    "rm",
    "sudo",
    "shutdown",
    "reboot",
    "halt",
    "mkfs",
    "dd",
}


def _resolve_workspace_path(path_value: str) -> Path:
    raw = Path(path_value)
    candidate = (
        (WORKSPACE_ROOT / raw).resolve() if not raw.is_absolute() else raw.resolve()
    )
    try:
        candidate.relative_to(WORKSPACE_ROOT)
    except ValueError as exc:
        raise ValueError(
            f"Path outside workspace is not allowed: {path_value}"
        ) from exc
    return candidate


def list_files(directory: str = ".") -> str:
    """List all files and directories in the given workspace path."""
    try:
        target = _resolve_workspace_path(directory)
        entries = sorted(os.listdir(target))
        return "\n".join(entries)
    except Exception as e:
        return f"Error: {e}"


def read_file(file_path: str) -> str:
    """Read the content of a file in the workspace."""
    try:
        target = _resolve_workspace_path(file_path)
        return target.read_text(encoding="utf-8")
    except Exception as e:
        return f"Error reading file {file_path}: {e}"


def write_file(file_path: str, content: str) -> str:
    """Write content to a file in the workspace."""
    try:
        target = _resolve_workspace_path(file_path)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")
        return f"Wrote to {target.relative_to(WORKSPACE_ROOT)}"
    except Exception as e:
        return f"Error writing to file {file_path}: {e}"


def run_command(command: str) -> str:
    """Run a shell command safely in the workspace and return output."""
    try:
        if not command.strip():
            return "Error: command is empty"

        if any(token in command for token in ["&&", "||", "|", ";", ">", "<", "$"]):
            return "Error: complex shell operators are not allowed"

        parts = shlex.split(command)
        if not parts:
            return "Error: command is empty"

        if parts[0] in BLOCKED_COMMANDS:
            return f"Error: blocked command '{parts[0]}'"

        result = subprocess.run(
            parts,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=100,
            cwd=str(WORKSPACE_ROOT),
            text=True,
        )
        return result.stdout
    except subprocess.CalledProcessError as e:
        return f"Command '{command}' failed with error: {e.stderr}"
    except Exception as e:
        return f"Error: {e}"
