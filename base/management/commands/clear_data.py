from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.apps import apps
from django.db import transaction

User = get_user_model()

class Command(BaseCommand):
    help = 'Clear all data from all models except the admin user (admin@admin.admin)'

    def handle(self, *args, **kwargs):
        admin_email = 'admin@admin.admin'
        
        self.stdout.write(f"Clearing data, keeping only user: {admin_email}...")

        try:
            with transaction.atomic():
                # 1. Clear all models in the 'base' app
                # We do this first because many models in 'base' depend on User/Vendor
                # and have on_delete=CASCADE, but it's cleaner to be explicit.
                base_app_models = apps.get_app_config('base').get_models()
                for model in base_app_models:
                    if model == User:
                        continue  # Handle User specifically later
                    
                    count = model.objects.all().count()
                    if count > 0:
                        self.stdout.write(f"Clearing {count} records from {model.__name__}...")
                        model.objects.all().delete()

                # 2. Clear all users except the admin
                other_users_count = User.objects.exclude(email=admin_email).count()
                if other_users_count > 0:
                    self.stdout.write(f"Clearing {other_users_count} other users...")
                    User.objects.exclude(email=admin_email).delete()

                # 3. Ensure the admin user exists (optional but good practice)
                if not User.objects.filter(email=admin_email).exists():
                    self.stdout.write(self.style.WARNING(f"Admin user {admin_email} not found. You might want to create it manually."))
                else:
                    self.stdout.write(self.style.SUCCESS(f"Kept user: {admin_email}"))

            self.stdout.write(self.style.SUCCESS("Successfully cleared all data!"))
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"An error occurred: {str(e)}"))
