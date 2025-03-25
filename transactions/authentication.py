from rest_framework import authentication
from rest_framework import exceptions
from django.contrib.auth.models import User
from django_otp import user_has_device, devices_for_user
from django_otp.plugins.otp_totp.models import TOTPDevice


class TwoFactorAuthentication(authentication.BaseAuthentication):
    """
    Custom authentication for DRF that verifies 2FA if enabled
    """
    
    def authenticate(self, request):
        # Get user from session authentication
        user = getattr(request._request, 'user', None)
        
        # If the user is already authenticated via session
        if user and user.is_authenticated:
            # Check if the user has 2FA enabled
            if user_has_device(user):
                # Get OTP from request headers
                otp_token = request.META.get('HTTP_X_OTP_TOKEN')
                
                if not otp_token:
                    # If no OTP token is provided, check if the session is already verified
                    if getattr(request._request, 'session', {}).get('otp_verified'):
                        return (user, None)
                    raise exceptions.AuthenticationFailed('OTP token required')
                
                # Verify the OTP token
                for device in devices_for_user(user):
                    if device.verify_token(otp_token):
                        # Mark the session as verified
                        request._request.session['otp_verified'] = True
                        return (user, None)
                
                raise exceptions.AuthenticationFailed('Invalid OTP token')
            
            # If 2FA is not enabled for the user, just return the user
            return (user, None)
        
        # No authenticated user found
        return None
    
    def authenticate_header(self, request):
        return 'Bearer realm="api"'


def get_user_totp_device(user, confirmed=None):
    """
    Helper to get a user's TOTP device
    """
    devices = TOTPDevice.objects.filter(user=user)
    if confirmed is not None:
        devices = devices.filter(confirmed=confirmed)
    
    return devices.first()