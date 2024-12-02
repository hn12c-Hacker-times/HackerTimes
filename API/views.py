from django.http import Http404
from django.shortcuts import get_object_or_404, render
from django.views.generic import ListView, DetailView, View
from django.utils import timezone
from django.conf import settings
from rest_framework import viewsets, status, generics
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.viewsets import ModelViewSet
from rest_framework import permissions
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.core.exceptions import ValidationError
from rest_framework.authentication import SessionAuthentication, TokenAuthentication
from rest_framework.authtoken.models import Token
from News.models import News, Comments, CustomUser, HiddenNews, Thread
from .serializers import NewsSerializer, CommentsSerializer, CustomUserSerializer, HiddenNewsSerializer, ThreadSerializer, AskSerializer, SubmitSerializer
import tldextract, boto3

# Create your views here.
"""
    Los métodos con rest frameworks cambian de nombre un poco, por ejemplo:
    - get() -> list()
    - (específico con pk en el path)get() -> retrieve()
    - post() -> create()
    - put() -> update()
    - delete() -> destroy()
    - patch() -> partial_update()
    - head() -> retrieve()
    - options() -> options()
    - etc.
    
    Pero siempre podéis crear un metodo propio y importalo en el urls.py como una view indicando el método. Por ejemplo:
    path('API/X/', {tu viewset X}.as_view({'post': '{tu_funcion def X}'}), name='X'),
"""

def calculate_relevance(points, published_date):
    # Calculate the time difference in hours
    hours_since_posted = (timezone.now() - published_date).total_seconds() / 3600
    # Relevance formula: adjust as needed to fine-tune the balance
    relevance_score = ((points + 1) / (1 + hours_since_posted))
    return relevance_score

def annotate_user_votes(news_list, user_email):
    if user_email:
        for news_item in news_list:
            news_item.user_has_voted = news_item.voters.filter(email=user_email).exists()
    else:
        for news_item in news_list:
            news_item.user_has_voted = False
    return news_list

def validate_api_key(request):
    """
    Valida la clau API i retorna l'usuari associat.
    """
    api_key = request.headers.get('X-API-Key')
    if not api_key:
        return None, Response({"error": "Cal proporcionar una clau API."}, status=status.HTTP_401_UNAUTHORIZED)

    try:
        user = CustomUser.objects.get(api_key=api_key)
        return user, None
    except CustomUser.DoesNotExist:
        return None, Response({"error": "Clau API no vàlida."}, status=status.HTTP_401_UNAUTHORIZED)

def get_news_or_404(pk):
    """
    Retorna la notícia pel seu `pk` o genera un error personalitzat en català.
    """
    try:
        return News.objects.get(id=pk)
    except News.DoesNotExist:
        raise Http404("No s'ha trobat cap notícia amb aquest identificador.")

def get_comment_or_404(pk):
    """
    Retorna el comentari pel seu `pk` o genera un error personalitzat en català.
    """
    try:
        return Comments.objects.get(id=pk)
    except Comments.DoesNotExist:
        raise Http404("No s'ha trobat cap comentari amb aquest identificador.")

