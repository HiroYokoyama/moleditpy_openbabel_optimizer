import json
import os
from pathlib import Path
import subprocess
import sys
import threading

import pytest
from rdkit import Chem
from rdkit.Chem import AllChem

import openbabel_optimizer
from openbabel_optimizer import runtime


def ethanol():
    mol = Chem.AddHs(Chem.MolFromSmiles("CCO"))
    assert AllChem.EmbedMolecule(mol, randomSeed=42) == 0
    return mol


def test_registration_loads_neither_qt_nor_babel():
    command = (
        "import sys, openbabel_optimizer as p; "
        "from unittest.mock import Mock; c=Mock(); p.initialize(c); "
        "assert c.register_optimization_method.call_count == 5; "
        "assert c.add_menu_action.call_count == 1; "
        "assert not any(n.startswith(('openbabel.', 'PySide6')) for n in sys.modules)"
    )
    subprocess.run([sys.executable, "-c", command], check=True)


@pytest.mark.parametrize(
    "value",
    [
        None,
        [],
        [[1, 2]],
        [[1, 2, float("nan")]],
        [[1, 2, float("inf")]],
        [[True, 2, 3]],
        [["1", 2, 3]],
    ],
)
def test_invalid_coordinates_rejected(value):
    with pytest.raises(ValueError):
        runtime.validate_coordinates(value, 1)


def test_valid_coordinates():
    assert runtime.validate_coordinates([[1, 2.5, -3]], 1) == [[1.0, 2.5, -3.0]]


def test_frozen_build_requires_external_python(monkeypatch):
    monkeypatch.setattr(sys, "frozen", True, raising=False)
    monkeypatch.delenv("MOLEDITPY_OPENBABEL_PYTHON", raising=False)
    with pytest.raises(RuntimeError, match="standalone Python"):
        runtime.python_executable()
    with pytest.raises(ValueError, match="standalone Python"):
        runtime.python_executable(sys.executable)


def test_configured_python_path(monkeypatch):
    monkeypatch.setenv("MOLEDITPY_OPENBABEL_PYTHON", sys.executable)
    assert runtime.python_executable() == str(Path(sys.executable).resolve())


def test_frozen_child_environment_is_sanitized(monkeypatch, tmp_path):
    bundle = tmp_path / "bundle"
    user = tmp_path / "user"
    monkeypatch.setattr(sys, "frozen", True, raising=False)
    monkeypatch.setattr(sys, "_MEIPASS", str(bundle), raising=False)
    monkeypatch.setenv("LD_LIBRARY_PATH", str(bundle))
    monkeypatch.setenv("LD_LIBRARY_PATH_ORIG", str(user))
    monkeypatch.setenv("PATH", os.pathsep.join([str(bundle / "Qt"), str(user)]))
    monkeypatch.setenv("PYTHONHOME", str(bundle))
    monkeypatch.setenv("PYTHONPATH", str(bundle))
    env = runtime._child_environment()
    assert env["LD_LIBRARY_PATH"] == str(user)
    assert env["PATH"] == str(user)
    assert "PYTHONHOME" not in env and "PYTHONPATH" not in env
    assert os.environ["LD_LIBRARY_PATH"] == str(bundle)


@pytest.mark.parametrize("cancel", [True, False])
def test_cancel_or_timeout_kills_real_child(monkeypatch, cancel):
    children = []

    def spawn(_command, env):
        child = subprocess.Popen(
            [sys.executable, "-c", "import time; time.sleep(60)"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            env=env,
        )
        children.append(child)
        return child

    monkeypatch.setattr(runtime, "_spawn", spawn)
    event = threading.Event()
    timer = threading.Timer(0.15, event.set)
    if cancel:
        timer.start()
    try:
        with pytest.raises(runtime.OptimizationCancelled if cancel else TimeoutError):
            runtime.optimize(
                "", 1, "UFF", cancelled=event, timeout=5 if cancel else 0.05
            )
    finally:
        if cancel:
            timer.cancel()
            timer.join()
    assert len(children) == 1
    assert children[0].poll() is not None


def test_already_cancelled_never_starts_child(monkeypatch):
    event = threading.Event()
    event.set()
    monkeypatch.setattr(runtime, "_spawn", lambda *_: pytest.fail("child was spawned"))
    with pytest.raises(runtime.OptimizationCancelled):
        runtime.optimize("", 1, "UFF", cancelled=event)


@pytest.fixture(scope="module")
def engine_python():
    executable = os.environ.get("OPENBABEL_TEST_PYTHON", sys.executable)
    check = subprocess.run(
        [
            executable,
            "-c",
            "from importlib.metadata import version; assert version('openbabel').startswith('3.2.')",
        ],
        capture_output=True,
        text=True,
    )
    if check.returncode:
        pytest.skip("Official Open Babel 3.2.x is not installed in engine Python")
    return executable


@pytest.mark.parametrize("method", openbabel_optimizer.FORCE_FIELDS)
def test_real_force_field_preserves_atoms_and_parent_isolation(engine_python, method):
    molecule = ethanol()
    original = molecule.GetConformer().GetPositions().copy()
    coordinates = runtime.optimize(
        Chem.MolToMolBlock(molecule),
        molecule.GetNumAtoms(),
        method,
        max_iterations=25,
        executable=engine_python,
    )
    assert len(coordinates) == 9
    assert (molecule.GetConformer().GetPositions() == original).all()
    assert "openbabel._openbabel" not in sys.modules


def test_real_failed_child(engine_python):
    molecule = ethanol()
    with pytest.raises(RuntimeError, match="Unsupported Open Babel force field"):
        runtime.optimize(
            Chem.MolToMolBlock(molecule), 9, "unknown", executable=engine_python
        )


def test_worker_rejects_invalid_iteration_budget(engine_python):
    worker = Path(runtime.__file__).with_name("_worker.py")
    result = subprocess.run(
        [engine_python, str(worker)],
        input=json.dumps({"method": "UFF", "max_iterations": True}),
        capture_output=True,
        text=True,
    )
    assert result.returncode != 0
    assert "max_iterations" in result.stderr
