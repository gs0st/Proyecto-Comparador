"""Lógica del comparador de aceleradores lineales (sin dependencias de Qt, para poder probarla)."""
import csv
import html
import io
import json
import math
import re
import sys
from collections import OrderedDict, namedtuple
from pathlib import Path


def recurso(nombre):
    """Ruta a un archivo de datos, tanto en desarrollo como dentro del ejecutable (PyInstaller)."""
    base = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent))
    return base / nombre


def _json(nombre):
    return json.loads(recurso(nombre).read_text(encoding="utf-8"))


CRIT = _json("criterios.json")
BY = {c["codigo"]: c for c in CRIT}
RELEVANCIA = _json("relevancia.json")
CATALOGOS = {k: v for k, v in _json("catalogos.json").items() if not k.startswith("_")}

ESTADOS = ["Declarado", "Verificado", "No encontrado"]
YES = {"si", "sí", "s", "yes", "true", "1"}
NO = {"no", "n", "false", "0"}
UMBRAL_DISPONIBILIDAD = 95.0  # C-058, criterio habilitante
MINUS = "\u2212"
NBSP = "\u00a0"

NIVELES = ["Básica", "Intermedia", "Avanzada"]
TECNICAS = list(RELEVANCIA["tecnica"].keys())
PACIENTES = list(RELEVANCIA["pacientes"].keys())

# ---- categorías -------------------------------------------------------------------------
CAT_CORTA = OrderedDict([
    ("Datos generales y regulatorios", "General"),
    ("Cabezal terapéutico y colimación", "Colimación"),
    ("Haz de tratamiento", "Haz"),
    ("Acelerador y microondas", "Acelerador"),
    ("Gantry y colimador", "Gantry y colimador"),
    ("Camilla de tratamiento", "Camilla"),
    ("Imagen y guía", "Imagen y guía"),
    ("Seguridad eléctrica y del paciente", "Seguridad"),
    ("Técnicas y software", "Técnicas y software"),
    ("Datos y ciberseguridad", "Ciberseguridad"),
    ("Dimensiones, peso y ergonomía", "Dimensiones y peso"),
    ("Accesorios", "Accesorios"),
    ("Alcance clínico", "Alcance clínico"),
    ("Experiencia del proveedor", "Experiencia"),
    ("Ambiente y fin de vida", "Fin de vida"),
    ("Mantenimiento y posventa", "Posventa"),
    ("Instalación y logística", "Instalación"),
    ("Costos de adquisición", "Costos"),
    ("Blindaje: materiales y barreras", "Blindaje"),
    ("Estructura y obra civil", "Obra civil"),
    ("Servicios eléctricos", "Servicios eléctricos"),
    ("Refrigeración y climatización (suministro del sitio)", "Climatización"),
    ("Dimensiones y distribución de ambientes (referencia independiente del equipo)", "Ambientes"),
])
CATEGORIAS = [c for c in CAT_CORTA if any(x["categoria"] == c for x in CRIT)]
CATEGORIAS += sorted({x["categoria"] for x in CRIT} - set(CATEGORIAS))


def cat_corta(cat):
    return CAT_CORTA.get(cat, cat)


def es_infra(c):
    return c["rol"].startswith("Infraestructura")


def es_costo(c):
    return c["rol"] == "Componente de costo"


def grupo(c):
    """Grupo para el resumen por categoría: la infraestructura se agrupa en un solo bloque."""
    return "Infraestructura" if es_infra(c) else cat_corta(c["categoria"])


# ---- números y texto --------------------------------------------------------------------
def num(s):
    """Número desde texto con coma o punto decimal y separadores de miles; None si no es número."""
    t = str(s).strip().replace(NBSP, "").replace(" ", "").replace(MINUS, "-")
    if not t:
        return None
    if "," in t and "." in t:
        dec = "," if t.rfind(",") > t.rfind(".") else "."
        mil = "." if dec == "," else ","
        t = t.replace(mil, "").replace(dec, ".")
    elif "," in t:
        t = t.replace(",", ".") if t.count(",") == 1 else t.replace(",", "")
    elif t.count(".") > 1:
        t = t.replace(".", "")
    try:
        v = float(t)
    except ValueError:
        return None
    return v if math.isfinite(v) else None


