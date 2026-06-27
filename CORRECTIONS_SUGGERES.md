# CORRECTIONS SUGGÉRÉES: Diffs pour Chaque Fichier

## 1. accounts/serializers.py - CORRECTION PRIORITAIRE

### ✅ Changement 1.1: UserRegistrationSerializer
```diff
class UserRegistrationSerializer(serializers.Serializer):
    """Serializer for user registration"""
    email = serializers.EmailField(required=True, help_text="Email de l'utilisateur")
    password = serializers.CharField(required=True, min_length=8, help_text="Mot de passe (minimum 8 caractères)")
-   first_name = serializers.CharField(required=True, help_text="Prénom de l'utilisateur")
-   last_name = serializers.CharField(required=True, help_text="Nom de l'utilisateur")
+   prenom = serializers.CharField(required=True, help_text="Prénom de l'utilisateur")
+   nom = serializers.CharField(required=True, help_text="Nom de l'utilisateur")
```

### ✅ Changement 1.2: UserSerializer
```diff
class UserSerializer(serializers.ModelSerializer):
    profile_picture_url = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            "id",
            "email",
-           "first_name",
-           "last_name",
+           "prenom",
+           "nom",
            "phone_number",
            "role",
            "sacrement",
            "username",
            "profile_picture",
            "profile_picture_url",
            "is_active",
            "is_verified",
            "created_at",
            "last_login",
        ]
```

### ✅ Changement 1.3: UserUpdateSerializer
```diff
class UserUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
-       fields = ["first_name", "last_name", "phone_number"]
+       fields = ["prenom", "nom", "phone_number"]
```

---

## 2. accounts/auth/services.py - CORRECTION PRIORITAIRE

### ✅ Changement 2.1: AuthenticationService.register()
```diff
@staticmethod
def register(email, password, first_name, last_name, request_meta=None):
    from accounts.verification.services import EmailVerificationService

    if not email or not password:
        return False, "Email et mot de passe sont requis.", 400

    # Log registration attempt
    if request_meta:
        logger.info(
            f"Registration attempt from IP: {request_meta.get('REMOTE_ADDR')} "
        )
    try:

        if User.objects.filter(email=email).exists():
            return (
                False,
                {
                    "success": False,
                    "error": "Un utilisateur avec cet email existe déjà.",
                },
                400,
            )
        # valider la complexité du mot de passe
        try:
            validate_password(password)
        except ValidationError as e:
            return (
                False,
                {
                    "success": False,
                    "error": f"Mot de passe invalide: {'; '.join(e.messages)}",
                },
                400,
            )
        # créer l'utilisateur
        user = User.objects.create_user(
            email=email,
            password=password,
-           first_name=first_name,
-           last_name=last_name,
+           nom=last_name,           # nom = last_name
+           prenom=first_name,       # prenom = first_name
            is_verified=False,
        )

        # reste du code...
```

---

## 3. accounts/admin.py - CORRECTION PRIORITAIRE

### ✅ Changement 3.1: UserAdmin - list_display
```diff
class UserAdmin(BaseUserAdmin):
    # model = User
    list_display = (
        "nom",
        "email",
-       "sacrement",        # ❌ Cette champ est dans Membre
        "role",
        "is_staff",
        "is_superuser",
    )
```

### ✅ Changement 3.2: UserAdmin - fieldsets (Personal info)
```diff
fieldsets = (
    (None, {"fields": ("username", "password")}),
    (
        "Personal info",
        {
            "fields": (
                "prenom",
                "nom",
                "email",
-               "sacrement",         # ❌ Dans Membre
                "profile_picture",
                "phone_number",
-               "quartier",          # ❌ Dans Membre
                "role",
            )
        },
    ),
```

### ✅ Changement 3.3: UserAdmin - fieldsets (Permissions)
```diff
    (
        "Permissions",
        {
            "fields": (
                "is_active",
                "is_staff",
                "is_superuser",
-               "groupe",            # ❌ Dans Membre
                "user_permissions",
            )
        },
    ),
```

### ✅ Changement 3.4: UserAdmin - add_fieldsets
```diff
add_fieldsets = (
    (
        None,
        {
            "classes": ("wide",),
            "fields": (
                "nom",
                "email",
-               "sacrement",         # ❌ Dans Membre
                "password1",
                "password2",
                'role',
                "is_active",
                "is_staff",
                "is_superuser",
            ),
        },
    ),
)
```

