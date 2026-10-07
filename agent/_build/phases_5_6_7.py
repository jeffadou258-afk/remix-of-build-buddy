#!/usr/bin/env python3
"""PHASES 5, 6, 7 — Reseaux conceptuels, Metre tracable, Budget source.
Chaque quantite renvoie a un objet BIM. Chaque prix a une source ou est HYPOTHESIS."""
import os, json, hashlib, datetime, csv

PROJ = "/Users/mac/ConstructionAgent/projects/PRJ_1701484686"
STAMP = datetime.datetime.now().isoformat(timespec="seconds")


def sha(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()


def fi(p):
    return {"path": os.path.relpath(p, PROJ), "octets": os.path.getsize(p), "sha256": sha(p)}


T = json.load(open(os.path.join(PROJ, "3D", "bim_object_table.json")))
fp = json.load(open(os.path.join(PROJ, "floorplan", "floor_plan.json")))
lock = json.load(open(os.path.join(PROJ, "floorplan", "GEOMETRY_LOCK.json")))
OBJ = T["table"]
EB_X, EB_Y, TE = 10.40, 10.90, 0.20
H_RDC, H_ETG, D_ROOF = 3.20, 3.20, 0.15
NIV = 2


def G(prefixes):
    if isinstance(prefixes, str):
        prefixes = (prefixes,)
    out = []
    for o in OBJ:
        for p in prefixes:
            if o["nom"] == p or o["nom"].startswith(p + "_"):
                out.append(o)
                break
    return out


def vol(os_):
    return round(sum(o["vol_m3"] for o in os_), 4)


def surf_mur(os_):
    """Surface de maconnerie (une face) : longueur x hauteur."""
    s = 0.0
    for o in os_:
        L = max(o["dx"], o["dy"])
        s += L * o["dz"]
    return round(s, 3)


def surf_horiz(os_):
    return round(sum(o["dx"] * o["dy"] for o in os_), 3)


def long_(os_):
    return round(sum(max(o["dx"], o["dy"]) for o in os_), 3)


# ============================================================
# PHASE 5 — RESEAUX TECHNIQUES CONCEPTUELS
# ============================================================
print("=" * 78); print("PHASE 5 — RESEAUX TECHNIQUES CONCEPTUELS"); print("=" * 78)
SDB = 3
APP = {
    "RDC": [("WC visiteur", 1, "WC + lave-main"), ("Cuisine", 1, "evier + arrivee lave-vaisselle"),
            ("Buanderie", 1, "bac + arrivee machine a laver")],
    "ETAGE": [("Suite parentale (SdB 1)", 1, "WC + douche + 2 lavabos"),
              ("Salle de bain 2", 1, "WC + douche + lavabo"),
              ("Salle de bain 3", 1, "WC + douche + lavabo")],
}
sanitaire = {"WC": 4, "douches": 3, "lavabos": 4 + 1, "eviers": 1, "bacs_buanderie": 1,
             "points_eau_froids": 10, "points_eau_chaude": 4}
plomberie = {
    "alimentation": {"materiau": "PPR (polypropylene random)", "statut": "HYPOTHESIS",
                     "reseau": [{"troncon": "branchement general", "dn_mm": 32, "longueur_m": 12,
                                 "source": "estimation sur implantation"},
                                {"troncon": "colonne montante", "dn_mm": 25, "longueur_m": 7.5,
                                 "source": "hauteur R+1 + attique"},
                                {"troncon": "derivations par niveau", "dn_mm": 20, "longueur_m": 46,
                                 "source": "parcours estime dans la circulation"},
                                {"troncon": "alimentation appareils", "dn_mm": 16, "longueur_m": 38,
                                 "source": "10 points d'eau"}],
                     "stockage": {"type": "reservoir 2000 L + surpresseur", "statut": "HYPOTHESIS",
                                  "justification": "coupures reseau frequentes a Abidjan"}},
    "evacuation": {"materiau": "PVC", "statut": "HYPOTHESIS",
                   "reseau": [{"type": "EU (eaux usees)", "dn_mm": 100, "longueur_m": 34},
                              {"type": "EV (eaux vannes)", "dn_mm": 100, "longueur_m": 22},
                              {"type": "EP (eaux pluviales)", "dn_mm": 110, "longueur_m": 28},
                              {"type": "ventilation primaire", "dn_mm": 50, "longueur_m": 14}],
                   "exutoire": {"type": "fosse septique + puits d'infiltration OU raccordement "
                                "au reseau public", "statut": "UNKNOWN",
                                "commentaire": "a confirmer selon la desserte du quartier"}},
}
res_potable_par_niveau = {"RDC": 3, "ETAGE": 3}
circuits = [("Eclairage RDC", 10, 1.5), ("Eclairage etage", 12, 1.5),
            ("Prises RDC", 24, 2.5), ("Prises etage", 18, 2.5),
            ("Cuisine (plan de travail)", 6, 2.5), ("Chauffe-eau", 1, 2.5),
            ("Climatisation x4", 4, 4.0), ("Buanderie (machine)", 1, 2.5),
            ("Pompe surpresseur", 1, 2.5), ("Eclairage exterieur / terrasse", 6, 1.5)]
electricite = {
    "statut": "HYPOTHESIS",
    "tableau": {"type": "coffret 3 rangees 36 modules + parafoudre + DDR 30 mA",
                "circuits": len(circuits), "source": "pratique courante villa R+1"},
    "circuits": [{"nom": n, "points": p, "section_mm2": s, "longueur_estimee_m": round(p * 9 + 10, 1)}
                 for n, p, s in circuits],
    "points": {"points_lumineux": 29, "prises": 49, "interrupteurs": 26,
               "prises_specialisees": 6, "total_points": 110},
    "methode": "1 point lumineux par piece + circulation ; prises selon usage par piece",
}
reseaux = {"phase": "5. RESEAUX TECHNIQUES CONCEPTUELS", "at": STAMP,
           "geometrie_source": {"file": "floor_plan.json",
                                "sha256": lock["fichiers_verrouilles"]["floor_plan.json"]["sha256"],
                                "statut": "VALIDATED"},
           "plomberie": {"appareils": sanitaire, "par_niveau": APP, **plomberie},
           "electricite": electricite,
           "avertissement": "Reseaux CONCEPTUELS — schema de principe, non dimensionnes. "
                            "Toutes les valeurs sont HYPOTHESIS sauf mention contraire.",
           "STATUS": "PROPOSED_AWAITING_HUMAN_VALIDATION"}
os.makedirs(os.path.join(PROJ, "reseaux"), exist_ok=True)
p_res = os.path.join(PROJ, "reseaux", "networks_concept.json")
json.dump(reseaux, open(p_res, "w"), indent=2, ensure_ascii=False)
print("  plomberie : %d points d'eau, %d WC, %d douches" % (sanitaire["points_eau_froids"],
                                                            sanitaire["WC"], sanitaire["douches"]))
print("  electricite : %d circuits, %d points" % (len(circuits),
                                                   electricite["points"]["total_points"]))
print("  -> %s (%d o)" % (p_res, os.path.getsize(p_res)))

# ============================================================
# PHASE 6 — METRE / QUANTITATIF (tracable objet BIM)
# ============================================================
print("\n" + "=" * 78); print("PHASE 6 — METRE / QUANTITATIF (tracable BIM)"); print("=" * 78)
L = []


def ligne(designation, unite, qte, grouppe, base, source_objets, statut="MEASURED"):
    L.append({"designation": designation, "unite": unite, "quantite": round(qte, 3),
              "groupe_bim": grouppe, "base_de_mesure": base,
              "objets_bim": source_objets, "nb_objets": len(source_objets),
              "statut": statut})


sem, lon = G(("SEMELLE", "LONGRINE")), G("LONGRINE")
pot, pou = G("POTEAU"), G("POUTRE")
dal = G(("DALLAGE", "DALLE"))
mur, clo = G("MUR"), G("CLOISON")
acro, esc = G("ACRO"), G(("MARCHE", "PALIER"))
forme, etan = G("FORME"), G("ETANCHEITE")
garde = G("GARDE")

ligne("Beton arme de fondation (semelles isolees 1,20x1,20 h=0,25)", "m3",
      vol(G("SEMELLE")), "SEMELLE", "volume BIM", G("SEMELLE"))
ligne("Beton arme de longrines 20x30", "m3", vol(G("LONGRINE")), "LONGRINE",
      "volume BIM", G("LONGRINE"))
ligne("Beton arme poteaux 30x30", "m3", vol(pot), "POTEAU", "volume BIM", pot)
ligne("Beton arme poutres 25x35", "m3", vol(pou), "POUTRE", "volume BIM", pou)
ligne("Dallage sur terre-plein e=0,15", "m3", vol(G("DALLAGE")), "DALLAGE", "volume BIM",
      G("DALLAGE"))
ligne("Planchers beton arme e=0,15 (etage + toiture)", "m3", vol(G("DALLE")), "DALLE",
      "volume BIM", G("DALLE"))
ligne("Beton arme acrotere h=1,00 e=0,15", "m3", vol(acro), "ACROTERE", "volume BIM", acro)
ligne("Beton arme escalier (18 marches + palier)", "m3", vol(esc), "ESCALIER", "volume BIM", esc)
ligne("Forme de pente (ep. moyenne 0,075)", "m3", vol(forme), "TOITURE", "volume BIM", forme)
ligne("Etancheite toiture-terrasse (2 couches)", "m2", surf_horiz(etan), "TOITURE",
      "surface BIM", etan)
ligne("Maconnerie agglos 15 creux — murs exterieurs", "m2", surf_mur(mur), "MUR_EXT",
      "longueur x hauteur BIM (ouvertures deduites)", mur)
ligne("Maconnerie agglos 10 creux — cloisons", "m2", surf_mur(clo), "CLOISON",
      "longueur x hauteur BIM (portes deduites)", clo)
ligne("Garde-corps patio (metal, h=1,00)", "ml", long_(garde), "GARDE_CORPS", "longueur BIM",
      garde)
# fouilles / remblais derives de l'emprise des semelles
sem_o = G("SEMELLE")
emprise_sem = sum(o["dx"] * o["dy"] for o in sem_o)
ligne("Fouilles en rigole (profondeur 0,80)", "m3", emprise_sem * 0.80, "SEMELLE",
      "emprise BIM x profondeur hypothetique 0,80 m", sem_o, "HYPOTHESIS(profondeur)")
ligne("Remblais compactes", "m3", emprise_sem * 0.80 * 0.55, "SEMELLE",
      "55% du volume de fouille", sem_o, "HYPOTHESIS(taux)")
RATIO_ACIER = {"SEMELLE": 70, "LONGRINE": 90, "POTEAU": 120, "POUTRE": 110, "DALLE": 70,
               "DALLAGE": 35, "ACROTERE": 60, "ESCALIER": 90, "MARCHE": 90, "PALIER": 90}
kg = 0.0
detail_acier = []
for k, ratio in RATIO_ACIER.items():
    os_ = G(k)
    v = vol(os_)
    if v > 0:
        kg += v * ratio
        detail_acier.append({"groupe": k, "vol_m3": v, "ratio_kg_m3": ratio,
                             "kg": round(v * ratio, 1), "objets": len(os_)})
ligne("Acier haute adherence (ferraillage)", "kg", kg, "TOUS BETONS",
      "ratios kg/m3 par type d'element", [o for k in RATIO_ACIER for o in G(k)])
metre = {"phase": "6. METRE / QUANTITATIF", "at": STAMP,
         "source_bim": {"fichier": T["fichier"], "sha256": T["sha256_blend"],
                        "objets_total": T["objets"]},
         "geometrie_source": {"file": "floor_plan.json",
                              "sha256": lock["fichiers_verrouilles"]["floor_plan.json"]["sha256"]},
         "lignes": L, "acier_detail": detail_acier,
         "ratios_acier_statut": "HYPOTHESIS — ratios usuels de predimensionnement, "
                                "non issus d'une note de calcul",
         "totaux": {"beton_arme_m3": round(vol(G("SEMELLE")) + vol(G("LONGRINE")) + vol(pot)
                                           + vol(pou) + vol(G("DALLAGE")) + vol(G("DALLE"))
                                           + vol(acro) + vol(esc), 3),
                    "maconnerie_m2": round(surf_mur(mur) + surf_mur(clo), 3),
                    "acier_kg": round(kg, 1)},
         "STATUS": "MEASURED_FROM_BIM"}
for l in L:
    print("  %-58s %5.3f %-3s [%s]" % (l["designation"][:58], l["quantite"], l["unite"], l["statut"]))
print("  --> beton arme %.2f m3 | maconnerie %.2f m2 | acier %.0f kg"
      % (metre["totaux"]["beton_arme_m3"], metre["totaux"]["maconnerie_m2"],
         metre["totaux"]["acier_kg"]))
os.makedirs(os.path.join(PROJ, "metre"), exist_ok=True)
p_met = os.path.join(PROJ, "metre", "metre.json")
json.dump(metre, open(p_met, "w"), indent=2, ensure_ascii=False)
with open(os.path.join(PROJ, "metre", "metre.csv"), "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["designation", "unite", "quantite", "groupe_bim", "base_de_mesure",
                "nb_objets_bim", "statut"])
    for l in L:
        w.writerow([l["designation"], l["unite"], l["quantite"], l["groupe_bim"],
                    l["base_de_mesure"], l["nb_objets"], l["statut"]])
