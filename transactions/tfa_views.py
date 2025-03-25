from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from rest_framework.decorators import api_view, permission_classes
from django_otp.plugins.otp_totp.models import TOTPDevice
from django_otp.util import random_hex
import qrcode
import qrcode.image.svg
from io import BytesIO
import base64
from .authentication import get_user_totp_device


class TOTPCreateView(APIView):
    """
    View for creating a new TOTP device
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request, format=None):
        user = request.user
        
        # Delete any existing devices
        TOTPDevice.objects.filter(user=user).delete()
        
        # Create a new TOTP device
        device = TOTPDevice.objects.create(
            user=user,
            name='Default',
            confirmed=False
        )
        
        # URL for QR code
        url = device.config_url
        
        # Generate QR code
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(url)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")
        
        # Save QR code to BytesIO buffer
        buffer = BytesIO()
        img.save(buffer)
        
        # Convert BytesIO to base64 for inline display
        qr_code_base64 = base64.b64encode(buffer.getvalue()).decode()
        
        # Return the device info and QR code
        return Response({
            'device_id': device.id,
            'qr_code': f"data:image/png;base64,{qr_code_base64}",
            'secret_key': device.key,  # Should be shown to user for manual entry
            'otpauth_url': url
        })


class TOTPVerifyView(APIView):
    """
    View for verifying a TOTP token and activating the device
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request, format=None):
        user = request.user
        token = request.data.get('token')
        
        if not token:
            return Response({
                'error': 'Token is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Get the device
        device = get_user_totp_device(user)
        
        if not device:
            return Response({
                'error': 'No TOTP device found for user'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Verify the token
        if device.verify_token(token):
            if not device.confirmed:
                device.confirmed = True
                device.save()
            
            # Mark the session as verified
            request.session['otp_verified'] = True
            
            return Response({
                'success': True,
                'message': 'TOTP device confirmed'
            })
        
        return Response({
            'success': False,
            'error': 'Invalid token'
        }, status=status.HTTP_400_BAD_REQUEST)


class TOTPDeleteView(APIView):
    """
    View for deleting a TOTP device (disabling 2FA)
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request, format=None):
        user = request.user
        
        # Get the device
        device = get_user_totp_device(user)
        
        if not device:
            return Response({
                'error': 'No TOTP device found for user'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Delete the device
        device.delete()
        
        return Response({
            'success': True,
            'message': 'TOTP device deleted'
        })


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def has_2fa(request):
    """
    Check if the user has 2FA enabled
    """
    user = request.user
    device = get_user_totp_device(user, confirmed=True)
    
    return Response({
        'has_2fa': device is not None
    })