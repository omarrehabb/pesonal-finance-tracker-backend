from django.contrib import admin

from .models import Transaction
from .models import UserProfile

admin.site.register(Transaction)
admin.site.register(UserProfile)