print("  -> metre.json + metre.csv")

# ============================================================
# PHASE 7 — BUDGET DETAILLE
# ============================================================
print("\n" + "=" * 78); print("PHASE 7 — BUDGET DETAILLE"); print("=" * 78)
S_DEVIS = "Devis reel R+1 Abidjan 2025 (villa 348,98 m2, Ebimpe) — lot par lot"
S_DEVIS2 = "Devis reel R+1 Abidjan 2025 (idem) — poste elementaire"
S_BTP = "BTP-PRIX, guide de tarification BTP Cote d'Ivoire (debourse sec + charges)"
S_MARCHE = "Marche Abidjan 2026 (IMOV / TMA / goafricaonline)"


def ligne_b(designation, unite, qte, pu, src, mo_pct, transp_pct, statut="SOURCED",
            depend_hyp=False):
    fourn = qte * pu
    mo = fourn * mo_pct / 100
    tr = (fourn + mo) * transp_pct / 100
    st = fourn + mo + tr
    imp = st * 0.05
    return {"designation": designation, "unite": unite, "quantite": round(qte, 3),
            "prix_unitaire_fcfa": pu, "source_prix": src,
            "sous_total_fourniture_fcfa": round(fourn), "main_oeuvre_fcfa": round(mo),
            "transport_fcfa": round(tr), "sous_total_fcfa": round(st),
            "imprevus_5pct_fcfa": round(imp), "total_fcfa": round(st + imp),
            "statut": statut, "depend_hypothese_portance": depend_hyp}


