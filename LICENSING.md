# Licensing and process boundary

Copyright (C) 2026 Hiromichi Yokoyama / HiroYokoyama and the contributors
identified in source history and notices.

Starting with **1.0.1**, first-party plugin runtime code is offered under the GNU
General Public License, **version 2 or (at your option) any later version**
(`GPL-2.0-or-later`). See LICENSE. Earlier tags and release assets retain their
original grants; changing current source does not rewrite historical releases.

The unchanged shared maintenance helper `scripts/release_common.py` retains
upstream LGPL-3.0-or-later terms, preserved by `scripts/LICENSE`, `scripts/COPYING`
and `scripts/common-tools.lock.json`. It is not included in the installed runtime
ZIP. Third-party libraries keep their own licenses.

## Why the GPLv2 option matters

The supported `openbabel>=3.2.1,<3.3` engine declares GPL-2.0-only. Open Babel's
documentation applies GPLv2 to Python users of its library. Choose GPLv2 for
the standalone worker when conveying it with that engine. Open Babel itself
does not become GPLv3 because we offer a later-version option on our own code.
Choose GPLv3 for the GUI code used with PySide6 under LGPLv3. The project relies
on the programs' separation, not compatibility between GPL-2.0-only and LGPLv3
inside one program. Installing the engine separately alone is not an exemption.

## Actual boundary

The editor imports `__init__.py`, `gui.py` and `runtime.py`. Open Babel is imported
only by `_worker.py`, launched by filename in a fresh Python interpreter.
That worker imports neither Qt, RDKit nor MoleditPy and can run independently:

```sh
python openbabel_optimizer/_worker.py < request.json
```

The input is JSON with MOL text, a force-field name and an iteration count.
The output is JSON with numeric Cartesian coordinates. The GUI validates the
coordinate count and finite numeric values before applying them. No `OBMol`,
native pointer, Qt object or shared Python object crosses the boundary.
The plugin does not bundle Open Babel, and frozen editors require a standalone
Python interpreter for the worker. Tests cover isolation and real optimization.

These facts support separate-program treatment with a molecular-data interface.
GNU's guidance also considers the semantics of communication: separate processes,
JSON or repositories alone do not establish legal independence. This document
records the project's approach, not a legal ruling or general clearance. Changes
that load Open Babel into the GUI or exchange internal native data require review.

## Distribution

Runtime ZIPs include complete plugin/worker source, LICENSE, this document and
README in the package directory. Keep the source and notices available under their applicable
terms. If you add compiled Open Babel binaries, fulfill the engine's applicable
corresponding-source and other redistribution obligations as well. Do not describe
the combined Open Babel/Qt installation as a single GPLv3 program.

## Sources

- [Open Babel library licensing, including Python](https://openbabel.org/docs/UseTheLibrary/intro.html)
- [Open Babel package metadata](https://pypi.org/pypi/openbabel/3.2.1/json)
- [GNU: GPLv2/GPLv3 compatibility](https://www.gnu.org/licenses/gpl-faq.en.html#v2v3Compatibility)
- [GNU: process boundaries and communication semantics](https://www.gnu.org/licenses/gpl-faq.en.html#MereAggregation)
- [Qt for Python licensing](https://doc.qt.io/qtforpython-6.10/)
