from django.apps import AppConfig


class MembresConfig(AppConfig):
    name = "membres"
    verbose_name = "Membres / Fidèles"

    def ready(self):
        """Enregistrer les signaux"""
        import membres.signals  # noqa
