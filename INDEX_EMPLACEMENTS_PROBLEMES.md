# INDEX: Emplacements Exacts des Problèmes

## 🔍 Fichiers Affectés par Catégorie

---

## 1️⃣ CHAMPS INEXISTANTS DANS SERIALIZERS

### accounts/serializers.py
```
Ligne 12-13: UserRegistrationSerializer - fields 'first_name', 'last_name'
❌ first_name = serializers.CharField(...)
❌ last_name = serializers.CharField(...)
✅ Correction: Renommer en 'prenom' et 'nom'

Ligne 73-74: UserSerializer - fields 'first_name', 'last_name'
❌ "first_name",
❌ "last_name",
✅ Correction: Remplacer par 'prenom' et 'nom'

Ligne 102: UserUpdateSerializer - fields 'first_name', 'last_name'
❌ fields = ["first_name", "last_name", "phone_number"]
✅ Correction: ["prenom", "nom", "phone_number"]
```

### membres/serializers.py
```
Ligne 31: MembreSerializer - fields incluent des champs inexistants
❌ "telephone" (n'existe pas dans Membre)
❌ "email" (n'existe pas dans Membre)
❌ "date_inscription" (n'existe pas dans Membre)
✅ Correction: 
   - Ajouter ces champs à Membre OU
   - Retirer du serializer OU
   - Utiliser SerializerMethodField pour accéder via user
```

---

## 2️⃣ USER.CREATE_USER() AVEC CHAMPS INCORRECTS

### accounts/auth/services.py
```
Ligne 62-63: AuthenticationService.register()
❌ user = User.objects.create_user(
      ...
      first_name=first_name,
      last_name=last_name,
      ...
   )
✅ Correction:
   user = User.objects.create_user(
      ...
      nom=first_name,        # Mapper first_name -> nom
      prenom=last_name,      # Mapper last_name -> prenom
      ...
   )
```

---

## 3️⃣ ADMIN.PY - CHAMPS MEMBRE INCORRECTS

### accounts/admin.py
```
Ligne 7-12: list_display
❌ "sacrement" (champ de Membre, pas User)

Ligne 21: add_fieldsets
❌ "sacrement" (champ de Membre)

Ligne 29: fieldsets - "Personal info"
❌ "sacrement" (Fk vers Sacrement, dans Membre)
❌ "quartier" (CharField dans Membre)

Ligne 36-37: fieldsets - "Permissions"
❌ "groupe" (FK vers Groupe, dans Membre)

Ligne 70: search_fields
❌ 'quartier' (champ de Membre)
❌ "sacrement" (relation Membre)

✅ Correction: Retirer tous ces champs de User Admin
   Ces champs doivent être gérés via Membre Admin
```

---

## 4️⃣ ACCÈS À USER.FIRST_NAME

### librairie/views.py
```
Ligne 118: VenteViewSet.create()
❌ description=f"Vente de l'article: {article.nom}, Qte: {quantite}, par: {request.user.first_name}",
✅ Correction:
   description=f"Vente de l'article: {article.nom}, Qte: {quantite}, par: {request.user.prenom}",
   OU
   description=f"Vente de l'article: {article.nom}, Qte: {quantite}, par: {request.user.nom_complet}",
```

---

## 5️⃣ TEMPLATES UTILISANT FIRST_NAME

### templates/emails/password_reset.html
```
Ligne 5:
❌ <p>Hello {{ user.first_name|default:"there" }},</p>
✅ Correction:
   <p>Hello {{ user.prenom|default:"there" }},</p>
```

---

## 6️⃣ SIGNALS SYNCHRONISANT NOM/PRENOM

### membres/signals.py
```
Ligne 44-50: update_membre_for_user()
⚠️ Fonctionne mais dépend de la relation OneToOne
   membre = instance.membre  # ⚠️ Suppose User.membre existe
   if membre.nom != instance.nom or membre.prenom != instance.prenom:
       membre.nom = instance.nom
       membre.prenom = instance.prenom
       membre.save()

Status: ⚠️ Fragile - Si la relation OneToOne est supprimée, ce signal se cassera
Note: Crée du code redondant entre User et Membre
```

---

## 7️⃣ DÉPENDANCES CACHÉES SUR USER.FULL_NAME

### Fichiers utilisant user.full_name:

**membres/serializers.py**
```
Ligne 19: get_officiant_nom()
return obj.officiant.full_name or obj.officiant.email
✅ Fonctionne (User.full_name existe)
⚠️ Mais dépend de propriété fragile
```

