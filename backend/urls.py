from django.contrib import admin
from django.urls import path, re_path, include
from two_factor.urls import urlpatterns as tf_urls
# Comment out the AdminSiteOTPRequired import for now
# from two_factor.admin import AdminSiteOTPRequired
from core.views import index, contact
from transactions.views import legacy_api_auth_login, legacy_api_auth_logout

# Comment out the admin site class modification for now
# admin.site.__class__ = AdminSiteOTPRequired

urlpatterns = [
    path('', index, name = 'index'),
    path('contact/', contact, name = 'contact'),
    path('admin/', admin.site.urls),
    path('accounts/', include('allauth.urls')),
    path('api/', include('transactions.urls')),
    # Legacy auth compatibility for frontend hitting DRF's login/logout
    path('api-auth/login/', legacy_api_auth_login, name='legacy-login'),
    path('api-auth/logout/', legacy_api_auth_logout, name='legacy-logout'),
    path('api-auth/', include('rest_framework.urls')),  # Optional for browsable API
    path('', include(tf_urls)),  # Two-Factor authentication URLs
    path('api/budgets/', include('budgets.urls')),
    # Catch-all: serve SPA for non-API/admin/two-factor paths
    re_path(r'^(?!admin/|api/|api-auth/|static/|media/|account/).*$', index),
]
