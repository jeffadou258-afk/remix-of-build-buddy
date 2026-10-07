# Memoire Construction Agent

Fichiers JSONL append-only. Une ligne = un enregistrement JSON.

| Fichier | Contenu |
|---|---|
| decisions.jsonl | DECISION -> SOURCE -> JUSTIFICATION -> IMPACT |
| assumptions.jsonl | hypotheses explicites, jamais presentees comme faits |
| constraints.jsonl | contraintes avec statut VERIFIED/USER_PROVIDED/DERIVED/HYPOTHESIS/UNKNOWN |
| design_history.jsonl | variantes et choix successifs |
| known_issues.jsonl | problemes connus, non resolus |
| project_lessons.jsonl | lecons projet |

**INTERDIT** : API keys, passwords, tokens, private keys, secrets.
