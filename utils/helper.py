import random
from datetime import timedelta
from django.utils import timezone
import string

def get_expiration_time():
    return timezone.now() + timedelta(minutes=10)

def generate_code():
    code = random.randint(100000,999999)
    return code

def generate_coupon_code():
    code = f"{random.choice(string.ascii_uppercase)}{random.choice(string.ascii_uppercase)}{random.randint(1000,9999)}{random.choice(string.ascii_uppercase)}{random.choice(string.ascii_uppercase)}"
    return code

def generate_theme_slug():
    code = random.randint(1000,9999)
    return code

def _format_remaining_period(value, singular, dual, plural, plural_after_ten):
    if value <= 1:
        return singular
    if value == 2:
        return dual
    if value <= 10:
        return f"{value} {plural}"
    return f"{value} {plural_after_ten}"

def _get_remaining_label(end_date) -> str:
    remaining_days = max((end_date - timezone.localdate()).days, 0)

    if remaining_days == 0:
        return 'ينتهي اليوم'

    if remaining_days >= 30:
        months = remaining_days // 30
        return f"متبقي {_format_remaining_period(months, 'شهر', 'شهران', 'أشهر', 'شهرا')}"

    return f"متبقي {_format_remaining_period(remaining_days, 'يوم', 'يومان', 'أيام', 'يوما')}"

def _get_ad_remaining_label(end_date):
    return _get_remaining_label(end_date)

def _get_offer_remaining_label(end_date):
    return _get_remaining_label(end_date)

def attach_ad_remaining_labels(ads):
    for ad in ads:
        ad.remaining_label = _get_ad_remaining_label(ad.end_date)
    return ads

def attach_offer_remaining_labels(offers):
    for offer in offers:
        offer.remaining_label = _get_offer_remaining_label(offer.end_date)
    return offers
