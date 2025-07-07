from django.contrib import admin
from django.urls import path, include
from two_factor.urls import urlpatterns as tf_urls
# Comment out the AdminSiteOTPRequired import for now
# from two_factor.admin import AdminSiteOTPRequired
from core.views import index, contact

# Comment out the admin site class modification for now
# admin.site.__class__ = AdminSiteOTPRequired

urlpatterns = [
    path('', index, name = 'index'),
    path('contact/', contact, name = 'contact'),
    path('admin/', admin.site.urls),
    path('api/', include('transactions.urls')),
    path('api-auth/', include('rest_framework.urls')),  # Optional for browsable API
    path('', include(tf_urls)),  # Two-Factor authentication URLs
    path('api/budgets/', include('budgets.urls')),
]