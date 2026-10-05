"""Ensure the admin CMS has a superuser.

`seed` deliberately never touches auth, so this is its own step and
`build_files.sh` runs it after seed. The hosted database is rebuilt on every
deploy, so without this command `/admin/` on the live site has no account.

The environment wins over the values below: set DJANGO_ADMIN_USERNAME,
DJANGO_ADMIN_PASSWORD and DJANGO_ADMIN_EMAIL on the host to move the account
off committed defaults without a code change. An existing account keeps its
password unless `--reset-password` is passed, so changing it in `/admin/`
survives a redeploy until someone passes that flag.
"""

import os

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

USERNAME = os.environ.get("DJANGO_ADMIN_USERNAME", "Rightpoint")
PASSWORD = os.environ.get("DJANGO_ADMIN_PASSWORD", "Rightpoint@2026")
EMAIL = os.environ.get("DJANGO_ADMIN_EMAIL", "")


class Command(BaseCommand):
    help = "Create the admin superuser if it does not exist yet."

    def add_arguments(self, parser):
        parser.add_argument(
            "--reset-password",
            action="store_true",
            help="Apply the configured password to an account that already exists.",
        )

    def handle(self, *args, **options):
        user, created = get_user_model().objects.get_or_create(username=USERNAME)
        if created or options["reset_password"]:
            user.set_password(PASSWORD)
            status = "created" if created else "password reset"
        else:
            status = "already present, password untouched"
        user.email = user.email or EMAIL
        user.is_staff = user.is_superuser = True
        user.save()
        self.stdout.write(self.style.SUCCESS(f"Admin '{USERNAME}': {status}"))