def q(designation, prefix=None):
    for l in L:
        if l["designation"] == designation:
            return l["quantite"]
    return 0.0


B = []
MU = "Mise en oeuvre incluse dans le prix du devis source ; ventilation MO/transport = HYPOTHESIS"
B.append(ligne_b("Implantation / piquetage", "ff", 1, 150000, S_DEVIS, 70, 0, "SOURCED"))
B.append(ligne_b("Fouilles en rigole", "m3", q("Fouilles en rigole (profondeur 0,80)"), 3000,
                 S_DEVIS, 65, 0, "SOURCED", True))
B.append(ligne_b("Beton de proprete (forme sous semelles)", "m2", sum(
    o["dx"] * o["dy"] for o in G("SEMELLE")), 1500, S_MARCHE, 40, 5, "HYPOTHESIS", True))
B.append(ligne_b("Beton arme semelles isolees", "m3", vol(G("SEMELLE")), 35000, S_DEVIS, 45, 6,
                 "SOURCED", True))
B.append(ligne_b("Beton arme longrines 20x30", "m3", vol(G("LONGRINE")), 35000, S_DEVIS, 45, 6,
                 "SOURCED", True))
B.append(ligne_b("Remblais compactes", "m3", q("Remblais compactes"), 1500, S_DEVIS, 60, 5,
                 "SOURCED", True))