def fmt_num(v, dec=2):
    """7400 -> '7 400'; 0.6 -> '0,6' (separador de miles = espacio duro)."""
    if v is None:
        return ""
    s = f"{abs(v):,.{dec}f}"
    if "." in s:
        s = s.rstrip("0").rstrip(".")
    s = s.replace(",", NBSP).replace(".", ",")
    return (MINUS if v < 0 and s.strip("0,") else "") + s


def fmt_signed(v, dec=2):
    s = fmt_num(abs(v), dec)
    if not s.strip("0,"):
        return s
    return ("+" if v > 0 else MINUS) + s


def partir_items(s):
    """Elementos de una respuesta de selección múltiple (separados por |, ; o ,), sin repetir."""
    vistos, out = set(), []
    for x in re.split(r"[;,|]", str(s)):
        x = x.strip()
        if x and x.lower() not in vistos:
            vistos.add(x.lower())
            out.append(x)
    return out


def items(s):
    return {x.lower() for x in partir_items(s)}


def unidad_corta(c):
    u = c["unidad"].split(" (")[0].strip()
    return "" if u in ("—", "-") else u


def usa_unidad(c):
    return c["tipo"] in ("Numérico", "Compuesto") or c["tipo"].startswith("Selección")


def present(d):
    return bool(d) and d.get("estado") != "No encontrado" and str(d.get("valor", "")).strip() != ""


def mostrar_valor(c, d):
    """Texto de la celda de un modelo en la comparación."""
    if not present(d):
        return "sin dato"
    raw = str(d["valor"]).strip()
    t = c["tipo"]
    if t == "Numérico" and num(raw) is not None:
        txt = fmt_num(num(raw))
    elif t == "Sí/No":
        txt = "Sí" if raw.lower() in YES else ("No" if raw.lower() in NO else raw)
    elif t.startswith("Selección"):
        txt = ", ".join(partir_items(raw))
    else:
        txt = raw
    u = unidad_corta(c)
    return f"{txt} {u}" if u and usa_unidad(c) else txt


# ---- comparación ------------------------------------------------------------------------
def compare(c, da, db):
    """-> (g, texto). g: 'A' | 'B' (más favorable), '=' igual, '?' sin dato, 'n' sin dirección."""
    if not (present(da) and present(db)):
        return "?", "—"
    a, b = str(da["valor"]).strip(), str(db["valor"]).strip()
    t, dr = c["tipo"], c["direccion"]
    if t == "Numérico":
        x, y = num(a), num(b)
        if x is None or y is None:
            return "n", "valor no numérico"
        d = y - x  # siempre B − A
        tol = c["tol_abs"] if c["tol_abs"] is not None else (c["tol_rel"] or 5) / 100 * max(abs(x), abs(y))
        u = unidad_corta(c)
        u = "pp" if u == "%" else u
        txt = fmt_signed(d) + (f" {u}" if u else "") + (f" ({fmt_signed(d / abs(x) * 100, 0)} %)" if x else "")
        if abs(d) <= tol:
            return "=", txt
        if dr == "Mayor es mejor":
            return ("B" if d > 0 else "A"), txt
        if dr == "Menor es mejor":
            return ("B" if d < 0 else "A"), txt
        return "n", txt
    if t == "Sí/No":
        x, y = a.lower() in YES, b.lower() in YES
        if x == y:
            return "=", "—"
        if dr == "Sí es mejor":
            return ("A" if x else "B"), "Difieren"
        if dr == "No es mejor":
            return ("B" if x else "A"), "Difieren"
        return "n", "Difieren"
    if t.startswith("Selección"):
        sa, sb = items(a), items(b)
        if sa == sb:
            return "=", "—"
        d = len(sb) - len(sa)
        if d == 0 or dr not in ("Más cobertura es mejor",):
            return "n", "Difieren"
        return ("B" if d > 0 else "A"), f"{fmt_signed(d, 0)} elemento{'s' if abs(d) != 1 else ''}"
    return ("=", "—") if a.lower() == b.lower() else ("n", "Difieren")


