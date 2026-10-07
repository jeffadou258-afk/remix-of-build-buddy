# QA/QC architectural

Skill interne de Construction Agent (`quality_control`).

## Regles

1. Chaine QA : PROGRAM > SURFACES > DIMENSIONS > GEOMETRY > CIRCULATION > STRUCTURE > 3D > RENDERS > DOCUMENTS > FILES > DELIVERY.
2. Aucune etape PASS sans preuve. Non execute = NOT_EXECUTED.
3. Un test echoue reste FAILED : jamais arrondi a PASS.
4. Un test non execute n'est jamais compte comme reussi.

## Preuve requise

Toute sortie de ce skill doit etre accompagnee d'un `evidence.json`
conforme au systeme Evidence (section 21 de la specification).

