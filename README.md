# Open Babel Optimizer for MoleditPy

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

This optional plugin is **GPL-3.0-or-later**, independently of the main editor's
LGPL license. Open Babel has its own GPL terms. This does not change the licenses
of unrelated plugins. The main editor does not depend on or distribute this plugin
as part of its core package.

## Development

```sh
python -m pip install -e ".[engine,test]"
QT_QPA_PLATFORM=offscreen PYTEST_QT_API=pyside6 python -m pytest
python -m build
```

For plugin-manager distribution, zip `openbabel_optimizer/` together with the
license and this README. Keep the package folder at the top level of the archive.

## 日本語

MoleditPy 5用の任意プラグインです。既存の3D構造に対し、MMFF94s・MMFF94・UFF・GAFF・
Ghemicalによる最適化を追加します。通常の3D変換とDirectモードにこのプラグインは不要です。

Open Babelは別のPythonプロセス内だけで読み込みます。キャンセル時は子プロセスを終了し、
エラー時は元の座標を維持します。原子の追加・削除は行いません。

Python 3.10〜3.14の環境に上記のコマンドで公式Open Babelをインストールし、
`openbabel_optimizer`フォルダーをMoleditPyのプラグインフォルダーにコピーしてください。
設定は「Settings → Open Babel Optimizer」にあります。

単体配布のWindows/macOS版では、Open Babelを導入した別のPython実行ファイルを指定します。
本体の実行ファイルをPythonとして指定することはできません。本体のバイナリにOpen Babelは
同梱しません。既存の`openbabel-wheel`とは同じ名前空間を使うため、先に削除してください。

このプラグインはGPL v3以降です。本体や、ほかのプラグインのライセンスは変更しません。
