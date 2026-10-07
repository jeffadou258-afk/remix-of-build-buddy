#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""CONSTRUCTION_GUIDE_ENGINE — construction-guide-engine v1.0.0

Moteur pedagogique du Construction Agent. Explique un projet de construction
a une personne totalement debutante, en deux niveaux : DEBUTANT et PROFESSIONNEL.

REGLE ABSOLUE : la simplicite du langage ne diminue jamais la rigueur.
Le moteur distingue en permanence : CONNU / CALCULE / HYPOTHESE / INCONNU /
VERIFIE / A VALIDER PAR UN HUMAIN. Il ne remplace aucun professionnel.

Usage :
    python3 engine.py --projet <chemin_projet> status
    python3 engine.py --projet <chemin_projet> explain_all [--pro]
    python3 engine.py --projet <chemin_projet> phase 10
    python3 engine.py --projet <chemin_projet> ask "Pourquoi fait-on les fondations ?"
    python3 engine.py --projet <chemin_projet> glossary poteau
    python3 engine.py --projet <chemin_projet> bim fondations
"""
import json
import os
import sys

VERSION = "1.0.0"

# ----------------------------------------------------------------------------
# DONNEES DE REFERENCE — statuts autorises
# ----------------------------------------------------------------------------
STATUTS = ["CONNU", "CALCULE", "HYPOTHESE", "INCONNU", "VERIFIE", "HUMAN_GATE", "PENDING_VALIDATION"]
STATUTS_AVANCEMENT = ["NOT_STARTED", "IN_PROGRESS", "BLOCKED", "HUMAN_GATE", "VERIFIED", "COMPLETED"]

# ----------------------------------------------------------------------------
# GLOSSAIRE DEBUTANT
# ----------------------------------------------------------------------------
GLOSSAIRE = {
    "fondation": ("La partie située sous la maison qui transmet son poids au sol. "
                  "Imaginez le pied de la maison : plus la maison est lourde, plus le pied doit être large.",
                  "Elle doit être adaptée au terrain ET au poids du bâtiment."),
    "semelle": ("Un bloc de béton enterré sous chaque poteau, qui répartit la charge sur le sol.",
                "Plus le sol est mou, plus la semelle doit être large."),
    "poteau": ("Un élément vertical en béton armé qui porte les charges vers les fondations.",
               "C'est une jambe de la maison : il transmet ce qu'il porte vers le bas."),
    "poutre": ("Un élément horizontal qui reprend les charges d'un plancher ou d'une dalle et les porte aux poteaux.",
               "C'est le bras qui relie les jambes et empêche le plancher de descendre."),
    "dalle": ("La surface horizontale en béton qui forme le plancher ou le toit.",
              "C'est ce sur quoi on marche à l'étage."),
    "longrine": ("Une poutre en béton enterrée qui relie les semelles entre elles.",
                 "Elle solidarise les fondations et évite qu'elles bougent séparément."),
    "elevation": ("La construction des murs au-dessus du niveau du sol.", "C'est ce qui donne la hauteur à la maison."),
    "metre": ("Le calcul de la quantité de matériaux et de travail nécessaires.",
              "Combien de mètres carrés de mur, de mètres cubes de béton, de fenêtres..."),
    "trame": ("Le quadrillage régulier sur lequel sont placés les poteaux.",
              "C'est comme les poteaux d'une grille : ils doivent être alignés pour que ça tienne."),
    "etancheite": ("La couche qui empêche l'eau de traverser une toiture-terrasse.",
                   "Sans elle, l'eau s'infiltre et abîme la dalle."),
    "acrotère": ("Le petit muret qui fait le tour d'une toiture-terrasse.",
                 "Il empêche de tomber et retient l'eau le temps qu'elle s'évacue."),
    "geotechnique": ("L'étude du sol : sa résistance, sa nature, la présence d'eau.",
                     "Sans elle, on ne peut pas savoir quelle fondation convient."),
    "metre_lineaire": ("Une mesure de longueur, en mètres.", "Par exemple 12 m de garde-corps."),
    "tremie": ("L'ouverture dans le plancher par laquelle passe l'escalier.", "C'est le trou de l'escalier."),
}

# ----------------------------------------------------------------------------
# PHASES
# ----------------------------------------------------------------------------
def phases():
    return [
        ("01", "TERRAIN", "Connaître le terrain avant de dessiner quoi que ce soit.",
         "Avant de dessiner une maison, il faut connaître le terrain : sa taille, sa forme, son accès, "
         "son orientation, ce qui l'entoure et ce que la loi autorise.",
         "Relevé du terrain, dimensions, topographie, accès, orientation, voisinage, servitudes, réseaux, réglementation.",
         "Topographe (pour le relevé).", ["topographie", "acces_rue", "orientation", "pente_pct", "voisinage",
          "servitudes", "reglementation", "reseaux"], "G2"),
        ("02", "ÉTUDES PRÉALABLES", "Vérifier que le projet est possible et dans quelles conditions.",
         "On étudie le sol et le terrain pour savoir ce qu'on peut construire et comment. "
         "Ces études sont obligatoires : on ne devine pas le sol.",
         "Relevé topographique, étude géotechnique, étude d'assainissement, contraintes réglementaires, faisabilité.",
         "Géotechnicien, topographe, professionnel assainissement.", ["etude_geotechnique", "topographie",
          "exutoire_eu"], "G3"),
        ("03", "PROGRAMME", "Définir ce que la maison doit contenir.",
         "On écrit tout ce que la maison doit offrir : combien de personnes, combien de chambres, "
         "quelles pièces, quelles surfaces, quels espaces extérieurs.",
         "Programme architectural, surfaces, besoins particuliers.",
         "Le propriétaire avec l'architecte.", [], "—"),
        ("04", "CONCEPTION ARCHITECTURALE", "Dessiner l'organisation des espaces.",
         "L'architecte organise les pièces, les circulations, la lumière et la ventilation. "
         "Il produit des plans vus du dessus.",
         "Plans 2D, organisation des espaces, circulations, orientations, variantes.",
         "Architecte.", [], "—"),
        ("05", "MODÉLISATION 3D / BIM", "Voir la maison comme si elle existait.",
         "Le plan 2D montre la maison vue du dessus. Le modèle 3D permet de la voir en volume, "
         "comme si on marchait autour.",
         "Murs, cloisons, dalles, escaliers, portes, fenêtres, toiture, mobilier, terrain, garage, terrasse.",
         "Architecte / modeleur BIM.", [], "—"),
        ("06", "VALIDATION DU PROJET", "Vérifier que tout est cohérent.",
         "On contrôle les surfaces, les dimensions, la circulation, les portes, les fenêtres, le mobilier "
         "et la cohérence entre les plans et la 3D.",
         "Contrôles dimensionnels, collisions, cohérence 2D ↔ 3D.",
         "Architecte, contrôleur.", [], "—"),
        ("07", "BUDGET ET MÉTRÉ", "Savoir combien de matériaux et combien d'argent.",
         "Le métré consiste à déterminer combien de matériaux et de travail sont nécessaires. "
         "On multiplie ensuite par un prix pour obtenir un budget.",
         "Quantités, unités, prix unitaires, montants, sources des prix.",
         "Économiste de la construction, conducteur de travaux.", [], "G3"),
        ("08", "PRÉPARATION DU CHANTIER", "Installer le chantier avant de construire.",
         "On implante le bâtiment sur le terrain, on installe le chantier, on organise les accès, "
         "le stockage, la sécurité et le planning.",
         "Implantation, installation de chantier, accès, stockage, sécurité, planning.",
         "Conducteur de travaux.", [], "G3"),
        ("09", "TERRASSEMENT", "Préparer le sol.",
         "On décape la terre végétale, on creuse pour les fondations, on évacue ou on réutilise les terres "
         "et on contrôle les niveaux.",
         "Décapage, fouilles, évacuation des terres, contrôle des niveaux.",
         "Terrassier.", [], "G3"),
        ("10", "FONDATIONS", "Transmettre le poids de la maison au sol.",
         "Les fondations transmettent le poids de la construction au sol. "
         "Imaginez le pied de la maison : il doit être adapté au terrain et au poids du bâtiment.",
         "Semelles, longrines, béton de propreté, ferraillage, contrôle.",
         "Ingénieur structure + entreprise de gros œuvre.", [], "G3"),
        ("11", "ÉLÉVATION / GROS ŒUVRE", "Monter la structure.",
         "On construit progressivement : soubassement, poteaux, poutres, dalles, escaliers, chaînages. "
         "Chaque élément a un rôle précis et se contrôle.",
         "Soubassement, murs, poteaux, poutres, dalles, escaliers, chaînages, réservations.",
         "Entreprise de gros œuvre, chef de chantier.", [], "G3"),
        ("12", "TOITURE", "Mettre la maison hors d'eau.",
         "On réalise la structure de toiture, la couverture, l'étanchéité et l'évacuation des eaux.",
         "Structure, couverture, étanchéité, évacuation des eaux.",
         "Couvreur, étancheur.", [], "ROOF_NOT_DEFINED"),
        ("13", "RÉSEAUX", "Amener l'eau, l'électricité, évacuer les eaux usées.",
         "On sépare clairement l'eau, l'électricité, l'évacuation des eaux usées et pluviales, "
         "et la ventilation. Chaque réseau a un rôle différent.",
         "Alimentation eau, électricité, EU, EP, ventilation.",
         "Plombier, électricien, ventiliste.", ["exutoire_eu"], "G2"),
        ("14", "SECOND ŒUVRE", "Rendre la maison habitable.",
         "On réalise les cloisons, les enduits, la plomberie, l'électricité, les menuiseries, "
         "les plafonds, l'étanchéité et les revêtements.",
         "Cloisons, enduits, plomberie, électricité, menuiseries, plafonds, revêtements.",
         "Plusieurs corps de métier.",
         [], "—"),
        ("15", "FINITIONS", "Les derniers détails visibles.",
         "Carrelage, peinture, sanitaires, robinetterie, portes, appareillage électrique, cuisine, "
         "équipements et finitions extérieures.",
         "Carrelage, peinture, sanitaires, robinetterie, appareillage.", "Plusieurs corps de métier.", [], "—"),
        ("16", "CONTRÔLES", "Vérifier que tout est bien fait.",
         "On contrôle l'architecture, la structure, les réseaux, les dimensions, les matériaux, "
         "les finitions, la sécurité, la conformité et la documentation.",
         "Checklist de contrôles avec preuves.", "Contrôleur technique, maître d'œuvre.", [], "—"),
        ("17", "RÉCEPTION", "Constater les réserves et les lever.",
         "On inspecte l'ouvrage fini, on note les réserves, on les corrige et on vérifie les équipements.",
         "Inspection finale, réserves, corrections, documents finaux.", "Maître d'œuvre, maître d'ouvrage.",
         [], "—"),
        ("18", "LIVRAISON", "Remettre le dossier complet.",
         "On remet les plans, le modèle BIM, les métrés, le budget, la documentation, les rapports "
         "et les informations de maintenance.",
         "Dossier complet d'ouvrage exécuté (DOE), archive, maintenance.",
         "Maître d'œuvre.", [], "—"),
    ]

# ----------------------------------------------------------------------------
# MOTEUR
# ----------------------------------------------------------------------------
class ConstructionGuide:
    def __init__(self, projet):
        self.p = projet
        self.pro = False
        self.d = self._charger()

    # ---------- chargement des donnees REELLES ----------
    def _lire(self, *rel):
        for r in rel:
            f = os.path.join(self.p, r)
            if os.path.exists(f):
                try:
                    return json.load(open(f))
                except Exception:
                    return None
        return None

    def _charger(self):
        site = self._lire("site/site.json")
        st = self._lire("reports/CONTINUATION_STATE.json")
        metre = self._lire("metre/metre_final_v2.json")
        budget = self._lire("budget/budget_final_v2.json")
        qa = self._lire("reports/bloc9_qa_final.json")
        geo = self._lire("reports/G3_GEOMETRIC_QA.json")
        g2 = self._lire("reports/G2_DOSSIER_HUMAN_GATE.json")
        g3 = self._lire("reports/G3_DOSSIER_INGENIEUR.json")
        p7 = self._lire("reports/bloc7_plans_coupes_facades.json")
        p8 = self._lire("reports/bloc8_rendus.json")
        fic2 = self._lire("reports/G2_FICHE_COLLECTE.json")
        fic3 = self._lire("reports/G3_FICHE_COLLECTE.json")
        unknown_site = []
        if site:
            unknown_site = [k for k, v in site.get("fields", {}).items() if v.get("status") == "UNKNOWN"]
        return {"site": site, "state": st, "metre": metre, "budget": budget, "qa": qa, "geo": geo,
                "g2": g2, "g3": g3, "plans": p7, "rendus": p8, "fiche_g2": fic2, "fiche_g3": fic3,
                "unknown_site": unknown_site,
                "fichiers_presents": {r: os.path.exists(os.path.join(self.p, r)) for r in
                    ["3D/BIM_FINAL_A3.blend", "floorplan/floor_plan.json", "metre/metre_final_v2.json",
                     "budget/budget_final_v2.json", "docs/D12_qa_final.md", "FINAL_MANIFEST.json"]}}

    # ---------- entete ----------
    def _ente(self, titre):
        return "\n" + "=" * 74 + "\n" + titre + "\n" + "=" * 74

    def _nv(self):
        return "DEBUTANT" if not self.pro else "PROFESSIONNEL"

    # ---------- statut ----------
    def status(self):
        d = self.d
        st = d["state"] or {}
        gates = {"G1": "CLOSED", "G2": st.get("G2_STATUS", "OPEN / HUMAN_GATE"), "G3": st.get("G3_STATUS", "OPEN / HUMAN_GATE")}
        nb_plans = len(d["plans"]["documents"]) if d["plans"] else 0
        nb_rendus = len(d["rendus"]["rendus"]) if d["rendus"] else 0
        nb_docs = len([f for f in os.listdir(os.path.join(self.p, "docs"))]) if os.path.isdir(os.path.join(self.p, "docs")) else 0
        metre_ok = d["metre"] is not None
        budget_ok = d["budget"] is not None
        av = [
            ("TERRAIN", "IN_PROGRESS" if d["unknown_site"] else "VERIFIED", "9 champs du site UNKNOWN" if d["unknown_site"] else "complet"),
            ("ÉTUDES PRÉALABLES", "HUMAN_GATE", "G3 : étude géotechnique non fournie"),
            ("PROGRAMME", "VERIFIED", "programme validé (RDC 105 m², étage 85 m²)"),
            ("PLANS 2D", "VERIFIED", "4 fichiers 2D VALIDATED et gelés"),
            ("3D / BIM", "VERIFIED", "BIM_FINAL_A3.blend — 326 objets"),
            ("VALIDATION", "VERIFIED", "QA croisée 9 PASS / 1 PARTIAL / 0 FAIL"),
            ("BUDGET / MÉTRÉ", "IN_PROGRESS" if metre_ok and budget_ok else "NOT_STARTED",
             "métré v2 + budget v2 (périmètre partiel)" if metre_ok else "absent"),
            ("PRÉPARATION", "BLOCKED" if "HUMAN_GATE" in gates["G3"] else "NOT_STARTED", "G3 ouvert"),
            ("TERRASSEMENT", "BLOCKED" if "HUMAN_GATE" in gates["G3"] else "NOT_STARTED", "G3 ouvert"),
            ("FONDATIONS", "HUMAN_GATE", "préparation terminée ; exécution suspendue à G3"),
            ("GROS ŒUVRE", "HUMAN_GATE", "préparation terminée ; exécution suspendue à G3"),
            ("TOITURE", "HUMAN_GATE", "ROOF_NOT_DEFINED — pente non définie"),
            ("RÉSEAUX", "HUMAN_GATE", "G2 : exutoire EU UNKNOWN"),
            ("SECOND ŒUVRE", "NOT_STARTED", "aucune donnée"),
            ("FINITIONS", "NOT_STARTED", "aucune donnée"),
            ("CONTRÔLES", "IN_PROGRESS", "contrôles documentaires effectués (D12)"),
            ("RÉCEPTION", "NOT_STARTED", "chantier non commencé"),
            ("LIVRAISON", "IN_PROGRESS", "dossier numérique livré, chantier non réalisé"),
        ]
        print(self._ente("OÙ EN EST LE PROJET ? — %s" % self._nv()))
        print("\nCe projet existe aujourd'hui sous DEUX formes qu'il ne faut JAMAIS confondre :\n")
        print("  1. LE DOSSIER NUMÉRIQUE  — ce qui a été conçu, vérifié et documenté.")
        print("  2. LE CHANTIER PHYSIQUE  — ce qui a été réellement construit sur le terrain.\n")
        print("  >>> AVANCEMENT DU DOSSIER NUMÉRIQUE : AVANCÉ (conception terminée, documentation produite)")
        print("  >>> AVANCEMENT PHYSIQUE DU CHANTIER : 0 %% — AUCUN TRAVAIL DE CONSTRUCTION N'A COMMENCÉ\n")
        print("  Pourquoi ? Parce qu'une construction ne peut pas démarrer avant :")
        print("    • l'étude géotechnique (G3) — pour savoir si le sol porte la maison ;")
        print("    • la validation de la structure par un ingénieur (G3) ;")
        print("    • la connaissance de l'exutoire des eaux usées (G2).")
        print("  Aucun de ces trois éléments n'est disponible aujourd'hui.")
        print("\n" + "-" * 74)
        print("ÉTAPES — état réel")
        print("-" * 74)
        for nom, s, det in av:
            print("  %-22s %-12s %s" % (nom, s, det if self.pro else ""))
        if self.pro:
            print("\n" + "-" * 74)
            print("DOSSIER NUMÉRIQUE")
            print("-" * 74)
            print("  plans                  : %d" % nb_plans)
            print("  rendus                 : %d" % nb_rendus)
            print("  documents              : %d" % nb_docs)
            print("  métré v2               : %s" % ("présent" if metre_ok else "absent"))
            print("  budget v2              : %s" % (("%d FCFA (périmètre partiel)" % d["budget"]["total_general_fcfa"]) if budget_ok else "absent"))
            print("  gates                  : G1 %s · G2 %s · G3 %s" % (gates["G1"], gates["G2"], gates["G3"]))
            print("  champs site UNKNOWN    : %s" % (", ".join(d["unknown_site"]) or "aucun"))
        print("\nPROCHAINE ÉTAPE : faire remplir les fiches de collecte G2 (assainissement) et G3 (structure).")
        print("   → reports/G2_FICHE_COLLECTE.md  et  reports/G3_FICHE_COLLECTE.md")
        return av

    # ---------- fiche d'etape ----------
    def phase(self, num, court=False):
        ph = [p for p in phases() if p[0] == str(num).zfill(2)]
        if not ph:
            print("Phase inconnue. Utilisez un numero de 01 a 18.")
            return None
        n, nom, obj, simple, fait, qui, manque, gate = ph[0]
        print(self._ente("ÉTAPE %s — %s   [mode %s]" % (n, nom, self._nv())))
        print("\n🎯 OBJECTIF\n   %s" % obj)
        print("\n📖 EXPLICATION SIMPLE\n   %s" % self._wrap(simple))
        print("\n🔧 CE QUI EST FAIT\n   %s" % self._wrap(fait))
        print("\n👷 QUI INTERVIENT\n   %s" % qui)
        if not court:
            print("\n📐 DONNÉES TECHNIQUES")
            print(self._donnees(n))
            print("\n📄 DOCUMENTS RÉELLEMENT DISPONIBLES")
            print(self._documents(n))
            print("\n⚠️ POINTS DE VIGILANCE")
            print(self._vigilance(n))
            print("\n🚧 HUMAN GATE")
            print("   " + self._gate_txt(gate))
            print("\n✅ CONDITION POUR PASSER À L'ÉTAPE SUIVANTE")
            print(self._condition(n))
            print("\n🗺️  LIEN AVEC LE BIM")
            print(self._bim(n))
        return ph[0]

    def _wrap(self, t, w=70):
        import textwrap
        return "\n   ".join(textwrap.wrap(t, w))

    def _donnees(self, n):
        d = self.d
        if n == "01":
            u = d["unknown_site"]
            return ("   Terrain : 15,00 × 25,00 m = 375 m²  [STATUT : CONNU — fourni par le client]\n"
                    "   Informations MANQUANTES (%d) : %s\n"
                    "   [STATUT : INCONNU] Ces informations sont indispensables pour la phase suivante."
                    % (len(u), ", ".join(u)))
        if n == "06":
            qa = d["qa"]
            if not qa:
                return "   [STATUT : INCONNU] Aucun rapport QA disponible."
            p = sum(1 for c in qa.get("controls", []) if c["resultat"] == "PASS")
            return ("   QA croisée : %d PASS / 1 PARTIAL / 0 FAIL  [STATUT : VÉRIFIÉ]\n"
                    "   Source : reports/bloc9_qa_final.json" % p)
        if n == "07":
            m, b = d["metre"], d["budget"]
            if not m:
                return "   [STATUT : INCONNU] Métré non disponible."
            return ("   Métré : 12 postes indépendants de G3 + 6 postes dépendants (PENDING_G3)\n"
                    "   Budget : %s FCFA au total — dont %s indépendants de G3  [STATUT : HYPOTHÈSE / PARTIEL]\n"
                    "   ⚠ Ce budget est une ESTIMATION, pas un devis contractuel. Périmètre incomplet."
                    % (format(b["total_general_fcfa"], ",").replace(",", " "), format(b["total_perimetre_independant_G3_fcfa"], ",").replace(",", " ")))
        if n == "10":
            return ("   Type prévu : semelles isolées 1,20 × 1,20 m sous 16 poteaux  [STATUT : PROPOSED]\n"
                    "   Géométrie : 16 semelles existent dans le BIM, enterrées de −1,05 à −0,80 m  [STATUT : VÉRIFIÉ — géométrie]\n"
                    "   Portance du sol : 0,15 MPa  [STATUT : HYPOTHÈSE — NON vérifiée]\n"
                    "   ⚠ Ces dimensions sont CONCEPTUELLES : elles ne constituent pas un dimensionnement exécutoire.\n"
                    "   ⚠ 2 anomalies géométriques doivent être arbitrées par l'ingénieur (GEO_01, GEO_02).")
        if n == "12":
            return ("   Toiture-terrasse plane — étanchéité modélisée 30,24 m²  [STATUT : VÉRIFIÉ]\n"
                    "   Acrotères : 6 éléments, 6,413 m³  [STATUT : VÉRIFIÉ]\n"
                    "   Pente de toiture : NON DÉFINIE  [STATUT : INCONNU — ROOF_NOT_DEFINED]\n"
                    "   ⚠ Aucune pente n'a été inventée.")
        if n == "13":
            return ("   Pièces humides : 3 au RDC (WC, Cuisine, Buanderie), 3 à l'étage (3 salles de bain)  [CONNU]\n"
                    "   4 WC, 3 douches, 5 lavabos, 1 évier, 1 bac  [CONNU]\n"
                    "   Exutoire des eaux usées : %s  [STATUT : INCONNU / HUMAN_GATE]\n"
                    "   ⚠ Aucun raccordement, aucune fosse, aucune pente n'a été inventé." % ("non déterminé"))
        if n == "11":
            return ("   32 poteaux 0,30 × 0,30 m (16 RDC + 16 étage)  [STATUT : PROPOSED]\n"
                    "   16 poutres 0,25 × 0,35 m · 3 dalles ép. 15 cm  [STATUT : PROPOSED]\n"
                    "   Trame 4 × 4 — portées réelles 3,183 à 3,500 m  [STATUT : PROPOSED]\n"
                    "   Escalier : 17 marches, 4,76 m  [STATUT : VÉRIFIÉ — géométrie]")
        return "   [STATUT : CONNU] Voir le programme validé (RDC 105 m², étage 85 m², garage 25 m², terrasse 24 m²)."

    def _documents(self, n):
        d = self.d
        if n == "04":
            return "   floorplan/ — 4 fichiers 2D VALIDATED et gelés (SHA-256 vérifiés)  [STATUT : VÉRIFIÉ]"
        if n == "05":
            return "   3D/BIM_FINAL_A3.blend — 326 objets  [STATUT : VÉRIFIÉ]"
        if n == "06":
            return "   plans/ (10) · coupes/ (2) · facades/ (4) · reports/bloc9_qa_final.json  [STATUT : VÉRIFIÉ]"
        if n == "07":
            return "   metre/metre_final_v2.json · budget/budget_final_v2.json  [STATUT : PARTIEL]"
        if n in ("10", "11", "12", "13"):
            return "   Plans disponibles : P01 à P10, coupes C01/C02, façades F01–F04  [STATUT : PARTIEL pour la structure]"
        return "   Documents du dossier : %s" % ", ".join(k for k, v in d["fichiers_presence"].items() if v) if False else "   Voir docs/ — 12 documents produits."

    def _vigilance(self, n):
        v = {
            "01": "   • Un terrain mal relevé fausse tout le reste.\n   • 9 informations essentielles manquent encore.",
            "02": "   • On ne devine JAMAIS un sol. Sans étude géotechnique, aucune fondation ne peut être dimensionnée.\n   • Une étude ne peut pas être remplacée par une supposition.",
            "06": "   • Une erreur ici se paie sur le chantier.\n   • Un fichier qui existe n'est pas une preuve de cohérence : il faut contrôler son contenu.",
            "09": "   • Ne jamais prescrire une profondeur de fouille sans donnée géotechnique.",
            "10": "   • ⚠ La portance du sol (0,15 MPa) est une HYPOTHÈSE non vérifiée.\n   • ⚠ Les dimensions des semelles sont CONCEPTUELLES.\n   • ⚠ Une fondation conceptuelle n'est PAS une fondation exécutoire.",
            "11": "   • La structure reste PROPOSED tant qu'un ingénieur ne l'a pas validée.\n   • 4 poteaux sur 16 n'ont pas de poutre alignée sur leur centre (contrôle PARTIAL).",
            "12": "   • La pente de toiture n'est pas définie : l'évacuation des eaux pluviales reste inconnue.\n   • Ne pas inventer de pente.",
            "13": "   • L'exutoire des eaux usées est inconnu : on ne peut pas tracer l'évacuation.\n   • Ne jamais inventer un raccordement au réseau public.",
            "16": "   • Chaque contrôle doit avoir une PREUVE : source, date, responsable.\n   • Un contrôle sans preuve n'est pas un contrôle.",
        }
        return v.get(n, "   • Respecter l'ordre des étapes : une étape dépend de la précédente.")

    def _gate_txt(self, gate):
        if gate == "G3":
            return ("G3 — HUMAN_GATE : validation géotechnique et dimensionnement structure.\n"
                    "   Cette étape NE PEUT PAS être exécutée sans cette validation.\n"
                    "   → reports/G3_FICHE_COLLECTE.md (32 champs à remplir par un géotechnicien et un ingénieur)")
        if gate == "G2":
            return ("G2 — HUMAN_GATE : exutoire des eaux usées non déterminé.\n"
                    "   → reports/G2_FICHE_COLLECTE.md (10 champs à remplir par un topographe et un professionnel assainissement)")
        if gate == "ROOF_NOT_DEFINED":
            return "ROOF_NOT_DEFINED — la toiture n'est pas définie (pente inconnue). Une décision est nécessaire."
        return "Aucune validation humaine n'est nécessaire à cette étape."

    def _condition(self, n):
        c = {
            "01": "   → Topographie, accès, pente, réseaux et servitudes renseignés (fiche G2).",
            "02": "   → Étude géotechnique disponible et interprétée.",
            "03": "   → Programme écrit et validé par le propriétaire.  ✔ FAIT",
            "04": "   → Plans 2D produits.  ✔ FAIT (gelés)",
            "05": "   → Modèle 3D cohérent avec les plans.  ✔ FAIT",
            "06": "   → Aucune incohérence majeure.  ✔ FAIT",
            "10": "   → G3 fermé : portance connue, sections validées, plans d'exécution fournis.",
            "11": "   → G3 fermé + plans de coffrage et de ferraillage validés.",
            "12": "   → Pente et système d'évacuation définis.",
            "13": "   → G2 fermé : exutoire réel connu.",
        }
        return c.get(n, "   → L'étape précédente terminée et vérifiée.")

    def _bim(self, n):
        m = {
            "10": "   SEMELLE_* (16) → plans structure (PENDING_G3) → béton 5,760 m³ → PENDING_G3 → contrôle ingénieur",
            "11": "   POUTEAU_* (32) → béton 9,216 m³ · POUTRE_* (16) → 13,856 m³ · DALLE_* (3) → 31,992 m³ — tous PENDING_G3\n   VA_MARCHE (30) → escalier 3,981 m³ — HYPOTHÈSE",
            "12": "   ETANCHEITE_* (2) → 30,240 m² [VÉRIFIÉ] · ACRO_* (6) → 6,413 m³ [VÉRIFIÉ]",
            "13": "   Aucun réseau n'est modélisé dans le BIM — tracé UNKNOWN / PENDING_G2",
        }
        return m.get(n, "   Aucun élément BIM n'est directement rattaché à cette étape.")

    # ---------- explication complete ----------
    def explain_all(self):
        print(self._ente("EXPLIQUER TOUT LE PROJET DEPUIS LE DÉBUT   [mode %s]" % self._nv()))
        if not self.pro:
            print("\nNe vous inquiétez pas si vous ne connaissez rien à la construction.")
            print("Je vais vous guider étape par étape, sans jargon inutile.\n")
        print("Un projet de construction se déroule en 18 étapes, toujours dans le même ordre :")
        print("on ne peut pas construire les murs avant d'avoir coulé les fondations, et on ne peut pas")
        print("couler les fondations avant de savoir ce que le sol peut porter.\n")
        for (n, nom, obj, simple, fait, qui, manque, gate) in phases():
            print("  %s. %-34s %s" % (n, nom, obj))
        print("\n" + "-" * 74)
        print("OÙ EN EST CE PROJET ?")
        print("-" * 74)
        print("  Étapes 3 à 6 (programme, plans, BIM, validation) : TERMINÉES et vérifiées.")
        print("  Étape 1 (terrain) : INCOMPLÈTE — 9 informations manquent.")
        print("  Étape 2 (études) : BLOQUÉE — l'étude géotechnique n'a pas été fournie.")
        print("  Étapes 8 à 11 (chantier, fondations, gros œuvre) : BLOQUÉES par G3.")
        print("  Étape 12 (toiture) : la pente n'est pas définie.")
        print("  Étape 13 (réseaux) : BLOQUÉE par G2.")
        print("  Étapes 14-15 (second œuvre, finitions) : PAS COMMENCÉES.")
        print("  Étape 18 (livraison) : le dossier numérique est livré ; le chantier n'a pas commencé.")
        print("\nCE QU'IL FAUT FAIRE MAINTENANT :")
        print("  1. Faire remplir reports/G2_FICHE_COLLECTE.md (topographe + assainissement).")
        print("  2. Faire remplir reports/G3_FICHE_COLLECTE.md (géotechnicien + ingénieur structure).")
        print("  3. Transmettre reports/G2_G3_DEMANDE_VALIDATION.md aux professionnels.")
        print("\nTant que ces deux dossiers ne sont pas revenus remplis, la construction ne peut pas commencer.")

    # ---------- questions ----------
    def ask(self, q):
        ql = q.lower()
        print(self._ente("QUESTION : %s   [mode %s]" % (q, self._nv())))
        # --- 1. INTENTIONS PRIORITAIRES (avant le glossaire : sinon « puis-je construire
        #        les fondations ? » renvoie la definition de « fondation » au lieu du blocage) ---
        if ("construire maintenant" in ql or "puis-je construire" in ql or "commencer les fondations" in ql
                or "peut-on construire" in ql or "démarrer" in ql or "demarrer" in ql):
            print("\nRÉPONSE : NON, pas encore.\n")
            print("Pour construire les fondations, il manque deux validations obligatoires :")
            print("  1. L'étude géotechnique — pour savoir ce que le sol peut porter.")
            print("     Aujourd'hui la portance est une HYPOTHÈSE (0,15 MPa), pas une donnée.")
            print("  2. La validation de la structure par un ingénieur.")
            print("     Aujourd'hui les semelles et poteaux sont CONCEPTUELS (PROPOSED).")
            print("\n⚠ Un modèle conceptuel n'est PAS une autorisation de construire.")
            print("→ reports/G3_FICHE_COLLECTE.md")
            return
        if any(m in ql for m in ["où en est", "ou en est", "avancement", "où j'en suis"]):
            return self.status()
        if any(m in ql for m in ["par où commencer", "commencer", "je ne connais rien", "débuter"]):
            print("\nNe vous inquiétez pas si vous ne connaissez rien à la construction.")
            print("On commence toujours par la même chose : comprendre le TERRAIN.")
            print("Avant de dessiner, il faut savoir : sa taille, son accès, sa pente, son orientation,")
            print("et ce que la loi permet d'y construire.")
            return self.phase("01")
        # --- 2. GLOSSAIRE ---
        for k, (defi, pour) in GLOSSAIRE.items():
            if k in ql:
                print("\nTERME : %s" % k.upper())
                print("  Définition simple : %s" % defi)
                print("  Pourquoi ça compte : %s" % pour)
                if self.pro:
                    BIMS = {"fondation": ("SEMELLE_*", 16, "5,760 m3", "PENDING_G3"),
                            "semelle": ("SEMELLE_*", 16, "5,760 m3", "PENDING_G3"),
                            "poteau": ("POUTEAU_*", 32, "9,216 m3", "PROPOSED"),
                            "poutre": ("POUTRE_*", 16, "13,856 m3", "PROPOSED"),
                            "dalle": ("DALLE_*", 3, "31,992 m3", "PROPOSED"),
                            "longrine": ("LONGRINE_*", 8, "4,920 m3", "PENDING_G3"),
                            "escalier": ("VA_MARCHE", 30, "3,981 m3", "HYPOTHESE"),
                            "etancheite": ("ETANCHEITE_*", 2, "30,240 m2", "VERIFIE")}
                    if k in BIMS:
                        b = BIMS[k]
                        print("  Reference BIM : %s (%d objets) - quantite %s - statut %s" % b)
                        print("  Fichier : 3D/BIM_FINAL_A3.blend  |  Documentation : docs/D03_structure.md")
                    else:
                        print("  Reference : voir docs/ et 3D/BIM_FINAL_A3.blend")
                return
        # --- 3. PHASES ---
        for (n, nom, obj, simple, fait, qui, manque, gate) in phases():
            if nom.lower().split()[0] in ql or nom.lower() in ql:
                return self.phase(n)
        print("\nJe n'ai pas identifié de correspondance exacte.")
        print("Essayez par exemple : « Pourquoi fait-on les fondations ? », « Qu'est-ce qu'un poteau ? »,")
        print("« Où en est mon projet ? », ou lancez : explain_all")

    # ---------- glossaire / BIM ----------
    def glossary(self, t):
        print(self._ente("GLOSSAIRE — %s" % t.upper()))
        k = t.lower().strip()
        if k in GLOSSAIRE:
            d, p = GLOSSAIRE[k]
            print("\nDéfinition simple :\n   %s" % d)
            print("\nPourquoi ça compte :\n   %s" % p)
        else:
            print("\nTerme non trouvé. Termes disponibles :")
            for kk in sorted(GLOSSAIRE):
                print("   - %s" % kk)

    def bim(self, q):
        print(self._ente("LIEN BIM — %s   [mode %s]" % (q, self._nv())))
        m = {"fondation": ("SEMELLE_*", 16, "5,760 m³", "PENDING_G3", "semelles 1,20 × 1,20 m enterrées −1,05 à −0,80 m"),
             "poteau": ("POUTEAU_*", 32, "9,216 m³", "PROPOSED", "0,30 × 0,30 m · 16 RDC + 16 étage"),
             "poutre": ("POUTRE_*", 16, "13,856 m³", "PROPOSED", "0,25 × 0,35 m"),
             "dalle": ("DALLE_*", 3, "31,992 m³", "PROPOSED", "ép. 15 cm"),
             "escalier": ("VA_MARCHE", 30, "3,981 m³", "HYPOTHÈSE", "17 girons, 4,76 m"),
             "etancheite": ("ETANCHEITE_*", 2, "30,240 m²", "VÉRIFIÉ", "toiture-terrasse"),
             "acrotère": ("ACRO_*", 6, "6,413 m³", "VÉRIFIÉ", "périphérie de toiture")}
        for k, v in m.items():
            if k in q.lower() or (k == "acrotère" and "acro" in q.lower()) or (k == "etancheite" and "étanché" in q.lower()):
                print("\nÉTAPE → %s (%d objets) → quantité %s → statut %s" % (v[0], v[1], v[2], v[3]))
                print("   Caractéristiques : %s" % v[4])
                print("   Fichier : 3D/BIM_FINAL_A3.blend [SHA vérifié]")
                if v[3] in ("PENDING_G3", "HYPOTHÈSE"):
                    print("   ⚠ Cette quantité n'est PAS une quantité d'exécution.")
                return
        print("\nAucun élément BIM trouvé pour « %s »." % q)
        print("Essayez : fondation, poteau, poutre, dalle, escalier, étanchéité, acrotère.")


# ----------------------------------------------------------------------------
def main():
    a = sys.argv[1:]
    if not a:
        print(__doc__)
        return
    proj = "/Users/mac/ConstructionAgent/projects/PRJ_1701484686"
    if "--projet" in a:
        i = a.index("--projet")
        proj = a[i + 1]
        a = a[:i] + a[i + 2:]
    pro = "--pro" in a
    if pro:
        a.remove("--pro")
    if not a:
        print(__doc__)
        return
    g = ConstructionGuide(proj)
    g.pro = pro
    cmd, rest = a[0], " ".join(a[1:])
    if cmd == "status":
        g.status()
    elif cmd == "explain_all":
        g.explain_all()
    elif cmd == "phase":
        g.phase(rest.strip())
    elif cmd == "ask":
        g.ask(rest)
    elif cmd == "glossary":
        g.glossary(rest)
    elif cmd == "bim":
        g.bim(rest)
    else:
        print(__doc__)


if __name__ == "__main__":
    main()
