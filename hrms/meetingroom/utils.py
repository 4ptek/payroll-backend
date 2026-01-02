import random
from django.utils import timezone
from .models import Bookings

def generate_unique_otp():
    while True:
        otp = random.randint(100000, 999999)
        if not Bookings.objects.filter(otp=otp).exists():
            return otp