**librairie/serializers.py**
```
Ligne 36: get_enregistre_par_nom()
return obj.enregistre_par.full_name or obj.enregistre_par.email
✅ Fonctionne (User.full_name existe)
⚠️ Mais dépend de propriété fragile
```

**finances/serializers.py**
```
Ligne 22: get_enregistre_par_nom()
return obj.enregistre_par.full_name or obj.enregistre_par.email
✅ Fonctionne (User.full_name existe)
⚠️ Mais dépend de propriété fragile
```

**evenements/serializers.py**
```
Ligne 33: get_createur_nom()
return obj.createur.full_name or obj.createur.email
✅ Fonctionne (User.full_name existe)
⚠️ Mais dépend de propriété fragile
```

**groupes/serializers.py**
```
Ligne 15: get_responsable_nom()
return obj.responsable.full_name or obj.responsable.email
✅ Fonctionne (User.full_name existe)
⚠️ Mais dépend de propriété fragile
```

**accounts/serializers.py**
```
Ligne 120: UserActivitySerializer
user_full_name = serializers.CharField(source="user.full_name", read_only=True)
✅ Fonctionne (User.full_name existe)
⚠️ Mais dépend de propriété fragile
```

---

## 8️⃣ DÉPENDANCES DE FIELDS INEXISTANTS

### accounts/admin.py - Champs problématiques
```
Ligne 70: search_fields = ('email', 'nom', 'prenom', 'quartier', "sacrement")
                                                    ^^^^^^^^^^^^^^^^^^^^^^^^
                                                    Ces champs n'existent pas dans User
Détail:
  - 'quartier': CharField(200) dans Membre
  - "sacrement": ForeignKey vers Sacrement dans Membre
```

---

## ⚠️ RÉSUMÉ DES DÉPENDANCES

### Fichiers avec Erreurs Critiques (2/5 Erreurs):
1. ❌ **accounts/serializers.py** - 3 champs (first_name, last_name) x 2 serializers + 1 mismatch
2. ❌ **accounts/auth/services.py** - first_name/last_name dans create_user
3. ❌ **accounts/admin.py** - Accès à sacrement, quartier, groupe
4. ❌ **membres/serializers.py** - telephone, email, date_inscription
5. ❌ **librairie/views.py** - user.first_name

### Fichiers avec Erreurs Moyennes (Affichage/Logique):
6. ⚠️ **templates/emails/password_reset.html** - user.first_name
7. ⚠️ **membres/signals.py** - Logique fragile

### Fichiers Dépendants (Pas d'erreur directe mais fragiles):
8. 🟠 **membres/serializers.py** - Dépend de user.full_name
9. 🟠 **librairie/serializers.py** - Dépend de user.full_name
10. 🟠 **finances/serializers.py** - Dépend de user.full_name
11. 🟠 **evenements/serializers.py** - Dépend de user.full_name
12. 🟠 **groupes/serializers.py** - Dépend de user.full_name
13. 🟠 **accounts/serializers.py** - Dépend de user.full_name

---

## 📋 Matrice de Correction

| Fichier | Problème | Correction | Type | Priorité |
|---------|----------|-----------|------|----------|
| accounts/serializers.py | first_name → nom | Renommer champs | Refactorisation | 🔴 P1 |
| accounts/serializers.py | last_name → prenom | Renommer champs | Refactorisation | 🔴 P1 |
| accounts/serializers.py | UserUpdateSerializer | Renommer champs | Refactorisation | 🔴 P1 |
| accounts/auth/services.py | create_user params | Mapper paramètres | Refactorisation | 🔴 P1 |
| accounts/admin.py | Champs Membre | Retirer du UserAdmin | Suppression | 🔴 P1 |
| membres/serializers.py | Champs manquants | Ajouter à Membre ou SerializerMethodField | Ajout/Refactorisation | 🔴 P1 |
| librairie/views.py | user.first_name | Utiliser user.prenom | Remplacement | 🔴 P1 |
| templates/emails/password_reset.html | user.first_name | Utiliser user.prenom | Remplacement | 🟠 P2 |
| membres/signals.py | Logique fragile | Refactoriser pour robustesse | Refactorisation | 🟠 P2 |
| Serializers (x6) | Dépendence user.full_name | Créer méthode dédiée ou champs clairs | Refactorisation | 🟠 P2 |

---

## 🧪 Points de Test à Vérifier

Après correction, tester:
1. ✅ Création d'utilisateur avec registration endpoint
2. ✅ Accès admin Django pour les utilisateurs
3. ✅ Sérialisation des Membres
4. ✅ Enregistrement de ventes (librairie)
5. ✅ Envoi d'emails (password_reset)
6. ✅ Affichage des noms dans tous les serializers