class NewListViewSet(viewsets.ModelViewSet):
    queryset = News.objects.all()
    serializer_class = NewsSerializer
    
    def list(self, request, *args, **kwargs):
        user_data = self.request.session.get('user_data')
        name = request.query_params.get("name","")
        user_email = user_data.get('email') if user_data else None
        name = request.query_params.get("name","")
        username = request.query_params.get("username","")
        email = request.query_params.get("email","")

        if name:
            queryset = News.objects.filter(title__icontains=name)
        else:
            queryset = News.objects.all()
        if username:
            author = CustomUser.objects.filter(username=username).first()
            if author:
                queryset = queryset.filter(author=author.email)
        if email:
            queryset = queryset.filter(author=email)

        if user_data:
            user = CustomUser.objects.get(email=user_data['email'])
            #print(f"User data: {user_data}")  # Ver el usuario y su información

            # Obtener las noticias ocultas de ese usuario
            hidden_news_ids = HiddenNews.objects.filter(user=user).values_list('news_id', flat=True)
            #print(f"Hidden news IDs: {list(hidden_news_ids)}")  # Ver los IDs de noticias ocultas
            
            # Excluir las noticias ocultas para el usuario actual y ordenarlas por puntos
            queryset = queryset.filter(is_hidden=False).exclude(id__in=hidden_news_ids)

            # Calculate relevance for each item and sort manually
            news_list = list(queryset)
            news_list.sort(
                key=lambda news: calculate_relevance(news.points, news.published_date),
                reverse=True  # Ensures descending order
            )
            sorted_queryset = News.objects.filter(id__in=[news.id for news in news_list])
            return Response(NewsSerializer(annotate_user_votes(sorted_queryset, user_email), many=True).data, status=status.HTTP_200_OK)

        # Si el usuario no está logueado, mostrar todas las noticias
        
        # Calculate relevance for each item and sort manually
        news_list = list(queryset)
        news_list.sort(
            key=lambda news: calculate_relevance(news.points, news.published_date),
            reverse=True  # Ensures descending order
        )
        sorted_queryset = News.objects.filter(id__in=[news.id for news in news_list])
        return Response(NewsSerializer(sorted_queryset, many=True).data, status=status.HTTP_200_OK)