def cumple(c, d):
    """Habilitantes: True / False / None (sin dato)."""
    if not present(d):
        return None
    if c["tipo"] == "Sí/No":
        return str(d["valor"]).strip().lower() in YES
    v = num(d["valor"])
    return None if v is None else v >= UMBRAL_DISPONIBILIDAD


Fila = namedtuple("Fila", "c da db g diff falta")


def filas(study):
    A, B = study["datos"]["A"], study["datos"]["B"]
    out = []
    for c in CRIT:
        if c["rol"] == "Habilitante":
            continue
        da, db = A.get(c["codigo"]), B.get(c["codigo"])
        g, diff = compare(c, da, db)
        falta = ("A" if not present(da) else "") + ("B" if not present(db) else "")
        out.append(Fila(c, da, db, g, diff, falta))
    return out


def lectura(study, f):
    nm = study["nombres"]
    if f.g in ("A", "B"):
        return f"{nm[f.g]} " + {"Menor exigencia": "menor exigencia"}.get(f.c["lectura"], "más favorable")
    if f.g == "=":
        return "Igual"
    if f.g == "?":
        return "Sin dato en " + " y ".join(nm[m] for m in f.falta)
    return "Sin dirección (descriptivo)"


def habilitantes(study):
    """{'A': (cumple, no_cumple, sin_dato, total), 'B': ...}"""
    hs = [c for c in CRIT if c["rol"] == "Habilitante"]
    out = {}
    for m in "AB":
        r = [cumple(c, study["datos"][m].get(c["codigo"])) for c in hs]
        out[m] = (r.count(True), r.count(False), r.count(None), len(hs))
    return out


def texto_habilitantes(study, m):
    ok, no, sin, tot = habilitantes(study)[m]
    return f"{ok}/{tot} cumple" + (f", {no} no cumple" if no else "") + (f", {sin} sin dato" if sin else "")


def resumen(rows):
    """Por grupo: [grupo, total, A, igual, B, sin_dato, sin_direccion]. Los costos van aparte."""
    out = OrderedDict()
    for f in rows:
        if es_costo(f.c):
            continue
        r = out.setdefault(grupo(f.c), [grupo(f.c), 0, 0, 0, 0, 0, 0])
        r[1] += 1
        r[{"A": 2, "=": 3, "B": 4, "?": 5, "n": 6}[f.g]] += 1
    orden = [cat_corta(c) for c in CATEGORIAS] + ["Infraestructura"]
    return sorted(out.values(), key=lambda r: orden.index(r[0]) if r[0] in orden else 99)


# ---- costos -----------------------------------------------------------------------------
COSTO_GRUPOS = [
    ("Compra", ["C-048", "C-049", "C-050", "C-051", "C-053"]),
    ("Obra civil y blindaje", ["C-052"]),
    ("Servicio en la vida útil", ["C-055"]),  # USD/año × vida útil
]


def costos(study):
    vu = study["vida_util"]
    out = {}
    for m in "AB":
        D, segs, ok = study["datos"][m], [], True
        for _, codes in COSTO_GRUPOS:
            t = 0.0
            for code in codes:
                d = D.get(code)
                v = num(d["valor"]) if present(d) else None
                if v is None:
                    ok = False
                    continue
                t += v * (vu if code == "C-055" else 1)
            segs.append(t)
        out[m] = {"segs": segs, "total": sum(segs), "ok": ok}
    return out


def menor_costo(study):
    k = costos(study)
    if k["A"]["ok"] and k["B"]["ok"] and k["A"]["total"] != k["B"]["total"]:
        return min("AB", key=lambda m: k[m]["total"])
    return None


