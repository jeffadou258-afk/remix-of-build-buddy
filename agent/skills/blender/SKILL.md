# Blender headless

Skill interne de Construction Agent (`blender`).

## Regles

1. Toujours : which blender PUIS blender --version (valeur reelle).
2. Si absent : STATUS = BLOCKED. Ne jamais pretendre avoir utilise Blender.
3. Apres creation : test -f scene.blend + ls -lh + stat + sha256.
4. Apres rendu : test -f + file + stat + resolution reelle (sips).
5. Echec de commande Blender => BLENDER_STATUS = FAILED, jamais SUCCESS.

## Preuve requise

Toute sortie de ce skill doit etre accompagnee d'un `evidence.json`
conforme au systeme Evidence (section 21 de la specification).

