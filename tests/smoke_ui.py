"""Prueba de humo de app.py SIN Qt: sustituye PySide6 por un doble que acepta todo.
Detecta NameError, atributos mal escritos y errores de lógica en los manejadores; NO valida el aspecto visual."""
import sys, types, itertools
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]; sys.path.insert(0, str(ROOT))

class Meta(type):
    def __getattr__(cls, n): return Any()
class Any(metaclass=Meta):
    def __init__(self, *a, **k): pass
    def __call__(self, *a, **k): return Any()
    def __getattr__(self, n): return Any()
    def __or__(self, o): return self
    __ror__ = __and__ = __rand__ = __add__ = __radd__ = __or__
    def __bool__(self): return False
    def __iter__(self): return iter(())
    def __index__(self): return 0
    def __int__(self): return 0
    def __float__(self): return 0.0
    def __eq__(self, o): return False
    def __hash__(self): return 1
    def connect(self, fn): pass
class Mod(types.ModuleType):
    def __getattr__(self, n):
        if n.startswith("__"): raise AttributeError(n)
        c = Meta(n, (Any,), {}); setattr(self, n, c); return c
pkg = Mod("PySide6"); pkg.__path__ = []
sys.modules["PySide6"] = pkg
for sub in ("QtCore", "QtGui", "QtWidgets"):
    m = Mod("PySide6." + sub); sys.modules["PySide6." + sub] = m; setattr(pkg, sub, m)

import app as A, core as K
class Fake(A.MenuButton):  # MenuButton con estado real
    def __init__(self, prefix, options, multi=False, on_change=None):
        self.prefix, self.multi, self.on_change, self._v = prefix, multi, on_change, [] if multi else ""
    def value(self): return self._v
    def set_value(self, v): self._v = v
    def _clicked(self, a): pass
A.MenuButton = Fake

w = A.Ventana()
assert w.dirty is False
for i, f in enumerate(("Varian_TrueBeam_importar.csv", "Elekta_Infinity_importar.csv")):
    w.set_modelo(i); w.importar_ruta(str(ROOT / "ejemplos" / f))
    assert len(w.prep["ok"]) > 40; w.aplicar_imp(); assert w.dirty
    for cat in K.CATEGORIAS: w.set_cat(cat)
w.ck_req.isChecked = lambda: True; w.set_cat(K.CATEGORIAS[0]); w.ck_req.isChecked = lambda: False
w.set_field("E-028", "valor", "123"); assert w.s["datos"]["B"]["E-028"]["valor"] == "123"
w.ir(2); n_all = len(w.vis); assert n_all == 140, n_all
for crit in ("Todos", "Relevantes al perfil", "Decisivos", "Informativos", "Infraestructura", "Costos"):
    for cat in ["Todas"] + [K.cat_corta(c) for c in K.CATEGORIAS] + ["Infraestructura"]:
        w.m_crit._v, w.m_cat._v = crit, cat; w.refresh_cmp()
for d, f in itertools.product((True, False), repeat=2):
    w.b_dif.isChecked = lambda d=d: d; w.b_fal.isChecked = lambda f=f: f; w.refresh_cmp()
w.b_dif.isChecked = lambda: False; w.b_fal.isChecked = lambda: False; w.m_crit._v = w.m_cat._v = ""; w.refresh_cmp()
w.m_nivel._v, w.m_tec._v, w.m_pac._v = "Básica", ["IMRT"], ">50"; w.perfil_changed()
w.detalle(0, 0); w.detalle(999, 0)
w.rename("A", types.SimpleNamespace(text=lambda: "Varian TrueBeam")); assert w.nm("A") == "Varian TrueBeam"
w.ir(1); w.ir(0)
print("smoke OK:", len(w.vis), "filas")
