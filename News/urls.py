from django.urls import path
from .views import NewListView
from . import views 

app_name='news'

urlpatterns = [
    path('', NewListView.as_view(), name='news_list'),
    path('submit/', views.create_news, name='submit_news'),
    #path('comments/', CommentListView.as_view(), name='comment_list'),
]