"""Standalone native worker; deliberately imports neither Qt nor RDKit.

Copyright (C) 2026 Hiromichi Yokoyama. SPDX-License-Identifier: GPL-3.0-or-later
"""

import json
import os
from pathlib import Path
import sys
from typing import Any


def _load_pybel() -> Any:
    import openbabel
    from openbabel import pybel

    datadir = os.environ.get("BABEL_DATADIR")
    if not datadir or not (Path(datadir) / "UFF.prm").is_file():
        base = Path(openbabel.__file__).parent
        candidates = [base / "bin" / "data"]
        candidates.extend((base / "share" / "openbabel").glob("*"))
        for candidate in candidates:
            if (candidate / "UFF.prm").is_file():
                os.environ["BABEL_DATADIR"] = str(candidate)
                break
    return pybel


def main() -> None:
    """Read one request and return coordinates, preserving all input atoms."""
    request = json.load(sys.stdin)
    method = request["method"].lower()
    if method not in {"mmff94s", "mmff94", "uff", "gaff", "ghemical"}:
        raise ValueError("Unsupported Open Babel force field.")
    iterations = request["max_iterations"]
    if type(iterations) is not int or not 1 <= iterations <= 100000:
        raise ValueError("max_iterations must be an integer between 1 and 100000.")
    pybel = _load_pybel()
    molecule = pybel.readstring("mol", request["mol_block"])
    forcefield = pybel.ob.OBForceField.FindForceField(method)
    if not forcefield or not forcefield.Setup(molecule.OBMol):
        raise RuntimeError(
            f"Open Babel could not parameterize this molecule with {method}."
        )
    steepest = min(100, iterations)
    forcefield.SteepestDescent(steepest)
    if iterations > steepest:
        forcefield.ConjugateGradients(iterations - steepest)
    forcefield.GetCoordinates(molecule.OBMol)
    coordinates = []
    for index in range(1, molecule.OBMol.NumAtoms() + 1):
        atom = molecule.OBMol.GetAtom(index)
        coordinates.append([atom.GetX(), atom.GetY(), atom.GetZ()])
    json.dump(coordinates, sys.stdout, allow_nan=False)


if __name__ == "__main__":
    main()
