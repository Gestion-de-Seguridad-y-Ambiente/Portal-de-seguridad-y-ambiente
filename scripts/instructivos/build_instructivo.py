"""
build_instructivo.py — Generador parametrizable de Instructivos Plantabal
Uso:
    python3 build_instructivo.py config.json [--out /ruta/salida.docx]

El JSON de config tiene la estructura definida en SKILL.md.
Soporta GE-SO-I, GE-SO-R, GE-SO-D (el código cambia la portada/encabezado).
"""
import argparse, copy, json, shutil, subprocess, sys
from pathlib import Path
from lxml import etree

TEMPLATE = Path("/root/.claude/uploads/873d328e-e6e2-50a6-bb43-ebf160679516/f16cdbf7-GE-SO-DXX_Plantilla_Instructivo.docx")
MERGE_RUNS = Path("/root/.claude/skills/synced/a0e77799-0b6d-46d2-aa0c-91658295909b_a93dcd9b-1f6c-4fa0-a611-b5956f26318f/docx/scripts/merge_runs.py")
SCRATCHPAD = Path("/tmp/claude-0/-home-user-kewei/873d328e-e6e2-50a6-bb43-ebf160679516/scratchpad")

W  = lambda t: f"{{http://schemas.openxmlformats.org/wordprocessingml/2006/main}}{t}"
NS = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}

# ── Helpers XML ───────────────────────────────────────────────────────────────

def set_cell_text(tc, paras):
    """Reemplaza todo el contenido de una celda <w:tc> con nuevos párrafos."""
    for child in list(tc):
        if child.tag != W("tcPr"):
            tc.remove(child)
    for pd in paras:
        p = etree.SubElement(tc, W("p"))
        pPr = etree.SubElement(p, W("pPr"))
        if pd.get("align"):
            jc = etree.SubElement(pPr, W("jc"))
            jc.set(W("val"), pd["align"])
        sp = etree.SubElement(pPr, W("spacing"))
        sp.set(W("before"), str(pd.get("sb", 0)))
        sp.set(W("after"),  str(pd.get("sa", 40)))
        if pd.get("indent"):
            ind = etree.SubElement(pPr, W("ind"))
            ind.set(W("left"), str(pd["indent"]))
        txt = pd.get("text", "")
        if not txt:
            continue
        r = etree.SubElement(p, W("r"))
        rPr = etree.SubElement(r, W("rPr"))
        if pd.get("bold"):
            etree.SubElement(rPr, W("b"))
        sz = etree.SubElement(rPr, W("sz"))
        sz.set(W("val"), str(pd.get("size", 20)))
        szCs = etree.SubElement(rPr, W("szCs"))
        szCs.set(W("val"), str(pd.get("size", 20)))
        if pd.get("color"):
            col = etree.SubElement(rPr, W("color"))
            col.set(W("val"), pd["color"])
        t = etree.SubElement(r, W("t"))
        t.text = txt
        if txt.startswith(" ") or txt.endswith(" "):
            t.set("{http://www.w3.org/XML/1998/namespace}space", "preserve")


def find_tc_with(root, keyword):
    for tc in root.iter(W("tc")):
        if keyword in "".join(x.text or "" for x in tc.iter(W("t"))):
            return tc
    return None


def find_table_with(root, *keywords):
    for tbl in root.iter(W("tbl")):
        txt = "".join(x.text or "" for x in tbl.iter(W("t")))
        if all(k in txt for k in keywords):
            return tbl
    return None


def replace_t(root, old, new):
    for t in root.iter(W("t")):
        if t.text and old in t.text:
            t.text = t.text.replace(old, new)


def set_para_spacing(p_elem, before=0, after=40):
    pPr = p_elem.find(W("pPr"))
    if pPr is None:
        pPr = etree.SubElement(p_elem, W("pPr"))
    sp = pPr.find(W("spacing"))
    if sp is None:
        sp = etree.SubElement(pPr, W("spacing"))
    sp.set(W("before"), str(before))
    sp.set(W("after"),  str(after))


def get_all_body_children(root):
    body = root.find(W("body"))
    return list(body) if body is not None else []


