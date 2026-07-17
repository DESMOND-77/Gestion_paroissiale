---
name: 🐛 Rapport de bug
about: Signaler un dysfonctionnement de l'API
title: "[Bug] "
labels: bug
assignees: DESMOND-77
---

> ⚠️ **Vulnérabilité de sécurité ?** N'ouvrez PAS d'issue publique — suivez
> [SECURITY.md](../../SECURITY.md).

## Description

Description claire et concise du problème.

## Étapes de reproduction

1. Appeler `POST /api/v1/...` avec le corps `{...}`
2. ...
3. Observer l'erreur

```bash
# Exemple de requête curl reproduisant le problème
curl -X POST http://127.0.0.1:8000/api/v1/... \
  -H "Content-Type: application/json" \
  -d '{}'
```

## Comportement attendu

Ce qui devrait se passer.

## Comportement observé

Ce qui se passe réellement (code HTTP, corps de la réponse standardisée).

```json
{
  "success": false,
  "error": "..."
}
```

## Captures d'écran

Le cas échéant (Swagger, admin, e-mails reçus).

## Environnement

- Déploiement : [local / docker-compose / Render]
- OS : [ex. Ubuntu 24.04]
- Python : [ex. 3.14]
- Base de données : [MySQL / MariaDB / PostgreSQL / SQLite]
- Redis : [oui / non]
- Version / commit : [ex. v1.0.0 ou SHA]

## Logs

Extraits pertinents de `logs/gestionparoisse.log`, `logs/auth.log` ou de la
console (**masquer les secrets, jetons et données personnelles**).

```text
(coller les logs ici)
```

## Contexte additionnel

Toute autre information utile.
