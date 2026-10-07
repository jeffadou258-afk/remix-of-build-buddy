"""PHASE 9 — DOCUMENTATION. Genere un rapport MD + HTML reel."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from _core import *

OPERATION = "documentation"


def run(project_dir):
    ev = Evidence(OPERATION, project_dir)
    log(project_dir, OPERATION, "start")
    pid = os.path.basename(os.path.normpath(project_dir))
    ctx = load_json(os.path.join(project_dir, "project_context.json"), {})
    prog = load_json(os.path.join(project_dir, "program", "program.json"), {})
    dims = load_json(os.path.join(project_dir, "dimensions", "dimensions.json"), {})
    site = load_json(os.path.join(project_dir, "site", "site.json"), {})
    mdl = load_json(os.path.join(project_dir, "3d", "model_3d.json"), {})
    ren = load_json(os.path.join(project_dir, "renders", "render.json"), {})
    out = os.path.join(project_dir, "documentation")
    os.makedirs(out, exist_ok=True)

    L = ["# Rapport architectural — %s" % pid, "",
         "> Genere par Construction Agent v%s le %s" % (AGENT_VERSION, now()),
         "> **Document CONCEPTUEL.** Ne remplace aucune validation professionnelle.",
         "", "## 1. Contexte", ""]
    bl = ctx.get("tools", {}).get("blender", {})
    L += ["- Blender : %s" % (bl.get("version") or "INDISPONIBLE"),
          "- Statut projet : %s" % ctx.get("status", "UNKNOWN"), ""]
    L += ["## 2. Programme", ""]
    if prog:
        L += ["| Code | Piece | Surface | Niveau | Statut |", "|---|---|---|---|---|"]
        for r in prog.get("rooms", []):
            L.append("| %s | %s | %.1f m2 | %s | %s |" %
                     (r["code"], r["name"], r["surface_m2"], r["level"], r["status"]))
        L += ["", "**Total : %.2f m2** (coherent : %s)" %
              (prog.get("total_surface_m2", 0), prog.get("coherent")), ""]
    L += ["## 3. Dimensions", ""]
    for lv in dims.get("levels", []):
        L.append("- %s : %.2f x %.2f m = **%.2f m2** (source %s)" %
                 (lv["level"], lv["width_m"], lv["depth_m"], lv["surface_m2"], lv["source"]))
    L += ["", "Controle de coherence : **%s**" % dims.get("surface_check", "NOT_EXECUTED"), ""]
    L += ["## 4. Site et contraintes", ""]
    for k, v in (site.get("fields") or {}).items():
        L.append("- %s : %s (%s)" % (k, v.get("value"), v.get("status")))
    L += ["", "Statut reglementaire : **%s**" % site.get("regulation_status", "UNKNOWN"), ""]
    L += ["## 5. Maquette 3D", ""]
    if mdl:
        L += ["- Fichier : `%s`" % mdl.get("blend_file"),
              "- Taille : %s octets" % mdl.get("blend_size_bytes"),
              "- SHA-256 : `%s`" % (mdl.get("blend_sha256") or "")[:32] + "...",
              "- Blender : %s" % mdl.get("blender_version"),
              "- Objets : %s" % mdl.get("objects"), ""]
    L += ["## 6. Rendus", ""]
    for v in ren.get("views", []):
        L.append("- %s — %s — %s — **%s**" %
                 (v["name"], v.get("resolution"), v.get("size_bytes"), "VERIFIE" if v["verified"] else "NON VERIFIE"))
    L += ["", "## 7. Hypotheses et donnees UNKNOWN", "",
          "Toute valeur `HYPOTHESIS` ou `UNKNOWN` ci-dessus n'est pas un fait.",
          "Aucune reglementation n'est affirmee conforme sans source verifiee.", ""]
    L += ["## 8. Human Gates", "",
          "- Validation de variante : REQUISE",
          "- Validation structurelle : REQUISE",
          "- Validation reglementaire : REQUISE", ""]

    md = "\n".join(L)
    f_md = os.path.join(out, "rapport_architectural.md")
    with open(f_md, "w", encoding="utf-8") as fh:
        fh.write(md)
    ev.created(f_md)
    html = "<!doctype html><meta charset='utf-8'><title>%s</title><body style=\"font-family:Helvetica;max-width:860px;margin:40px auto\"><pre style='white-space:pre-wrap;line-height:1.5'>%s</pre></body>" % (
        pid, md.replace("&", "&amp;").replace("<", "&lt;"))
    f_html = os.path.join(out, "rapport_architectural.html")
    with open(f_html, "w", encoding="utf-8") as fh:
        fh.write(html)
    ev.created(f_html)
    ev.test("md_written", os.path.getsize(f_md) > 500, "%d octets" % os.path.getsize(f_md))
    ev.test("html_written", os.path.getsize(f_html) > 500, "%d octets" % os.path.getsize(f_html))
    ev.close("EXECUTED")
    ev.out()
    log(project_dir, OPERATION, "status=EXECUTED")
    return {"status": "EXECUTED", "markdown": f_md, "html": f_html}


if __name__ == "__main__":
    cli(OPERATION, run)