class AskViewSet(viewsets.ModelViewSet):
    queryset = News.objects.filter(url='').order_by('-published_date')  # Solo las publicaciones tipo Ask
    serializer_class = AskSerializer

    def list(self, request, *args, **kwargs):
        # Calcular relevancia y ordenar
        print("Se accedió al endpoint de AskViewSet")
        asks_list = list(self.queryset)
        asks_list.sort(
            key=lambda ask: calculate_relevance(ask.points, ask.published_date),
            reverse=True  # Orden descendente
        )

        # Anotar si el usuario ha votado en los asks (si hay un usuario logueado)
        user_email = request.user.email if request.user.is_authenticated else None
        annotated_asks = annotate_user_votes(asks_list, user_email)

        # Serializar los datos
        serializer = self.get_serializer(annotated_asks, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class NewestListViewSet(viewsets.ModelViewSet):
    queryset = News.objects.all()
    serializer_class = NewsSerializer
    
    def list(self, request, *args, **kwargs):
        user_data = self.request.session.get('user_data')
        user_email = user_data.get('email') if user_data else None
        
        name = request.query_params.get("name","")
        username = request.query_params.get("username","")
        email = request.query_params.get("email","")
        queryset = News.objects.all()
        if name:
            queryset = queryset.filter(title__icontains=name)

        if username:
            author = CustomUser.objects.filter(username=username).first()
            if author:
                queryset = queryset.filter(author=author.email)
            else:
                queryset = News.objects.none()

        if email:
            queryset = queryset.filter(author=email)

        queryset.filter(is_hidden=False).order_by('-published_date')
        queryset = annotate_user_votes(queryset, user_email)
        return Response(NewsSerializer(queryset, many=True).data, status=status.HTTP_200_OK)

class SubmitViewSet(viewsets.ModelViewSet):
    queryset = News.objects.all()
    serializer_class = NewsSerializer
    
    def get_serializer_context(self):
        """
        Extra context provided to the serializer class.
        """
        context = super().get_serializer_context()
        # Si hay API key, añadir el usuario al contexto
        api_key = self.request.META.get('HTTP_X_API_KEY') or self.request.query_params.get('api_key')
        if api_key:
            try:
                user = CustomUser.objects.get(api_key=api_key)
                self.request.user = user
            except CustomUser.DoesNotExist:
                pass
        return context
    
    def create(self, request, *args, **kwargs):
        # Verificar API key
        api_key = request.META.get('HTTP_X_API_KEY') or request.query_params.get('api_key')
        if not api_key:
            return Response(
                {"error": "API key is required"}, 
                status=status.HTTP_401_UNAUTHORIZED
            )

        try:
            user = CustomUser.objects.get(api_key=api_key)
            request.user = user  # Asignar el usuario a la request
            
            # Preparar los datos
            data = request.data.copy()
            
            serializer = self.get_serializer(data=data)
            if serializer.is_valid():
                serializer.save()  # El autor se asignará automáticamente en el serializer
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            
        except CustomUser.DoesNotExist:
            return Response(
                {"error": "Invalid API key"}, 
                status=status.HTTP_401_UNAUTHORIZED
            )
        except Exception as e:
            return Response(
                {"error": str(e)}, 
                status=status.HTTP_400_BAD_REQUEST
            )

    def retrieve(self, request, pk=None):
        try:
            print(pk)
            # Obtener la submission específica
            submission = News.objects.get(id=pk)
            print(id)
            # Serializar y devolver los datos
            serializer = self.get_serializer(submission)
            return Response(serializer.data, status=status.HTTP_200_OK)
            
        except News.DoesNotExist:
            return Response(
                {"error": "La submission no existeix"}, 
                status=status.HTTP_404_NOT_FOUND
            )

    def update(self, request, pk=None):
        # Verificar API key
        key = request.headers.get('X-API-Key')
        if not key:
            return Response({"error": "L'usuari no ha iniciat sessió"}, status=status.HTTP_401_UNAUTHORIZED)
            
        try:
            # Obtener usuario
            user = CustomUser.objects.get(api_key=key)
            
            # Obtener submission
            submission = News.objects.get(id=pk)
            
            # Verificar autoría
            if submission.author != user:
                return Response({"error": "No tens permisos per editar aquesta submission"}, 
                            status=status.HTTP_403_FORBIDDEN)

            # Validar campos permitidos
            allowed_fields = ["title", "text"] if not submission.url else ["title", "url"]
            for key in request.data.keys():
                if key not in allowed_fields:
                    return Response(
                        {"error": f"No es pot modificar el camp {key}, o aquest no existeix."}, 
                        status=status.HTTP_400_BAD_REQUEST
                    )

            # Usar el serializer para actualizar
            serializer = self.get_serializer(submission, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data, status=status.HTTP_200_OK)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        except CustomUser.DoesNotExist:
            return Response({"error": "L'usuari no existeix"}, 
                        status=status.HTTP_404_NOT_FOUND)
        except News.DoesNotExist:
            return Response({"error": "La submission no existeix"}, 
                        status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"error": str(e)}, 
                        status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, submission_id):
        # Obtener la clave API de las cabeceras de la solicitud
        key = request.headers.get('X-API-Key')
        if not key:
            return Response({"error": "L'usuari no ha iniciat sessió"}, status=status.HTTP_401_UNAUTHORIZED)

        # Intentar obtener al usuario mediante la clave API
        try:
            user = CustomUser.objects.get(api_key=key)
        except CustomUser.DoesNotExist:
            return Response({"error": "L'usuari no existeix"}, status=status.HTTP_404_NOT_FOUND)
        except Exception:
            return Response({"error": "Api-key amb format incorrecte"}, status=status.HTTP_400_BAD_REQUEST)

        # Intentar obtener la submission a eliminar
        try:
            submission = News.objects.get(id=submission_id)
        except News.DoesNotExist:
            return Response({"error": "La submission no existeix"}, status=status.HTTP_404_NOT_FOUND)

        # Verificar que el usuario es el autor de la submission
        if submission.author != user:
            return Response({"error": "No tens permisos per eliminar aquesta submission"}, status=status.HTTP_403_FORBIDDEN)

        # Eliminar la submission
        submission.delete()

        return Response({"detail": "Submission esborrada correctament"}, status=status.HTTP_204_NO_CONTENT)  