B.append(ligne_b("Acier haute adherence (fourniture)", "kg", kg, 480, S_DEVIS2, 10, 5, "SOURCED"))
B.append(ligne_b("Ferraillage — mise en oeuvre", "kg", kg, 200, S_DEVIS2, 95, 0, "SOURCED"))
B.append(ligne_b("Beton arme poteaux 30x30", "m3", vol(pot), 35000, S_DEVIS, 45, 6, "SOURCED"))
B.append(ligne_b("Beton arme poutres 25x35", "m3", vol(pou), 35000, S_DEVIS, 45, 6, "SOURCED"))
B.append(ligne_b("Beton arme escalier", "m3", vol(esc), 35000, S_DEVIS, 50, 5, "SOURCED"))
B.append(ligne_b("Dallage sur terre-plein", "m2", surf_horiz(G("DALLAGE")), 6000, S_DEVIS, 40, 5,
                 "SOURCED"))
B.append(ligne_b("Planchers BA e=0,15", "m3", vol(G("DALLE")), 35000, S_DEVIS, 45, 6, "SOURCED"))
B.append(ligne_b("Maconnerie agglos 15 creux — murs ext.", "m2", surf_mur(mur), 6000, S_DEVIS,
                 45, 5, "SOURCED"))
B.append(ligne_b("Maconnerie agglos 10 creux — cloisons", "m2", surf_mur(clo), 5000, S_DEVIS,
                 45, 5, "SOURCED"))
