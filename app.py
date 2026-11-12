"""Comparador de aceleradores lineales — interfaz (PySide6). Ejecutar: python app.py"""
import html
import json
import sys
from pathlib import Path

from PySide6.QtCore import Property, QEasingCurve, QPropertyAnimation, QRect, QRectF, QSize, Qt, QUrl, Signal
from PySide6.QtGui import QAction, QBrush, QColor, QDesktopServices, QFont, QKeySequence, QPainter, QPalette, QPen, QTextOption
from PySide6.QtWidgets import (
    QAbstractItemView, QApplication, QButtonGroup, QCheckBox, QComboBox, QDialog, QFileDialog, QFrame,
    QGridLayout, QHBoxLayout, QHeaderView, QLabel, QLineEdit, QMainWindow, QMenu, QMessageBox, QPushButton,
    QScrollArea, QSizePolicy, QSpinBox, QStackedWidget, QStyle, QStyledItemDelegate, QTableWidget, QTableWidgetItem,
    QTextBrowser, QToolButton, QVBoxLayout, QWidget,
)

import core as K

esc = html.escape

# ---- sistema visual ejecutivo ---------------------------------------------------------
INK, MUTED, BG, LINE = "#1a2430", "#56626e", "#f4f5f6", "#d8dde2"
DARK = "#12303b"                     # cabecera y acciones principales
A_C, A_L = "#0e6b73", "#d9ebed"      # modelo A: petróleo
B_C, B_L = "#a45a1a", "#f2e4d3"      # modelo B: siena quemada
GRAY, GRAY_L = "#8a97a3", "#d3dae0"
COST_COLORS = ["#12303b", "#4f7e8c", "#b9ccd3"]
SB_THUMB, SB_TRACK = "#6f7c88", "#d3dae0"   # barras de desplazamiento: asa gris oscuro sobre pista gris claro
SERIF = '"Georgia","Cambria","Times New Roman",serif'

QSS = f"""
QWidget {{ font-family: "Segoe UI Variable Text","Segoe UI","SF Pro Text","Inter","Helvetica Neue",Arial,sans-serif; font-size: 13px; color: {INK}; }}
#page {{ background: {BG}; }}
#masthead {{ background: {DARK}; border: none; }}
QLabel#kicker {{ color: #9fb7c0; font-size: 12px; }}
QLabel#title {{ font-family: {SERIF}; font-size: 21px; color: #ffffff; }}
#band {{ background: #ffffff; border: none; border-bottom: 1px solid {LINE}; }}
QLabel#vsname {{ font-family: {SERIF}; font-size: 24px; }}
#vsrule {{ background: {LINE}; border: none; }}
#card {{ background: #ffffff; border: 1px solid {LINE}; border-radius: 2px; }}
#ledger {{ background: #ffffff; border: none; border-top: 2px solid {INK}; }}
#side {{ background: transparent; border: none; border-right: 1px solid {LINE}; }}
QLabel {{ background: transparent; border: none; }}
QLabel#h1, QLabel#h2 {{ font-family: {SERIF}; font-size: 16px; }}
QLabel#muted {{ color: {MUTED}; font-size: 12px; }}
QPushButton, QToolButton {{ background: #ffffff; border: 1px solid {GRAY}; border-radius: 3px; padding: 7px 14px; }}
QPushButton:hover, QToolButton:hover {{ background: {BG}; }}
QPushButton:focus, QToolButton:focus {{ border: 2px solid {DARK}; padding: 6px 13px; }}
QPushButton:checked {{ background: {DARK}; color: #ffffff; border-color: {DARK}; }}
QPushButton#primary {{ background: {DARK}; color: #ffffff; border-color: {DARK}; }}
QPushButton#ghost {{ background: transparent; color: #ffffff; border: 1px solid #5f7f8b; }}
QPushButton#ghost:hover {{ background: #1d4352; }}
QPushButton#tab {{ background: transparent; color: #b9ccd3; border: none; border-bottom: 3px solid transparent; border-radius: 0; padding: 12px 4px; margin-right: 22px; }}
QPushButton#tab:hover {{ color: #ffffff; background: transparent; }}
QPushButton#tab:checked {{ color: #ffffff; background: transparent; border-bottom: 3px solid #ffffff; }}
QPushButton#cat {{ text-align: left; padding: 10px 14px; border: none; border-left: 3px solid transparent; border-radius: 0; background: transparent; }}
QPushButton#cat:hover {{ background: #e9edf0; }}
QPushButton#cat:checked {{ background: #e3e9ed; color: {INK}; border-left: 3px solid {DARK}; font-weight: 600; }}
QPushButton#small {{ padding: 5px 12px; }}
QToolButton::menu-indicator {{ image: none; width: 0px; }}
QMenu {{ background: #ffffff; border: 1px solid {GRAY}; padding: 4px 0; }}
QMenu::item {{ background: transparent; color: {INK}; padding: 7px 26px 7px 30px; }}
QMenu::item:selected {{ background: #e3e9ed; color: {INK}; }}
QMenu::indicator {{ width: 12px; height: 12px; left: 8px; border: 1px solid {GRAY}; border-radius: 2px; background: #ffffff; }}
QMenu::indicator:checked {{ background: {DARK}; border-color: {DARK}; }}
QLineEdit {{ background: #ffffff; border: 1px solid {GRAY}; border-radius: 3px; padding: 6px 8px; }}
QLineEdit:focus {{ border: 2px solid {DARK}; padding: 5px 7px; }}
QLineEdit[invalid="true"] {{ border-color: #b91c1c; background: #fef2f2; }}
QTableWidget {{ background: #ffffff; border: none; selection-background-color: #eaf0f2; selection-color: {INK}; }}
QHeaderView::section {{ background: #ffffff; border: none; border-bottom: 1px solid {INK}; color: {INK}; font-weight: 600; padding: 9px 10px; }}
QScrollArea {{ background: transparent; border: none; }}
QScrollArea > QWidget > QWidget {{ background: transparent; }}
QScrollBar:vertical {{ background: {SB_TRACK}; width: 10px; margin: 0; border: none; }}
QScrollBar:horizontal {{ background: {SB_TRACK}; height: 10px; margin: 0; border: none; }}
QScrollBar::handle:vertical {{ background: {SB_THUMB}; min-height: 40px; border: none; border-radius: 0; }}
QScrollBar::handle:horizontal {{ background: {SB_THUMB}; min-width: 40px; border: none; border-radius: 0; }}
QScrollBar::handle:vertical:hover, QScrollBar::handle:horizontal:hover, QScrollBar::handle:pressed {{ background: {MUTED}; }}
QScrollBar::add-line, QScrollBar::sub-line {{ width: 0; height: 0; background: none; border: none; }}
QScrollBar::add-page, QScrollBar::sub-page {{ background: none; }}
QAbstractScrollArea::corner {{ background: {SB_TRACK}; border: none; }}
QPushButton#nav {{ min-width: 32px; max-width: 32px; min-height: 32px; max-height: 32px; padding: 0; border: 1px solid {GRAY}; border-radius: 16px; font-size: 20px; background: #ffffff; }}
QPushButton#nav:hover {{ background: {BG}; }}
QPushButton#nav:focus {{ border: 2px solid {DARK}; padding: 0; }}
QPushButton#nav:disabled {{ color: {GRAY_L}; border-color: {GRAY_L}; }}
QPushButton#dot {{ min-width: 10px; max-width: 10px; min-height: 10px; max-height: 10px; padding: 0; border: none; border-radius: 5px; background: {GRAY_L}; }}
QPushButton#dot:hover {{ background: {GRAY}; }}
QPushButton#dot:checked {{ background: {DARK}; border: none; }}
QPushButton#dot:focus {{ border: 2px solid {DARK}; padding: 0; }}
"""

