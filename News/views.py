from django.shortcuts import render,redirect
from django.views.generic import ListView, DetailView, View
from django.http import HttpResponse, HttpRequest
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from .models import News, Comments, Search, CustomUser, HiddenNews, Thread
from .forms import NewsForm, UserForm, AskNewsForm, CommentForm
from django.shortcuts import render, get_object_or_404
from django.contrib.auth.models import User
from datetime import date, datetime
from google.oauth2 import id_token
from google.auth.transport import requests
from django.contrib.auth import logout as auth_logout
from django.db.models import Q
from django.conf import settings
from django.contrib import messages 
import os, re
import tldextract

# Create your views here.

class NewListView(ListView):
    model = News
    template_name = 'Newslist.html'
    context_object_name = 'news_list'
    
    def get_queryset(self):
        user_data = self.request.session.get('user_data')
        user_email = user_data.get('email') if user_data else None
        username = self.request.GET.get("username", "")

        if user_data:
            user = CustomUser.objects.get(email=user_data['email'])
            print(f"User data: {user_data}")  # Ver el usuario y su información

            # Obtener las noticias ocultas de ese usuario
            hidden_news_ids = HiddenNews.objects.filter(user=user).values_list('news_id', flat=True)
            print(f"Hidden news IDs: {list(hidden_news_ids)}")  # Ver los IDs de noticias ocultas

            # Si hay un nombre de usuario, mostrar solo las noticias de ese usuario
            if username:
                author = CustomUser.objects.filter(username=username).first()
                if author:
                    queryset = News.objects.filter(author=author, is_hidden=False).exclude(id__in=hidden_news_ids).order_by('-published_date')
                    print(f"Query for author '{username}': {queryset}")  # Ver la consulta para el autor
                    if not queryset.exists():
                        return HttpResponse(status=404)
                    return annotate_user_votes(queryset, user_email)
            
            # Excluir las noticias ocultas para el usuario actual y ordenarlas por puntos
            queryset = News.objects.filter(is_hidden=False).exclude(id__in=hidden_news_ids).order_by('-points')
            return annotate_user_votes(queryset, user_email)

        # Si el usuario no está logueado, solo mostrar las noticias no ocultas
        queryset = News.objects.filter(is_hidden=False).order_by('-published_date')
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        username = self.request.GET.get("username", "")
        if username:
            context['viewing_user'] = username
        return context       

# Vista de la lista de news
class NewestListView(ListView):
    model = News
    template_name = 'Newestlist.html'
    context_object_name = 'newest_list'
    
    def get_queryset(self):
        user_data = self.request.session.get('user_data')
        user_email = user_data.get('email') if user_data else None

        queryset = News.objects.filter(is_hidden=False).order_by('-published_date')
        return annotate_user_votes(queryset, user_email)

class AskListView(ListView):
    model = News
    template_name = 'askList.html'
    context_object_name = 'ask_list'

    def get_queryset(self):
        user_data = self.request.session.get('user_data')
        user_email = user_data.get('email') if user_data else None

        queryset = News.objects.filter(url='').order_by('-published_date')
        return annotate_user_votes(queryset, user_email)

# Vista de la lista de comments
class CommentListView(ListView):
    model = Comments
    template_name = 'Commentslist.html'
    context_object_name = 'comments_list'
    
    def get_queryset(self):
        user_data = self.request.session.get('user_data')
        user_email = user_data.get('email') if user_data else None

        username = self.request.GET.get("username", "")
        if username:
            queryset = Comments.objects.filter(author__username=username).order_by('-published_date')
            if not queryset.exists():
                return HttpResponse(status=404)  # No comments found
            return annotate_comment_votes(queryset, user_email)
        
        queryset = Comments.objects.order_by('-published_date')
        return annotate_comment_votes(queryset, user_email)

