from django.shortcuts import render
from django.views.generic import ListView, DetailView, View
from django.utils import timezone
from django.conf import settings
from rest_framework import viewsets, status, generics
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.viewsets import ModelViewSet
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
        user = CustomUser.objects.get(email=email)

        if user:
            return Response(CustomUserSerializer(user).data, status=status.HTTP_200_OK)
        else:
            return Response({"error": "L'usuari no existeix"}, status=status.HTTP_404_NOT_FOUND)

    def create(self, request):
        serializer = CustomUserSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


    def update(self,request):
        serializer = CustomUserSerializer(data=request.data)


        if serializer.is_valid():
            serializer.save()
            key = request.headers.get('X-API-Key')
            if not key:
                return Response({"error": "L'usuari no ha iniciat sessió"},status=status.HTTP_401_UNAUTHORIZED)

            try:
                user = CustomUser.objects.get(api_key=key)
            except CustomUser.DoesNotExist:
                return Response({"error": "L'usuari no existeix"},status=status.HTTP_404_NOT_FOUND)
            except Exception:
                return Response({"error": "Api-key amb format incorrecte"},status=status.HTTP_400_BAD_REQUEST)

            if 'banner' in request.data and request.data['banner'] == '':
                user.banner = 'https://hn12c-hackertimes.s3.us-east-1.amazonaws.com/banners/DefaultBanner.jpg'  #Reinicia el campo en el modelo
                user.save()  #Guarda el usuario después de eliminar los archivos, si es necesario
                
            if 'avatar' in request.data and request.data['banner'] == '':
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
            
            return Response(CustomUserSerializer(user).data, status=status.HTTP_200_OK)

        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def destroy(self,request):
        if 'api_key' in request.data:
            user = CustomUser.objects.get(api_key=request.data['api_key'])
        else:
            return Response({"error": "L'usuari no ha iniciat sessió"},status=status.HTTP_401_UNAUTHORIZED)
        user.delete()
        return Response({'detail: Usuari esborrat correctament'}, status=status.HTTP_204_NO_CONTENT)


class ThreadViewSet(viewsets.ModelViewSet):
    queryset = Thread.objects.all().order_by('-updated_at')
    serializer_class = ThreadSerializer
    permission_classes = [IsAuthenticated]  # Requerir que el usuario esté autenticado

    def list(self, request, *args, **kwargs):
        # Verificar si el usuario está autenticado
        if not request.user.is_authenticated:
            return Response({"error": "User is not authenticated"}, status=status.HTTP_401_UNAUTHORIZED)

        # Obtener el usuario autenticado
        user = request.user

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