KIND, SUB, BOLD = Qt.UserRole + 1, Qt.UserRole + 2, Qt.UserRole + 3
FILL = {"A": A_L, "B": B_L}
EDGE = {"A": A_C, "B": B_C}


# ---- widgets propios --------------------------------------------------------------------
def card():
    f = QFrame()
    f.setObjectName("card")
    return f


def label(text="", name=None, wrap=False):
    l = QLabel(text)
    if name:
        l.setObjectName(name)
    l.setWordWrap(wrap)
    return l


class MenuButton(QToolButton):
    """Botón con menú desplegable 'Prefijo: valor ▾' (selección simple o múltiple)."""

    def __init__(self, prefix, options, multi=False, on_change=None):
        super().__init__()
        self.prefix, self.multi, self.on_change = prefix, multi, on_change
        self.setPopupMode(QToolButton.InstantPopup)
        self._menu = QMenu(self)
        self.setMenu(self._menu)
        self.acts = []
        for o in options:
            a = QAction(o, self._menu)
            a.setCheckable(True)
            a.triggered.connect(lambda _=False, act=a: self._clicked(act))
            self._menu.addAction(a)
            self.acts.append(a)
        self._refresh()

    def _clicked(self, act):
        if not self.multi:
            for a in self.acts:
                a.setChecked(a is act)
        self._refresh()
        if self.on_change:
            self.on_change()

    def _refresh(self):
        v = self.value()
        txt = ", ".join(v) if self.multi else v
        self.setText(f"{self.prefix}: {txt or '—'} ▾")

    def value(self):
        sel = [a.text() for a in self.acts if a.isChecked()]
        return sel if self.multi else (sel[0] if sel else "")

    def set_value(self, v):
        vs = set(v if self.multi else [v])
        for a in self.acts:
            a.setChecked(a.text() in vs)
        self._refresh()


class Carrusel(QWidget):
    """Láminas en una fila horizontal que se desplazan de a una, como las imágenes de una publicación."""

    cambio = Signal(int)

    def __init__(self):
        super().__init__()
        self.pages, self.idx, self._x = [], 0, 0.0
        self.setMinimumSize(940, 300)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.anim = QPropertyAnimation(self, b"offset", self)
        self.anim.setDuration(300)
        self.anim.setEasingCurve(QEasingCurve.OutCubic)

    def add(self, page):
        page.setParent(self)
        page.show()
        self.pages.append(page)
        self._place() 

    def _get_x(self):
        return self._x

    def _set_x(self, v):
        self._x = v
        self._place()

    offset = Property(float, _get_x, _set_x)

    def _place(self):
        r = self.rect()
        w, h = int(r.width()), int(r.height())
        for i, p in enumerate(self.pages):
            p.setGeometry(round(i * w - self._x), 0, w, h)

    def resizeEvent(self, e):
        self.anim.stop()
        self._x = float(self.idx * self.rect().width())
        self._place()
        super().resizeEvent(e)

    def ir(self, i):
        i = max(0, min(len(self.pages) - 1, i))
        if i != self.idx:
            self.anim.stop()
            self.idx = i
            self.anim.setStartValue(self._x)
            self.anim.setEndValue(float(i * self.rect().width()))
            self.anim.start()
        self.cambio.emit(i)

    def paso(self, d):
        self.ir(self.idx + d)


class ResumenChart(QWidget):
    """Barras apiladas por categoría: A · igual · B · sin dirección · sin dato (rayado)."""

    ROW = 32

    def __init__(self):
        super().__init__()
        self.rows = []

    def set_rows(self, rows):
        self.rows = rows
        self.setMinimumHeight(self.ROW * len(rows) + 6)
        self.update()

    def sizeHint(self):
        return QSize(400, self.ROW * len(self.rows) + 6)

    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        lab, cnt = 190, 190
        bw = max(60, self.width() - lab - cnt - 10)
        for i, (name, tot, a, eq, b, sd, sn) in enumerate(self.rows):
            y = i * self.ROW + 3
            p.setPen(QColor(INK))
            p.drawText(QRect(0, y, lab - 8, self.ROW - 6), Qt.AlignVCenter | Qt.AlignLeft, f"{name} ({tot})")
            p.fillRect(QRectF(lab, y + 2, bw, self.ROW - 10), QColor('#e9edf0'))
            x = float(lab)
            for n, color, hatch in ((a, A_C, False), (eq, GRAY, False), (b, B_C, False), (sn, GRAY_L, False), (sd, None, True)):
                if not n or not tot:
                    continue
                w = bw * n / tot
                r = QRectF(x, y + 2, w, self.ROW - 10)
                if hatch:
                    p.fillRect(r, QColor("#f3f5f7"))
                    p.fillRect(r, QBrush(QColor(GRAY), Qt.BDiagPattern))
                    p.setPen(QPen(QColor(GRAY), 1))
                    p.drawRect(r.adjusted(0.5, 0.5, -0.5, -0.5))
                else:
                    p.fillRect(r, QColor(color))
                x += w
            p.setPen(QColor(MUTED))
            p.drawText(QRect(lab + bw + 10, y, cnt, self.ROW - 6), Qt.AlignVCenter | Qt.AlignLeft, ", ".join(f"{l} {n}" for l, n in (("A", a), ("igual", eq), ("B", b), ("sin dato", sd)) if n))