# ---- perfil y relevancia ----------------------------------------------------------------
def codigos_relevantes(perfil):
    cods = set()
    nivel = perfil.get("nivel", "Avanzada")
    for n in NIVELES[: NIVELES.index(nivel) + 1 if nivel in NIVELES else 0]:
        cods |= set(RELEVANCIA["nivel"].get(n, []))
    for t in perfil.get("tecnicas", []):
        cods |= set(RELEVANCIA["tecnica"].get(t, []))
    cods |= set(RELEVANCIA["pacientes"].get(perfil.get("pacientes", ""), []))
    return cods


# ---- estudio ----------------------------------------------------------------------------
def nuevo_estudio():
    return {
        "titulo": "Linac para servicio de radioterapia",
        "nombres": {"A": "Modelo A", "B": "Modelo B"},
        "vida_util": 10,
        "perfil": {"nivel": "Avanzada", "tecnicas": ["VMAT", "SRS/SBRT"], "pacientes": "25–50"},
        "datos": {"A": {}, "B": {}},
    }


def normalizar_estudio(s):
    """Completa y valida campos (estudios guardados con versiones anteriores o editados a mano).
    Lanza ValueError si el archivo no tiene forma de estudio."""
    if not isinstance(s, dict) or not isinstance(s.get("datos", {}), dict):
        raise ValueError("falta la estructura básica del estudio (titulo, nombres, datos…)")
    n = nuevo_estudio()
    for k, v in n.items():
        if k != "vida_util" and not isinstance(s.get(k), type(v)):
            s[k] = v
    s["titulo"] = str(s["titulo"]).strip() or n["titulo"]
    try:
        s["vida_util"] = min(30, max(1, int(s["vida_util"])))
    except (TypeError, ValueError):
        s["vida_util"] = n["vida_util"]
    for k, v in n["nombres"].items():
        if not isinstance(s["nombres"].get(k), str) or not s["nombres"][k].strip():
            s["nombres"][k] = v
    p = s["perfil"]
    if p.get("nivel") not in NIVELES:
        p["nivel"] = n["perfil"]["nivel"]
    if not isinstance(p.get("tecnicas"), list):
        p["tecnicas"] = list(n["perfil"]["tecnicas"])
    p["tecnicas"] = [t for t in p["tecnicas"] if t in TECNICAS]
    if p.get("pacientes") not in PACIENTES:
        p["pacientes"] = n["perfil"]["pacientes"]
    for m in "AB":
        D = s["datos"].get(m)
        D = D if isinstance(D, dict) else {}
        limpio = {}
        for code, d in D.items():
            if isinstance(d, dict):
                limpio[code] = {"valor": str(d.get("valor") or ""), "fuente": str(d.get("fuente") or ""),
                                "estado": d.get("estado") if d.get("estado") in ESTADOS else "Declarado",
                                "nota": str(d.get("nota") or "")}
        s["datos"][m] = limpio
    return s


def codigos_desconocidos(study):
    """Códigos guardados en el estudio que no existen en criterios.json (se conservan pero no se muestran)."""
    return sorted({c for m in "AB" for c in study["datos"][m] if c not in BY})


def completitud(study, m):
    """(con dato, total) sobre los criterios obligatorios."""
    req = [c for c in CRIT if c["requerido"] == "Sí"]
    D = study["datos"][m]
    return sum(present(D.get(c["codigo"])) for c in req), len(req)


def avance_categoria(study, m, cat):
    cs = [c for c in CRIT if c["categoria"] == cat]
    D = study["datos"][m]
    return sum(present(D.get(c["codigo"])) for c in cs), len(cs)


# ---- importación CSV --------------------------------------------------------------------
def leer_csv(raw):
    try:
        txt = raw.decode("utf-8-sig")
    except UnicodeDecodeError:
        txt = raw.decode("cp1252")
    first = txt.splitlines()[0] if txt.strip() else ""
    rd = csv.DictReader(io.StringIO(txt), restkey="_extra", delimiter=";" if first.count(";") >= first.count(",") else ",")
    out = []
    for row in rd:
        out.append({_clave(k): (v if isinstance(v, str) else ";".join(v)).strip() for k, v in row.items() if v is not None})
    return out


