# Open Babel Optimizer for MoleditPy

[![CI](https://github.com/HiroYokoyama/moleditpy_openbabel_optimizer/actions/workflows/test.yml/badge.svg)](https://github.com/HiroYokoyama/moleditpy_openbabel_optimizer/actions/workflows/test.yml)
[![GitHub tag](https://img.shields.io/github/v/tag/HiroYokoyama/moleditpy_openbabel_optimizer?label=version)](https://github.com/HiroYokoyama/moleditpy_openbabel_optimizer/tags)
[![GitHub Downloads](https://img.shields.io/github/downloads/HiroYokoyama/moleditpy_openbabel_optimizer/total)](https://github.com/HiroYokoyama/moleditpy_openbabel_optimizer/releases)
[![License: GPL v2 or later](https://img.shields.io/badge/License-GPLv2%2B-blue.svg)](LICENSE)

An optional **MoleditPy 5 / PySide6** plugin for MMFF94s, MMFF94, UFF, GAFF and
Ghemical geometry optimization. It optimizes an existing 3D structure; ordinary
conversion and Direct mode belong to the editor and do not need this plugin.

Open Babel is loaded only by a separate Python process. The editor process never
imports its native libraries. Cancellation terminates the child; errors and invalid
results leave the molecule unchanged. The plugin does not add or remove atoms.
Force fields still require suitable parameters for the molecule being optimized.

## Install

Use Python 3.10–3.14. In the interpreter that will run the engine:

```sh
python -m pip install "openbabel>=3.2.1,<3.3"
```

Copy the `openbabel_optimizer/` directory into `~/.moleditpy/plugins/`
(`%USERPROFILE%\.moleditpy\plugins\` on Windows), then restart MoleditPy.
Alternatively install the packaged plugin ZIP with the editor's Plugin Manager.

The five methods appear in the **Optimize 3D** menu. Configuration is under
**Settings → Open Babel Optimizer**. Set the maximum iteration count and, if
needed, the absolute path to a Python executable containing Open Babel.

For a pip-installed editor, the current interpreter is the default. For a frozen
Windows/macOS editor, select a **separate Python installation**. The MoleditPy
executable is not a general Python interpreter. You may also set the environment
variable `MOLEDITPY_OPENBABEL_PYTHON` to the full interpreter path. No Open Babel
library is added to the main application's frozen bundle.

When upgrading an old environment, uninstall `openbabel-wheel` before installing
official `openbabel`; those distributions share the same import namespace.

## License

The first-party plugin runtime is **GPL-2.0-or-later** starting with 1.0.1.
The standalone Open Babel worker can be conveyed under GPLv2; the GUI can use
GPLv3 with PySide6. Open Babel retains its own GPL-2.0-only terms.
See [LICENSING.md](LICENSING.md) for scope, process boundaries and distribution
requirements. Earlier releases keep their original grants.

## Development

```sh
python -m pip install -e ".[engine,test]"
QT_QPA_PLATFORM=offscreen PYTEST_QT_API=pyside6 python -m pytest
```

For plugin-manager distribution, zip `openbabel_optimizer/` together with the
LICENSE, LICENSING.md and this README. Keep the package folder at the top level of the archive.