class CustomUserViewSet(viewsets.ModelViewSet):
    queryset = CustomUser.objects.all()
    serializer_class = CustomUserSerializer
    
    def list(self, request):
        key = request.headers.get('X-API-Key')
        if not key:
            return Response({"error": "L'usuari no ha iniciat sessió"},status=status.HTTP_401_UNAUTHORIZED)
        
        try:
            user = CustomUser.objects.get(api_key=key)
        except CustomUser.DoesNotExist:
            return Response({"error": "L'usuari no existeix"},status=status.HTTP_404_NOT_FOUND)
        except Exception:
            return Response({"error": "Api-key amb format incorrecte"},status=status.HTTP_400_BAD_REQUEST)

        if user:
            return Response(CustomUserSerializer(user).data, status=status.HTTP_200_OK)  # Renderiza el html

    def retrieve(self, request, email, *args, **kwargs):
        
        try:
            user = CustomUser.objects.get(email=email)
        except CustomUser.DoesNotExist:
            return Response({"error": "L'usuari no existeix"}, status=status.HTTP_404_NOT_FOUND)
        return Response(CustomUserSerializer(user).data, status=status.HTTP_200_OK)

    def create(self, request):
        serializer = CustomUserSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


    def update(self,request):
        serializer = CustomUserSerializer(data=request.data)


        key = request.headers.get('X-API-Key')
        if not key:
            return Response({"error": "L'usuari no ha iniciat sessió"},status=status.HTTP_401_UNAUTHORIZED)

        try:
            user = CustomUser.objects.get(api_key=key)
        except CustomUser.DoesNotExist:
            return Response({"error": "L'usuari no existeix"},status=status.HTTP_404_NOT_FOUND)
        except Exception:
            return Response({"error": "Api-key amb format incorrecte"},status=status.HTTP_400_BAD_REQUEST)

        for key, value in request.data.items():
            if key not in ["username", "about","banner_file", "avatar_file", "remove_banner", "remove_avatar"]:
                return Response({"error": "No es pot modificar el camp, o aquest no existeix " + key}, status=status.HTTP_400_BAD_REQUEST)
            elif key != "banner" and key != "avatar" and key != "remove_banner" and key != "remove_avatar":
                if request.data[key] != '':
                    if key == 'username':
                        try:
                            user.username = value
                            user.full_clean()
                        except ValidationError as e:
                            return Response({"error": "El nom d'usuari ja existeix"}, status=status.HTTP_400_BAD_REQUEST)
                    setattr(user, key, value)


        if 'remove_banner' in request.data:
            user.banner = 'https://hn12c-hackertimes.s3.us-east-1.amazonaws.com/banners/DefaultBanner.jpg'  #Reinicia el campo en el modelo
            user.save()  #Guarda el usuario después de eliminar los archivos, si es necesario
            
        if 'remove_avatar' in request.data:
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
        user.full_clean()
        user.save()
        return Response(CustomUserSerializer(user).data, status=status.HTTP_200_OK)


    def destroy(self,request):
        
        key = request.headers.get('X-API-Key')
        if not key:
            return Response({"error": "L'usuari no ha iniciat sessió"},status=status.HTTP_401_UNAUTHORIZED)

        try:
            user = CustomUser.objects.get(api_key=key)
        except CustomUser.DoesNotExist:
            return Response({"error": "L'usuari no existeix"},status=status.HTTP_404_NOT_FOUND)
        except Exception:
            return Response({"error": "Api-key amb format incorrecte"},status=status.HTTP_400_BAD_REQUEST)
        user.delete()

        return Response({'detail: Usuari esborrat correctament'}, status=status.HTTP_204_NO_CONTENT)


