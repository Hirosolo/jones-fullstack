"""
Django management command to create default admin account.
Usage: python manage.py create_default_admin
"""
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User


class Command(BaseCommand):
    help = 'Create default admin account with username "admin" and password "t123"'

    def handle(self, *args, **options):
        username = 'admin'
        password = 't123'
        
        # Check if admin user already exists
        if User.objects.filter(username=username).exists():
            user = User.objects.get(username=username)
            user.set_password(password)
            user.is_staff = True
            user.is_superuser = True
            user.save()
            self.stdout.write(
                self.style.SUCCESS(
                    f'✓ Admin account updated: username="{username}", password="{password}"'
                )
            )
        else:
            user = User.objects.create_superuser(
                username=username,
                email='admin@jones.local',
                password=password
            )
            self.stdout.write(
                self.style.SUCCESS(
                    f'✓ Admin account created: username="{username}", password="{password}"'
                )
            )
        
        self.stdout.write(
            self.style.SUCCESS(
                '\n✓ Setup complete! Access admin panel at: http://localhost:8000/admin/login/'
            )
        )
