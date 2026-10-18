"""PySide6 settings and cancellable optimization dialog."""

import logging
import threading
from typing import Any

from PySide6.QtCore import QSettings, QThread, Signal, Slot
from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from .runtime import OptimizationCancelled, optimize, python_executable


def _settings() -> QSettings:
    return QSettings("MoleditPy", "OpenBabelOptimizer")


def configure(parent: QWidget | None) -> None:
    """Choose an external engine interpreter and its iteration budget."""
    settings = _settings()
    dialog = QDialog(parent)
    dialog.setWindowTitle("Open Babel Optimizer Settings")
    layout = QFormLayout(dialog)
    interpreter = QLineEdit(str(settings.value("python", "")), dialog)
    interpreter.setPlaceholderText(
        "Current Python; standalone Python required for frozen builds"
    )
    browse = QPushButton("Browse...", dialog)

    def choose_python() -> None:
        selected, _ = QFileDialog.getOpenFileName(dialog, "Select Python executable")
        if selected:
            interpreter.setText(selected)

    browse.clicked.connect(choose_python)
    row = QHBoxLayout()
    row.addWidget(interpreter)
    row.addWidget(browse)
    layout.addRow("Python", row)
    iterations = QSpinBox(dialog)
    iterations.setRange(1, 100000)
    iterations.setValue(int(settings.value("iterations", 1000)))
    layout.addRow("Maximum iterations", iterations)
    note = QLabel(
        "Install the engine in that Python environment:\n"
        'python -m pip install "openbabel>=3.2.1,<3.3"\n'
        "Open Babel runs separately from the editor.",
        dialog,
    )
    note.setWordWrap(True)
    layout.addRow(note)
    buttons = QDialogButtonBox(
        QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel,
        parent=dialog,
    )

    def save() -> None:
        try:
            python_executable(interpreter.text())
        except (OSError, ValueError, RuntimeError) as error:
            QMessageBox.warning(dialog, "Invalid Python executable", str(error))
            return
        settings.setValue("python", interpreter.text().strip())
        settings.setValue("iterations", iterations.value())
        dialog.accept()

    buttons.accepted.connect(save)
    buttons.rejected.connect(dialog.reject)
    layout.addRow(buttons)
    dialog.exec()


class _EngineThread(QThread):
    coordinates_ready = Signal(object)
    failed = Signal(str)
    cancelled = Signal()

    def __init__(self, request: dict[str, Any], parent: QWidget) -> None:
        super().__init__(parent)
        self.request = request
        self.cancel_event = threading.Event()

    def run(self) -> None:
        try:
            coordinates = optimize(**self.request, cancelled=self.cancel_event)
        except OptimizationCancelled:
            self.cancelled.emit()
        except Exception as error:
            logging.exception("Open Babel optimizer failed")
            self.failed.emit(str(error))
        else:
            self.coordinates_ready.emit(coordinates)


class OptimizationDialog(QDialog):
    """Keep the GUI responsive while a native worker runs in another process."""

    def __init__(
        self, parent: QWidget | None, method: str, request: dict[str, Any]
    ) -> None:
        super().__init__(parent)
        self.setWindowTitle(f"Optimizing with {method} (Open Babel)")
        self.coordinates: list[list[float]] | None = None
        self.error = ""
        self._completed = False
        layout = QVBoxLayout(self)
        self.status = QLabel("Optimizing the current 3D structure...", self)
        layout.addWidget(self.status)
        progress = QProgressBar(self)
        progress.setRange(0, 0)
        layout.addWidget(progress)
        self.buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Cancel, parent=self
        )
        self.buttons.rejected.connect(self.reject)
        layout.addWidget(self.buttons)
        self.thread = _EngineThread(request, self)
        self.thread.coordinates_ready.connect(self._success)
        self.thread.failed.connect(self._failure)
        self.thread.cancelled.connect(self._cancelled)

    @Slot(object)
    def _success(self, coordinates: list[list[float]]) -> None:
        self.coordinates = coordinates
        self._completed = True
        self.accept()

    @Slot(str)
    def _failure(self, error: str) -> None:
        self.error = error
        self._completed = True
        super().reject()

    @Slot()
    def _cancelled(self) -> None:
        self._completed = True
        super().reject()

    def reject(self) -> None:
        if not self._completed:
            self.thread.cancel_event.set()
            self.status.setText("Cancelling...")
            self.buttons.setEnabled(False)
            return
        super().reject()

    def execute(self) -> int:
        self.thread.start()
        try:
            return self.exec()
        finally:
            self.thread.cancel_event.set()
            self.thread.wait()


def optimize_molecule(parent: QWidget | None, molecule: Any, method: str) -> bool:
    """Update the host molecule only after an entire successful optimization."""
    from rdkit import Chem

    if molecule.GetNumConformers() == 0:
        QMessageBox.warning(
            parent, "Open Babel Optimizer", "Create a 3D structure first."
        )
        return False
    settings = _settings()
    try:
        executable = python_executable(str(settings.value("python", "")))
        iterations = int(settings.value("iterations", 1000))
    except (OSError, ValueError, RuntimeError) as error:
        QMessageBox.warning(parent, "Open Babel Optimizer", str(error))
        return False
    request = {
        "mol_block": Chem.MolToMolBlock(molecule),
        "atom_count": molecule.GetNumAtoms(),
        "method": method,
        "max_iterations": iterations,
        "executable": executable,
    }
    dialog = OptimizationDialog(parent, method, request)
    if dialog.execute() != QDialog.DialogCode.Accepted or dialog.coordinates is None:
        if dialog.error:
            QMessageBox.warning(parent, "Open Babel Optimization Failed", dialog.error)
        return False
    conformer = molecule.GetConformer()
    for index, point in enumerate(dialog.coordinates):
        conformer.SetAtomPosition(index, point)
    return True
