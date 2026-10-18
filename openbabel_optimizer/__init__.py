"""Optional Open Babel force fields for MoleditPy, GPL-3.0-or-later."""

from functools import partial
from typing import Any

PLUGIN_NAME = "Open Babel Optimizer"
PLUGIN_VERSION = "1.0.0"
PLUGIN_AUTHOR = "HiroYokoyama"
PLUGIN_DESCRIPTION = (
    "Optional MMFF94s, MMFF94, UFF, GAFF and Ghemical optimization in an isolated "
    "Open Babel process. Open Babel is never loaded into the editor process."
)
PLUGIN_CATEGORY = "Optimization"
PLUGIN_TAGS = ["Optimization"]
PLUGIN_SUPPORTED_MOLEDITPY_VERSION = ">=5.0.0,<6"
PLUGIN_DEPENDENCIES = ["openbabel>=3.2.1,<3.3"]

FORCE_FIELDS = ("MMFF94s", "MMFF94", "UFF", "GAFF", "Ghemical")


def _optimize(context: Any, method: str, molecule: Any) -> bool:
    from .gui import optimize_molecule

    return optimize_molecule(context.get_main_window(), molecule, method)


def _settings(context: Any) -> None:
    from .gui import configure

    configure(context.get_main_window())


def initialize(context: Any) -> None:
    """Register optional force fields without importing Open Babel or Qt."""
    for method in FORCE_FIELDS:
        context.register_optimization_method(
            f"{method} (Open Babel)", partial(_optimize, context, method)
        )
    context.add_menu_action(
        "Settings/Open Babel Optimizer...", partial(_settings, context)
    )
