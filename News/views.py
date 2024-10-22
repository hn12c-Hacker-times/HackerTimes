from django.shortcuts import render,redirect
from django.views.generic import ListView
from django.http import HttpResponse, HttpRequest
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from .models import News, Comments, Search
from .forms import NewsForm
from django.shortcuts import render, get_object_or_404
from django.contrib.auth.models import User
from datetime import date, datetime
from google.oauth2 import id_token
from google.auth.transport import requests
from django.contrib.auth import logout as auth_logout
from django.db.models import Q
import os
import tldextract

# Create your views here.

class NewListView(ListView):
    model = News
    template_name = 'Newslist.html'
    context_object_name = 'news_list'
    
    def get_queryset(self):

        username = self.request.GET.get("username", "")
        if username:
            res = News.objects.filter(author=username).order_by('-published_date')
            if not res.exists():
                return HttpResponse(status=404)
            else: 
                return res
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
    template_name = 'Commentslist.html'
    context_object_name = 'comments_list'
    
    def get_queryset(self):
        username = self.request.GET.get("username", "")
        if username:
            res = Comments.objects.filter(username=username).order_by('-published_date')
            if not res.exists():
                return HttpResponse(status=404)  # No se encontraron comentarios
            else:
                return res
        return Comments.objects.order_by('-published_date')

# Vista de la lista de search
class SearchListView(ListView):
    model = News  # We are searching through the News model
    template_name = 'searchlist.html'  # The template that displays the search results
    context_object_name = 'search_list'  # The name of the context passed to the template

    def get_queryset(self):
        # Get the search query from the URL parameters
        query = self.request.GET.get('q')

        if query:
            # Save the search query in the Search model for tracking (optional)
            if self.request.user.is_authenticated:
                Search.objects.create(text=query, author=self.request.user)

            # Filter the news items based on the search query
            return News.objects.filter(
                Q(title__icontains=query)
            ).order_by('-published_date')
        else:
            return News.objects.none()

def user_profile(request):
    
    # Pasar la información del usuario al template
    return render(request, 'user_profile.html')

#LOGIN DE GOOGLE

@csrf_exempt
def submit(request):
    user_data = request.session.get('user_data')

    username = request.GET.get("username", "")
    if username:
         return redirect('/?username=' + username)
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

def logout(request):
    # Cerrar la sesión del usuario
    auth_logout(request)  
    # Limpiar la sesión
    request.session.flush()  
    # Redirigir a la lista de noticias
    return redirect('news:news_list')