def _clave(k):
    """Nombre de columna normalizado: 'Código' -> 'codigo', 'Observación' -> 'observacion'."""
    k = (k or "").strip().lower()
    return k.translate(str.maketrans("áéíóúü", "aeiouu"))


def preparar_importacion(raw, D):
    """Clasifica el CSV sin modificar nada. -> dict(ok, desc, inv, sob)."""
    ok, desc, inv, sob = [], [], [], 0
    for row in leer_csv(raw):
        code, val = row.get("codigo", "").upper(), row.get("respuesta", "")
        if not val:
            continue
        if code not in BY:
            desc.append(code)
            continue
        t = BY[code]["tipo"]
        if t == "Numérico" and num(val) is None:
            inv.append(code)
            continue
        if t == "Sí/No":
            v = val.lower()
            if v not in YES and v not in NO:
                inv.append(code)
                continue
            val = "Sí" if v in YES else "No"
        elif t.startswith("Selección"):
            val = "|".join(partir_items(val))
        sob += present(D.get(code))
        ok.append((code, val, row))
    return {"ok": ok, "desc": desc, "inv": inv, "sob": sob}


def aplicar_importacion(D, prep):
    por_minuscula = {e.lower(): e for e in ESTADOS}
    for code, val, row in prep["ok"]:
        est = por_minuscula.get(row.get("estado", "").lower())
        D[code] = {
            "valor": val,
            "fuente": row.get("fuente", ""),
            "estado": est if est and est != "No encontrado" else "Declarado",
            "nota": row.get("observacion", ""),
        }


def plantilla_csv(path):
    with open(path, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f, delimiter=";")
        w.writerow(["codigo", "respuesta", "fuente", "estado", "criterio", "unidad"])
        for c in CRIT:
            w.writerow([c["codigo"], "", "", "", c["criterio"], c["unidad"]])


def exportar_csv(path, study):
    nm = study["nombres"]
    with open(path, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f, delimiter=";")
        w.writerow(["codigo", "criterio", nm["A"], nm["B"], "diferencia", "lectura"])
        for r in filas(study):
            w.writerow([r.c["codigo"], r.c["criterio"], (r.da or {}).get("valor", ""), (r.db or {}).get("valor", ""), r.diff, lectura(study, r)])