class ThreadViewSet(viewsets.ModelViewSet):
    queryset = Thread.objects.all().order_by('-updated_at')
    serializer_class = ThreadSerializer

    def list(self, request, *args, **kwargs):
        # Verificar API key
        api_key = request.headers.get('X-API-Key') or request.query_params.get('api_key')
        if not api_key:
            return Response(
                {"error": "API key is required"}, 
                status=status.HTTP_401_UNAUTHORIZED
            )

        try:
            # Obtener usuario autenticado mediante la API key
            user = CustomUser.objects.get(api_key=api_key)

            # Obtener los comentarios del usuario
            comments = Comments.objects.filter(author=user)

            threads = []
            for comment in comments:
                # Verificar si el comentario es una respuesta
                if comment.parent:
                    parent_thread = Thread.objects.filter(comments=comment.parent).first()
                    if parent_thread:
                        thread = parent_thread
                    else:
                        thread = Thread.objects.create(title=comment.parent.text)
                        thread.comments.add(comment.parent)
                        thread.save()
                else:
                    # Si no es respuesta, crear un nuevo thread
                    thread = Thread.objects.filter(comments=comment).first()
                    if not thread:
                        thread = Thread.objects.create(title=comment.text)
                    thread.comments.add(comment)
                    thread.save()

                # Actualizar fecha de última publicación
                last_comment = comment.replies.last() if comment.replies.exists() else comment
                thread.updated_at = last_comment.published_date
                thread.save()

                if thread not in threads:
                    threads.append(thread)

            # Ordenar threads por la última actualización
            threads.sort(key=lambda t: t.updated_at, reverse=True)

            # Serializar threads
            serializer = self.get_serializer(threads, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)

        except CustomUser.DoesNotExist:
            return Response(
                {"error": "Invalid API key"}, 
                status=status.HTTP_401_UNAUTHORIZED
            )
        except Exception as e:
            return Response(
                {"error": str(e)}, 
                status=status.HTTP_400_BAD_REQUEST
            )

    
class NewsVoteViewSet(viewsets.ViewSet):
    """
    ViewSet per votar i desvotar notícies.
    """

    def create(self, request, pk=None):
        """
        Crida API per votar una notícia.
        """
        user, error_response = validate_api_key(request)
        if error_response:
            return error_response

        news = get_news_or_404(pk)

        if user == news.author:
            return Response({"error": "No pots votar les teves pròpies notícies."}, status=status.HTTP_403_FORBIDDEN)

        if user in news.voters.all():
            return Response({"error": "L'usuari ja ha votat aquesta notícia."}, status=status.HTTP_400_BAD_REQUEST)

        # Afegeix el vot
        news.voters.add(user)
        news.points += 1
        news.save()

        # Actualitza el karma de l'autor
        news.author.karma += 1
        news.author.save()

        return Response({
            "message": "Vot registrat correctament.",
            "news_id": news.id,
            "current_votes": news.points
        }, status=status.HTTP_201_CREATED)

    def delete(self, request, pk=None):
        """
        Crida API per eliminar un vot d'una notícia.
        """
        user, error_response = validate_api_key(request)
        if error_response:
            return error_response

        news = get_news_or_404(pk)

        if user not in news.voters.all():
            return Response({"error": "L'usuari no ha votat aquesta notícia."}, status=status.HTTP_400_BAD_REQUEST)

        # Elimina el vot
        news.voters.remove(user)
        news.points -= 1
        news.save()

        # Actualitza el karma de l'autor
        news.author.karma = max(0, news.author.karma - 1)
        news.author.save()

        return Response({
            "message": "Vot eliminat correctament.",
            "news_id": news.id,
            "current_votes": news.points
        }, status=status.HTTP_200_OK)
    
