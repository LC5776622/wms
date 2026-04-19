from django.utils.deprecation import MiddlewareMixin
from django.contrib.auth.middleware import get_user

class UserMiddleware(MiddlewareMixin):
    def process_request(self, request):
        request.user = get_user(request)
       