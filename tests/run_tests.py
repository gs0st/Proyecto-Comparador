"""Ejecuta las pruebas sin necesitar pytest:  python tests/run_tests.py"""
import subprocess, sys, traceback
from pathlib import Path
here = Path(__file__).resolve().parent
sys.path.insert(0, str(here)); sys.path.insert(0, str(here.parent))
import test_core
fallas = 0
for n in sorted(dir(test_core)):
    if n.startswith("test_"):
        try:
            getattr(test_core, n)(); print("ok  ", n)
        except Exception:
            fallas += 1; print("FALLA", n); traceback.print_exc()
r = subprocess.run([sys.executable, str(here / "smoke_ui.py")])  # proceso aparte: sustituye PySide6 por un doble
sys.exit(1 if fallas or r.returncode else 0)
