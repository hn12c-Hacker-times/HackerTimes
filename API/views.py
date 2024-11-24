from django.shortcuts import render
from django.views.generic import ListView, DetailView, View
from django.utils import timezone
from rest_framework import viewsets, status, generics
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.core.exceptions import ValidationError
from rest_framework.authentication import SessionAuthentication, TokenAuthentication
from rest_framework.authtoken.models import Token
from News.models import News, Comments, CustomUser, HiddenNews, Thread
from .serializers import NewsSerializer, CommentsSerializer, CustomUserSerializer, HiddenNewsSerializer, ThreadSerializer, AskSerializer

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

class NewListView(viewsets.ModelViewSet):
    queryset = News.objects.all()
    serializer_class = NewsSerializer
    
    def list(self, request, *args, **kwargs):
        user_data = self.request.session.get('user_data')
        user_email = user_data.get('email') if user_data else None
        username = self.request.GET.get("username", "")

        if user_data:
            user = CustomUser.objects.get(email=user_data['email'])
            #print(f"User data: {user_data}")  # Ver el usuario y su información

            # Obtener las noticias ocultas de ese usuario
            hidden_news_ids = HiddenNews.objects.filter(user=user).values_list('news_id', flat=True)
            #print(f"Hidden news IDs: {list(hidden_news_ids)}")  # Ver los IDs de noticias ocultas

            # Si hay un nombre de usuario, mostrar solo las noticias de ese usuario
            if username:
                author = CustomUser.objects.filter(username=username).first()
                if author:
                    queryset = News.objects.filter(author=author, is_hidden=False).exclude(id__in=hidden_news_ids).order_by('-published_date')
                    #print(f"Query for author '{username}': {queryset}")  # Ver la consulta para el autor
                    if not queryset.exists():
                        return Response(NewsSerializer(News.objects.none(), many=True).data, status=status.HTTP_404_NOT_FOUND)
                    return Response(NewsSerializer(annotate_user_votes(queryset, user_email), many=True).data, status=status.HTTP_200_OK)
            
            # Excluir las noticias ocultas para el usuario actual y ordenarlas por puntos
            queryset = News.objects.filter(is_hidden=False).exclude(id__in=hidden_news_ids)

            # Calculate relevance for each item and sort manually
            news_list = list(queryset)
            news_list.sort(
                key=lambda news: calculate_relevance(news.points, news.published_date),
                reverse=True  # Ensures descending order
            )
            sorted_queryset = News.objects.filter(id__in=[news.id for news in news_list])
            return Response(NewsSerializer(annotate_user_votes(sorted_queryset, user_email), many=True).data, status=status.HTTP_200_OK)

        # Si el usuario no está logueado, solo mostrar las noticias no ocultas
        queryset = News.objects.filter(is_hidden=False)

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