class CommentVoteViewSet(viewsets.ViewSet):
    """
    ViewSet per votar i desvotar comentaris.
    """

    def create(self, request, pk=None):
        """
        Crida API per votar un comentari.
        """
        user, error_response = validate_api_key(request)
        if error_response:
            return error_response

        comment = get_comment_or_404(pk)

        if user == comment.author:
            return Response({"error": "No pots votar els teus propis comentaris."}, status=status.HTTP_403_FORBIDDEN)

        if user in comment.voters.all():
            return Response({"error": "L'usuari ja ha votat aquest comentari."}, status=status.HTTP_400_BAD_REQUEST)

        # Afegeix el vot
        comment.voters.add(user)
        comment.save()

        return Response({
            "message": "Vot registrat correctament.",
            "comment_id": comment.id
        }, status=status.HTTP_201_CREATED)

    def delete(self, request, pk=None):
        """
        Crida API per eliminar un vot d'un comentari.
        """
        user, error_response = validate_api_key(request)
        if error_response:
            return error_response

        comment = get_comment_or_404(pk)

        if user not in comment.voters.all():
            return Response({"error": "L'usuari no ha votat aquest comentari."}, status=status.HTTP_400_BAD_REQUEST)

        # Elimina el vot
        comment.voters.remove(user)
        comment.save()

        return Response({
            "message": "Vot eliminat correctament.",
            "comment_id": comment.id
        }, status=status.HTTP_200_OK)
    
