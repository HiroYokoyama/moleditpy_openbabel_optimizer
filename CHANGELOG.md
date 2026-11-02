# Changelog

## 1.0.1 (2026-11-02)

- Offer first-party runtime code under GPL-2.0-or-later so the standalone
  Open Babel worker can use GPLv2 and the PySide6 GUI can use GPLv3.
- Include GPLv2 text and process-boundary licensing notes in all distribution formats.
- Preserve the original grants for historical releases.

## 1.0.0

- Add optional Open Babel MMFF94s, MMFF94, UFF, GAFF and Ghemical optimizers
  through MoleditPy 5's public plugin API.
- Keep Open Babel native libraries in a separate process, with cancellation,
  timeout handling, and validation before applying coordinates.
- Support an external Python interpreter for frozen editor builds.
- Keep the plugin independently licensed under GPL-3.0-or-later.
