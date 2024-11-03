from django.shortcuts import render,redirect
from django.views.generic import ListView, DetailView, View
from django.http import HttpResponse, HttpRequest
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from .models import News, Comments, Search, CustomUser
from .forms import NewsForm, UserForm, AskNewsForm
from django.shortcuts import render, get_object_or_404
from django.contrib.auth.models import User
from datetime import date, datetime
from google.oauth2 import id_token
from google.auth.transport import requests
from django.contrib.auth import logout as auth_logout
from django.db.models import Q
from django.conf import settings
import os, boto3
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
        # Ordenar por puntos
        return News.objects.order_by('-points')
        

# Vista de la lista de news
class NewestListView(ListView):
    model = News
    template_name = 'Newestlist.html'
    context_object_name = 'newest_list'
    
    def get_queryset(self):
        return News.objects.order_by('-published_date')

class AskListView(ListView):
    model = News
    template_name = 'askList.html'
    context_object_name = 'ask_list'

    def get_queryset(self):
        # Filtrar los objetos News que no tienen URL
        return News.objects.filter(url='').order_by('-published_date')

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

def ask_detail(request, ask_id):
    ask = get_object_or_404(News, id=ask_id)
    return render(request, 'ask_detail.html', {'ask': ask})

class UserView(View):
    model = CustomUser
    template_name = 'user_profile.html'
    context_object_name = 'user_profile'
    
    def get(self, request):
        email = request.session['user_data'].get('email')
        user_data = request.session['user_data']
        user = CustomUser.objects.get(email=email)
        
        if user:
            form = UserForm(instance=user)  # Crea el formulario con la instancia del usuario
            context = {
                self.context_object_name: user,
                'form': form,
                'user_data': user_data
            }
            return render(request, self.template_name, context)  # Renderiza el html
        else:
            return HttpResponse(status=404)
    
    def post(self,request):
        email = request.session['user_data'].get('email')
        user = CustomUser.objects.get(email=email)
        form = UserForm(request.POST, request.FILES, instance=user)
        if form.is_valid():
            form.save()
            if request.POST.get('remove_banner'):
                user.banner = 'https://hn12c-hackertimes.s3.us-east-1.amazonaws.com/banners/DefaultBanner.jpg'  #Reinicia el campo en el modelo
                user.save()  #Guarda el usuario después de eliminar los archivos, si es necesario
                
            if request.POST.get('remove_avatar'):
                user.avatar = 'https://hn12c-hackertimes.s3.us-east-1.amazonaws.com/avatars/DefaultProfile_IJlCHTZ.png' #Reinicia el campo en el modelo
                user.save()
            
            if 'banner_file' in request.FILES:
                banner_file = request.FILES['banner_file']
                s3 = boto3.client('s3', aws_access_key_id=settings.AWS_ACCESS_KEY_ID, aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY, aws_session_token=settings.AWS_SESSION_TOKEN)
                s3.upload_fileobj(banner_file, settings.AWS_STORAGE_BUCKET_NAME, "banner/" + banner_file.name, ExtraArgs={'ACL': 'public-read'})
                user.banner = f'{settings.AWS_S3_CUSTOM_DOMAIN}/banner/{banner_file.name}'  # Guarda la URL
                user.save()

            if 'avatar_file' in request.FILES:
                avatar_file = request.FILES['avatar_file']
                s3 = boto3.client('s3', aws_access_key_id=settings.AWS_ACCESS_KEY_ID, aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY, aws_session_token=settings.AWS_SESSION_TOKEN)
                s3.upload_fileobj(avatar_file, settings.AWS_STORAGE_BUCKET_NAME, "avatar/" + avatar_file.name, ExtraArgs={'ACL': 'public-read'})
                user.avatar = f'{settings.AWS_S3_CUSTOM_DOMAIN}/avatar/{avatar_file.name}'  # Guarda la URL
                user.save()
            
            return redirect('news:user_profile')

        else:
            #Manejo de errores, podrías incluir más información
            return HttpResponse(status=400)

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
            print("*" + news.urlDomain + "*")
            if news.urlDomain == "": return redirect('news:ask_list')
            return redirect('news:news_list')  # Redirige a la página 'newest'
    else:
        form = NewsForm()
    return render(request, 'submit.html', {'form': form, 'user_data': user_data})

# Vista de edicion de News
def edit_news(request, news_id):
    user_data = request.session.get('user_data')
    if not user_data:
        return redirect('news:login')
        
    news = get_object_or_404(News, id=news_id)
    
    # Verificar que el usuario actual es el autor
    if news.author != user_data['name']:
        return HttpResponse(status=403)  # Forbidden
    
    # Determinar si es un ask post (url vacía)
    is_ask = not news.url
    
    if request.method == "POST":
        form = AskNewsForm(request.POST, instance=news) if is_ask else NewsForm(request.POST, instance=news)
        if form.is_valid():
            news = form.save(commit=False)
            if not is_ask:
                news.urlDomain = tldextract.extract(form.cleaned_data.get('url')).domain
            news.save()
            if is_ask:
                return redirect('news:ask_list')
            return redirect('news:news_list')
    else:
        form = AskNewsForm(instance=news) if is_ask else NewsForm(instance=news)
    
    return render(request, 'edit_news.html', {
        'form': form, 
        'user_data': user_data,
        'is_ask': is_ask,
        'news': news  # Añadimos el objeto news al contexto
    })

# Vista de borrado de News
def delete_news(request, news_id):
    user_data = request.session.get('user_data')
    if not user_data:
        return redirect('news:login')
        
    news = get_object_or_404(News, id=news_id)
    
    # Verificar que el usuario actual es el autor
    if news.author != user_data['name']:
        return HttpResponse(status=403)  # Forbidden
        
    if request.method == "POST":
        news.delete()
        return redirect('news:news_list')
        
    return render(request, 'delete_confirmation.html', {'news': news, 'user_data': user_data})


def login(request):
    if request.method == "POST":
        token = request.POST.get('credential')  # Obtener el token de Google
        if token:
            try:
                user_data = id_token.verify_oauth2_token(
                    token, requests.Request(), os.environ['GOOGLE_OAUTH_CLIENT_ID']
                )
                if CustomUser.objects.filter(email=user_data['email']).exists():
                    user = CustomUser.objects.get(email=user_data['email'])
                else:
                    user = CustomUser.objects.create(
                        username=user_data['given_name'],
                        email=user_data['email'],
                        karma=1,
                        about='',
                        banner='https://hn12c-hackertimes.s3.us-east-1.amazonaws.com/banners/DefaultBanner.jpg',
                        avatar='https://hn12c-hackertimes.s3.us-east-1.amazonaws.com/avatars/DefaultProfile.png',
                        show_dead=True,
                        no_procrastinate=False,
                        max_visit=20,
                        min_away=180,
                        delay=0
                    );
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
