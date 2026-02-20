#!/usr/bin/env python3
"""
Expert System — Graphical User Interface
Launch the tkinter-based UI for the expert system.

Usage:
    python3 run_ui.py
"""

import sys
from pathlib import Path

# Ensure the project root is in sys.path
_root = Path(__file__).resolve().parent
if str(_root) not in sys.path:
    sys.path.insert(0, str(_root))

from ui.app import ExpertSystemApp


def main():
    app = ExpertSystemApp()
    app.run()
    return 0


if __name__ == "__main__":
    sys.exit(main())
