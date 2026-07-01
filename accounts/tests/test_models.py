"""Tests du modèle User et de son manager."""
from django.test import TestCase

from accounts.models import User, UserActivity


class UserManagerTests(TestCase):
    def test_create_user_success(self):
        user = User.objects.create_user(
            email="a@b.com", password="secret123", prenom="Jean", nom="Dupont"
        )
        self.assertEqual(user.email, "a@b.com")
        self.assertTrue(user.check_password("secret123"))
        self.assertFalse(user.is_staff)
        self.assertEqual(user.role, "fidele")

    def test_create_user_derives_username_from_email(self):
        user = User.objects.create_user(
            email="alice@example.com", password="secret123", prenom="A", nom="B"
        )
        self.assertEqual(user.username, "alice")

    def test_create_user_normalizes_email_domain(self):
        user = User.objects.create_user(
            email="Bob@EXAMPLE.COM", password="secret123", prenom="B", nom="C"
        )
        self.assertEqual(user.email, "Bob@example.com")

    def test_create_user_without_email_raises(self):
        with self.assertRaises(ValueError):
            User.objects.create_user(email="", password="secret123")

    def test_create_user_without_password_raises(self):
        with self.assertRaises(ValueError):
            User.objects.create_user(email="x@y.com", password=None)

    def test_create_superuser_sets_flags_and_role(self):
        admin = User.objects.create_superuser(
            email="admin@b.com", password="secret123", prenom="Ad", nom="Min"
        )
        self.assertTrue(admin.is_staff)
        self.assertTrue(admin.is_superuser)
        self.assertTrue(admin.is_active)
        self.assertEqual(admin.role, "admin")

    def test_create_superuser_without_password_raises(self):
        with self.assertRaises(ValueError):
            User.objects.create_superuser(email="admin@b.com", password="")


class UserModelTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="jean@b.com", password="secret123", prenom="Jean", nom="Dupont"
        )

    def test_name_properties(self):
        self.assertEqual(self.user.nom_complet, "Jean Dupont")
        self.assertEqual(self.user.full_name, "Jean Dupont")
        self.assertEqual(self.user.first_name, "Jean")  # alias de prenom
        self.assertEqual(self.user.last_name, "Dupont")  # alias de nom
        self.assertEqual(self.user.get_short_name(), "Jean")

    def test_str_representation(self):
        self.assertEqual(str(self.user), "Dupont (jean@b.com)")

    def test_role_display_name(self):
        self.user.role = "tresorier"
        self.assertEqual(self.user.get_role_display_name(), "Trésorier")

    def test_has_permission_admin_has_all(self):
        self.user.role = "admin"
        self.assertTrue(self.user.has_permission("manage_finances"))
        self.assertTrue(self.user.has_permission("manage_users"))

    def test_has_permission_fidele_has_none(self):
        self.user.role = "fidele"
        self.assertFalse(self.user.has_permission("manage_finances"))

    def test_has_permission_unknown_permission(self):
        self.user.role = "tresorier"
        self.assertFalse(self.user.has_permission("does_not_exist"))


class UserActivityModelTests(TestCase):
    def test_activity_str_and_ordering(self):
        user = User.objects.create_user(
            email="log@b.com", password="secret123", prenom="L", nom="Og"
        )
        a1 = UserActivity.objects.create(user=user, action="login", details="1")
        a2 = UserActivity.objects.create(user=user, action="logout", details="2")
        # ordering = ["-timestamp"] : le plus récent en premier
        activities = list(UserActivity.objects.all())
        self.assertEqual(activities[0], a2)
        self.assertIn("login", str(a1))