def make_header_row(tbl, texts, bold=True, bg="2E6DB4", fg="FFFFFF", size=20):
    """Crea una fila de encabezado azul con los textos dados."""
    tr = etree.SubElement(tbl, W("tr"))
    for txt in texts:
        tc = etree.SubElement(tr, W("tc"))
        tcPr = etree.SubElement(tc, W("tcPr"))
        shd = etree.SubElement(tcPr, W("shd"))
        shd.set(W("val"), "clear")
        shd.set(W("color"), "auto")
        shd.set(W("fill"), bg)
        p = etree.SubElement(tc, W("p"))
        pPr = etree.SubElement(p, W("pPr"))
        jc = etree.SubElement(pPr, W("jc"))
        jc.set(W("val"), "center")
        sp = etree.SubElement(pPr, W("spacing"))
        sp.set(W("before"), "0")
        sp.set(W("after"),  "40")
        r = etree.SubElement(p, W("r"))
        rPr = etree.SubElement(r, W("rPr"))
        if bold:
            etree.SubElement(rPr, W("b"))
        col = etree.SubElement(rPr, W("color"))
        col.set(W("val"), fg)
        sz_el = etree.SubElement(rPr, W("sz"))
        sz_el.set(W("val"), str(size))
        szCs = etree.SubElement(rPr, W("szCs"))
        szCs.set(W("val"), str(size))
        t = etree.SubElement(r, W("t"))
        t.text = txt
    return tr


def rebuild_table(tbl, header_rows_count, rows_data):
    """Elimina filas de datos (no header) y agrega las nuevas."""
    all_rows = tbl.findall(W("tr"))
    for tr in all_rows[header_rows_count:]:
        tbl.remove(tr)
    for cells in rows_data:
        tr = etree.SubElement(tbl, W("tr"))
        for cell_paras in cells:
            tc = etree.SubElement(tr, W("tc"))
            if isinstance(cell_paras, str):
                cell_paras = [{"text": cell_paras}]
            set_cell_text(tc, cell_paras)


# ── Build principal ────────────────────────────────────────────────────────────

