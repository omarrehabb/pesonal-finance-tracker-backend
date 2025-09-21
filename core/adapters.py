from allauth.account.adapter import DefaultAccountAdapter
from allauth.account.utils import perform_login
from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from django.contrib.auth import get_user_model


class AccountAdapter(DefaultAccountAdapter):
    def populate_username(self, request, user):
        # Auto-generate a unique username if missing (e.g., social signup)
        if not user.username:
            # Prefer the email localpart as base
            email = (user.email or "").strip()
            base = email.split("@")[0] if "@" in email else "user"
            user.username = self.generate_unique_username([base, email, "user"])  # type: ignore


class SocialAdapter(DefaultSocialAccountAdapter):
    def populate_user(self, request, sociallogin, data):
        # Let default populate common fields first
        user = super().populate_user(request, sociallogin, data)

        # Ensure username is populated to avoid intermediate signup form
        if not getattr(user, "username", None):
            email = (data.get("email") or getattr(user, "email", "") or "").strip()
            base = email.split("@")[0] if "@" in email else (data.get("name") or "user")
            user.username = DefaultAccountAdapter().generate_unique_username([base, email, "user"])  # type: ignore

        return user

    def is_auto_signup_allowed(self, request, sociallogin):
        # Always allow auto-signup for social accounts to skip the extra
        # '3rd-party signup' confirmation form.
        return True

    def pre_social_login(self, request, sociallogin):
        """
        If the user is already authenticated and is initiating a provider flow,
        automatically connect the social account to the logged-in user
        (skipping the intermediate signup/confirm page).
        """
        user = getattr(request, "user", None)
        if user and user.is_authenticated and not sociallogin.is_existing:
            # Attach this social account to the currently logged-in user
            sociallogin.connect(request, user)
            return

        # If not logged in, auto-link to an existing account with the same email
        if not sociallogin.is_existing:
            email = (getattr(sociallogin.user, "email", "") or "").strip().lower()
            if email:
                User = get_user_model()
                try:
                    existing = User.objects.get(email__iexact=email)
                    sociallogin.connect(request, existing)
                    # Log the user in immediately
                    perform_login(request, existing, email_verification='optional')
                except User.DoesNotExist:
                    pass
