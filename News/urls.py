from django.urls import path
from .views import NewListView
from .views import NewestListView
from . import views 

app_name='news'

urlpatterns = [
    path('', NewListView.as_view(), name='news_list'),
    path('submit/', views.submit, name='submit_news'),
    path('newest/', NewestListView.as_view(), name='newest_news'),
    path('login/', views.login, name='login'),
    path('user/', views.user_profile, name='user_profile'),
    path('logout/', views.logout, name='logout'),
    #path('comments/', CommentListView.as_view(), name='comment_list'),
]