class CostChart(QWidget):
    """Costo lado a lado: compra / obra civil y blindaje / servicio en la vida útil (sin ponderar)."""

    ROW, BAR = 70, 42

    def __init__(self):
        super().__init__()
        self.data, self.names, self.win = None, {"A": "A", "B": "B"}, None
        self.setFixedHeight(self.ROW * 2 + 6)

    def set_data(self, data, names, win):
        self.data, self.names, self.win = data, names, win
        self.update()

    def paintEvent(self, _):
        if not self.data:
            return
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        lab, tot_w = 170, 210
        bw = max(60, self.width() - lab - tot_w - 10)
        mx = max(self.data["A"]["total"], self.data["B"]["total"], 1.0)
        for i, m in enumerate("AB"):
            y = 6 + i * self.ROW
            f = QFont(self.font())
            f.setBold(self.win == m)
            p.setFont(f)
            p.setPen(QColor(INK))
            p.drawText(QRect(0, y, lab - 10, self.BAR + 4), Qt.AlignVCenter | Qt.AlignLeft, self.names[m])
            x = float(lab)
            for seg, color in zip(self.data[m]["segs"], COST_COLORS):
                w = bw * seg / mx
                p.fillRect(QRectF(x, y + 2, w, self.BAR), QColor(color))
                x += w
            if self.win == m:
                p.setPen(QPen(QColor(INK), 2))
                p.setBrush(Qt.NoBrush)
                p.drawRect(QRectF(lab - 1, y + 1, x - lab + 2, self.BAR + 2))
            f.setBold(False)
            p.setFont(f)
            p.setPen(QColor(MUTED))
            txt = f"{K.fmt_num(self.data[m]['total'], 0)} USD" + ("" if self.data[m]["ok"] else " (parcial)")
            p.drawText(QRect(int(x) + 10, y, tot_w + 40, self.BAR + 4), Qt.AlignVCenter | Qt.AlignLeft, txt)


class CmpDelegate(QStyledItemDelegate):
    """Celda favorable = color + borde izquierdo; sin dato = rayado; la primera columna lleva código debajo."""

    def sizeHint(self, opt, idx):
        return QSize(100, 58)

    def paint(self, p, opt, idx):
        r, kind, col = opt.rect, idx.data(KIND), idx.column()
        p.save()
        p.setClipRect(r)
        if opt.state & QStyle.State_Selected:
            p.fillRect(r, QColor("#eaf2f4"))
        if kind in ("A", "B"):
            p.fillRect(r, QColor(FILL[kind]))
            p.fillRect(QRect(r.left(), r.top(), 3, r.height()), QColor(EDGE[kind]))
        elif kind == "hatch":
            p.fillRect(r, QColor("#f3f5f7"))
            p.fillRect(r, QBrush(QColor(GRAY), Qt.BDiagPattern))
        font = QFont(opt.font)
        font.setBold(bool(idx.data(BOLD)))
        p.setFont(font)
        p.setPen(QColor(MUTED if kind == "hatch" else INK))
        topt = QTextOption(Qt.AlignVCenter)
        topt.setWrapMode(QTextOption.WordWrap)
        txt = idx.data(Qt.DisplayRole) or ""
        if col == 0:
            p.drawText(QRectF(r.left() + 12, r.top() + 3, r.width() - 20, r.height() - 22), txt, topt)
            small = QFont(opt.font)
            small.setPointSizeF(max(7.0, (opt.font.pointSizeF() if opt.font.pointSizeF() > 0 else 9.0) - 1.5))
            p.setFont(small)
            p.setPen(QColor(MUTED))
            p.drawText(QRect(r.left() + 12, r.bottom() - 19, r.width() - 20, 16), Qt.AlignVCenter | Qt.AlignLeft, idx.data(SUB) or "")
        else:
            p.drawText(QRectF(r.left() + 12, r.top() + 3, r.width() - 20, r.height() - 6), txt, topt)
        p.setPen(QColor("#e6eaee"))
        p.drawLine(r.bottomLeft(), r.bottomRight())
        p.restore()