# ---- informe HTML -----------------------------------------------------------------------
def informe_html(study):
    esc = html.escape
    nm, rows, k = study["nombres"], filas(study), costos(study)
    rel = codigos_relevantes(study["perfil"])
    p = study["perfil"]
    hab = "".join(
        f'<span class="{m.lower()}">{esc(nm[m])}: {esc(texto_habilitantes(study, m))}</span>' for m in "AB"
    )
    res = "".join(
        f"<tr><td>{esc(r[0])} ({r[1]})</td><td class='a'>{r[2]}</td><td>{r[3]}</td><td class='b'>{r[4]}</td><td>{r[5]}</td><td>{r[6]}</td></tr>"
        for r in resumen(rows)
    )
    ganador = menor_costo(study)
    mx = max(k["A"]["total"], k["B"]["total"], 1)
    cost = ""
    for m in "AB":
        segs = "".join(
            f'<i class="s{i}" style="width:{v / mx * 100:.1f}%" title="{esc(COSTO_GRUPOS[i][0])}: {fmt_num(v, 0)} USD"></i>'
            for i, v in enumerate(k[m]["segs"])
        )
        marca = " ← menor costo total" if ganador == m else ""
        parcial = "" if k[m]["ok"] else " (parcial: faltan componentes)"
        cost += f'<div class="cr"><b>{esc(nm[m])}</b><div class="bar">{segs}</div><span>{fmt_num(k[m]["total"], 0)} USD{parcial}{marca}</span></div>'
    cuerpo = ""
    for r in rows:
        ca = "fav-a" if r.g == "A" else ""
        cb = "fav-b" if r.g == "B" else ""
        ha = "hatch" if "A" in r.falta else ""
        hb = "hatch" if "B" in r.falta else ""
        mark = "●&nbsp;" if r.c["codigo"] in rel else ""
        cuerpo += (
            f"<tr><td>{mark}{esc(r.c['criterio'])}<small>{esc(r.c['codigo'])} · {esc(cat_corta(r.c['categoria']))}</small></td>"
            f"<td class='{ca} {ha}'>{esc(mostrar_valor(r.c, r.da))}</td><td class='{cb} {hb}'>{esc(mostrar_valor(r.c, r.db))}</td>"
            f"<td>{esc(r.diff)}</td><td>{esc(lectura(study, r))}</td></tr>"
        )
    return f"""<!doctype html><html lang="es"><head><meta charset="utf-8"><title>Informe — {esc(study['titulo'])}</title>
<style>
body{{font-family:'Segoe UI',Inter,Arial,sans-serif;color:#1b2733;background:#f3f5f7;margin:0;padding:24px}}
h1{{font-size:20px;margin:0 0 4px}}h2{{font-size:15px;margin:0 0 10px}}.sub{{color:#5b6773;font-size:13px;margin-bottom:16px}}
.card{{background:#fff;border:1px solid #dfe3e8;border-radius:8px;padding:16px 18px;margin-bottom:16px}}
.a{{color:#0f766e;font-weight:600}}.b{{color:#b45309;font-weight:600}}.hab span{{margin-right:18px;font-weight:600}}
.hab .a{{color:#0f766e}}.hab .b{{color:#b45309}}
table{{border-collapse:collapse;width:100%;font-size:13px}}th{{text-align:left;color:#5b6773;font-weight:500;padding:6px 10px}}
td{{padding:8px 10px;border-top:1px solid #e6eaee;vertical-align:top}}small{{display:block;color:#5b6773;font-size:11px}}
td.fav-a{{background:#d4ece8;border-left:3px solid #0f766e;font-weight:700}}td.fav-b{{background:#fbe3c8;border-left:3px solid #b45309;font-weight:700}}
td.hatch{{background:repeating-linear-gradient(135deg,#eef1f4 0 5px,#c3cbd3 5px 6px);color:#5b6773}}
.cr{{display:flex;align-items:center;gap:12px;margin:8px 0}}.cr b{{width:130px}}.bar{{flex:1;display:flex;height:18px;background:#f0f3f5;border-radius:3px;overflow:hidden}}
.bar i{{display:block;height:100%}}.s0{{background:#0f3d4c}}.s1{{background:#5b92a8}}.s2{{background:#c8d5dc}}.cr span{{width:340px;font-size:12px}}
.leg{{font-size:12px;color:#5b6773}}@media print{{body{{background:#fff;padding:0}}.card{{break-inside:avoid}}}}
</style></head><body>
<h1>Estudio: {esc(study['titulo'])}</h1>
<div class="sub">{esc(nm['A'])} vs {esc(nm['B'])} · Perfil: nivel {esc(p['nivel'])}, técnicas {esc(', '.join(p['tecnicas']) or '—')}, pacientes/día {esc(p['pacientes'])} · ● = relevante para el perfil</div>
<div class="card hab"><h2>Habilitantes</h2>{hab}</div>
<div class="card"><h2>Resumen de diferencias por categoría (sin puntajes)</h2>
<table><tr><th>Categoría</th><th>{esc(nm['A'])} más favorable</th><th>Igual</th><th>{esc(nm['B'])} más favorable</th><th>Sin dato</th><th>Sin dirección</th></tr>{res}</table></div>
<div class="card"><h2>Costo lado a lado (sin ponderar, {study['vida_util']} años)</h2>{cost}
<div class="leg">■ Compra &nbsp; ■ Obra civil y blindaje &nbsp; ■ Servicio en la vida útil. El menor costo se resalta; no suma a ningún puntaje.</div></div>
<div class="card"><h2>Comparación por criterio</h2>
<table><tr><th>Criterio</th><th>{esc(nm['A'])}</th><th>{esc(nm['B'])}</th><th>Diferencia ({esc(nm['B'])} − {esc(nm['A'])})</th><th>Lectura</th></tr>{cuerpo}</table></div>
</body></html>"""
