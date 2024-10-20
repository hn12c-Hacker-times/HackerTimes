from django.shortcuts import render,redirect
from django.views.generic import ListView
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from .models import News, Comments
from .forms import NewsForm  
from datetime import date, datetime
from google.oauth2 import id_token
from google.auth.transport import requests
import os
import tldextract

# Create your views here.

class NewListView(ListView):
    model = News
    template_name = 'Newslist.html'
    context_object_name = 'news_list'
    
    def get_queryset(self):
        # Ordenar por puntos (o el criterio que elijas)
        return News.objects.order_by('-points')

# Vista de la lista de news
class NewestListView(ListView):
    model = News
    template_name = 'Newestlist.html'
    context_object_name = 'newest_list'
    
    def get_queryset(self):
        return News.objects.order_by('-published_date')

# Vista de la lista de comments
class CommentListView(ListView):
    model = Comments
    template_name = 'Comments_list.html'
    context_object_name = 'books'

@csrf_exempt
def submit(request):
    user_data = request.session.get('user_data')

    if user_data:
        return create_news(request, user_data)
    return login(request)

# Vista para crear una nueva News
def create_news(request, user_data):
    if request.method == "POST":
        form = NewsForm(request.POST)
        if form.is_valid():
            news = form.save(commit=False) 
            news.author = user_data['name']
            news.urlDomain =  tldextract.extract(form.cleaned_data.get('url')).domain
            news.save()
            return redirect('news:news_list')  # Redirige a la página 'newest'
    else:
        form = NewsForm()
    return render(request, 'submit.html', {'form': form, 'user_data': user_data})

def login(request):
    if request.method == "POST":
        token = request.POST.get('credential')  # Obtener el token de Google
        if token:
            try:
                user_data = id_token.verify_oauth2_token(
                    token, requests.Request(), os.environ['GOOGLE_OAUTH_CLIENT_ID']
                )
                request.session['user_data'] = user_data  # Almacenar datos del usuario en la sesión
                return redirect('news:submit_news')  # Redirigir a la vista de submit para crear noticias
            except ValueError:
                return HttpResponse(status=403)  # Token no válido
    
    return render(request, 'sign_in.html')  # Mostrar la página de login de Google