def build(cfg: dict, out_path: Path):
    work = SCRATCHPAD / "instructivo_work"
    if work.exists():
        shutil.rmtree(work)
    subprocess.run(["unzip", "-q", str(TEMPLATE), "-d", str(work)], check=True)
    subprocess.run(["python3", str(MERGE_RUNS), str(work)],
                   check=True, capture_output=True)

    doc_xml  = work / "word/document.xml"
    hdr_xml  = work / "word/header1.xml"

    # ── document.xml ─────────────────────────────────────────────────────────
    tree = etree.parse(str(doc_xml))
    root = tree.getroot()

    codigo  = cfg["codigo"]        # e.g. "GE-SO-I002"
    titulo  = cfg["titulo"]
    version = cfg.get("version", "01")
    elabora = cfg.get("elaborado_por", "Pasante de Seguridad y Ambiente")
    revisa  = cfg.get("revisado_por",  "Jefe de Seguridad y Ambiente")
    aprueba = cfg.get("aprobado_por",  "Gerente de Planta")

    # 1. Código: puede estar partido en varias runs — reemplazamos por celda completa
    # Buscar todas las celdas que juntas formen el código del template
    for tc in root.iter(W("tc")):
        tc_txt = "".join(x.text or "" for x in tc.iter(W("t")))
        if "GE-SO-D" in tc_txt and len(tc_txt) < 20:
            # Reemplazar todo el contenido por el nuevo código
            for child in list(tc):
                if child.tag != W("tcPr"):
                    tc.remove(child)
            p = etree.SubElement(tc, W("p"))
            pPr = etree.SubElement(p, W("pPr"))
            jc = etree.SubElement(pPr, W("jc")); jc.set(W("val"), "center")
            r = etree.SubElement(p, W("r"))
            rPr = etree.SubElement(r, W("rPr"))
            etree.SubElement(rPr, W("b"))
            sz = etree.SubElement(rPr, W("sz")); sz.set(W("val"), "20")
            szCs = etree.SubElement(rPr, W("szCs")); szCs.set(W("val"), "20")
            t_el = etree.SubElement(r, W("t")); t_el.text = codigo

    # 2. Tabla de encabezado (objetivo/alcance) — buscamos por etiqueta y tomamos la celda siguiente
    obj_tbl = find_table_with(root, "Objetivo")
    if obj_tbl is None:
        obj_tbl = find_table_with(root, "OBJETIVO")
    if obj_tbl is not None:
        all_tcs = list(obj_tbl.iter(W("tc")))
        for i, tc in enumerate(all_tcs):
            tc_txt = "".join(x.text or "" for x in tc.iter(W("t")))
            if "Objetivo" in tc_txt and i + 1 < len(all_tcs):
                set_cell_text(all_tcs[i + 1], [{"text": cfg.get("objetivo", ""), "size": 20}])
            elif "Alcance" in tc_txt and i + 1 < len(all_tcs):
                set_cell_text(all_tcs[i + 1], [{"text": cfg.get("alcance", ""), "size": 20}])

    # 3. Tabla de definiciones
    def_tbl = find_table_with(root, "TÉRMINO", "DEFINICIÓN")
    if def_tbl is not None:
        defs = cfg.get("definiciones", [])
        rows = []
        for d in defs:
            rows.append([
                [{"text": d["termino"], "bold": True, "size": 20}],
                [{"text": d["definicion"], "size": 20}],
            ])
        rebuild_table(def_tbl, 1, rows)

    # 4. Tabla responsabilidades
    resp_tbl = find_table_with(root, "RESPONSABLE", "RESPONSABILIDAD")
    if resp_tbl is None:
        resp_tbl = find_table_with(root, "CARGO", "RESPONSABILIDAD")
    if resp_tbl is not None:
        resps = cfg.get("responsabilidades", [])
        rows = []
        for rs in resps:
            rows.append([
                [{"text": rs["cargo"], "bold": True, "size": 20}],
                [{"text": rs["responsabilidad"], "size": 20}],
            ])
        rebuild_table(resp_tbl, 1, rows)

    # 5. Tabla de desarrollo
    desa_tbl = find_table_with(root, "ACTIVIDAD", "RESPONSABLE", "NOTIFICAR")
    if desa_tbl is None:
        desa_tbl = find_table_with(root, "Actividad", "Responsable")
    if desa_tbl is not None:
        fases = cfg.get("desarrollo", [])
        all_rows = desa_tbl.findall(W("tr"))
        # borrar filas de datos (no encabezado)
        for tr in all_rows[1:]:
            desa_tbl.remove(tr)
        num = 1
        for fase in fases:
            # Fila de fase — span 4 celdas fusionadas visualmente (1 celda con vMerge no funciona fácil)
            # Simplificamos: 1 celda col1 vacía, col2 con el texto de fase bold+color, col3+4 vacías
            tr_fase = etree.SubElement(desa_tbl, W("tr"))
            # col #
            tc0 = etree.SubElement(tr_fase, W("tc"))
            tcPr0 = etree.SubElement(tc0, W("tcPr"))
            shd0 = etree.SubElement(tcPr0, W("shd"))
            shd0.set(W("val"), "clear"); shd0.set(W("color"), "auto"); shd0.set(W("fill"), "DDEEFF")
            p0 = etree.SubElement(tc0, W("p"))
            # col actividad — texto de fase
            tc1 = etree.SubElement(tr_fase, W("tc"))
            tcPr1 = etree.SubElement(tc1, W("tcPr"))
            shd1 = etree.SubElement(tcPr1, W("shd"))
            shd1.set(W("val"), "clear"); shd1.set(W("color"), "auto"); shd1.set(W("fill"), "DDEEFF")
            set_cell_text(tc1, [{"text": fase["fase"], "bold": True, "size": 20, "color": "1F3864"}])
            # col responsable + notificar vacías
            for _ in range(2):
                tc_e = etree.SubElement(tr_fase, W("tc"))
                tcPr_e = etree.SubElement(tc_e, W("tcPr"))
                shd_e = etree.SubElement(tcPr_e, W("shd"))
                shd_e.set(W("val"), "clear"); shd_e.set(W("color"), "auto"); shd_e.set(W("fill"), "DDEEFF")
                etree.SubElement(tc_e, W("p"))
            for act in fase.get("actividades", []):
                tr = etree.SubElement(desa_tbl, W("tr"))
                for cell_data in [
                    [{"text": str(num), "align": "center", "size": 20}],
                    [{"text": act["actividad"], "size": 20}],
                    [{"text": act.get("responsable", ""), "size": 20}],
                    [{"text": act.get("notificar", ""), "size": 20}],
                ]:
                    tc = etree.SubElement(tr, W("tc"))
                    set_cell_text(tc, cell_data)
                num += 1

    # 6. Tabla disposición reglamentaria / información documentada
    info_tbl = find_table_with(root, "INFORMACIÓN DOCUMENTADA")
    if info_tbl is None:
        info_tbl = find_table_with(root, "Información documentada")
    if info_tbl is not None:
        docs_ref = cfg.get("documentos_referencia", [])
        rows = []
        for d in docs_ref:
            rows.append([
                [{"text": d.get("codigo", ""), "size": 20}],
                [{"text": d.get("nombre", ""), "size": 20}],
                [{"text": d.get("tipo", "Registro"), "size": 20}],
            ])
        if rows:
            rebuild_table(info_tbl, 1, rows)

    # 7. Tabla control de cambios
    cc_tbl = find_table_with(root, "CONTROL DE CAMBIOS", "VERSIÓN")
    if cc_tbl is None:
        cc_tbl = find_table_with(root, "Control de Cambios", "Versión")
    if cc_tbl is not None:
        cambios = cfg.get("control_cambios", [
            {"version": version, "fecha": cfg.get("fecha", ""), "descripcion": "Emisión inicial",
             "elabora": elabora, "revisa": revisa, "aprueba": aprueba}
        ])
        rows = []
        for c in cambios:
            rows.append([
                [{"text": c.get("version", ""), "align": "center", "size": 18}],
                [{"text": c.get("fecha", ""), "align": "center", "size": 18}],
                [{"text": c.get("descripcion", ""), "size": 18}],
                [{"text": c.get("elabora", elabora), "size": 18}],
                [{"text": c.get("revisa",  revisa),  "size": 18}],
                [{"text": c.get("aprueba", aprueba), "size": 18}],
            ])
        rebuild_table(cc_tbl, 1, rows)

    # 8. Comprimir espacios en párrafos vacíos entre tablas
    body = root.find(W("body"))
    if body is not None:
        for child in body:
            if child.tag == W("p"):
                txt = "".join(t.text or "" for t in child.iter(W("t"))).strip()
                if not txt:
                    set_para_spacing(child, 0, 0)

    # Guardar document.xml
    tree.write(str(doc_xml), xml_declaration=True, encoding="UTF-8", standalone=True)

    # ── header1.xml ──────────────────────────────────────────────────────────
    if hdr_xml.exists():
        htree = etree.parse(str(hdr_xml))
        hroot = htree.getroot()
        # Reemplazar código en todas las celdas que lo contengan
        # El código puede estar partido en múltiples runs ("GE-SO-D" + "XX")
        # Buscar la celda que contiene el código parcial y reemplazar toda la celda
        for tc in hroot.iter(W("tc")):
            tc_txt = "".join(x.text or "" for x in tc.iter(W("t")))
            if "GE-SO-D" in tc_txt and len(tc_txt) < 25:
                for child in list(tc):
                    if child.tag != W("tcPr"):
                        tc.remove(child)
                p = etree.SubElement(tc, W("p"))
                pPr = etree.SubElement(p, W("pPr"))
                jc = etree.SubElement(pPr, W("jc")); jc.set(W("val"), "center")
                r = etree.SubElement(p, W("r"))
                rPr = etree.SubElement(r, W("rPr"))
                etree.SubElement(rPr, W("b"))
                sz = etree.SubElement(rPr, W("sz")); sz.set(W("val"), "18")
                szCs = etree.SubElement(rPr, W("szCs")); szCs.set(W("val"), "18")
                t_el = etree.SubElement(r, W("t")); t_el.text = codigo
        # Buscar celda del título (suele ser la del medio con texto largo)
        all_tc = list(hroot.iter(W("tc")))
        for tc in all_tc:
            tc_text = "".join(x.text or "" for x in tc.iter(W("t")))
            if len(tc_text) > 20 and ("INSTRUCTIVO" in tc_text.upper() or
                                       "ESTÁNDAR" in tc_text.upper() or
                                       "PROCEDIMIENTO" in tc_text.upper() or
                                       "PLANTILLA" in tc_text.upper() or
                                       "CAPACITACIÓN" in tc_text.upper()):
                set_cell_text(tc, [
                    {"text": titulo, "bold": True, "size": 20, "align": "center"}
                ])
                break
        htree.write(str(hdr_xml), xml_declaration=True, encoding="UTF-8", standalone=True)

    # ── Rezip ─────────────────────────────────────────────────────────────────
    out_path.parent.mkdir(parents=True, exist_ok=True)
    if out_path.exists():
        out_path.unlink()
    subprocess.run(["bash", "-c", f"cd '{work}' && zip -Xr '{out_path}' ."],
                   check=True, capture_output=True)
    print(f"OK → {out_path}")
    return out_path


# ── CLI ───────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Genera un instructivo Plantabal desde un JSON de config")
    parser.add_argument("config", help="Ruta al archivo JSON de configuración")
    parser.add_argument("--out", default=None, help="Ruta de salida .docx (opcional)")
    args = parser.parse_args()

    cfg = json.loads(Path(args.config).read_text(encoding="utf-8"))

    if args.out:
        out = Path(args.out)
    else:
        codigo  = cfg.get("codigo", "GE-SO-X000").replace("/", "-").replace(" ", "_")
        titulo_slug = cfg.get("titulo", "instructivo")[:40].replace(" ", "_").replace("/", "-")
        ver = cfg.get("version", "01")
        out = Path(f"/home/user/kewei/{codigo}_{titulo_slug}_v{ver}.docx")

    build(cfg, out)


if __name__ == "__main__":
    main()
