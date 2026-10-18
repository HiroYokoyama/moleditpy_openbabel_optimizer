"""Run native optimization separately, keeping failures out of the GUI process."""

import ctypes
import json
import math
import os
from pathlib import Path
import subprocess
import sys
import threading
import time
from typing import Any


class OptimizationCancelled(Exception):
    """Raised after a cancelled optimization child has been terminated."""


def python_executable(configured: str = "") -> str:
    """A frozen editor needs a separately installed Python for this plugin."""
    chosen = configured.strip() or os.environ.get("MOLEDITPY_OPENBABEL_PYTHON", "")
    if not chosen:
        if getattr(sys, "frozen", False):
            raise RuntimeError(
                "Select a standalone Python executable in Settings > Open Babel Optimizer. "
                "Install Open Babel there with: python -m pip install 'openbabel>=3.2.1,<3.3'"
            )
        chosen = sys.executable
    executable = Path(chosen).expanduser().resolve()
    if not executable.is_file():
        raise ValueError(f"Python executable does not exist: {executable}")
    if getattr(sys, "frozen", False) and executable == Path(sys.executable).resolve():
        raise ValueError(
            "Choose standalone Python, rather than the MoleditPy executable."
        )
    return str(executable)


def _child_environment() -> dict[str, str]:
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"
    if not getattr(sys, "frozen", False):
        return env
    if "LD_LIBRARY_PATH_ORIG" in env:
        env["LD_LIBRARY_PATH"] = env["LD_LIBRARY_PATH_ORIG"]
    else:
        env.pop("LD_LIBRARY_PATH", None)
    bundle = str(getattr(sys, "_MEIPASS", ""))
    if bundle:
        for key in ("PATH", "DYLD_LIBRARY_PATH"):
            if key in env:
                env[key] = os.pathsep.join(
                    part
                    for part in env[key].split(os.pathsep)
                    if part
                    and not Path(part).resolve().is_relative_to(Path(bundle).resolve())
                )
    env.pop("PYTHONHOME", None)
    env.pop("PYTHONPATH", None)
    return env


def _spawn(command: list[str], env: dict[str, str]) -> subprocess.Popen[str]:
    kwargs: dict[str, Any] = {
        "stdin": subprocess.PIPE,
        "stdout": subprocess.PIPE,
        "stderr": subprocess.PIPE,
        "text": True,
        "encoding": "utf-8",
        "env": env,
    }
    if sys.platform == "win32":
        kwargs["creationflags"] = subprocess.CREATE_NO_WINDOW
    if sys.platform == "win32" and getattr(sys, "frozen", False):
        # PyInstaller's DLL directory propagates to external processes. Restore
        # it immediately after spawning, so the editor keeps its own libraries.
        kernel32 = ctypes.windll.kernel32
        original = ctypes.create_unicode_buffer(32768)
        kernel32.GetDllDirectoryW(len(original), original)
        kernel32.SetDllDirectoryW(None)
        try:
            return subprocess.Popen(command, **kwargs)
        finally:
            kernel32.SetDllDirectoryW(original.value or None)
    return subprocess.Popen(command, **kwargs)


def validate_coordinates(value: Any, atom_count: int) -> list[list[float]]:
    """Validate every coordinate before any atom in the editor is changed."""
    if not isinstance(value, list) or len(value) != atom_count:
        raise ValueError("Open Babel returned an unexpected atom count.")
    coordinates = []
    for point in value:
        if not isinstance(point, list) or len(point) != 3:
            raise ValueError("Open Babel returned an invalid coordinate.")
        if any(
            type(number) not in (int, float) or not math.isfinite(number)
            for number in point
        ):
            raise ValueError("Open Babel returned a non-finite coordinate.")
        coordinates.append([float(number) for number in point])
    return coordinates


def optimize(
    mol_block: str,
    atom_count: int,
    method: str,
    max_iterations: int = 1000,
    executable: str = "",
    cancelled: threading.Event | None = None,
    timeout: float = 300,
) -> list[list[float]]:
    """Optimize atom positions; cancellation, timeout and native errors reap the child."""
    if cancelled is not None and cancelled.is_set():
        raise OptimizationCancelled()
    command = [
        python_executable(executable),
        str(Path(__file__).with_name("_worker.py")),
    ]
    payload: str | None = json.dumps(
        {"mol_block": mol_block, "method": method, "max_iterations": max_iterations}
    )
    deadline = time.monotonic() + timeout
    with _spawn(command, _child_environment()) as process:
        try:
            while True:
                if cancelled is not None and cancelled.is_set():
                    raise OptimizationCancelled()
                if time.monotonic() >= deadline:
                    raise TimeoutError(
                        "Open Babel optimization exceeded its time limit."
                    )
                try:
                    output, error = process.communicate(input=payload, timeout=0.1)
                    break
                except subprocess.TimeoutExpired:
                    payload = None
            if cancelled is not None and cancelled.is_set():
                raise OptimizationCancelled()
            if process.returncode:
                raise RuntimeError(error.strip() or "The Open Babel worker failed.")
            return validate_coordinates(json.loads(output), atom_count)
        finally:
            if process.poll() is None:
                process.kill()
                process.communicate()
