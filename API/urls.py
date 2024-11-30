from django.conf import settings
from django.urls import path, include
from django.conf.urls.static import static
from .views import CommentVoteViewSet, NewListViewSet, AskViewSet, NewsVoteViewSet, SubmitViewSet, CustomUserViewSet, NewestListViewSet, ThreadViewSet
from . import views
from rest_framework.routers import DefaultRouter

app_name='API'

"""
    En rest_framework los paths se creat en un router y no hace falta indicar el método siempre las funciones se llamen igual que los métodos de rest_framework. Ej: list(), retrieve(), create(), update(), destroy(), partial_update(), etc.
    
    Pero siempre podéis crear un metodo propio y importalo en el urls.py como una view indicando el método. Por ejemplo:
    path('API/X/', {tu viewset X}.as_view({'post': '{tu_funcion def X}'}), name='X'),
    
    IMPORTANTE: Si creais un método retrieve() en un viewset por ejemplo en el path 'API/' i luego creais un path como 'API/newest/', asseguraos de que 'API/newest/' está antes que path('', include(router.urls)), porque sino interpretará 'newest' como una pk de la vista 'API/'.
"""

router = DefaultRouter()
router.register(r'ask', AskViewSet, basename='asks')
router.register(r'submit', SubmitViewSet, basename='submit')
router.register(r'user', CustomUserViewSet, basename='user')
router.register(r'newest', NewestListViewSet, basename='newest')
router.register(r'threads', ThreadViewSet, basename='threads')
router.register(r'', NewListViewSet, basename='news')
router.register(r'news-vote', NewsVoteViewSet, basename='news-vote')
router.register(r'comment-vote', CommentVoteViewSet, basename='comment-vote')

urlpatterns = [

    path('user/delete/', views.CustomUserViewSet.as_view({'delete': 'destroy'}), name='customuser_delete'),
    path('user/update/', views.CustomUserViewSet.as_view({'put': 'update'}), name='customuser_detail'),
    path('user/<str:email>/', views.CustomUserViewSet.as_view({'get': 'retrieve'}), name='customuser_detail'),
    path('news-vote/<int:pk>/', NewsVoteViewSet.as_view({'post': 'create', 'delete': 'delete'}), name='news-vote-detail'),
    path('comment-vote/<int:pk>/', CommentVoteViewSet.as_view({'post': 'create', 'delete': 'delete'}), name='comment-vote-detail'),
    path('', include(router.urls)),
]
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)