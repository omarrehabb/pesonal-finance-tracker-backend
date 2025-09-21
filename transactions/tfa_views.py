from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from rest_framework.decorators import api_view, permission_classes, authentication_classes
from rest_framework.authentication import SessionAuthentication, BasicAuthentication
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
    # Allow access with session auth even when 2FA enforcement is on
    authentication_classes = [SessionAuthentication, BasicAuthentication]
    
    def get(self, request, format=None):
        user = request.user
        
        # Clean up any previous unconfirmed devices, keep confirmed ones
        TOTPDevice.objects.filter(user=user, confirmed=False).delete()
        
        # Create a new TOTP device
        device = TOTPDevice.objects.create(
            user=user,
            name='Default',
            confirmed=False
        )
        
        # URL for QR code
        url = device.config_url
        
        # Generate QR code (PNG)
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(url)
        qr.make(fit=True)
        img_png = qr.make_image(fill_color="black", back_color="white")

        # Save PNG
        png_buffer = BytesIO()
        img_png.save(png_buffer, format='PNG')
        qr_png_b64 = base64.b64encode(png_buffer.getvalue()).decode()

        # Also generate SVG (more lightweight and universally renderable)
        svg_img = qrcode.make(url, image_factory=qrcode.image.svg.SvgImage)
        svg_buffer = BytesIO()
        svg_img.save(svg_buffer)
        qr_svg_b64 = base64.b64encode(svg_buffer.getvalue()).decode()
        
        # Return the device info and QR code
        resp = Response({
            'device_id': device.id,
            'qr_code': f"data:image/png;base64,{qr_png_b64}",
            'qr_svg': f"data:image/svg+xml;base64,{qr_svg_b64}",
            'secret_key': device.key,  # Should be shown to user for manual entry
            'otpauth_url': url
        })
        resp['Cache-Control'] = 'no-store'
        return resp


class TOTPVerifyView(APIView):
    """
    View for verifying a TOTP token and activating the device
    """
    permission_classes = [permissions.IsAuthenticated]
    authentication_classes = [SessionAuthentication, BasicAuthentication]
    
    def post(self, request, format=None):
        user = request.user
        token = request.data.get('token')
        
        if not token:
            return Response({
                'error': 'Token is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Verify against any of the user's devices with a small time tolerance
        token = str(token).strip()
        matched_device = None
        for device in TOTPDevice.objects.filter(user=user):
            try:
                if device.verify_token(token, tolerance=1):  # allow +/- 1 step drift
                    matched_device = device
                    break
            except TypeError:
                # Older django-otp may not support tolerance kw; fall back
                if device.verify_token(token):
                    matched_device = device
                    break

        if not matched_device:
            return Response({
                'success': False,
                'error': 'Invalid token'
            }, status=status.HTTP_400_BAD_REQUEST)

        if not matched_device.confirmed:
            matched_device.confirmed = True
            matched_device.save()

        # Mark the session as verified
        request.session['otp_verified'] = True

        resp = Response({
            'success': True,
            'message': 'TOTP device confirmed'
        })
        resp['Cache-Control'] = 'no-store'
        return resp


class TOTPDeleteView(APIView):
    """
    View for deleting a TOTP device (disabling 2FA)
    """
    permission_classes = [permissions.IsAuthenticated]
    authentication_classes = [SessionAuthentication, BasicAuthentication]
    
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
        
        resp = Response({
            'success': True,
            'message': 'TOTP device deleted'
        })
        resp['Cache-Control'] = 'no-store'
        return resp


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
@authentication_classes([SessionAuthentication, BasicAuthentication])
def has_2fa(request):
    """
    Check if the user has 2FA enabled
    """
    user = request.user
    device = get_user_totp_device(user, confirmed=True)
    
    verified = bool(request.session.get('otp_verified'))
    resp = Response({
        'has_2fa': device is not None,
        'verified': verified,
    })
    resp['Cache-Control'] = 'no-store'
    return resp
