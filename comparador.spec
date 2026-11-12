# PyInstaller: genera un único ejecutable sin consola.  Uso:  pyinstaller --noconfirm comparador.spec
a = Analysis(
    ["app.py"],
    pathex=["."],
    datas=[("criterios.json", "."), ("relevancia.json", "."), ("catalogos.json", ".")],
    hiddenimports=["core"],
    excludes=["tkinter", "unittest", "pydoc"],
)
pyz = PYZ(a.pure)
exe = EXE(
    pyz, a.scripts, a.binaries, a.datas, [],
    name="Comparador-Linac",
    console=False,
    upx=False,
)
