# Pull Request

## Résumé

Décrivez le changement et sa motivation. Liez l'issue correspondante :

Closes #

## Type de changement

- [ ] 🐛 Correction de bug (changement non cassant qui corrige un problème)
- [ ] ✨ Nouvelle fonctionnalité (changement non cassant qui ajoute une capacité)
- [ ] 💥 Breaking change (changement qui casse un comportement existant)
- [ ] ♻️ Refactorisation (sans changement de comportement)
- [ ] 📝 Documentation uniquement
- [ ] 🔧 CI / outillage / dépendances

## Checklist

- [ ] Ma branche suit la convention (`feature/…`, `fix/…`) et les commits le format Conventional Commits
- [ ] `ruff check .` et `ruff format --check .` passent sans erreur
- [ ] `python manage.py check` passe sans erreur
- [ ] `python manage.py test` passe (tests ajoutés pour la nouvelle logique)
- [ ] Migrations générées et committées **séparément** si les modèles changent
- [ ] Entrée ajoutée dans `fixs.md` (si correction de bug - Problème / Cause / Solution / Fichiers)
- [ ] `CHANGELOG.md` mis à jour (section « Non publié ») pour un changement notable
- [ ] Documentation mise à jour (README, `docs/`, docstrings Swagger)
- [ ] Réponses au format standardisé (`standardized_response()`) et permissions vérifiées

## Tests

Comment ce changement a-t-il été vérifié ? (commandes, scénarios, captures de
réponses API)

```bash
python manage.py test <app>
```

## Captures d'écran

Le cas échéant (Swagger, admin, e-mails).

## Breaking changes

Détaillez tout changement cassant (endpoints modifiés, champs renommés,
migrations destructives) et le chemin de migration pour les clients.