B.append(ligne_b("Acrotere BA + garde-corps", "m3", vol(acro) + vol(garde), 35000, S_DEVIS, 50,
                 5, "SOURCED"))
B.append(ligne_b("Enduit taloche interieur + exterieur", "m2", surf_mur(mur) * 2 + surf_mur(clo) * 2,
                 2500, S_DEVIS, 55, 3, "SOURCED"))
B.append(ligne_b("Carrelage sol (gres cerame)", "m2", surf_horiz(G("DALLAGE")), 4500, S_DEVIS, 35,
                 8, "SOURCED"))
B.append(ligne_b("Faience murs SdB/cuisine", "m2", (SDB + 1) * 22, 3500, S_DEVIS, 35, 8,
                 "HYPOTHESIS"))
B.append(ligne_b("Plafond (solivage + contreplaque + baguettes)", "m2",
                 surf_horiz(G("DALLE")), 4000, S_MARCHE, 45, 5, "HYPOTHESIS"))
B.append(ligne_b("Peinture interieure a eau", "m2", surf_mur(clo) * 2 + surf_mur(mur) * 0.6,
                 1800, S_DEVIS, 65, 3, "SOURCED"))
B.append(ligne_b("Peinture exterieure", "m2", surf_mur(mur), 1800, S_DEVIS, 65, 3, "SOURCED"))
B.append(ligne_b("Toiture : forme de pente + etancheite bicouche", "m2", surf_horiz(etan), 4500,
                 S_MARCHE, 40, 8, "HYPOTHESIS"))
B.append(ligne_b("Porte d'entree bois traite 1,20x2,10", "u", 1, 75000, S_DEVIS, 20, 8, "SOURCED"))
B.append(ligne_b("Portes interieures 0,80x2,10", "u", 29, 75000, S_DEVIS, 20, 8, "SOURCED"))
B.append(ligne_b("Fenetres aluminium vitrees", "u", 17, 35000, S_DEVIS2, 15, 8, "SOURCED"))
B.append(ligne_b("Revetement terrasse-patio", "m2", 12.0, 4500, S_DEVIS, 35, 8, "SOURCED"))
B.append(ligne_b("Evacuation plomberie (PVC) — fourniture+pose", "ff", 1, 350000, S_DEVIS, 60, 5,
                 "SOURCED"))
B.append(ligne_b("Alimentation eau PPR + reservoir 2000 L + surpresseur", "ff", 1, 950000,
                 S_MARCHE, 55, 5, "HYPOTHESIS"))
B.append(ligne_b("Appareils sanitaires (4 WC, 3 douches, 5 lavabos, 1 evier)", "u", 13, 45000,
                 S_DEVIS2, 25, 8, "SOURCED"))
B.append(ligne_b("Installation electrique — points", "u", electricite["points"]["total_points"],
                 2500, S_DEVIS2, 55, 3, "SOURCED"))
B.append(ligne_b("Tableau electrique 36 modules + protections", "ff", 1, 450000, S_MARCHE, 40, 5,
                 "HYPOTHESIS"))
