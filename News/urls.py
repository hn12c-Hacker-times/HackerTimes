from django.urls import path
from .views import NewListView
from .views import NewestListView
from .views import CommentListView
from .views import SearchListView
from .views import AskListView
from . import views 

app_name='news'

urlpatterns = [
    path('', NewListView.as_view(), name='news_list'),
    path('submit/', views.submit, name='submit_news'),
    path('newest/', NewestListView.as_view(), name='newest_news'),
    path('ask/', AskListView.as_view(), name='ask_list'),
    path('ask/<int:ask_id>/', views.ask_detail, name='ask_detail'),
    path('login/', views.login, name='login'),
    path('user/', views.user_profile, name='user_profile'),
    path('logout/', views.logout, name='logout'),
    path('comments/', CommentListView.as_view(), name='comments_list'),
    path('search/', SearchListView.as_view(), name='search_list'),
]