class SearchListView(ListView):
    model = News  # We are searching through the News model
    template_name = 'Searchlist.html'  # The template that displays the search results
    context_object_name = 'search_list'  # The name of the context passed to the template

    def get_queryset(self):
        # Get the search query from the URL parameters
        query = self.request.GET.get('q')
        user_data = self.request.session.get('user_data')
        user_email = user_data.get('email') if user_data else None

        if query:
            # Save the search query in the Search model for tracking (optional)
            if self.request.user.is_authenticated:
                Search.objects.create(text=query, author=self.request.user)

            # Filter the news items based on the search query
            queryset = News.objects.filter(
                Q(title__icontains=query)
            ).order_by('-published_date')

            # Annotate the queryset with user voting data
            return annotate_user_votes(queryset, user_email)
        else:
            return News.objects.none()
        
class FavoriteNewsView(ListView):
    model = News
    template_name = 'favorite_news.html'
    context_object_name = 'favorite_news'

    def get_queryset(self):
        user_data = self.request.session.get('user_data')
        
        # Redirect to login if user is not logged in
        if not user_data:
            return redirect('news:login')
        
        user_email = user_data.get('email')
        user = get_object_or_404(CustomUser, email=user_email)

        # Retrieve favorite news items for the user
        favorite_news = user.favorite_news.all().order_by('-published_date')

        # Annotate favorite news items with voting status
        return annotate_user_votes(favorite_news, user_email)
        
class FavoriteCommentsView(ListView):
    model = Comments
    template_name = 'favorite_comments.html'
    context_object_name = 'favorite_comments'

    def get_queryset(self):
        user_data = self.request.session.get('user_data')
        
        # Redirect to login if user is not logged in
        if not user_data:
            return redirect('news:login')
        
        user_email = user_data.get('email')
        user = get_object_or_404(CustomUser, email=user_email)

        # Retrieve favorite comments for the user
        favorite_comments = user.favorite_comments.all().order_by('-published_date')

        # Annotate favorite comments with voting status
        return annotate_comment_votes(favorite_comments, user_email)
    
class VotedNewsView(ListView):
    model = News
    template_name = 'voted_news.html'
    context_object_name = 'voted_news'

    def get_queryset(self):
        user_data = self.request.session.get('user_data')
        
        # Redirect to login if user is not logged in
        if not user_data:
            return redirect('news:login')
        
        user_email = user_data.get('email')
        user = get_object_or_404(CustomUser, email=user_email)
        if user:
            # Use the related_name to access voted news through the user
            queryset = user.voted_news.all().order_by('-published_date')
            # Annotate the queryset with user voting data
            return annotate_user_votes(queryset, user_email)
        else:
            return News.objects.none()  # Return an empty queryset if the user is not authenticated

