import random
from datetime import timedelta
from django.utils import timezone

def get_expiration_time():
    return timezone.now() + timedelta(minutes=10)

def generate_code():
    code = random.randint(100000,999999)
    return code

def generate_theme_slug():
    code = random.randint(1000,9999)
    return code