import threading

from PySide6.QtWidgets import QDialog
import pytest
from rdkit import Chem
from rdkit.Chem import AllChem

from openbabel_optimizer import gui
from openbabel_optimizer.runtime import OptimizationCancelled


def test_dialog_success_with_real_pyside(qtbot, monkeypatch):
    monkeypatch.setattr(gui, "optimize", lambda **_: [[1.0, 2.0, 3.0]])
    dialog = gui.OptimizationDialog(None, "UFF", {})
    qtbot.addWidget(dialog)
    assert dialog.execute() == QDialog.DialogCode.Accepted
    assert dialog.coordinates == [[1.0, 2.0, 3.0]]
    assert not dialog.thread.isRunning()


def test_dialog_cancel_joins_thread(qtbot, monkeypatch):
    def engine(cancelled, **_):
        assert isinstance(cancelled, threading.Event)
        assert cancelled.wait(5)
        raise OptimizationCancelled()

    monkeypatch.setattr(gui, "optimize", engine)
    dialog = gui.OptimizationDialog(None, "UFF", {})
    qtbot.addWidget(dialog)
    from PySide6.QtCore import QTimer

    QTimer.singleShot(30, dialog.reject)
    assert dialog.execute() == QDialog.DialogCode.Rejected
    assert not dialog.thread.isRunning()
    assert dialog.coordinates is None


@pytest.mark.parametrize("success", [True, False])
def test_host_molecule_changes_only_on_success(qtbot, monkeypatch, success):
    molecule = Chem.AddHs(Chem.MolFromSmiles("C"))
    AllChem.EmbedMolecule(molecule, randomSeed=4)
    original = molecule.GetConformer().GetPositions().copy()
    target = [[float(i), 2.0, 3.0] for i in range(molecule.GetNumAtoms())]

    def engine(**_):
        if not success:
            raise RuntimeError("simulated native failure")
        return target

    monkeypatch.setattr(gui, "optimize", engine)
    monkeypatch.setattr(gui.QMessageBox, "warning", lambda *_: None)

    class Settings:
        @staticmethod
        def value(_name, default):
            return default

    monkeypatch.setattr(gui, "_settings", Settings)
    assert gui.optimize_molecule(None, molecule, "UFF") is success
    if success:
        assert molecule.GetConformer().GetPositions().tolist() == target
    else:
        assert (molecule.GetConformer().GetPositions() == original).all()
