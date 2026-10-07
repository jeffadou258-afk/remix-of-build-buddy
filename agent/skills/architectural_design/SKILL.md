# Conception architecturale

Skill interne de Construction Agent (`architectural_design`).

## Regles

1. Raisonner PROGRAM FIRST : aucune piece sans justification.
2. Produire VARIANT_A / VARIANT_B / VARIANT_C quand plusieurs solutions existent.
3. Aucune variante ne devient la variante de travail sans HUMAN GATE.
4. Tracer chaque decision : DECISION -> SOURCE -> JUSTIFICATION -> IMPACT.

## Preuve requise

Toute sortie de ce skill doit etre accompagnee d'un `evidence.json`
conforme au systeme Evidence (section 21 de la specification).

