# Roadmap
- [x] Site, comptes, assistant par projet (étape 1)
- [x] Relire toutes les capacités de l'agent GitHub et les refléter dans l'app
- [ ] Paiement par projet (Côte d'Ivoire) — après validation des prix
- [x] Maquette 3D interactive dans le navigateur (structure prête pour Blender)
- [ ] Rendus Blender sur serveur externe (RunPod) — nécessite compte + clé
- [x] Relais app → API ConstructionAgent v1 : parcours création → message → extraction → Informations → run → gate
- [ ] Test du parcours dans l'application depuis un compte réel — attend la création d'un premier compte
- [ ] Brancher : décisions de gates, Memory, programme, plans, BIM/maquette 3D, historique
- [ ] Mise en ligne de l'API (tunnel/serveur) puis remplacement de CA_API_URL / CA_API_KEY

- [x] Socle de sécurité Admin v1 (rôles, permissions serveur, journal immuable, accès audité, filtre des secrets)
- [x] Shell /admin (9 sections, accès contrôlé serveur)
- [ ] Brancher les données réelles des sections Admin + double authentification
- [x] Premier admin désigné

- [ ] Validation réelle Gates : API ConstructionAgent déployée sur Render (en attente : déploiement Render par le propriétaire, puis adresse HTTPS + clé), puis vrai projet relié et contrôle /admin/gates.
