# path: profiles/api/views/account/social_auth.py

from allauth.socialaccount.providers.google.views import GoogleOAuth2Adapter
from dj_rest_auth.registration.views import SocialLoginView


class GoogleLogin(SocialLoginView):
    """
    View that handles Google login using OAuth2.
    """
    adapter_class = GoogleOAuth2Adapter
