"""Insère des données de démonstration (~100 enregistrements par module).

Usage :
    python manage.py seed_demo            # insère les données
    python manage.py seed_demo --wipe     # supprime d'abord les données de démo

Les utilisateurs de démo sont reconnaissables à leur domaine e-mail
(@paroisse-demo.ga) ; toutes les autres données de démo sont préfixées ou
rattachées à ces comptes. Mot de passe commun : « Demo#2026! ».
"""

import random
from datetime import date, timedelta
from decimal import Decimal

from django.contrib.auth.hashers import make_password
from django.core.management.base import BaseCommand
from django.db import transaction as db_transaction
from django.utils import timezone

from accounts.models import User
from evenements.models import Evenement, Participation
from finances.models import Transaction
from groupes.models import Groupe
from librairie.models import Article, Vente
from membres.models import Membre, Sacrement

DEMO_DOMAIN = "paroisse-demo.ga"
DEMO_PASSWORD = "Demo#2026!"

PRENOMS_M = [
    "Jean",
    "Pierre",
    "Paul",
    "André",
    "Joseph",
    "Marc",
    "Luc",
    "Thomas",
    "François",
    "Antoine",
    "Étienne",
    "Georges",
    "Henri",
    "Michel",
    "Albert",
    "Serge",
    "Rodrigue",
    "Landry",
    "Davy",
    "Yannick",
    "Ulrich",
    "Brice",
]
PRENOMS_F = [
    "Marie",
    "Jeanne",
    "Thérèse",
    "Claire",
    "Anne",
    "Lucie",
    "Agnès",
    "Cécile",
    "Bernadette",
    "Monique",
    "Sylvie",
    "Chantal",
    "Pélagie",
    "Prisca",
    "Ornella",
    "Vanessa",
    "Grâce",
    "Divine",
    "Esther",
    "Rachel",
]
NOMS = [
    "Mba",
    "Ndong",
    "Obame",
    "Nguema",
    "Ondo",
    "Mintsa",
    "Essono",
    "Bekale",
    "Nzue",
    "Abessolo",
    "Moussavou",
    "Koumba",
    "Mbadinga",
    "Ibinga",
    "Bouanga",
    "Mavoungou",
    "Pambou",
    "Makaya",
    "Loundou",
    "Boulingui",
    "Ogandaga",
    "Rogombe",
    "Mihindou",
    "Ntoutoume",
    "Eyeghe",
]
QUARTIERS = [
    "Nombakélé",
    "Glass",
    "Batterie IV",
    "Lalala",
    "Nzeng-Ayong",
    "Akébé",
    "Owendo",
    "PK8",
    "Oloumi",
    "Mont-Bouët",
    "Sotega",
    "Alibandeng",
    "Charbonnages",
    "Okala",
    "Angondjé",
]
GROUPE_TYPES = [
    "Chorale",
    "Fraternité",
    "Mouvement",
    "Commission",
    "Groupe de prière",
    "Aumônerie",
    "Confrérie",
    "Équipe liturgique",
    "Cellule",
    "Atelier",
]
GROUPE_SAINTS = [
    "Sainte-Cécile",
    "Saint-Joseph",
    "Sainte-Thérèse",
    "Saint-Paul",
    "Sainte-Rita",
    "Saint-Augustin",
    "Notre-Dame de Lourdes",
    "Saint-Michel",
    "Sainte-Anne",
    "Saint-Jean-Baptiste",
]
LIEUX = [
    "Église principale",
    "Chapelle Sainte-Marie",
    "Salle paroissiale",
    "Presbytère",
    "Grotte mariale",
    "Esplanade",
    "Salle de catéchèse",
]
ARTICLES = {
    "livre": [
        "Bible de Jérusalem",
        "Missel romain",
        "Youcat",
        "Vie des saints",
        "Catéchisme de l'Église",
        "Prions en Église",
        "Magnificat",
    ],
    "bougie": [
        "Bougie de neuvaine",
        "Cierge pascal",
        "Bougie votive",
        "Bougie parfumée Sainte-Rita",
    ],
    "chapelet": [
        "Chapelet en bois d'ébène",
        "Chapelet nacré",
        "Dizainier",
        "Chapelet de la Miséricorde",
    ],
    "vetement": [
        "Tee-shirt paroisse",
        "Pagne des fêtes patronales",
        "Aube de servant",
        "Foulard de chorale",
    ],
    "autre": [
        "Statuette de la Vierge",
        "Icône du Sacré-Cœur",
        "Crucifix mural",
        "Médaille miraculeuse",
        "Encens liturgique",
    ],
}


