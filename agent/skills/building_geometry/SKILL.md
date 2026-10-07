# Geometrie du batiment

Skill interne de Construction Agent (`building_geometry`).

## Regles

1. surface calculee == somme des surfaces des espaces, sinon FAIL.
2. dimensions -> surface -> geometrie -> circulation doivent rester coherents.
3. Toute incoherence BLOQUE la validation (section 5, PHASE 5).
4. Largeurs de couloir et portes : valeurs proposees, pas normatives.

## Preuve requise

Toute sortie de ce skill doit etre accompagnee d'un `evidence.json`
conforme au systeme Evidence (section 21 de la specification).