class VotedCommentsView(ListView):
    model = Comments
    template_name = 'voted_comments.html'
    context_object_name = 'voted_comments'

    def get_queryset(self):
        user_data = self.request.session.get('user_data')
        
        # Redirect to login if user is not logged in
        if not user_data:
            return redirect('news:login')
        
        user_email = user_data.get('email')
        user = get_object_or_404(CustomUser, email=user_email)
        if user:
            # Use the related_name to access voted news through the user
            queryset = user.voted_comments.all().order_by('-published_date')
            return annotate_comment_votes(queryset, user_email)
        else:
            return Comments.objects.none()  # Return an empty queryset if the user is not authenticated


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
            hidden_news = News.objects.filter(id__in=HiddenNews.objects.filter(user=user).values('news')) 
            hidden_count = hidden_news.count()
            
            form = UserForm(instance=user)  # Crea el formulario con la instancia del usuario
            context = {
                self.context_object_name: user,
                'form': form,
                'user_data': user_data,
                'hidden_news': hidden_news,
                'hidden_count': hidden_count
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
                #s3 = boto3.client('s3', aws_access_key_id=settings.AWS_ACCESS_KEY_ID, aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY, aws_session_token=settings.AWS_SESSION_TOKEN)
                #s3.upload_fileobj(banner_file, settings.AWS_STORAGE_BUCKET_NAME, "banner/" + banner_file.name, ExtraArgs={'ACL': 'public-read'})
                user.banner = f'{settings.AWS_S3_CUSTOM_DOMAIN}/banner/{banner_file.name}'  # Guarda la URL
                user.save()

            if 'avatar_file' in request.FILES:
                avatar_file = request.FILES['avatar_file']
                #s3 = boto3.client('s3', aws_access_key_id=settings.AWS_ACCESS_KEY_ID, aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY, aws_session_token=settings.AWS_SESSION_TOKEN)
                #s3.upload_fileobj(avatar_file, settings.AWS_STORAGE_BUCKET_NAME, "avatar/" + avatar_file.name, ExtraArgs={'ACL': 'public-read'})
                user.avatar = f'{settings.AWS_S3_CUSTOM_DOMAIN}/avatar/{avatar_file.name}'  # Guarda la URL
                user.save()
            
            return redirect('news:user_profile')

        else:
            #Manejo de errores, podrías incluir más información
            return HttpResponse(status=400)

def annotate_user_votes(news_list, user_email):
    if user_email:
        for news_item in news_list:
            news_item.user_has_voted = news_item.voters.filter(email=user_email).exists()
    else:
        for news_item in news_list:
            news_item.user_has_voted = False
    return news_list

@csrf_exempt
def submit(request):
    user_data = request.session.get('user_data')

    username = request.GET.get("username", "")
    if username:
        return redirect('/' + username+'/')
    if user_data:
        return create_news(request, user_data)

    return login(request)

# Vista para crear una nueva News
def create_news(request, user_data):
    if request.method == "POST":
        form = NewsForm(request.POST)
        if form.is_valid():
            news = form.save(commit=False)
            # Obtener el objeto CustomUser en lugar de solo el nombre
            author = CustomUser.objects.get(email=user_data['email'])
            news.author = author  # Asignar el objeto CustomUser
            news.urlDomain = tldextract.extract(form.cleaned_data.get('url')).domain
            news.save()
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
    
    author = CustomUser.objects.get(email=user_data['email'])
    # Verificar que el usuario actual es el autor
    if news.author != author:
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
    
    author = CustomUser.objects.get(email=user_data['email'])
    # Verificar que el usuario actual es el autor
    if news.author != author:
        return HttpResponse(status=403)  # Forbidden
        
    if request.method == "POST":
        news.delete()
        return redirect('news:news_list')
        
    return render(request, 'delete_confirmation.html', {'news': news, 'user_data': user_data})

from django.shortcuts import get_object_or_404, redirect, render
from .models import News, Comments, CustomUser

# Vista de la noticia y su campo de creacion de comentario
def item_detail(request, news_id):
    news = get_object_or_404(News, id=news_id)
    comments = Comments.objects.filter(New=news).order_by('-published_date')
    user_data = request.session.get('user_data')
    is_favorited = False
    user_email = user_data.get('email') if user_data else None

    # Annotate vote status for the news and comments item
    if user_email:
        news.user_has_voted = news.voters.filter(email=user_email).exists()
        comments = annotate_comment_votes(comments, user_email)

    # Check if the user has favorited the news
    if user_data:
        user = CustomUser.objects.filter(email=user_email).first()
        if user:
            is_favorited = news in user.favorite_news.all()

    # Handle comment creation if POST data is provided
    if request.method == "POST":
        if not user_data:
            return redirect('news:login')
        
        # Process a new comment
        text = request.POST.get('text')
        parent_id = request.POST.get('parent_id')
        if text:
            author = CustomUser.objects.get(email=user_email)
            parent = get_object_or_404(Comments, id=parent_id) if parent_id else None
            Comments.objects.create(text=text, author=author, New=news, parent=parent)
            return redirect('news:item_detail', news_id=news_id)

    return render(request, 'item_detail.html', {
        'item': news,
        'comments': comments,
        'is_favorited': is_favorited,
        'user_data': user_data,
    })

# Helper function to annotate comment votes
def annotate_comment_votes(comments, user_email):
    if user_email:
        for comment in comments:
            comment.user_has_voted = comment.voters.filter(email=user_email).exists()
    else:
        for comment in comments:
            comment.user_has_voted = False
    return comments

    
# Funcionalidad parent
def comment_context(request, news_id, comment_id):
    news = get_object_or_404(News, id=news_id)
    parent_comment = get_object_or_404(Comments, id=comment_id)
    replies = Comments.objects.filter(parent=parent_comment).order_by('-published_date')
    user_data = request.session.get('user_data')
    user_email = user_data.get('email') if user_data else None

    is_favorited = False

    # Annotate vote status for the parent comment and replies
    if user_email:
        # Annotate the parent comment
        parent_comment.user_has_voted = parent_comment.voters.filter(email=user_email).exists()
        # Annotate replies
        replies = annotate_comment_votes(replies, user_email)

    # Check if the user has favorited the comment
    if user_data:
        user = CustomUser.objects.filter(email=user_email).first()
        if user:
            is_favorited = parent_comment in user.favorite_comments.all()
    
    return render(request, 'comment_context.html', {
        'news': news,
        'parent_comment': parent_comment,
        'replies': replies,
        'is_favorited': is_favorited,
        'user_data': user_data
    })

def edit_comment(request, comment_id):
    comment = get_object_or_404(Comments, id=comment_id)
    news = comment.New  # Obtener la noticia asociada al comentario
    
    if not request.session.get('user_data') or request.session['user_data']['given_name'] != comment.author.username:
        return HttpResponse(status=403)
        
    if request.method == "POST":
        text = request.POST.get('text')
        if text:
            comment.text = text
            comment.save()
        return redirect('news:item_detail', news_id=news.id)
    
    return render(request, 'edit_comment.html', {
        'comment': comment,
        'news': news,
        'user_data': request.session.get('user_data')
    })

def delete_comment(request, comment_id):
    comment = get_object_or_404(Comments, id=comment_id)
    
    if not request.session.get('user_data') or request.session['user_data']['email'] != comment.author.email:
        return HttpResponse(status=403)
        
    news_id = comment.New.id
    comment.delete()
    return redirect('news:item_detail', news_id=news_id)

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
                    if CustomUser.objects.filter(username=user_data['given_name']).exists():
                        while CustomUser.objects.filter(username=user_data['given_name']+i).exists():
                            i += 1
                            nom = user_data['given_name']+i
                    else:
                        nom = user_data['given_name']
                        
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
    print("Session data before flush:", request.session.items())  # Imprime los datos de la sesión antes de limpiar
    # Limpiar la sesión
    request.session.flush()
    print("Session data after flush:", request.session.items())  # Imprime los datos de la sesión después de limpiar
    # Redirigir a la lista de noticias
    return redirect('news:news_list')

class CustomUserDetailView(DetailView):
    model = CustomUser
    template_name = 'user.html'
    context_object_name = 'user'
    
    def get_object(self, queryset=None):
        # Obtenemos el valor del parámetro slug desde la URL
        identifier = self.kwargs.get(self.slug_url_kwarg)
        
        # Intentamos obtener el usuario por email
        if re.match(r"[^@]+@[^@]+\.[^@]+", identifier):  # Verifica si el parámetro tiene formato de email
            # Buscamos por email
            user = get_object_or_404(self.model, email=identifier)
        else:
            # Si no es un email, lo buscamos por username
            user = get_object_or_404(self.model, username=identifier)
        
        return user

    slug_field = 'email'
    slug_url_kwarg = 'email'



def vote(request, news_id):
    user_data = request.session.get('user_data')
    
    if user_data:
        email = user_data.get('email')  # Retrieve the email from the session data
        if email:
            try:
                user = CustomUser.objects.get(email=email)
            except CustomUser.DoesNotExist:
                return HttpResponse("User not found", status=404)

            news = get_object_or_404(News, id=news_id)
            
            if user in news.voters.all():
                # Unvote logic
                news.voters.remove(user)
                news.points -= 1  # Decrease the vote count
                news.save()
            else:
                # Vote logic
                news.voters.add(user)
                news.points += 1  # Increase the vote count
                news.save()
            
            print(f"User {user.email} has voted/unvoted")
            return redirect('news:news_list')  # Redirect to a relevant page after voting

    return login(request)

def vote_comment(request, comment_id):
    user_data = request.session.get('user_data')
    
    if user_data:
        email = user_data.get('email')  # Retrieve the email from the session data
        if email:
            try:
                user = CustomUser.objects.get(email=email)
            except CustomUser.DoesNotExist:
                return HttpResponse("User not found", status=404)

            comment = get_object_or_404(Comments, id=comment_id)
            
            if user in comment.voters.all():
                # Unvote logic
                comment.voters.remove(user)
                comment.save()
            else:
                # Vote logic
                comment.voters.add(user)
                comment.save()
            
            print(f"User {user.email} has voted/unvoted on comment {comment_id}")
            return redirect('news:comments_list')  # Redirect to a relevant page after voting

    return login(request)

def favorite_news(request, news_id):
    user_data = request.session.get('user_data')
    
    if user_data:
        email = user_data.get('email')  # Retrieve the email from session data
        if email:
            user = get_object_or_404(CustomUser, email=email)
            news = get_object_or_404(News, id=news_id)
            
            if news in user.favorite_news.all():
                # Unfavorite logic
                user.favorite_news.remove(news)
            else:
                # Favorite logic
                user.favorite_news.add(news)
                # Print the list of favorite news titles
                favorites = [n.title for n in user.favorite_news.all()]
                print(f"Current favorite news for {user.email}: {favorites}")
                
            print(f"User {user.email} has favorited/unfavorited '{news.title}'")
            
            # Redirect back to the same page to show updated status
            return redirect('news:item_detail', news_id=news_id)

    return redirect('news:login')  # Redirect to login if user is not authenticated


def favorite_comment(request, comment_id):
    user_data = request.session.get('user_data')
    
    if user_data:
        email = user_data.get('email')  # Retrieve the email from session data
        if email:
            user = get_object_or_404(CustomUser, email=email)
            comment = get_object_or_404(Comments, id=comment_id)
            
            if comment in user.favorite_comments.all():
                # Unfavorite logic
                user.favorite_comments.remove(comment)
            else:
                # Favorite logic
                user.favorite_comments.add(comment)
                favorites = [n.text for n in user.favorite_comments.all()]
                print(f"Current favorite comments for {user.email}: {favorites}")
            
            # Redirect back to the same page to show updated status
            return redirect('news:favoriteComments_list')

    return login(request)

@csrf_exempt
def hide_submission(request, submission_id):
    user_data = request.session.get('user_data')

    if user_data:
        news_item = get_object_or_404(News, id=submission_id)
        user = CustomUser.objects.get(email=user_data['email'])

        if not HiddenNews.objects.filter(user=user, news=news_item).exists():
            HiddenNews.objects.create(user=user, news=news_item, hidden_at=timezone.now())
            news_item.is_hidden = True
            news_item.save(update_fields=['is_hidden'])
            print(f"News {news_item.title} has been hidden for {user.email}")
        else:
            print(f"News {news_item.title} is already hidden for {user.email}")

        next_url = request.GET.get('next', 'news:news_list')
        return redirect(next_url)

    return login(request)


def hidden_submissions(request):
    user_data = request.session.get('user_data')
    if user_data:
        user = CustomUser.objects.get(email=user_data['email'])
        
        hidden_news = News.objects.filter(id__in=HiddenNews.objects.filter(user=user).values('news'))

        return render(request, 'hidden_submissions.html', {'hidden_news': hidden_news})

    return redirect('news:sign_in') 

@csrf_exempt
def unhide_submission(request, submission_id):
    user_data = request.session.get('user_data')

    if user_data:
        news_item = get_object_or_404(News, id=submission_id)
        user = CustomUser.objects.get(email=user_data['email'])

        HiddenNews.objects.filter(user=user, news=news_item).delete()

        news_item.is_hidden = False
        news_item.save(update_fields=['is_hidden'])

        print(f"La noticia \"{news_item.title}\" ha sido desocultada.")

        return redirect('news:hidden_submissions')  

    return login(request)


class ThreadListView(ListView):
    model = Thread
    template_name = 'threads.html' 
    context_object_name = 'threads'