class FavoriteNewsViewSet(viewsets.ViewSet):
    """
    API ViewSet per gestionar les notícies preferides d'un usuari.
    """

    def list(self, request):
        """
        Crida API per obtenir les notícies preferides d'un usuari.
        """
        username = request.query_params.get('username')
        if not username:
            return Response({"error": "Cal proporcionar un 'username'."}, status=status.HTTP_400_BAD_REQUEST)

        # Recuperar l'usuari pel username
        user = get_object_or_404(CustomUser, username=username)

        # Recuperar les notícies preferides de l'usuari
        favorite_news = user.favorite_news.all().order_by('-published_date')
        serializer = NewsSerializer(favorite_news, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def create(self, request, pk=None):
        """
        Afegir una notícia a la llista de preferits de l'usuari autenticat.
        """
        user, error_response = validate_api_key(request)
        if error_response:
            return error_response

        news = get_news_or_404(pk)
        if news in user.favorite_news.all():
            return Response({"error": "La notícia ja està als preferits."}, status=status.HTTP_400_BAD_REQUEST)

        # Afegir als preferits
        user.favorite_news.add(news)
        return Response({"message": "Notícia afegida als preferits.", "news_id": news.id}, status=status.HTTP_201_CREATED)

    def destroy(self, request, pk=None):
        """
        Eliminar una notícia de la llista de preferits de l'usuari autenticat.
        """
        user, error_response = validate_api_key(request)
        if error_response:
            return error_response

        news = get_news_or_404(pk)
        if news not in user.favorite_news.all():
            return Response({"error": "La notícia no està als preferits."}, status=status.HTTP_400_BAD_REQUEST)

        # Eliminar dels preferits
        user.favorite_news.remove(news)
        return Response({"message": "Notícia eliminada dels preferits.", "news_id": news.id}, status=status.HTTP_200_OK)


class FavoriteCommentsViewSet(viewsets.ViewSet):
    """
    API ViewSet per gestionar els comentaris preferits d'un usuari.
    """

    def list(self, request):
        """
        Crida API per obtenir els comentaris preferits d'un usuari.
        """
        username = request.query_params.get('username')
        if not username:
            return Response({"error": "Cal proporcionar un 'username'."}, status=status.HTTP_400_BAD_REQUEST)

        # Recuperar l'usuari pel username
        user = get_object_or_404(CustomUser, username=username)

        # Recuperar els comentaris preferits de l'usuari
        favorite_comments = user.favorite_comments.all().order_by('-published_date')
        serializer = CommentsSerializer(favorite_comments, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def create(self, request, pk=None):
        """
        Afegir un comentari a la llista de preferits de l'usuari autenticat.
        """
        user, error_response = validate_api_key(request)
        if error_response:
            return error_response

        comment = get_comment_or_404(pk)
        if comment in user.favorite_comments.all():
            return Response({"error": "El comentari ja està als preferits."}, status=status.HTTP_400_BAD_REQUEST)

        # Afegir als preferits
        user.favorite_comments.add(comment)
        return Response({"message": "Comentari afegit als preferits.", "comment_id": comment.id}, status=status.HTTP_201_CREATED)

    def destroy(self, request, pk=None):
        """
        Eliminar un comentari de la llista de preferits de l'usuari autenticat.
        """
        user, error_response = validate_api_key(request)
        if error_response:
            return error_response

        comment = get_comment_or_404(pk)
        if comment not in user.favorite_comments.all():
            return Response({"error": "El comentari no està als preferits."}, status=status.HTTP_400_BAD_REQUEST)

        # Eliminar dels preferits
        user.favorite_comments.remove(comment)
        return Response({"message": "Comentari eliminat dels preferits.", "comment_id": comment.id}, status=status.HTTP_200_OK)

class VotedNewsViewSet(viewsets.ViewSet):
    """
    API ViewSet per obtenir les notícies votades per un usuari.
    """

    def list(self, request):
        """
        Crida API per obtenir les notícies votades per un usuari.
        """
        user, error_response = validate_api_key(request)
        if error_response:
            return error_response

        # Recuperar les notícies votades
        voted_news = user.voted_news.all().order_by('-published_date')
        serializer = NewsSerializer(voted_news, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
class VotedCommentsViewSet(viewsets.ViewSet):
    """
    API ViewSet per obtenir els comentaris votats per un usuari.
    """

    def list(self, request):
        """
        Crida API per obtenir els comentaris votats per un usuari.
        """
        user, error_response = validate_api_key(request)
        if error_response:
            return error_response

        # Recuperar els comentaris votats
        voted_comments = user.voted_comments.all().order_by('-published_date')
        serializer = CommentsSerializer(voted_comments, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
class CommentViewSet(viewsets.ViewSet):
    """
    API ViewSet per gestionar els comentaris.
    """
    def list(self, request):
        """
        Retorna una llista de comentaris o els comentaris d'un usuari si s'especifica el `username`.
        """
        username = request.query_params.get('username')
        if username:
            # Recuperar l'usuari pel username
            user = get_object_or_404(CustomUser, username=username)

            # Recuperar els comentaris de l'usuari
            comments = Comments.objects.filter(author=user).order_by('-published_date')
            serializer = CommentsSerializer(comments, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)

        # Recuperar tots els comentaris si no s'especifica el `username`
        comments = Comments.objects.all().order_by('-published_date')
        serializer = CommentsSerializer(comments, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    def retrieve(self, request, pk=None):
        """
        Retorna un comentari específic pel seu identificador.
        """
        comment = get_comment_or_404(pk)
        serializer = CommentsSerializer(comment)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def create(self, request):
        """
        Crear un nou comentari per a una notícia (sense pare).
        """
        user, error_response = validate_api_key(request)
        if error_response:
            return error_response

        news_id = request.data.get("news_id")
        text = request.data.get("text")
        if not news_id or not text:
            return Response({"error": "S'han de proporcionar tant el 'news_id' com el 'text'."}, status=status.HTTP_400_BAD_REQUEST)

        news = get_news_or_404(news_id)

        comment = Comments.objects.create(text=text, author=user, New=news)
        serializer = CommentsSerializer(comment)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'])
    def reply(self, request, pk=None):
        """
        Crear una resposta a un comentari existent (pare).
        """
        user, error_response = validate_api_key(request)
        if error_response:
            return error_response

        parent = get_comment_or_404(pk)
        text = request.data.get("text")
        if not text:
            return Response({"error": "S'ha de proporcionar el 'text' per al comentari."}, status=status.HTTP_400_BAD_REQUEST)

        comment = Comments.objects.create(text=text, author=user, parent=parent, New=parent.New)
        serializer = CommentsSerializer(comment)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def update(self, request, pk=None):
        """
        Editar un comentari existent.
        """
        user, error_response = validate_api_key(request)
        if error_response:
            return error_response

        comment = get_comment_or_404(pk)
        if comment.author != user:
            return Response({"error": "No pots editar comentaris d'un altre usuari."}, status=status.HTTP_403_FORBIDDEN)

        text = request.data.get("text")
        if not text:
            return Response({"error": "S'ha de proporcionar el 'text' per actualitzar el comentari."}, status=status.HTTP_400_BAD_REQUEST)

        comment.text = text
        comment.save()
        serializer = CommentsSerializer(comment)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def destroy(self, request, pk=None):
        """
        Eliminar un comentari existent.
        """
        user, error_response = validate_api_key(request)
        if error_response:
            return error_response

        comment = get_comment_or_404(pk)
        if comment.author != user:
            return Response({"error": "No pots eliminar comentaris d'un altre usuari."}, status=status.HTTP_403_FORBIDDEN)

        comment.delete()
        return Response({"message": "Comentari eliminat correctament."}, status=status.HTTP_200_OK)


class HideSubmissionViewSet(viewsets.ViewSet):
    """
    ViewSet per amagar una submission.
    """

    def create(self, request, pk=None):
        """
        Crida API per amagar una submission.
        """
        # Validar la API key
        user, error_response = validate_api_key(request)
        if error_response:
            return error_response

        # Obtenir la submission
        try:
            news_item = News.objects.get(id=pk)
        except News.DoesNotExist:
            return Response({"error": "La submission no existeix."}, status=status.HTTP_404_NOT_FOUND)

        # Verificar si ja està amagada
        if HiddenNews.objects.filter(user=user, news=news_item).exists():
            return Response({"error": "Aquesta submission ja està amagada."}, status=status.HTTP_400_BAD_REQUEST)

        # Amagar la submission
        HiddenNews.objects.create(user=user, news=news_item, hidden_at=timezone.now())
        news_item.is_hidden = True
        news_item.save(update_fields=["is_hidden"])

        return Response({
            "message": "La submission s'ha amagat correctament.",
            "submission_id": news_item.id
        }, status=status.HTTP_201_CREATED)


class UnhideSubmissionViewSet(viewsets.ViewSet):
    """
    ViewSet per desamagar una submission.
    """

    def delete(self, request, pk=None):
        """
        Crida API per desamagar una submission.
        """
        # Validar la API key
        user, error_response = validate_api_key(request)
        if error_response:
            return error_response

        # Obtenir la submission amagada
        try:
            news_item = News.objects.get(id=pk)
        except News.DoesNotExist:
            return Response({"error": "La submission no existeix."}, status=status.HTTP_404_NOT_FOUND)

        # Comprovar si la submission està amagada
        hidden_news = HiddenNews.objects.filter(user=user, news=news_item).first()
        if not hidden_news:
            return Response({"error": "La submission no està amagada."}, status=status.HTTP_400_BAD_REQUEST)

        # Eliminar la submission amagada
        hidden_news.delete()
        news_item.is_hidden = False
        news_item.save(update_fields=["is_hidden"])

        return Response({
            "message": "La submission s'ha desamagat correctament.",
            "submission_id": news_item.id
        }, status=status.HTTP_200_OK)


class HiddenSubmissionsViewSet(viewsets.ViewSet):
    """
    ViewSet per obtenir les submissions amagades d'un usuari.
    """

    def list(self, request):
        """
        Crida API per obtenir totes les submissions amagades per l'usuari.
        """
        # Validar la API key
        user, error_response = validate_api_key(request)
        if error_response:
            return error_response

        # Obtenir les submissions amagades
        hidden_submissions = HiddenNews.objects.filter(user=user).select_related('news')

        # Serialitzar les submissions amagades
        hidden_news_data = [
            {
                "submission_id": hidden_submission.news.id,
                "title": hidden_submission.news.title,
                "url": hidden_submission.news.url,
                "text": hidden_submission.news.text,
                "hidden_at": hidden_submission.hidden_at,
            }
            for hidden_submission in hidden_submissions
        ]

        return Response({
            "hidden_submissions": hidden_news_data
        }, status=status.HTTP_200_OK)