### ✅ Changement 3.5: UserAdmin - search_fields
```diff
-search_fields = ('email', 'nom', 'prenom', 'quartier', "sacrement")
+search_fields = ('email', 'nom', 'prenom')  # Retirer quartier et sacrement
```

---

## 4. membres/serializers.py - CORRECTION PRIORITAIRE

### ✅ Changement 4.1: Remover champs inexistants OU les ajouter à Membre

**Option A: Retirer du serializer**
```diff
class MembreSerializer(serializers.ModelSerializer):
    nom_complet = serializers.ReadOnlyField()
    groupe_nom = serializers.SerializerMethodField()

    class Meta:
        model = Membre
        fields = [
            "id", "user", "nom", "prenom", "nom_complet", "date_naissance",
-           "sexe", "telephone", "email", "quartier", "date_inscription",
+           "sexe", "quartier",     # Retirer telephone, email, date_inscription
            "est_baptise", "est_confirme", "groupe", "groupe_nom",
        ]
        read_only_fields = ["nom_complet"]  # Retirer "date_inscription"
```

**Option B: Ajouter SerializerMethodField**
```python
class MembreSerializer(serializers.ModelSerializer):
    nom_complet = serializers.ReadOnlyField()
    groupe_nom = serializers.SerializerMethodField()
    email = serializers.SerializerMethodField()  # ✅ Accéder via user
    telephone = serializers.SerializerMethodField()  # ✅ Accéder via user
    date_inscription = serializers.SerializerMethodField()  # ✅ Accéder via user

    class Meta:
        model = Membre
        fields = [
            "id", "user", "nom", "prenom", "nom_complet", "date_naissance",
            "sexe", "telephone", "email", "quartier", "date_inscription",
            "est_baptise", "est_confirme", "groupe", "groupe_nom",
        ]
        read_only_fields = ["date_inscription", "nom_complet", "email", "telephone"]

    def get_groupe_nom(self, obj):
        return obj.groupe.nom if obj.groupe else None

    def get_email(self, obj):
        return obj.user.email if obj.user else None

    def get_telephone(self, obj):
        return obj.user.phone_number if obj.user else None

    def get_date_inscription(self, obj):
        return obj.user.created_at if obj.user else None
```

---

## 5. librairie/views.py - CORRECTION PRIORITAIRE

### ✅ Changement 5.1: VenteViewSet.create()
```diff
def create(self, request, *args, **kwargs):
    logger.info(f"Creating vente by user {request.user}: {request.data}")
    serializer = self.get_serializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    vente = serializer.save(enregistre_par=request.user)
    logger.debug(f"Vente {vente.id} saved, creating transaction")

    try:
        if serializer.is_valid:
            article = self.article_model.objects.get(id=request.data.get("article"))
            quantite = request.data.get("quantite")
            montant = article.prix_unitaire * quantite

            transaction = self.transaction_model.objects.create(
                categorie="librairie",
                type="recette",
-               description=f"Vente de l'article: {article.nom}, Qte: {quantite}, par: {request.user.first_name}",
+               description=f"Vente de l'article: {article.nom}, Qte: {quantite}, par: {request.user.prenom}",
                montant=montant,
                date=datetime.datetime.now(),
                enregistre_par=request.user,
                membre=self.membre_model.objects.get(id=request.data.get("membre"))
            )
```

---

## 6. templates/emails/password_reset.html - CORRECTION SECONDAIRE

### ✅ Changement 6.1: Utiliser prenom au lieu de first_name
```diff
{% extends "emails/base_email.html" %}

{% block content %}
- <p>Hello {{ user.first_name|default:"there" }},</p>
+ <p>Hello {{ user.prenom|default:"there" }},</p>
  <p>You have requested to reset your password. Click the link below to reset it:</p>
```

---

## 7. accounts/auth/views.py - CORRECTION PRIORITAIRE