class Command(BaseCommand):
    help = "Insère des données de démonstration (~100 enregistrements par module)."

    def add_arguments(self, parser):
        parser.add_argument(
            "--wipe",
            action="store_true",
            help="Supprime d'abord les données de démo existantes.",
        )

    def _wipe(self):
        demo_users = User.objects.filter(email__endswith=f"@{DEMO_DOMAIN}")
        Vente.objects.filter(enregistre_par__in=demo_users).delete()
        Article.objects.filter(description__contains="[démo]").delete()
        Transaction.objects.filter(enregistre_par__in=demo_users).delete()
        Participation.objects.filter(evenement__createur__in=demo_users).delete()
        Evenement.objects.filter(createur__in=demo_users).delete()
        Sacrement.objects.filter(observations__contains="[démo]").delete()
        Membre.objects.filter(quartier__contains="[démo]").delete()
        Groupe.objects.filter(description__contains="[démo]").delete()
        count = demo_users.count()
        demo_users.delete()  # supprime aussi les Membres liés (CASCADE)
        self.stdout.write(
            self.style.WARNING(f"Données de démo supprimées ({count} comptes).")
        )

    @db_transaction.atomic
    def handle(self, *args, **options):
        rng = random.Random(42)
        today = timezone.now()

        if options["wipe"]:
            self._wipe()

        if User.objects.filter(email__endswith=f"@{DEMO_DOMAIN}").exists():
            self.stderr.write(
                self.style.ERROR(
                    "Des données de démo existent déjà. Relancer avec --wipe "
                    "pour les régénérer."
                )
            )
            return

        def personne():
            sexe = rng.choice(["M", "F"])
            prenom = rng.choice(PRENOMS_M if sexe == "M" else PRENOMS_F)
            nom = rng.choice(NOMS)
            return sexe, prenom, nom

        def naissance():
            return date(rng.randint(1950, 2015), rng.randint(1, 12), rng.randint(1, 28))

        # ------------------------------------------------------------------ #
        # accounts — 100 utilisateurs (le signal crée leur fiche Membre)
        # ------------------------------------------------------------------ #
        password_hash = make_password(DEMO_PASSWORD)
        roles = (
            ["admin"]
            + ["pretre"] * 2
            + ["secretaire"] * 3
            + ["tresorier"] * 2
            + ["responsable"] * 12
            + ["fidele"] * 80
        )
        users = []
        for i, role in enumerate(roles, start=1):
            sexe, prenom, nom = personne()
            user = User(
                email=f"demo.{role}.{i:03d}@{DEMO_DOMAIN}",
                prenom=prenom,
                nom=nom,
                role=role,
                is_verified=True,
                phone_number=f"+241{rng.randint(60000000, 79999999)}",
                password=password_hash,
            )
            user.save()  # save unitaire : déclenche le signal de création du Membre
            users.append(user)
        self.stdout.write(
            f"accounts  : {len(users)} utilisateurs (mdp : {DEMO_PASSWORD})"
        )

        pretres = [u for u in users if u.role == "pretre"]
        gestionnaires = [
            u for u in users if u.role in ("secretaire", "tresorier", "admin")
        ]
        membres_lies = list(Membre.objects.filter(user__in=users))

        # ------------------------------------------------------------------ #
        # membres — 100 fiches sans compte + 100 sacrements
        # ------------------------------------------------------------------ #
        membres_sans_compte = []
        for _ in range(100):
            sexe, prenom, nom = personne()
            membres_sans_compte.append(
                Membre(
                    nom=nom,
                    prenom=prenom,
                    sexe=sexe,
                    date_naissance=naissance(),
                    quartier=f"{rng.choice(QUARTIERS)} [démo]",
                    est_baptise=rng.random() < 0.8,
                    est_confirme=rng.random() < 0.5,
                )
            )
        Membre.objects.bulk_create(membres_sans_compte)
        tous_membres = membres_lies + membres_sans_compte

        sacrements = []
        for membre in rng.sample(tous_membres, 100):
            type_s = rng.choice([t for t, _ in Sacrement.TYPE_CHOICES])
            sacrements.append(
                Sacrement(
                    type=type_s,
                    membre=membre,
                    date=today.date() - timedelta(days=rng.randint(30, 8000)),
                    officiant=rng.choice(pretres),
                    observations=f"Célébration de démonstration [démo] — {type_s}.",
                )
            )
        Sacrement.objects.bulk_create(sacrements)
        self.stdout.write(
            f"membres   : {len(membres_sans_compte)} fiches sans compte "
            f"(+{len(membres_lies)} liées aux comptes), {len(sacrements)} sacrements"
        )

        # ------------------------------------------------------------------ #
        # groupes — 100 groupes
        # ------------------------------------------------------------------ #
        groupes = []
        noms_groupes = [f"{t} {s}" for t in GROUPE_TYPES for s in GROUPE_SAINTS]
        for nom_groupe in rng.sample(noms_groupes, 100):
            groupes.append(
                Groupe(
                    nom=nom_groupe,
                    description=f"Groupe paroissial de démonstration [démo] : {nom_groupe}.",
                    responsable=rng.choice(users),
                )
            )
        Groupe.objects.bulk_create(groupes)
        for groupe in groupes:
            groupe.responsables.set(rng.sample(users, rng.randint(1, 3)))
        # Rattacher des membres aux groupes
        for membre in tous_membres:
            if rng.random() < 0.7:
                membre.groupe = rng.choice(groupes)
        Membre.objects.bulk_update(tous_membres, ["groupe"])
        self.stdout.write(f"groupes   : {len(groupes)} groupes")

        # ------------------------------------------------------------------ #
        # evenements — 100 événements + participations
        # ------------------------------------------------------------------ #
        evenements = []
        for i in range(100):
            type_e, type_label = rng.choice(Evenement.TYPE_CHOICES)
            debut = today + timedelta(
                days=rng.randint(-180, 180), hours=rng.randint(6, 19)
            )
            invite_tous = rng.random() < 0.4
            evenements.append(
                Evenement(
                    titre=f"{type_label} — {rng.choice(GROUPE_SAINTS)} n°{i + 1}",
                    type=type_e,
                    description=f"Événement de démonstration [démo] ({type_label}).",
                    date_debut=debut,
                    date_fin=debut + timedelta(hours=rng.randint(1, 5)),
                    lieu=rng.choice(LIEUX),
                    est_inscription_requise=rng.random() < 0.5,
                    createur=rng.choice(gestionnaires + pretres),
                    invite_tous=invite_tous,
                    roles_invites=[]
                    if invite_tous
                    else rng.sample(
                        [r for r, _ in User.ROLES_CHOICES], rng.randint(0, 3)
                    ),
                )
            )
        Evenement.objects.bulk_create(evenements)
        participations = []
        for evenement in evenements:
            if not evenement.invite_tous:
                evenement.groupes_invites.set(rng.sample(groupes, rng.randint(0, 3)))
                evenement.membres_invites.set(
                    rng.sample(tous_membres, rng.randint(0, 5))
                )
            for membre in rng.sample(tous_membres, rng.randint(0, 6)):
                participations.append(Participation(evenement=evenement, membre=membre))
        Participation.objects.bulk_create(participations, ignore_conflicts=True)
        self.stdout.write(
            f"evenements: {len(evenements)} événements, ~{len(participations)} participations"
        )

        # ------------------------------------------------------------------ #
        # finances — 100 transactions
        # ------------------------------------------------------------------ #
        transactions = []
        for _ in range(100):
            categorie = rng.choice([c for c, _ in Transaction.CATEGORIE_CHOICES])
            type_t = (
                "depense" if categorie == "autre" and rng.random() < 0.5 else "recette"
            )
            transactions.append(
                Transaction(
                    type=type_t,
                    categorie=categorie,
                    montant=Decimal(rng.randrange(500, 500000, 500)),
                    description=f"Transaction de démonstration [démo] ({categorie}).",
                    date=today.date() - timedelta(days=rng.randint(0, 365)),
                    membre=rng.choice(tous_membres)
                    if categorie in ("don", "quete")
                    else None,
                    enregistre_par=rng.choice(gestionnaires),
                )
            )
        Transaction.objects.bulk_create(transactions)
        self.stdout.write(f"finances  : {len(transactions)} transactions")

        # ------------------------------------------------------------------ #
        # librairie — 100 articles + 100 ventes
        # ------------------------------------------------------------------ #
        articles = []
        for i in range(100):
            categorie = rng.choice(list(ARTICLES))
            articles.append(
                Article(
                    nom=f"{rng.choice(ARTICLES[categorie])} (réf. {i + 1:03d})",
                    description=f"Article de démonstration [démo] ({categorie}).",
                    categorie=categorie,
                    prix_unitaire=Decimal(rng.randrange(500, 25000, 250)),
                    stock_disponible=rng.randint(0, 60),
                    seuil_alerte=5,
                )
            )
        Article.objects.bulk_create(articles)
        ventes = []
        for _ in range(100):
            article = rng.choice(articles)
            quantite = rng.randint(1, 5)
            ventes.append(
                Vente(
                    article=article,
                    quantite=quantite,
                    prix_total=article.prix_unitaire * quantite,
                    membre=rng.choice(tous_membres) if rng.random() < 0.7 else None,
                    enregistre_par=rng.choice(gestionnaires),
                )
            )
        Vente.objects.bulk_create(ventes)
        self.stdout.write(f"librairie : {len(articles)} articles, {len(ventes)} ventes")

        self.stdout.write(self.style.SUCCESS("Données de démonstration insérées."))
