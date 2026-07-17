# Politique de sécurité

Le projet **Gestion Paroissiale** manipule des données personnelles sensibles
(identités, sacrements, dons financiers). La sécurité est prise au sérieux et
les signalements responsables sont les bienvenus.

## Versions supportées

Seule la dernière version publiée (branche `main`) reçoit des correctifs de
sécurité.

| Version | Supportée |
| --- | --- |
| `main` (dernière release) | ✅ |
| 1.0.x | ✅ |
| < 1.0 | ❌ |

## Signaler une vulnérabilité

**Ne signalez jamais une vulnérabilité via une issue, une discussion ou une
pull request publique.**

Canaux de signalement privés, par ordre de préférence :

1. **GitHub Private Vulnerability Reporting** :
   [Security → Report a vulnerability](https://github.com/DESMOND-77/Gestion_paroissiale/security/advisories/new)
2. **E-mail** : `guimapidesmond@outlook.com` avec l'objet
   `[SECURITY] Gestion Paroissiale - <résumé court>`

Merci d'inclure dans le signalement :

- une description de la vulnérabilité et de son impact ;
- les étapes de reproduction (requêtes, payloads, comptes de test) ;
- la version / le commit concerné ;
- le cas échéant, une proposition de correctif.

## Délais de réponse

| Étape | Délai visé |
| --- | --- |
| Accusé de réception | 72 heures |
| Évaluation initiale (validité + gravité) | 7 jours |
| Correctif pour une vulnérabilité critique | 30 jours |
| Correctif pour une vulnérabilité modérée / faible | 90 jours |

Ce projet est maintenu bénévolement : ces délais sont des objectifs, pas des
engagements contractuels. Vous serez tenu·e informé·e de l'avancement.

## Divulgation responsable

- Laissez-nous un délai raisonnable pour corriger avant toute divulgation
  publique (par défaut **90 jours** après l'accusé de réception, négociable).
- N'exploitez pas la vulnérabilité au-delà du strict nécessaire pour la
  démontrer ; n'accédez pas aux données d'autres utilisateurs ; ne dégradez pas
  le service.
- Les signalements de bonne foi respectant ces règles ne feront l'objet
  d'aucune poursuite de notre part.
- Avec votre accord, votre contribution sera créditée dans l'avis de sécurité
  et le `CHANGELOG.md`.

## Politique CVE

Pour toute vulnérabilité confirmée de gravité **modérée ou supérieure**, un
avis de sécurité GitHub (GHSA) sera publié après correction ; une demande de
CVE sera effectuée via GitHub Security Advisories lorsque c'est pertinent.
L'avis mentionnera les versions affectées, la version corrigée et les mesures
de contournement éventuelles.

## Périmètre

Sont notamment dans le périmètre :

- contournement d'authentification / d'autorisation (JWT, RBAC `core/rbac.py`) ;
- injection (SQL, en-têtes, templates d'e-mails) ;
- fuite de données personnelles ou financières ;
- élévation de privilèges entre rôles (fidèle → admin, etc.) ;
- vulnérabilités des flux de vérification d'e-mail / réinitialisation de mot de passe.

Hors périmètre : déni de service volumétrique, ingénierie sociale,
vulnérabilités des dépendances sans preuve d'exploitabilité dans ce projet
(signalez-les quand même, elles seront traitées via Dependabot).