# ---- ventana principal ------------------------------------------------------------------
class Ventana(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Comparador de equipos — acelerador lineal")
        self.resize(1360, 880)
        self.s, self.path, self.dirty = K.nuevo_estudio(), None, False
        self.prep, self.prep_m, self.idx_m, self.w_eval, self.vis = None, "A", 0, {}, []
        self.cur_cat = K.CATEGORIAS[0]

        root = QWidget()
        root.setObjectName("page")
        root.setAttribute(Qt.WA_StyledBackground, True)
        self.setCentralWidget(root)
        v = QVBoxLayout(root)
        v.setContentsMargins(0, 0, 0, 0)
        v.setSpacing(0)
        v.addWidget(self.make_topbar())
        self.stack = QStackedWidget()
        v.addWidget(self.stack, 1)
        for pag in (self.pag_modelos(), self.pag_eval(), self.pag_cmp()):
            self.stack.addWidget(pag)
        for key, fn in (("Ctrl+S", self.guardar), ("Ctrl+O", self.abrir)):
            a = QAction(self)
            a.setShortcut(QKeySequence(key))
            a.triggered.connect(fn)
            self.addAction(a)
        for key, d in (("Left", -1), ("Right", 1)):
            a = QAction(self)
            a.setShortcut(QKeySequence(key))
            a.triggered.connect(lambda _=False, d=d: self.car.paso(d) if self.stack.currentIndex() == 2 else None)
            self.addAction(a)
        self.sync_all()
        self.ir(0)

    # ---------- estructura ----------
    def make_topbar(self):
        bar = QFrame()
        bar.setObjectName("masthead")
        h = QHBoxLayout(bar)
        h.setContentsMargins(28, 10, 28, 0)
        h.setSpacing(0)
        tit = QVBoxLayout()
        tit.setSpacing(0)
        tit.setContentsMargins(0, 0, 0, 10)
        tit.addWidget(label("Comparador de aceleradores lineales", "kicker"))
        self.lb_titulo = label("", "title")
        tit.addWidget(self.lb_titulo)
        h.addLayout(tit)
        h.addSpacing(48)
        self.pills = []
        for i, t in enumerate(("1 Modelos", "2 Evaluación", "3 Comparación")):
            b = QPushButton(t)
            b.setObjectName("tab")
            b.setCheckable(True)
            b.setCursor(Qt.PointingHandCursor)
            b.clicked.connect(lambda _=False, i=i: self.ir(i))
            h.addWidget(b, 0, Qt.AlignBottom)
            self.pills.append(b)
        h.addStretch(1)
        self.b_informe = QPushButton("Informe")
        self.b_informe.setObjectName("ghost")
        self.b_informe.clicked.connect(self.informe)
        h.addWidget(self.b_informe, 0, Qt.AlignVCenter)
        return bar

    def ir(self, i):
        self.stack.setCurrentIndex(i)
        for j, b in enumerate(self.pills):
            b.setChecked(j == i)
        self.b_informe.setVisible(i == 2)
        if i == 1:
            self.fill_eval()
        if i == 2:
            self.refresh_cmp()

    def touch(self):
        self.dirty = True

    def mod(self):
        return "AB"[self.idx_m]

    def nm(self, m):
        return self.s["nombres"][m]

    # ---------- 1 · Modelos ----------
    def pag_modelos(self):
        w = QWidget()
        lay = QVBoxLayout(w)
        lay.setContentsMargins(28, 24, 28, 20)
        c = card()
        c.setMinimumWidth(720)
        c.setMaximumWidth(820)
        g = QGridLayout(c)
        g.setContentsMargins(22, 20, 22, 20)
        g.setHorizontalSpacing(16)
        g.setVerticalSpacing(12)
        g.addWidget(label("Datos del estudio", "h2"), 0, 0, 1, 2)
        self.le_titulo, self.le_a, self.le_b = QLineEdit(), QLineEdit(), QLineEdit()
        self.le_titulo.editingFinished.connect(self.set_titulo)
        self.le_a.editingFinished.connect(lambda: self.rename("A", self.le_a))
        self.le_b.editingFinished.connect(lambda: self.rename("B", self.le_b))
        self.sp = QSpinBox()
        self.sp.setRange(1, 30)
        self.sp.valueChanged.connect(self.set_vida)
        for r, (t, wd) in enumerate((("Título del estudio:", self.le_titulo), ("Modelo A (marca y modelo):", self.le_a),
                                     ("Modelo B (marca y modelo):", self.le_b), ("Vida útil para el costo total (años):", self.sp)), 1):
            g.addWidget(label(t), r, 0)
            g.addWidget(wd, r, 1)
        g.setColumnStretch(1, 1)
        bt = QHBoxLayout()
        for t, fn in (("Nuevo estudio", self.btn_nuevo), ("Abrir…", self.abrir), ("Guardar…", self.guardar)):
            b = QPushButton(t)
            b.clicked.connect(fn)
            bt.addWidget(b)
        bt.addStretch(1)
        g.addLayout(bt, 5, 0, 1, 2)
        g.addWidget(label("Defina los dos modelos, evalúe cada uno (valor técnico, fuente y estado, o importe un CSV) y compare. "
                          "Ctrl+S guarda y Ctrl+O abre el estudio (.json).", "muted", True), 6, 0, 1, 2)
        row = QHBoxLayout()
        row.addStretch(1)
        row.addWidget(c, 100)
        row.addStretch(1)
        lay.addStretch(2)   # un poco más de aire abajo que arriba: el centro óptico queda sobre el geométrico
        lay.addLayout(row)
        lay.addStretch(3)
        return w

    def set_titulo(self):
        nuevo = self.le_titulo.text().strip() or "Estudio sin título"
        if nuevo == self.s["titulo"]:  # editingFinished también salta al perder el foco sin cambios
            return
        self.s["titulo"] = nuevo
        self.lb_titulo.setText(nuevo)
        self.touch()

    def set_vida(self, v):
        if v == self.s["vida_util"]:
            return
        self.s["vida_util"] = v
        self.touch()
        if self.stack.currentIndex() == 2:
            self.refresh_cmp()

    def rename(self, m, e):
        nuevo = e.text().strip() or f"Modelo {m}"
        if nuevo == self.s["nombres"][m]:
            return
        self.s["nombres"][m] = nuevo
        self.touch()
        self.sync_nombres()

    def escribir(self, titulo, fn):
        """Ejecuta una escritura de archivo y avisa si falla (p. ej. el archivo está abierto en Excel)."""
        try:
            fn()
            return True
        except OSError as e:
            QMessageBox.warning(self, titulo, f"No se pudo escribir el archivo. ¿Está abierto en otro programa?\n\n{e}")
            return False

    def sync_nombres(self):
        for i, m in enumerate("AB"):
            self.bm[i].setText(self.nm(m))
        self.upd_counts()
        if self.stack.currentIndex() == 2:
            self.refresh_cmp()

    def confirmar(self):
        if not self.dirty:
            return True
        r = QMessageBox.question(self, "Cambios sin guardar", "Hay cambios sin guardar. ¿Continuar y descartarlos?")
        return r == QMessageBox.Yes

    def btn_nuevo(self):
        if self.confirmar():
            self.s, self.path, self.dirty = K.nuevo_estudio(), None, False
            self.sync_all()

    def guardar(self):
        p, _ = QFileDialog.getSaveFileName(self, "Guardar estudio", self.path or "estudio.json", "Estudio (*.json)")
        if p and self.escribir("No se pudo guardar",
                               lambda: Path(p).write_text(json.dumps(self.s, ensure_ascii=False, indent=1), encoding="utf-8")):
            self.path, self.dirty = p, False

    def abrir(self):
        if not self.confirmar():
            return
        p, _ = QFileDialog.getOpenFileName(self, "Abrir estudio", "", "Estudio (*.json)")
        if p:
            self.abrir_ruta(p)

    def abrir_ruta(self, p):
        try:
            s = K.normalizar_estudio(json.loads(Path(p).read_text(encoding="utf-8-sig")))
        except (OSError, ValueError, AttributeError, TypeError, KeyError) as e:
            QMessageBox.warning(self, "No se pudo abrir", f"El archivo no es un estudio válido.\n\n{e}")
            return
        self.s, self.path = s, p
        self.sync_all()
        desc = K.codigos_desconocidos(s)
        if desc:
            QMessageBox.information(self, "Códigos no reconocidos",
                                    f"El estudio tiene {len(desc)} código(s) que no existen en criterios.json y no se mostrarán "
                                    f"(se conservan al guardar):\n\n{', '.join(desc)}")

    def sync_all(self):
        s = self.s
        self.le_titulo.setText(s["titulo"])
        self.le_a.setText(self.nm("A"))
        self.le_b.setText(self.nm("B"))
        self.sp.setValue(s["vida_util"])
        self.lb_titulo.setText(s['titulo'])
        self.m_nivel.set_value(s["perfil"]["nivel"])
        self.m_tec.set_value(s["perfil"]["tecnicas"])
        self.m_pac.set_value(s["perfil"]["pacientes"])
        self.cancelar_imp()
        self.sync_nombres()
        self.fill_eval()
        self.refresh_cmp()
        self.dirty = False  # los setValue/setText de arriba no cuentan como cambios del usuario

    # ---------- 2 · Evaluación ----------
    def pag_eval(self):
        w = QWidget()
        v = QVBoxLayout(w)
        v.setContentsMargins(28, 16, 28, 20)
        v.setSpacing(12)
        h = QHBoxLayout()
        self.bm, grp = [], QButtonGroup(self)
        for i in range(2):
            b = QPushButton()
            b.setCheckable(True)
            b.setChecked(i == 0)
            grp.addButton(b)
            b.clicked.connect(lambda _=False, i=i: self.set_modelo(i))
            h.addWidget(b)
            self.bm.append(b)
        for b, col in zip(self.bm, (A_C, B_C)):
            b.setStyleSheet(f"QPushButton:checked {{ background: {col}; border-color: {col}; }}")
        self.lb_comp = label("", "muted")
        h.addWidget(self.lb_comp)
        h.addSpacing(12)
        self.ck_req = QCheckBox("Solo obligatorios")
        self.ck_req.toggled.connect(self.fill_eval)
        h.addWidget(self.ck_req)
        h.addStretch(1)
        for t, fn in (("Descargar plantilla CSV", self.plantilla), ("Importar CSV", self.importar)):
            b = QPushButton(t)
            b.clicked.connect(fn)
            h.addWidget(b)
        v.addLayout(h)

        self.card_prev = card()
        ph = QHBoxLayout(self.card_prev)
        ph.setContentsMargins(18, 12, 18, 12)
        self.lb_prev = label("")
        ph.addWidget(self.lb_prev, 1)
        b = QPushButton("Cancelar")
        b.clicked.connect(self.cancelar_imp)
        ph.addWidget(b)
        b = QPushButton("Aplicar")
        b.setObjectName("primary")
        b.clicked.connect(self.aplicar_imp)
        ph.addWidget(b)
        self.card_prev.hide()
        v.addWidget(self.card_prev)

        body = QHBoxLayout()
        body.setSpacing(14)
        side = QFrame()
        side.setObjectName("side")
        side.setFixedWidth(230)
        sl = QVBoxLayout(side)
        sl.setContentsMargins(8, 8, 8, 8)
        sc = QScrollArea()
        sc.setWidgetResizable(True)
        inner = QWidget()
        il = QVBoxLayout(inner)
        il.setContentsMargins(4, 4, 4, 4)
        il.setSpacing(8)
        self.cat_btns, cg = {}, QButtonGroup(self)
        for cat in K.CATEGORIAS:
            b = QPushButton()
            b.setObjectName("cat")
            b.setCheckable(True)
            b.setChecked(cat == self.cur_cat)
            cg.addButton(b)
            b.clicked.connect(lambda _=False, cat=cat: self.set_cat(cat))
            il.addWidget(b)
            self.cat_btns[cat] = b
        il.addStretch(1)
        sc.setWidget(inner)
        sl.addWidget(sc)
        body.addWidget(side)

        main = card()
        ml = QVBoxLayout(main)
        ml.setContentsMargins(14, 10, 14, 10)
        ml.addWidget(label("Criterios de la categoría — en negrita los obligatorios.", "muted"))
        self.tb = QTableWidget(0, 5)
        self.tb.setHorizontalHeaderLabels(["Criterio", "Valor técnico", "Fuente", "Estado", "Referencia"])
        hd = self.tb.horizontalHeader()
        hd.setSectionResizeMode(0, QHeaderView.Stretch)
        for j, wd in ((1, 300), (2, 220), (3, 140), (4, 190)):
            hd.setSectionResizeMode(j, QHeaderView.Fixed)
            self.tb.setColumnWidth(j, wd)
        hd.setHighlightSections(False)
        hd.setDefaultAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        self.tb.verticalHeader().hide()
        self.tb.setShowGrid(False)
        self.tb.setSelectionMode(QAbstractItemView.NoSelection)
        self.tb.setFocusPolicy(Qt.NoFocus)
        ml.addWidget(self.tb)
        body.addWidget(main, 1)
        v.addLayout(body, 1)
        return w

    def set_modelo(self, i):
        self.idx_m = i
        self.cancelar_imp()
        self.fill_eval()

    def set_cat(self, cat):
        self.cur_cat = cat
        self.fill_eval()

    def upd_counts(self):
        m = self.mod()
        for cat, b in self.cat_btns.items():
            n, t = K.avance_categoria(self.s, m, cat)
            b.setText(f"{K.cat_corta(cat)}   {n}/{t}")
        n, t = K.completitud(self.s, m)
        self.lb_comp.setText(f"Completitud {self.nm(m)}: {n * 100 // t} %  ({n}/{t} obligatorios)")

    def fill_eval(self):
        m, other = self.mod(), "B" if self.mod() == "A" else "A"
        rows = [c for c in K.CRIT if c["categoria"] == self.cur_cat and (not self.ck_req.isChecked() or c["requerido"] == "Sí")]
        t = self.tb
        t.setRowCount(0)
        t.setRowCount(len(rows))
        self.w_eval = {}
        for r, c in enumerate(rows):
            code = c["codigo"]
            d = self.s["datos"][m].get(code, {})
            rol = {"Componente de costo": "Costo"}.get(c["rol"], c["rol"].split(" ")[0])
            name = f"<b>{esc(c['criterio'])}</b>" if c["requerido"] == "Sí" else esc(c["criterio"])
            lb = QLabel(f"{name}<br><span style='color:{MUTED};font-size:11px'>{code}  {esc(rol)}</span>")
            lb.setWordWrap(True)
            lb.setContentsMargins(10, 4, 10, 4)
            lb.setToolTip(c["criterio"])
            t.setCellWidget(r, 0, lb)
            t.setCellWidget(r, 1, self.make_valor(c, d))
            fe = QLineEdit(d.get("fuente", ""))
            fe.setPlaceholderText("Enlace o documento")
            fe.textEdited.connect(lambda txt, code=code: self.set_field(code, "fuente", txt))
            t.setCellWidget(r, 2, self.wrap(fe))
            cb = QComboBox()
            cb.addItems(K.ESTADOS)
            cb.setCurrentText(d.get("estado") or "No encontrado")
            cb.currentTextChanged.connect(lambda val, code=code: self.set_field(code, "estado", val))
            self.w_eval[code] = {"estado": cb}
            t.setCellWidget(r, 3, self.wrap(cb))
            od = self.s["datos"][other].get(code)
            ref = f"{self.nm(other)}: {K.mostrar_valor(c, od)}" if K.present(od) else "—"
            rl = QLabel(ref)
            rl.setObjectName("muted")
            rl.setWordWrap(True)
            rl.setContentsMargins(8, 0, 8, 0)
            t.setCellWidget(r, 4, rl)
            t.setRowHeight(r, 76 if c["tipo"].startswith("Selección") and code in K.CATALOGOS else 64)
        self.upd_counts()

    @staticmethod
    def wrap(widget):
        box = QWidget()
        h = QHBoxLayout(box)
        h.setContentsMargins(6, 0, 6, 0)
        h.addWidget(widget)
        return box

    def make_valor(self, c, d):
        code, tipo, val = c["codigo"], c["tipo"], str(d.get("valor", ""))
        box = QWidget()
        if tipo == "Sí/No":
            h = QHBoxLayout(box)
            h.setContentsMargins(6, 0, 6, 0)
            bs = []

            def click(i, checked):
                if checked:
                    bs[1 - i].setChecked(False)
                    self.set_field(code, "valor", ("Sí", "No")[i])
                else:
                    self.set_field(code, "valor", "")

            for i, txt in enumerate(("Sí", "No")):
                b = QPushButton(txt)
                b.setCheckable(True)
                b.setChecked(val.strip().lower() in (K.YES if i == 0 else K.NO))
                b.clicked.connect(lambda checked, i=i: click(i, checked))
                h.addWidget(b)
                bs.append(b)
            h.addStretch(1)
            return box
        if tipo.startswith("Selección") and code in K.CATALOGOS:
            g = QGridLayout(box)
            g.setContentsMargins(6, 0, 6, 0)
            g.setVerticalSpacing(2)
            cats, cur = K.CATALOGOS[code], K.partir_items(val)
            lows = {x.lower() for x in cur}
            chks = []
            extra = QLineEdit("|".join(x for x in cur if x.lower() not in {y.lower() for y in cats}))
            extra.setPlaceholderText("otras (separe con |)")

            def push():
                sel = [ch.text() for ch in chks if ch.isChecked()]
                self.set_field(code, "valor", "|".join(sel + K.partir_items(extra.text())))

            for k, o in enumerate(cats):
                ch = QCheckBox(o)
                ch.setChecked(o.lower() in lows)
                ch.toggled.connect(lambda _=False: push())
                g.addWidget(ch, k // 4, k % 4)
                chks.append(ch)
            u = K.unidad_corta(c)
            g.addWidget(label(u, "muted"), 0, 4)
            g.addWidget(extra, (len(cats) - 1) // 4 + 1, 0, 1, 5)
            extra.textEdited.connect(lambda _: push())
            return box
        h = QHBoxLayout(box)
        h.setContentsMargins(6, 0, 6, 0)
        e = QLineEdit(val)
        e.setPlaceholderText(K.unidad_corta(c) or ("separe con |" if tipo.startswith("Selección") else "valor"))
        e.setToolTip(c["unidad"])

        def edited(txt):
            if tipo == "Numérico":
                e.setProperty("invalid", bool(txt.strip()) and K.num(txt) is None)
                e.style().unpolish(e)
                e.style().polish(e)
            self.set_field(code, "valor", txt)

        e.textEdited.connect(edited)
        if tipo == "Numérico" and val.strip() and K.num(val) is None:
            e.setProperty("invalid", True)
        h.addWidget(e)
        return box

    def set_field(self, code, key, val):
        d = self.s["datos"][self.mod()].setdefault(code, {"valor": "", "fuente": "", "estado": "No encontrado", "nota": ""})
        d[key] = val
        if key == "valor" and str(val).strip() and d["estado"] == "No encontrado":
            d["estado"] = "Declarado"
            cb = self.w_eval.get(code, {}).get("estado")
            if cb:
                cb.blockSignals(True)
                cb.setCurrentText("Declarado")
                cb.blockSignals(False)
        self.touch()
        self.upd_counts()

    def plantilla(self):
        p, _ = QFileDialog.getSaveFileName(self, "Plantilla", "plantilla.csv", "CSV (*.csv)")
        if p:
            self.escribir("No se pudo guardar la plantilla", lambda: K.plantilla_csv(p))

    def importar(self):
        p, _ = QFileDialog.getOpenFileName(self, "Importar CSV", "", "CSV (*.csv)")
        if p:
            self.importar_ruta(p)

    def importar_ruta(self, p):
        try:
            self.prep = K.preparar_importacion(Path(p).read_bytes(), self.s["datos"][self.mod()])
        except (OSError, ValueError) as e:
            QMessageBox.warning(self, "No se pudo leer el CSV", str(e))
            return
        self.prep_m = self.mod()
        pr = self.prep
        sep = "&nbsp;&nbsp;&nbsp;"
        self.lb_prev.setText(
            f"<b>Vista previa de importación para {esc(self.nm(self.prep_m))}:</b>{sep}{len(pr['ok'])} reconocidas{sep}"
            f"{len(pr['desc'])} códigos desconocidos{sep}{len(pr['inv'])} valores de tipo inválido{sep}"
            f"{pr['sob']} sobrescriben datos existentes"
        )
        self.lb_prev.setToolTip(
            "Desconocidos: " + (", ".join(pr["desc"]) or "—") + "\nTipo inválido: " + (", ".join(pr["inv"]) or "—")
        )
        self.card_prev.show()

    def cancelar_imp(self):
        self.prep = None
        self.card_prev.hide()

    def aplicar_imp(self):
        if self.prep:
            K.aplicar_importacion(self.s["datos"][self.prep_m], self.prep)
            self.touch()
        self.cancelar_imp()
        self.fill_eval()

    # ---------- 3 · Comparación ----------
    def pag_cmp(self):
        w = QWidget()
        outer = QVBoxLayout(w)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)
        band = QFrame()
        band.setObjectName("band")
        bl = QGridLayout(band)
        bl.setContentsMargins(28, 14, 28, 12)
        bl.setHorizontalSpacing(28)
        bl.setVerticalSpacing(2)
        self.vs = {}
        for col, m, color in ((0, "A", A_C), (2, "B", B_C)):
            nl, ml = label("", "vsname"), label("")
            nl.setStyleSheet(f"color: {color}")
            bl.addWidget(nl, 0, col)
            bl.addWidget(ml, 1, col)
            self.vs[m] = (nl, ml)
        rule = QFrame()
        rule.setObjectName("vsrule")
        rule.setFixedWidth(1)
        bl.addWidget(rule, 0, 1, 2, 1)
        bl.setColumnStretch(0, 1)
        bl.setColumnStretch(2, 1)
        self.lb_hab = QLabel()  # texto compatible; la información se muestra en cada columna
        outer.addWidget(band)
        body = QWidget()
        v = QVBoxLayout(body)
        v.setContentsMargins(28, 16, 28, 14)
        v.setSpacing(10)
        outer.addWidget(body, 1)

        # Tres láminas que se desplazan en horizontal, como las imágenes de una publicación.
        self.car = Carrusel()
        v.addWidget(self.car, 1)

        # 1 · Resumen de diferencias por categoría
        s1 = self.lamina()
        l1 = QVBoxLayout(s1)
        l1.setContentsMargins(24, 18, 24, 16)
        l1.setSpacing(8)
        l1.addWidget(label("Resumen de diferencias por categoría (sin puntajes)", "h2"))
        self.lb_leg = label("")
        l1.addWidget(self.lb_leg)
        self.chart = ResumenChart()
        sc = QScrollArea()
        sc.setWidgetResizable(True)
        sc.setWidget(self.chart)
        l1.addWidget(sc, 1)
        l1.addWidget(label("Orden de lectura: A, igual, B, sin dato. Los criterios descriptivos, sin dirección, no se cuentan como favorables "
                           "(barra gris clara).", "muted", True))
        self.car.add(s1)

        # 2 · Comparación por criterio (con sus filtros, que solo actúan sobre esta tabla)
        s2 = self.lamina()
        l3 = QVBoxLayout(s2)
        l3.setContentsMargins(24, 18, 24, 12)
        l3.setSpacing(10)
        hh = QHBoxLayout()
        hh.addWidget(label("Comparación por criterio", "h2"))
        self.lb_n = label("", "muted")
        hh.addWidget(self.lb_n)
        hh.addStretch(1)
        b = QPushButton("Exportar CSV")
        b.setObjectName("small")
        b.clicked.connect(self.exportar)
        hh.addWidget(b)
        l3.addLayout(hh)
        h = QHBoxLayout()
        h.setSpacing(10)
        h.addWidget(label("Resaltar relevancia:", "muted"))
        self.m_nivel = MenuButton("Nivel", K.NIVELES, False, self.perfil_changed)
        self.m_tec = MenuButton("Técnicas", K.TECNICAS, True, self.perfil_changed)
        self.m_pac = MenuButton("Pacientes/día", K.PACIENTES, False, self.perfil_changed)
        h.addWidget(self.m_nivel)
        h.addWidget(self.m_tec)
        h.addWidget(self.m_pac)
        h.addSpacing(14)
        h.addWidget(label("Mostrar:", "muted"))
        grupos = [K.cat_corta(c) for c in K.CATEGORIAS if any(x["categoria"] == c and x["rol"] != "Habilitante" and not K.es_infra(x) for x in K.CRIT)]
        self.m_cat = MenuButton("Categoría", ["Todas"] + grupos + ["Infraestructura"], False, self.refresh_cmp)
        self.m_crit = MenuButton("Criterios", ["Todos", "Relevantes al perfil", "Decisivos", "Informativos", "Infraestructura", "Costos"], False, self.refresh_cmp)
        self.m_cat.set_value("Todas")
        self.m_crit.set_value("Todos")
        self.b_dif, self.b_fal = QPushButton("Solo diferencias"), QPushButton("Solo faltantes")
        for b in (self.b_dif, self.b_fal):
            b.setCheckable(True)
            b.toggled.connect(self.refresh_cmp)
        for x in (self.m_cat, self.m_crit, self.b_dif, self.b_fal):
            h.addWidget(x)
        h.addStretch(1)
        l3.addLayout(h)
        self.cm = QTableWidget(0, 5)
        hd = self.cm.horizontalHeader()
        hd.setSectionResizeMode(0, QHeaderView.Stretch)
        for j, wd in ((1, 190), (2, 190), (3, 170), (4, 230)):
            hd.setSectionResizeMode(j, QHeaderView.Fixed)
            self.cm.setColumnWidth(j, wd)
        hd.setHighlightSections(False)
        hd.setDefaultAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        self.cm.verticalHeader().hide()
        self.cm.verticalHeader().setDefaultSectionSize(58)
        self.cm.setShowGrid(False)
        self.cm.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.cm.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.cm.setSelectionMode(QAbstractItemView.SingleSelection)
        self.cm.setFocusPolicy(Qt.NoFocus)
        self.cm.setItemDelegate(CmpDelegate(self.cm))
        self.cm.cellClicked.connect(self.detalle)
        l3.addWidget(self.cm, 1)
        l3.addWidget(label("Favorable = celda con color y borde, más el texto de la columna Lectura; dentro de la banda de empate se muestra "
                           "“Igual”. ● = relevante para el perfil. Clic en una fila abre el detalle con fuente y estado. "
                           "Diferencia = Modelo B − Modelo A.", "muted", True))
        self.car.add(s2)

        # 3 · Costo lado a lado
        s3 = self.lamina()
        l2 = QVBoxLayout(s3)
        l2.setContentsMargins(24, 18, 24, 16)
        self.lb_costo_t = label("", "h2")
        l2.addWidget(self.lb_costo_t)
        l2.addStretch(5)
        self.cost = CostChart()
        l2.addWidget(self.cost)
        l2.addSpacing(12)
        l2.addWidget(label("".join(f"<span style='color:{col}'>■</span> {n} &nbsp;&nbsp;" for (n, _), col in zip(K.COSTO_GRUPOS, COST_COLORS)), "muted"))
        l2.addSpacing(6)
        self.lb_menor = label("", wrap=True)
        l2.addWidget(self.lb_menor)
        l2.addStretch(7)
        self.car.add(s3)

        # Navegación: flechas y puntos (también con las teclas ← →)
        nav = QHBoxLayout()
        nav.setSpacing(14)
        nav.addStretch(1)
        self.b_prev, self.b_next = QPushButton("‹"), QPushButton("›")
        for b, tip, d in ((self.b_prev, "Anterior", -1), (self.b_next, "Siguiente", 1)):
            b.setObjectName("nav")
            b.setToolTip(tip)
            b.setAccessibleName(tip)
            b.setFocusPolicy(Qt.TabFocus)
            b.setCursor(Qt.PointingHandCursor)
            b.clicked.connect(lambda _=False, d=d: self.car.paso(d))
        dl = QHBoxLayout()
        dl.setSpacing(9)
        self.dots, dg = [], QButtonGroup(self)
        for i, t in enumerate(("Resumen de diferencias por categoría", "Comparación por criterio", "Costo lado a lado")):
            d = QPushButton()
            d.setObjectName("dot")
            d.setCheckable(True)
            d.setToolTip(t)
            d.setAccessibleName(t)
            d.setFocusPolicy(Qt.TabFocus)
            d.setCursor(Qt.PointingHandCursor)
            d.clicked.connect(lambda _=False, i=i: self.car.ir(i))
            dg.addButton(d)
            dl.addWidget(d)
            self.dots.append(d)
        nav.addWidget(self.b_prev)
        nav.addLayout(dl)
        nav.addWidget(self.b_next)
        nav.addStretch(1)
        v.addLayout(nav)
        self.car.cambio.connect(self.sync_nav)
        self.sync_nav(0)
        return w

    @staticmethod
    def lamina():
        f = QFrame()
        f.setObjectName("ledger")
        return f

    def sync_nav(self, i):
        self.dots[i].setChecked(True)
        self.b_prev.setEnabled(i > 0)
        self.b_next.setEnabled(i < len(self.dots) - 1)

    def perfil_changed(self):
        self.s["perfil"] = {"nivel": self.m_nivel.value() or "Avanzada", "tecnicas": self.m_tec.value(), "pacientes": self.m_pac.value() or K.PACIENTES[0]}
        self.touch()
        self.refresh_cmp()

    def pasa_filtro(self, f, rel):
        c, g = f.c, f.g
        cat, crit = self.m_cat.value() or "Todas", self.m_crit.value() or "Todos"
        if cat != "Todas" and K.grupo(c) != cat:
            return False
        if crit == "Relevantes al perfil" and c["codigo"] not in rel:
            return False
        if crit == "Decisivos" and c["rol"] != "Decisivo":
            return False
        if crit == "Informativos" and not c["rol"].startswith("Informativo"):
            return False
        if crit == "Infraestructura" and not K.es_infra(c):
            return False
        if crit == "Costos" and not K.es_costo(c):
            return False
        if self.b_dif.isChecked() and g not in ("A", "B", "n"):
            return False
        if self.b_fal.isChecked() and g != "?":
            return False
        return True

    def refresh_cmp(self):
        s, nm = self.s, self.s["nombres"]
        rows = K.filas(s)
        rel = K.codigos_relevantes(s["perfil"])
        self.lb_hab.setText(
            "Habilitantes: " + "&nbsp;&nbsp;&nbsp;&nbsp;".join(
                f"<span style='color:{col};font-weight:600'>{esc(nm[m])} {esc(K.texto_habilitantes(s, m))}</span>"
                for m, col in (("A", A_C), ("B", B_C))
            )
        )
        k0 = K.costos(s)
        for m in "AB":
            n, t = K.completitud(s, m)
            self.vs[m][0].setText(esc(nm[m]))
            self.vs[m][1].setText(f"Habilitantes: {esc(K.texto_habilitantes(s, m))}<br>Datos obligatorios: {n * 100 // t} %<br>Costo total: {K.fmt_num(k0[m]['total'], 0)} USD" + ("" if k0[m]["ok"] else " (parcial)"))
        self.lb_leg.setText(
            f"<span style='color:{A_C}'>■</span> <b style='color:{A_C}'>{esc(nm['A'])} más favorable</b> &nbsp; "
            f"<span style='color:{GRAY}'>■</span> Igual &nbsp; "
            f"<span style='color:{B_C}'>■</span> <b style='color:{B_C}'>{esc(nm['B'])} más favorable</b> &nbsp; "
            f"<span style='color:{GRAY}'>▨</span> Sin dato"
        )
        self.chart.set_rows(K.resumen(rows))
        win = K.menor_costo(s)
        self.lb_costo_t.setText(f"Costo lado a lado (sin ponderar, {s['vida_util']} años)")
        self.cost.set_data(K.costos(s), nm, win)
        k = K.costos(s)
        if win:
            self.lb_menor.setText(f"Menor costo total: <b>{esc(nm[win])}</b> (se resalta, no suma a ningún puntaje).")
        elif k["A"]["ok"] and k["B"]["ok"]:
            self.lb_menor.setText("Costo total igual en ambos modelos.")
        else:
            self.lb_menor.setText("Costo parcial: faltan componentes de costo en algún modelo, por eso no se señala el menor.")
        self.cm.setHorizontalHeaderLabels(["Criterio", nm["A"], nm["B"], "Diferencia", "Lectura"])
        self.vis = [f for f in rows if self.pasa_filtro(f, rel)]
        self.lb_n.setText(f"{len(self.vis)} de {len(rows)} criterios")
        t = self.cm
        t.setRowCount(len(self.vis)) 
        for r, f in enumerate(self.vis):
            c = f.c
            fav = f.g in ("A", "B")
            vals = [("● " if c["codigo"] in rel else "") + c["criterio"], K.mostrar_valor(c, f.da), K.mostrar_valor(c, f.db), f.diff, K.lectura(s, f)]
            for j, txt in enumerate(vals):
                it = QTableWidgetItem(txt)
                kind = None
                if j in (1, 2):
                    m = "AB"[j - 1]
                    kind = "hatch" if m in f.falta else (f.g if f.g == m else None)
                it.setData(KIND, kind)
                it.setData(BOLD, (kind in ("A", "B")) or (j == 4 and fav))
                if j == 0:
                    it.setData(SUB, f"{c['codigo']}   {K.cat_corta(c['categoria'])}")
                    it.setToolTip(c["criterio"] + ("\nRelevante para el perfil" if c["codigo"] in rel else ""))
                t.setItem(r, j, it)

    def detalle(self, row, _col):
        if not 0 <= row < len(self.vis):
            return
        f, s = self.vis[row], self.s
        c = f.c
        tol = f"± {K.fmt_num(c['tol_abs'])} {K.unidad_corta(c)}" if c["tol_abs"] is not None else (f"± {c['tol_rel']} %" if c["tol_rel"] else "—")
        parts = [f"<h3>{esc(c['criterio'])}</h3><p style='color:{MUTED}'>{esc(c['codigo'])}, {esc(c['categoria'])}, {esc(c['rol'])}</p>",
                 f"<p><b>Tipo:</b> {esc(c['tipo'])} &nbsp; <b>Dirección:</b> {esc(c['direccion'])} &nbsp; <b>Unidad:</b> {esc(c['unidad'])} &nbsp; "
                 f"<b>Banda de empate:</b> {esc(tol)}</p>",
                 f"<p><b>Lectura:</b> {esc(K.lectura(s, f))} &nbsp; <b>Diferencia (B − A):</b> {esc(f.diff)}</p>",
                 "<table cellpadding='6' style='border-collapse:collapse'><tr><th></th><th align='left'>Valor</th><th align='left'>Fuente</th><th align='left'>Estado</th><th align='left'>Nota</th></tr>"]
        for m, d in (("A", f.da), ("B", f.db)):
            d = d or {}
            parts.append(f"<tr><td><b style='color:{A_C if m == 'A' else B_C}'>{esc(s['nombres'][m])}</b></td><td>{esc(K.mostrar_valor(c, f.da if m == 'A' else f.db))}</td>"
                         f"<td>{esc(d.get('fuente') or '—')}</td><td>{esc(d.get('estado') or 'No encontrado')}</td><td>{esc(d.get('nota') or '—')}</td></tr>")
        parts.append("</table>")
        dlg = QDialog(self)
        dlg.setWindowTitle(f"Detalle — {c['codigo']}")
        dlg.resize(760, 380)
        lay = QVBoxLayout(dlg)
        tb = QTextBrowser()
        tb.setHtml("".join(parts))
        lay.addWidget(tb)
        dlg.exec()

    def exportar(self):
        p, _ = QFileDialog.getSaveFileName(self, "Exportar comparación", "comparacion.csv", "CSV (*.csv)")
        if p:
            self.escribir("No se pudo exportar", lambda: K.exportar_csv(p, self.s))

    def informe(self):
        p, _ = QFileDialog.getSaveFileName(self, "Guardar informe", "informe.html", "Informe HTML (*.html)")
        if p and self.escribir("No se pudo guardar el informe", lambda: Path(p).write_text(K.informe_html(self.s), encoding="utf-8")):
            QDesktopServices.openUrl(QUrl.fromLocalFile(p))

    def closeEvent(self, e):
        if self.confirmar():
            e.accept()
        else:
            e.ignore()


def paleta_clara():
    p = QPalette()
    for rol, col in ((QPalette.Window, BG), (QPalette.WindowText, INK), (QPalette.Base, "#ffffff"), (QPalette.AlternateBase, BG),
                     (QPalette.Text, INK), (QPalette.Button, "#ffffff"), (QPalette.ButtonText, INK), (QPalette.ToolTipBase, "#ffffff"),
                     (QPalette.ToolTipText, INK), (QPalette.PlaceholderText, MUTED), (QPalette.Highlight, DARK),
                     (QPalette.HighlightedText, "#ffffff"), (QPalette.Link, A_C)):
        p.setColor(rol, QColor(col))
    for rol in (QPalette.Text, QPalette.ButtonText, QPalette.WindowText):
        p.setColor(QPalette.Disabled, rol, QColor(GRAY))
    return p


def main():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    try:  # Qt >= 6.8: ignora el modo oscuro del sistema
        app.styleHints().setColorScheme(Qt.ColorScheme.Light)
    except AttributeError:
        pass
    app.setPalette(paleta_clara())  # con Windows en modo oscuro, spinbox, menús y cuadros de texto heredaban fondo oscuro
    app.setStyleSheet(QSS)
    w = Ventana()
    w.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()