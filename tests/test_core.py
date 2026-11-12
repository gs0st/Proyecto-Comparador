import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import core as k

def D(v, est="Declarado"): return {"valor": v, "fuente": "", "estado": est}

def test_num():
    assert k.num("6.428.000") == 6428000 and k.num("1.234,5") == 1234.5 and k.num("0,6") == 0.6
    assert k.num("abc") is None and k.num("nan") is None and k.num("") is None

def test_wireframe_rows():
    c = k.BY["E-028"]
    assert k.compare(c, D("120"), D("160")) == ("B", "+40 láminas (+33 %)")
    c = k.BY["E-033"]; g, t = k.compare(c, D("0,6"), D("1,2")); assert g == "A" and t.startswith("+0,6 pp")
    c = k.BY["E-087"]; assert k.compare(c, D("7400"), D("6900")) == ("B", f"{k.MINUS}500 kg ({k.MINUS}7 %)")
    assert k.compare(k.BY["E-030"], None, D("3,5"))[0] == "?"
    assert k.compare(k.BY["E-046"], D("Brazo en C"), D("Anillo"))[0] == "n"
    assert k.compare(k.BY["E-040"], D("Sí"), D("sí"))[0] == "="
    assert k.compare(k.BY["E-028"], D("120", "No encontrado"), D("160"))[0] == "?"

def test_tolerance_is_equal():
    assert k.compare(k.BY["E-033"], D("0.5"), D("0.55"))[0] == "="

def test_import_and_study():
    s = k.nuevo_estudio()
    for m, f in (("A", "Varian_TrueBeam_importar.csv"), ("B", "Elekta_Infinity_importar.csv")):
        prep = k.preparar_importacion((Path(__file__).resolve().parents[1] / "ejemplos" / f).read_bytes(), s["datos"][m])
        assert len(prep["ok"]) > 40 and not prep["desc"]
        k.aplicar_importacion(s["datos"][m], prep)
    rows = k.filas(s)
    assert len(rows) == 203
    res = k.resumen(rows)
    assert res[-1][0] == "Infraestructura" and res[-1][1] == 40
    assert all(r[1] == sum(r[2:]) for r in res)
    assert k.costos(s)["A"]["segs"][0] > 0
    assert k.menor_costo(s) in (None, "A", "B")
    assert "<table" in k.informe_html(s)
    for r in rows: k.lectura(s, r); k.mostrar_valor(r.c, r.da)

def test_import_validation():
    prep = k.preparar_importacion("codigo;respuesta\nE-028;abc\nZ-999;1\nE-040;quizás\nE-040;no\nE-036;6, 10, 15\n".encode(), {})
    assert prep["inv"] == ["E-028", "E-040"] and prep["desc"] == ["Z-999"] and len(prep["ok"]) == 2
    assert prep["ok"][1][1] == "6|10|15"

def test_habilitantes_and_profile():
    s = k.nuevo_estudio()
    s["datos"]["A"] = {"C-057": D("Sí"), "C-058": D("97"), "C-059": D("Sí")}
    s["datos"]["B"] = {"C-057": D("Sí"), "C-058": D("90"), "C-059": D("Sí")}
    assert k.texto_habilitantes(s, "A") == "3/3 cumple" and k.texto_habilitantes(s, "B") == "2/3 cumple, 1 no cumple"
    assert "E-030" in k.codigos_relevantes(s["perfil"]) and "E-030" not in k.codigos_relevantes({"nivel": "Básica", "tecnicas": [], "pacientes": "<25"})

def test_import_headers_with_accents():
    prep = k.preparar_importacion("Código;Respuesta;Estado\ne-028;120;verificado\n".encode(), {})
    assert [c for c, _, _ in prep["ok"]] == ["E-028"]
    D = {}; k.aplicar_importacion(D, prep); assert D["E-028"]["estado"] == "Verificado"

def test_normalizar_estudio():
    s = k.normalizar_estudio({"vida_util": "12", "perfil": {"nivel": "X", "tecnicas": "VMAT"}, "datos": {"A": {"E-028": {"valor": 120}, "E-029": "malo"}}})
    assert s["vida_util"] == 12 and s["perfil"]["nivel"] == "Avanzada" and isinstance(s["perfil"]["tecnicas"], list)
    assert s["datos"]["A"] == {"E-028": {"valor": "120", "fuente": "", "estado": "Declarado", "nota": ""}} and s["datos"]["B"] == {}
    try:
        k.normalizar_estudio([1, 2]); assert False
    except ValueError:
        pass
    ej = k.normalizar_estudio(__import__("json").loads((Path(__file__).resolve().parents[1] / "ejemplos" / "estudio_ejemplo.json").read_text(encoding="utf-8")))
    assert len(k.filas(ej)) == 203
