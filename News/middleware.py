from django.http import JsonResponse
from .models import CustomUser

class APIKeyMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.path.startswith('/api/'):
            api_key = request.headers.get('X-API-Key')
            if not api_key:
                return JsonResponse({'error': 'API key required'}, status=401)
            
            try:
                user = CustomUser.objects.get(api_key=api_key)
                request.user = user
            except CustomUser.DoesNotExist:
                return JsonResponse({'error': 'Invalid API key'}, status=401)

        return self.get_response(request)