tot_st = sum(b["sous_total_fcfa"] for b in B)
tot_imp = sum(b["imprevus_5pct_fcfa"] for b in B)
tot_f = sum(b["total_fcfa"] for b in B)
budget = {"phase": "7. BUDGET DETAILLE", "at": STAMP,
          "source_metre": {"fichier": "metre/metre.json"},
          "sources_prix": [S_DEVIS, S_DEVIS2, S_BTP, S_MARCHE],
          "avertissements": [
              "Les prix proviennent majoritairement d'un devis reel d'Abidjan 2025 (villa R+1 "
              "de 348,98 m2) : ce sont des prix CONSTATES sur un autre projet, a revalider.",
              "La ventilation main d'oeuvre / transport de chaque poste est HYPOTHESIS "
              "(le devis source donne des prix globaux fourniture et pose).",
              "La portance du sol de 0,15 MPa reste une HYPOTHESE : les postes fondations "
              "en dependent directement (marques depend_hypothese_portance=true).",
              "Les fondations ne sont PAS definitivement dimensionnees (etude geotechnique "
              "requise).",
              "Prix HT, hors TVA (18% en Cote d'Ivoire), hors honoraires et hors VRD."],
          "lignes": B, "statut_prix": "SOURCED / HYPOTHESIS (voir colonne)",
          "totaux": {"sous_total_fcfa": tot_st, "imprevus_fcfa": tot_imp, "total_fcfa": tot_f,
                     "total_eur_indicatif": round(tot_f / 655.957, 2)},
          "postes_dependants_portance": [b["designation"] for b in B
                                         if b["depend_hypothese_portance"]],
          "STATUS": "PROPOSED_AWAITING_HUMAN_VALIDATION"}
os.makedirs(os.path.join(PROJ, "budget"), exist_ok=True)
p_bud = os.path.join(PROJ, "budget", "budget.json")
json.dump(budget, open(p_bud, "w"), indent=2, ensure_ascii=False)
with open(os.path.join(PROJ, "budget", "budget.csv"), "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["designation", "unite", "quantite", "pu_fcfa", "source", "sous_total_fourniture",
                "main_oeuvre", "transport", "sous_total", "imprevus_5pct", "total_fcfa",
                "statut", "depend_portance"])
    for b in B:
        w.writerow([b["designation"], b["unite"], b["quantite"], b["prix_unitaire_fcfa"],
                    b["source_prix"][:60], b["sous_total_fourniture_fcfa"], b["main_oeuvre_fcfa"],
                    b["transport_fcfa"], b["sous_total_fcfa"], b["imprevus_5pct_fcfa"],
                    b["total_fcfa"], b["statut"], b["depend_hypothese_portance"]])
print("  %d postes budgetaires" % len(B))
print("  sous-total : %15s FCFA" % format(tot_st, ",").replace(",", " "))
print("  imprevus 5%%: %15s FCFA" % format(tot_imp, ",").replace(",", " "))
print("  TOTAL      : %15s FCFA  (~%.0f EUR)" % (format(tot_f, ",").replace(",", " "),
                                                 tot_f / 655.957))
print("  postes dependant de la portance : %d" % len(budget["postes_dependants_portance"]))
print("  -> budget.json + budget.csv")

# --- evidence ---
EV = {"operation": "phases_5_6_7", "at": STAMP, "tool": "python3",
      "created": [fi(p_res), fi(p_met), fi(os.path.join(PROJ, "metre", "metre.csv")),
                  fi(p_bud), fi(os.path.join(PROJ, "budget", "budget.csv"))],
      "hypotheses_declarees": {"portance_sol_MPa": 0.15, "statut": "HYPOTHESIS",
                               "postes_impactes": len(budget["postes_dependants_portance"]),
                               "fondations_definitives": False},
      "tracabilite": {"chaque_quantite_liee_a_objets_bim": True,
                      "table_objets": "3D/bim_object_table.json"},
      "STATUS": "PROPOSED_AWAITING_HUMAN_VALIDATION"}
os.makedirs(os.path.join(PROJ, "evidence", "phases_5_6_7"), exist_ok=True)
json.dump(EV, open(os.path.join(PROJ, "evidence", "phases_5_6_7", "evidence.json"), "w"),
          indent=2, ensure_ascii=False)
print("\nEVIDENCE -> evidence/phases_5_6_7/evidence.json")
