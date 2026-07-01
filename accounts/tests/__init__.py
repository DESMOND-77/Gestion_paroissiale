"""Suite de tests unitaires pour l'authentification (accounts).

Couvre : modèle User, inscription, connexion, tokens (refresh/validate),
déconnexion, changement de mot de passe, vérification d'email et
réinitialisation du mot de passe, ainsi que la couche service.

Tous les tests s'exécutent avec un cache local (LocMemCache), un backend
email en mémoire, et sans dépendance à Redis (client Redis neutralisé).
"""
