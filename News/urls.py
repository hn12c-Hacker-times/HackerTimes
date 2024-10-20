from django.urls import path
from .views import NewListView
from .views import NewestListView
from . import views 

app_name='news'

urlpatterns = [
    path('', NewListView.as_view(), name='news_list'),
    path('submit/', views.submit, name='submit_news'),
    path('newest/', NewestListView.as_view(), name='newest_news'),
    #path('comments/', CommentListView.as_view(), name='comment_list'),
]