### ✅ Changement 7.1: UserRegistrationView.post()
```diff
def post(self, request):
    try:
        email = request.data.get("email")
        password = request.data.get("password")
-       first_name = request.data.get("first_name")
-       last_name = request.data.get("last_name")
+       first_name = request.data.get("prenom")    # Récupérer depuis les bons champs
+       last_name = request.data.get("nom")

        # use service layer for registration logic
        success, response_data, status_code = AuthenticationService.register(
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name,
            request_meta=request.META,
        )
```

---

## 8. membres/signals.py - CORRECTION ROBUSTESSE (Optionnel)

### ⚠️ Changement 8.1: Ajouter gestion d'erreur
```diff
@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def update_membre_for_user(sender, instance, created, **kwargs):
    """
    Signal pour synchroniser les informations du User vers le Membre.
    """
    if not created:
        try:
-           membre = instance.membre
+           membre = instance.membre  # Peut lever DoesNotExist
            # Mettre à jour les infos du membre à partir du user
            if membre.nom != instance.nom or membre.prenom != instance.prenom:
                membre.nom = instance.nom
                membre.prenom = instance.prenom
                membre.save()
                logger.debug(f"Infos du Membre synchronisées pour: {instance.email}")
        except Membre.DoesNotExist:
            # Si le Membre n'existe pas, le créer
            try:
                Membre.objects.create(
                    user=instance,
                    nom=instance.nom,
                    prenom=instance.prenom
                )
                logger.info(f"Membre créé (rattrappage) pour l'utilisateur: {instance.email}")
            except Exception as e:
                logger.error(f"Erreur lors de la création du Membre pour {instance.email}: {str(e)}")
        except Exception as e:
            logger.error(f"Erreur lors de la synchronisation du Membre pour {instance.email}: {str(e)}")
            # ✅ Ajouter: Ne pas faire échouer l'update de User
            pass
```

---

## 📋 Résumé des Changements par Fichier

| Fichier | Changements | Type |
|---------|-------------|------|
| accounts/serializers.py | 3 changements (first_name→prenom, last_name→nom) | Refactorisation |
| accounts/auth/services.py | 2 changements (create_user params) | Refactorisation |
| accounts/auth/views.py | 2 changements (getData mapping) | Refactorisation |
| accounts/admin.py | 5 changements (retirer champs Membre) | Suppression |
| membres/serializers.py | 2 options pour 3 champs | Refactorisation/Ajout |
| librairie/views.py | 1 changement (first_name→prenom) | Remplacement |
| templates/emails/password_reset.html | 1 changement (first_name→prenom) | Remplacement |
| membres/signals.py | 1 changement (gestion d'erreur) | Robustesse |

---

## ✅ Étapes d'Application

1. Commencer par **accounts/serializers.py** - Impact sur tout le système
2. Puis **accounts/auth/services.py** - Affecte la création d'utilisateurs
3. Puis **accounts/admin.py** - Affecte l'interface d'administration
4. Puis **membres/serializers.py** - Affecte l'API Membres
5. Puis **librairie/views.py** et **templates/emails/password_reset.html**
6. Enfin, valider avec les **tests**

---

## 🧪 Tests de Vérification

```python
# Test 1: Création d'utilisateur
def test_user_creation():
    user = User.objects.create_user(
        email="test@example.com",
        password="SecurePass123",
        nom="Dupont",           # ✅ Doit marcher
        prenom="Jean",         # ✅ Doit marcher
    )
    assert user.nom == "Dupont"
    assert user.prenom == "Jean"
    assert user.nom_complet == "Jean Dupont"
    assert user.full_name == "Jean Dupont"

# Test 2: Registration API
def test_registration_api():
    data = {
        "email": "new@example.com",
        "password": "SecurePass123",
        "prenom": "Marie",     # ✅ Doit marcher
        "nom": "Martin",       # ✅ Doit marcher
    }
    response = client.post('/api/auth/register', data)
    assert response.status_code == 201

# Test 3: Serializer
def test_user_serializer():
    user = User.objects.create_user(...)
    serializer = UserSerializer(user)
    assert 'prenom' in serializer.data  # ✅ Doit marcher
    assert 'nom' in serializer.data     # ✅ Doit marcher

# Test 4: Membre creation
def test_membre_creation():
    user = User.objects.create_user(...)
    # Signal devrait créer Membre automatiquement
    assert hasattr(user, 'membre')
    assert user.membre.nom == user.nom
    assert user.membre.prenom == user.prenom
```

