from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import TransactionViewSet, UserProfileViewSet
from .tfa_views import TOTPCreateView, TOTPVerifyView, TOTPDeleteView, has_2fa

# Create a router and register our viewsets with it
router = DefaultRouter()
router.register(r'transactions', TransactionViewSet, basename='transaction')
router.register(r'profiles', UserProfileViewSet, basename='profile')

# The API URLs are determined automatically by the router
urlpatterns = [
    path('', include(router.urls)),
    
    # Two-factor authentication endpoints
    path('2fa/create/', TOTPCreateView.as_view(), name='2fa-create'),
    path('2fa/verify/', TOTPVerifyView.as_view(), name='2fa-verify'),
    path('2fa/delete/', TOTPDeleteView.as_view(), name='2fa-delete'),
    path('2fa/status/', has_2fa, name='2fa-status'),
]