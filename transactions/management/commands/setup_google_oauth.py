from django.core.management.base import BaseCommand, CommandError
from django.contrib.sites.models import Site
from allauth.socialaccount.models import SocialApp
import os


class Command(BaseCommand):
    help = "Configure Google OAuth SocialApp and Site from environment variables"

    def add_arguments(self, parser):
        parser.add_argument(
            "--domain",
            dest="domain",
            help="Domain for the Django Site (e.g., 127.0.0.1:8000 or myapp.fly.dev)",
        )
        parser.add_argument(
            "--name",
            dest="name",
            help="Display name for the Django Site",
        )

    def handle(self, *args, **options):
        client_id = os.getenv("GOOGLE_CLIENT_ID")
        client_secret = os.getenv("GOOGLE_CLIENT_SECRET")
        if not client_id or not client_secret:
            raise CommandError(
                "GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET must be set in the environment."
            )

        domain = options.get("domain") or os.getenv("SITE_DOMAIN") or "127.0.0.1:8000"
        name = options.get("name") or os.getenv("SITE_NAME") or "Local"

        # Ensure Site exists and is correct
        site = Site.objects.get_or_create(id=1, defaults={"domain": domain, "name": name})[0]
        site.domain = domain
        site.name = name
        site.save()

        # Create or update SocialApp
        app, _created = SocialApp.objects.get_or_create(provider="google", defaults={"name": "Google"})
        app.name = "Google"
        app.client_id = client_id
        app.secret = client_secret
        app.save()
        app.sites.set([site])

        self.stdout.write(self.style.SUCCESS(
            f"Configured Google OAuth for site '{site.domain}'."
        ))

