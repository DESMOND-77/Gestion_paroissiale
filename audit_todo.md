# Audit Todo — Gestion Paroissiale API

Rapport d'audit technique complet analysant le projet. Cette liste de tâches organise les 20 problèmes identifiés (5 critiques, 8 majeurs, 7 mineurs) en 3 phases de correction.

**Audit Date**: Juin 2026  
**Auditor**: Claude Sonnet (Analyse automatisée IA)  
**Référence**: `Audit_Technique_Gestion_paroissiale.pdf`

---

## Phase 1 — Urgences Sécurité (0-1 semaine)

### Critique: P1.1 Rôle admin par défaut

**Fichier**: `accounts/models.py`  
**Problème**: Tout nouvel utilisateur créé via `POST /api/auth/register/` ou `manage.py createsuperuser` reçoit automatiquement le rôle "admin" avec accès COMPLET au système.

```python
# ❌ ACTUEL
role = models.CharField(max_length=20, choices=ROLES_CHOICES, default="admin")
```

**Impact**: Faille de sécurité critique — accès non autorisé à TOUS les modules.

**Correction requise**:

```python
# ✅ CORRIGÉ
default="fidele"  # Le rôle le plus restrictif
```

**Fichier**: `accounts/auth/services.py` (si existant) ou `accounts/views.py`  
**Ajouter dans le service d'inscription**:

```python
user = User.objects.create_user(
    email=email,
    password=password,
    first_name=first_name,
    last_name=last_name,
    role="fidele",  # Explicitly set restrictive role
    is_verified=False
)
```

**Checklist**:

- [ ] Changer `default="admin"` → `default="fidele"` dans User model
- [ ] Ajouter `role="fidele"` dans `create_user()` du service d'inscription
- [ ] Tester: créer nouvel utilisateur, vérifier `role="fidele"`
- [ ] Migration si nécessaire

---

### Critique: P1.2 CORS ouvert à toutes les origines

**Fichier**: `gestion_p/settings.py`  
**Problème**:

```python
# ❌ ACTUEL
CORS_ALLOW_ALL_ORIGINS = True
```

**Impact**: L'API accepte AJAX de n'importe quel site web. En production, cela expose à:

- Attaques CSRF cross-origin
- Filtration de données par des sites malveillants

**Correction requise**:

```python
# ✅ CORRIGÉ
CORS_ALLOWED_ORIGINS = ["https://votre-domaine-front.com"]
```

**Checklist**:

- [ ] Remplacer `CORS_ALLOW_ALL_ORIGINS = True`
- [ ] Définir liste explicite d'origines autorisées
- [ ] En `.env`: `DJANGO_CORS_ORIGINS=https://example.com,https://app.example.com`
- [ ] Lire depuis `.env`: `CORS_ALLOWED_ORIGINS = env("DJANGO_CORS_ORIGINS").split(",")`

---

### Critique: P1.3 Durée d'accès JWT (3 jours → 15 min)

**Fichier**: `gestion_p/settings.py`  
**Problème**: Access token valide 3 jours — trop long pour respecter les normes de sécurité.

```python
# ❌ ACTUEL
ACCESS_TOKEN_LIFETIME = timedelta(days=3)
REFRESH_TOKEN_LIFETIME = timedelta(days=14)

# ✅ RECOMMANDÉ (normes OWASP)
ACCESS_TOKEN_LIFETIME = timedelta(minutes=15)  # Courte durée
REFRESH_TOKEN_LIFETIME = timedelta(days=7)     # Rotation rapide
```

**Impact**:

- Norme OWASP: ≤60 min (idéalement 15 min)
- Actuellement, un token volé reste valide 3 jours (même après déconnexion si Redis n'est pas dispo)
- Impossible de révoquer rapidement un token compromis

**Checklist**:

- [ ] Changer `ACCESS_TOKEN_LIFETIME = timedelta(minutes=15)`
- [ ] Changer `REFRESH_TOKEN_LIFETIME = timedelta(days=7)`
- [ ] Tester: Login → attendre 15 min → endpoint doit retourner 401
- [ ] Vérifier refresh token fonctionnne correctement

---

### Critique: P1.4 Test Redis au chargement de settings.py

**Fichier**: `gestion_p/settings.py`  
**Problème**:

```python
# ❌ ACTUEL
redis_client = redis.from_url(REDIS_URL)
redis_client.ping()  # ← Exécuté à CHAQUE démarrage Django
print("Redis cache configuré avec succès")
```

**Impact**:

- Code exécuté lors de `python manage.py runserver`, `migrate`, `collectstatic`, etc.
- Si Redis n'est pas disponible → **application entière crash** dès le démarrage
- En production: migration échouée = downtime
- Print pollue les logs Gunicorn/Render

**Correction requise**: Déplacer le test vers `AppConfig.ready()` ou un healthcheck séparé.

```python
# ✅ CORRIGÉ - Dans gestion_p/settings.py
# Configurer Redis SANS test immédiat
CACHES = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": REDIS_URL,
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
        }
    }
}

# Pas de redis_client.ping() ici
```

**Faire un healthcheck séparé**: Créer `core/health.py`:

```python
def check_redis_health():
    from django.core.cache import cache
    try:
        cache.set("health_check", "ok", 10)
        return True
    except:
        return False
```

**Utiliser dans un endpoint**: `GET /api/health/` qui retourne l'état de Redis.

**Checklist**:

- [ ] Supprimer `redis_client.ping()` de settings.py
- [ ] Supprimer `print("Redis cache configuré...")`
- [ ] Créer `core/health.py` avec `check_redis_health()`
- [ ] Créer endpoint `GET /api/health/` qui teste Redis
- [ ] Tester: `python manage.py runserver` sans Redis disponible (ne doit pas crasher)

---

### Critique: P1.5 Statement print() de debug en production

**Fichier**: `accounts/auth/views.py`  
**Problème**:

```python
# ❌ EN PRODUCTION
print("Request data:", request)  # Debug print oublié
```

**Impact**:

- Affiche métadonnées complètes de la requête dans logs Gunicorn/Render
- Peut exposer: adresses IP, user-agents, cookies, données sensibles
- Pollution des logs en production

**Localisation**: `accounts/auth/views.py` — fonction inscription

**Correction requise**:

- Supprimer tous les `print()` debug
- Utiliser logger à la place

```python
# ✅ CORRIGÉ
import logging
logger = logging.getLogger('auth')
logger.debug(f"Registration attempt for email: {email}")  # Logué, pas affiché stdout
```

**Checklist**:

- [ ] Chercher tous les `print(` dans le projet: `grep -r "print(" accounts/`
- [ ] Remplacer par `logger.debug()` ou `logger.info()`
- [ ] S'assurer aucun `print()` en views.py / services.py
- [ ] Tester: vérifier aucun output en console sauf logs structurés

---

## Phase 2 — Performance & Architecture (1-4 semaines)

### Majeur: P2.1 Absence de pagination globale

**Fichier**: `gestion_p/settings.py`  
**Problème**: Aucune pagination dans `REST_FRAMEWORK`. Endpoints comme `GET /api/membres/` retournent TOUS les enregistrements.

```python
# ❌ ACTUEL
REST_FRAMEWORK = {
    "DEFAULT_FILTER_BACKENDS": [...],
    "DEFAULT_PAGINATION_CLASS": None,  # ← Aucune pagination!
}
```

**Impact**: Sur une paroisse avec 500+ membres / 2000+ transactions:

- Response > 10 MB
- Temps réponse > 30 secondes
- Client navigateur crash
- Gunicorn timeout

**Correction requise**:

```python
# ✅ CORRIGÉ
REST_FRAMEWORK = {
    ...
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": 50,
}
```

**Checklist**:

- [ ] Ajouter `DEFAULT_PAGINATION_CLASS` et `PAGE_SIZE` à `REST_FRAMEWORK`
- [ ] Tester: `GET /api/membres/?page=1` retourne 50 enregistrements + metadata
- [ ] Vérifier endpoints retournent structure paginée: `{"count": 500, "next": "...", "previous": null, "results": [...]}`

---

### Majeur: P2.2 Index base de données manquants

**Fichier**: `finances/models.py`, `evenements/models.py`, `membres/models.py`  
**Problème**: Champs fréquemment filtrés n'ont PAS d'index. Les requêtes font des FULL TABLE SCAN.

| Champ | Raison du besoin d'index |
|-------|-------------------------|
| `Transaction.date` | Filtres rapport financier (date_debut, date_fin) |
| `Transaction.type` | Filtres recettes/dépenses |
| `Transaction.categorie` | Filtres dons par catégorie |
| `Evenement.date_debut` | Tri et filtrage événements à venir |
| `Evenement.type` | Filtres par type (messe, fête, réunion) |
| `Membre.nom` + `Membre.prenom` | Recherche par nom (très fréquent) |
| `UserActivity.timestamp` | Logs, tri par date |

**Correction requise**: Ajouter `Meta.indexes`:

```python
# ✅ CORRIGÉ - finances/models.py
class Transaction(models.Model):
    date = models.DateField()
    type = models.CharField(max_length=20, choices=TRANSACTION_TYPES)
    categorie = models.CharField(max_length=50)
    # ...
    
    class Meta:
        indexes = [
            models.Index(fields=["date"], name="transaction_date_idx"),
            models.Index(fields=["type", "date"], name="transaction_type_date_idx"),
            models.Index(fields=["categorie"], name="transaction_categorie_idx"),
        ]
```

**Checklist**:

- [ ] `finances/models.py`: Ajouter indexes sur Transaction.date, type, categorie
- [ ] `evenements/models.py`: Ajouter indexes sur Evenement.date_debut, type
- [ ] `membres/models.py`: Ajouter indexes sur Membre.nom, prenom (compound index)
- [ ] Créer migration: `python manage.py makemigrations`
- [ ] Appliquer: `python manage.py migrate`
- [ ] Tester performance: requête filtrée avant/après

---

### Majeur: P2.3 Requêtes N+1 — select_related/prefetch_related manquants

**Fichier**: `groupes/views.py`, `membres/views.py`, `evenements/views.py`, `librairie/views.py`  
**Problème**: ViewSets font des requêtes N+1 (une requête par objet lié).

| Fichier | Problème |
|---------|---------|
| `groupes/views.py` | Pas de `select_related` sur `Groupe` |
| `membres/views.py` | Pas de `select_related('user', 'groupe')` |
| `evenements/views.py` | Pas de `prefetch_related('participations')` |
| `librairie/views.py` | Pas de `select_related` sur `Vente.article` |

**Exemple du problème**:

```python
# ❌ MAUVAIS — N+1 requêtes
class GroupeViewSet(viewsets.ModelViewSet):
    queryset = Groupe.objects.all()  # 1 requête
    # Dans la sérialisation: 1 requête par groupe pour accéder à user
```

**Correction requise**:

```python
# ✅ CORRIGÉ
class GroupeViewSet(viewsets.ModelViewSet):
    def get_queryset(self):
        return Groupe.objects.select_related('user')  # 1 requête + join

class MembreViewSet(viewsets.ModelViewSet):
    def get_queryset(self):
        return Membre.objects.select_related('user', 'groupe')

class EvenementViewSet(viewsets.ModelViewSet):
    def get_queryset(self):
        return Evenement.objects.prefetch_related('participations')

class VenteViewSet(viewsets.ModelViewSet):
    def get_queryset(self):
        return Vente.objects.select_related('article')
```

**Checklist**:

- [ ] `groupes/views.py`: Ajouter `select_related('user')`
- [ ] `membres/views.py`: Ajouter `select_related('user', 'groupe')`
- [ ] `evenements/views.py`: Ajouter `prefetch_related('participations')`
- [ ] `librairie/views.py`: Ajouter `select_related('article')` sur Vente
- [ ] `finances/views.py`: Vérifier si relations à optimiser
- [ ] Tester: `python manage.py runserver --verbosity 2` avec requête, vérifier nombre de SQL queries

---

### Majeur: P2.4 Rate limiting incomplet

**Fichier**: `gestion_p/settings.py`  
**Problème**: Seul `UserRegistrationView` a `AnonRateThrottle`. Les endpoints critiques (`/api/auth/login/`, `/api/auth/password-reset/`) n'ont PAS de limitation.

**Impact**: Attaque par force brute sur login / email enumeration.

**Correction requise**: Ajouter throttle sur endpoints critiques.

```python
# gestion_p/settings.py
REST_FRAMEWORK = {
    ...
    "DEFAULT_THROTTLE_CLASSES": [
        "rest_framework.throttling.AnonRateThrottle",
        "rest_framework.throttling.UserRateThrottle",
    ],
    "DEFAULT_THROTTLE_RATES": {
        "anon": "100/hour",
        "user": "1000/hour",
    }
}
```

```python
# accounts/auth/views.py
class LoginView(BaseView):
    throttle_classes = [AnonRateThrottle]  # Max 100 requêtes/heure anonyme
    
class PasswordResetView(BaseView):
    throttle_classes = [AnonRateThrottle]  # Protéger contre enumeration emails
```

**Checklist**:

- [ ] Configurer `DEFAULT_THROTTLE_CLASSES` et `DEFAULT_THROTTLE_RATES`
- [ ] Ajouter `throttle_classes = [AnonRateThrottle]` aux views login + password-reset
- [ ] Tester: faire 101 requêtes login rapidement → 429 Too Many Requests

---

### Majeur: P2.5 Couche service incohérente

**Problème**: Seul le module `accounts` a une vraie couche service (`auth/services.py`, `verification/services.py`). Les autres modules mélangent la logique métier dans les views.

**Recommandation architecturale**:

- Extraire la logique métier des `views.py` → fichiers `services.py` dans chaque module
- Les ViewSets ne doivent gérer que HTTP: validation, appel service, formatage réponse

**Exemple - Finances**:

```python
# ✅ finances/services.py (À CRÉER)
class FinanceService:
    @staticmethod
    def calculer_rapport(date_debut, date_fin):
        recettes = Transaction.objects.filter(
            type='recette', date__range=[date_debut, date_fin]
        ).aggregate(Sum('montant'))
        depenses = Transaction.objects.filter(
            type='depense', date__range=[date_debut, date_fin]
        ).aggregate(Sum('montant'))
        return {
            'recettes': recettes,
            'depenses': depenses,
            'solde': recettes - depenses
        }
```

```python
# finances/views.py (SIMPLIFIÉ)
class FinanceViewSet(viewsets.ModelViewSet):
    def rapport(self, request):
        service = FinanceService()
        data = service.calculer_rapport(request.GET['date_debut'], request.GET['date_fin'])
        return standardized_response(success=True, data=data)
```

**Checklist**:

- [ ] Créer `membres/services.py` avec logique métier
- [ ] Créer `groupes/services.py`
- [ ] Créer `evenements/services.py`
- [ ] Créer `finances/services.py` (important: calcul rapport)
- [ ] Créer `librairie/services.py`
- [ ] Simplifier `views.py` correspondants
- [ ] Ajouter imports dans chaque app's `__init__.py`

---

### Majeur: P2.6 Docker Compose serveur de développement en conteneur

**Fichier**: `docker-compose.yaml`  
**Problème**:

```yaml
# ❌ ACTUEL
command: python manage.py runserver 0.0.0.0:8000
```

**Impact**:

- `runserver` est single-threaded, pas de gestion signaux, crash handling faible
- **Ne doit JAMAIS être en production**
- Pas de Dockerfile → build absent
- Aucun multi-worker

**Correction requise**:

1. Créer `Dockerfile`
2. Utiliser Gunicorn avec workers
3. Ajouter health checks

```dockerfile
# Dockerfile
FROM python:3.14-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
EXPOSE 8000
CMD ["gunicorn", "gestion_p.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "4"]
```

```yaml
# docker-compose.yaml — CORRIGÉ
version: "3.8"
services:
  web:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DEBUG=False
      - DJANGO_ALLOWED_HOSTS=*
    depends_on:
      - redis
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/api/health/"]
      interval: 30s
      timeout: 10s
      retries: 3
  
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
```

**Checklist**:

- [ ] Créer `Dockerfile` avec Gunicorn
- [ ] Mettre à jour `docker-compose.yaml`: utiliser `build:` + Gunicorn
- [ ] Ajouter healthcheck
- [ ] Tester: `docker-compose up` → service accessible sur `http://localhost:8000`

---

### Majeur: P2.7 Absence de service layer dans 5 modules

*(Voir P2.5 — créer services.py pour membres, groupes, evenements, finances, librairie)*

---

### Majeur: P2.8 Channels Redis en double dans config Redis

**Fichier**: `gestion_p/settings.py`  
**Problème**: `CHANNEL_LAYERS` utilise Redis mais `channels` + `channels_redis` ne sont PAS dans `requirements.txt`.

```python
# ❌ ACTUEL
CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels_redis.core.RedisChannelLayer",
        "CONFIG": {
            "hosts": [("127.0.0.1", 6379)],
        },
    },
}
# Mais channels_redis n'est pas installé !
```

**Correction requise**:

- OU supprimer la config `CHANNEL_LAYERS` (si WebSockets pas utilisés)
- OU ajouter à `requirements.txt`: `channels==4.0.0` + `channels-redis==4.1.0`

**Checklist**:

- [ ] Déterminer: avez-vous besoin WebSockets?
- [ ] OUI: Ajouter `channels==4.0.0` et `channels-redis==4.1.0` à requirements.txt
- [ ] NON: Supprimer la section `CHANNEL_LAYERS` entière de settings.py
- [ ] Supprimer `ASGI_APPLICATION = "gestion_p.asgi.application"` si pas WebSockets

---

## Phase 3 — Qualité & Tests (1-2 mois)

### Mineur: P3.1 Slash final manquant sur `/api/auth/token/refresh`

**Fichier**: `accounts/urls.py`  
**Problème**: Tous les endpoints sauf un ont trailing slash.

```python
# ❌ ACTUEL
path('auth/token/refresh', ...)  # Pas de slash final
```

**Correction requise**:

```python
# ✅ CORRIGÉ
path('auth/token/refresh/', ...)  # Avec slash
```

**Checklist**:

- [ ] Ajouter `/` final à `refresh`
- [ ] Tester: `POST /api/auth/token/refresh/` fonctionne

---

### Mineur: P3.2 Aucune versioning API

**Fichier**: `gestion_p/settings.py`, `gestion_p/urls.py`  
**Problème**: Pas de préfixe `/api/v1/`. Évolutions futures cassent les clients.

**Correction requise**:

```python
# urls.py
urlpatterns = [
    path('api/v1/', include([
        path('auth/', include('accounts.urls')),
        path('membres/', include('membres.urls')),
        ...
    ])),
]
```

**Checklist**:

- [ ] Ajouter `/v1/` dans tous les chemins URL
- [ ] Tester: endpoints accessibles sur `/api/v1/...`
- [ ] Documenter: rupture de compatibilité avec anciens clients

---

### Mineur: P3.3 Fichiers test vides (63 octets)

**Fichier**: Tous les `tests.py` de chaque app  
**Problème**: Seul `import Django` — aucun test.

```python
# ❌ ACTUEL - accounts/tests.py, membres/tests.py, etc.
from django.test import TestCase
# Vide
```

**Impact**: Couverture de tests < 1%, risque majeur de regression.

**Phase 3.1 — Écrire tests**:

1. Tests d'authentification: inscription, connexion, logout, refresh, blocage après 5 tentatives
2. Tests permissions: chaque rôle ne peut accéder qu'à ses ressources
3. Tests sécurité: injection SQL, XSS sur paramètres
4. Tests métier: calcul rapport finance, validations modèles
5. Tests librairie: décrément stock après vente, alerte stock faible

Exemple test:

```python
# accounts/tests.py
from django.test import TestCase
from django.contrib.auth import get_user_model

User = get_user_model()

class RegistrationTestCase(TestCase):
    def test_user_registration_success(self):
        """Un nouvel utilisateur doit avoir role='fidele'"""
        response = self.client.post('/api/auth/register/', {
            'email': 'test@example.com',
            'password': 'securepass123',
            'first_name': 'Jean',
            'last_name': 'Dupont',
        })
        self.assertEqual(response.status_code, 201)
        user = User.objects.get(email='test@example.com')
        self.assertEqual(user.role, 'fidele')  # ← Vérifier rôle par défaut
```

**Checklist**:

- [ ] Configurer pytest: `pytest.ini` ou `pyproject.toml` avec `DJANGO_SETTINGS_MODULE`
- [ ] Installer: `pip install pytest-django==4.8.0 pytest-cov==5.0.0`
- [ ] Écrire tests auth (P3.1)
- [ ] Écrire tests permissions (P3.2)
- [ ] Écrire tests sécurité (P3.3)
- [ ] Écrire tests métier: finances, librairie
- [ ] Atteindre 80% couverture: `pytest --cov`

---

### Mineur: P3.4 Code mort & commentaires obsolètes

**Fichier**: `accounts/auth/services.py`, `accounts/auth/views.py`, `accounts/urls.py`, `accounts/core/jwt_utils.py`, `settings.py`

**Code mort à supprimer**:

| Fichier | Ligne | Problème |
|---------|-------|---------|
| `accounts/auth/services.py` | 66-80 | Blocs entiers commentés: gestion rôle, phone_number |
| `accounts/auth/views.py` | Imports commentés | Anciens ViewSets commentés |
| `accounts/urls.py` | Lignes 1, 10, 14 | Router et routes commentées |
| `accounts/core/jwt_utils.py` | 48-66 | print() commentés pour debug |
| `settings.py` | LOGGING, DATABASE | Commentaires handler console, DATABASE |

**Checklist**:

- [ ] Supprimer blocs commentés dans `accounts/auth/services.py`
- [ ] Supprimer imports commentés dans `accounts/auth/views.py`
- [ ] Nettoyer `accounts/urls.py`
- [ ] Supprimer tous les `print()` commentés
- [ ] Supprimer commentaires DATABASE, LOGGING obsolètes

---

### Mineur: P3.5 Bugs Python identifiés

#### P3.5.1 Double définition de BASE_DIR

**Fichier**: `gestion_p/settings.py` (lignes 14 et 23)

```python
# ❌ ACTUEL
BASE_DIR = Path(__file__).resolve().parent.parent  # Ligne 14
BASE_DIR = Path(__file__).resolve().parent.parent  # Ligne 23 — DOUBLON
```

**Correction**:

```python
# ✅ CORRIGÉ
BASE_DIR = Path(__file__).resolve().parent.parent  # Garder une seule fois
```

#### P3.5.2 Double docstring dans TokenManager

**Fichier**: `accounts/core/jwt_utils.py`

```python
# ❌ ACTUEL
class TokenManager:
    """Gestion des tokens JWT."""
    """Gestion des tokens JWT avec Redis."""  # DOUBLON
```

**Correction**: Garder une seule docstring claire.

#### P3.5.3 Import double de django.contrib.admin

**Fichier**: `gestion_p/urls.py`

```python
# ❌ ACTUEL
from django.contrib import admin  # Ligne 2
from django.contrib import admin  # Ligne 7 — DOUBLON
```

**Correction**: Supprimer un import.

#### P3.5.4 Import direct de settings non idiomatique

**Fichier**: `accounts/auth/services.py`

```python
# ❌ MAUVAIS (couplage fort)
from gestion_p import settings as pj_settings
```

**Correction**:

```python
# ✅ CORRECT
from django.conf import settings
```

**Checklist**:

- [ ] Supprimer `BASE_DIR` doublon
- [ ] Fusionner docstrings TokenManager
- [ ] Supprimer import `admin` doublon
- [ ] Remplacer imports directs par `from django.conf import settings`

---

### Mineur: P3.6 User model REQUIRED_FIELDS manquant

**Fichier**: `accounts/models.py`  
**Problème**: Le modèle User personnalisé étend `AbstractBaseUser` mais ne définit pas `REQUIRED_FIELDS`.

```python
# ❌ ACTUEL
class User(AbstractBaseUser, PermissionsMixin):
    USERNAME_FIELD = 'email'
    # REQUIRED_FIELDS manquant
```

**Impact**: `python manage.py createsuperuser` ne demande pas `first_name`, `last_name`.

**Correction requise**:

```python
# ✅ CORRIGÉ
class User(AbstractBaseUser, PermissionsMixin):
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name']  # ← Ajouter cette ligne
```

**Checklist**:

- [ ] Ajouter `REQUIRED_FIELDS = ['first_name', 'last_name']` à User model
- [ ] Tester: `python manage.py createsuperuser` demande les champs

---

### Mineur: P3.7 Configuration ASGI / WebSockets non fonctionnelle

**Fichier**: `gestion_p/settings.py`, `gestion_p/asgi.py`  
**Problème**: `ASGI_APPLICATION = "gestion_p.asgi.application"` est configurée mais:

- `asgi.py` utilise l'ASGI Django standard sans intégration Channels
- Aucun WebSocket n'est défini dans le projet
- Cela peut causer `ModuleNotFoundError` si `channels_redis` n'est pas installé

**Correction**: Déterminer si WebSockets sont nécessaires.

- **OUI**: Installer `channels` + `channels-redis`, configurer consumer WebSocket
- **NON**: Supprimer `ASGI_APPLICATION`, rester en WSGI (Gunicorn)

**Checklist**:

- [ ] Clarifier: besoin WebSockets?
- [ ] Si OUI: `pip install channels channels-redis`, configurer consumer
- [ ] Si NON: Supprimer `ASGI_APPLICATION` de settings

---

### Mineur: P3.8 Headers sécurité HTTP manquants

**Fichier**: `gestion_p/settings.py`  
**Problème**: Aucun header de sécurité HTTP n'est configuré.

```python
# ✅ À AJOUTER à settings.py
SECURE_HSTS_SECONDS = 31536000  # 1 an
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_BROWSER_XSS_FILTER = True
X_FRAME_OPTIONS = "DENY"
SECURE_SSL_REDIRECT = True  # En production uniquement
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
```

**Middleware requis**:

```python
MIDDLEWARE = [
    # ... autres middlewares
    "django.middleware.security.SecurityMiddleware",  # Doit être en premier
]
```

**Checklist**:

- [ ] Ajouter tous les paramètres `SECURE_*` listés
- [ ] Vérifier `SecurityMiddleware` en première position
- [ ] Tester: `curl -I http://localhost:8000` → vérifier headers `Strict-Transport-Security`, `X-Content-Type-Options`, etc.

---

### Mineur: P3.9 Incohérence nom log

**Fichier**: `README.md` mention `gestion_paroisse.log`, mais `settings.py` mentionne `gestionparoisse.log` (sans underscore).

**Correction**: Standardiser sur `gestionparoisse.log`.

**Checklist**:

- [ ] Vérifier `LOGGING['handlers']['file']['filename']` dans settings
- [ ] Mettre à jour README si nécessaire

---

### Mineur: P3.10 Absence de versioning et changelog

**Fichier**: Projet entier  
**Problème**: Pas de CHANGELOG.md, pas de versioning (tags git), pas de guide contribution.

**À créer**:

- `CHANGELOG.md` — suivi des versions
- `CONTRIBUTING.md` — guide pour contributeurs
- Git tags avec format `v1.0.0`

**Checklist**:

- [ ] Créer `CHANGELOG.md` avec format standard
- [ ] Créer `CONTRIBUTING.md`
- [ ] Tagger version actuelle: `git tag v1.0.0`

---

## Configuration de test recommandée (Phase 3)

Pour atteindre 80% couverture:

```ini
# pytest.ini
[pytest]
DJANGO_SETTINGS_MODULE = gestion_p.settings
python_files = tests.py test_*.py *_tests.py
addopts = --cov=. --cov-report=html --cov-report=term-missing --cov-fail-under=80
testpaths = .
```

```txt
# requirements-dev.txt
pytest-django==4.8.0
pytest-cov==5.0.0
factory-boy==3.3.0
faker==24.0.0
```

**Commandes**:

```bash
pytest --cov               # Voir couverture globale
pytest --cov-report=html   # Rapport HTML détaillé (htmlcov/index.html)
pytest -k auth             # Tests seulement auth
pytest -v                  # Verbose
```

---

## Documentation manquante (Phase 3)

Voir `README.md` → sections à améliorer:

- [ ] ❌ Aucun badge (version, build status, coverage)
- [ ] ❌ Aucun exemple curl/JSON de requête/réponse
- [ ] ❌ Pas de CHANGELOG
- [ ] ❌ Pas de guide CONTRIBUTING
- [ ] ❌ Pas de LICENSE

**À ajouter**:

1. Badges: `[![Build](...)` `[![Coverage](...)` `[![Python](...)` `[![Django](...)`
2. Exemples d'usage: curl, JSON
3. CHANGELOG.md
4. CONTRIBUTING.md
5. LICENSE (MIT ou GPL)

---

## Résumé de priorités

### 🔴 URGENT (Jour 1)

- [ ] P1.1: Rôle admin par défaut
- [ ] P1.2: CORS ouvert
- [ ] P1.3: JWT durée
- [ ] P1.4: Redis ping au startup
- [ ] P1.5: print() debug

### 🟠 IMPORTANT (Semaine 1)

- [ ] P2.1: Pagination globale
- [ ] P2.2: Index BD
- [ ] P2.3: select_related/prefetch_related
- [ ] P2.4: Rate limiting
- [ ] P2.5: Service layer cohérente

### 🟡 SOUHAITABLE (Mois 1-2)

- [ ] P3.1-3.10: Tests, qualité, documentation

---

## Liens vers fichiers

- `accounts/models.py` — User model
- `accounts/auth/services.py` — Service inscription
- `accounts/auth/views.py` — Views auth
- `gestion_p/settings.py` — Configuration principal
- `gestion_p/urls.py` — URLs
- `docker-compose.yaml` — Composition Docker
- `requirements.txt` — Dépendances

---

**Généré par**: Audit Automatisé IA (Claude Sonnet)  
**Date**: Juin 2026  
**Mise à jour**: À mettre à jour après chaque correction
