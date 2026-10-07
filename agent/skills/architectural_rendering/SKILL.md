# Rendu architectural

Skill interne de Construction Agent (`architectural_rendering`).

## Regles

1. Chaque rendu repond a une INTENTION architecturale declaree.
2. Vues : 01_Facade 02_Entree 03_Terrasse 04_Garage 05_Aerienne 06_Salon 07_Cuisine 08_Suite 09_Circulation 10_Generale.
3. Un PNG noir, blanc, vide ou unicolore = ECHEC de rendu.
4. Chaque image : existence + taille + format + resolution + inspection visuelle.

## Preuve requise

Toute sortie de ce skill doit etre accompagnee d'un `evidence.json`
conforme au systeme Evidence (section 21 de la specification).

