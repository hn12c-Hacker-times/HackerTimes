from django.conf import settings
from django.urls import path
from django.conf.urls.static import static
from .views import NewListView
from .views import NewestListView
from .views import CommentListView
from .views import SearchListView
from .views import AskListView
from .views import UserView, CustomUserDetailView
from . import views

app_name='news'

urlpatterns = [
    path('', NewListView.as_view(), name='news_list'),
    path('submit/', views.submit, name='submit_news'),
    path('newest/', NewestListView.as_view(), name='newest_news'),
    path('ask/', AskListView.as_view(), name='ask_list'),
    path('login/', views.login, name='login'),
    path('user/', UserView.as_view(), name='user_profile'),
    path('user/<str:email>/', CustomUserDetailView.as_view(), name='customuser_detail'),
    path('logout/', views.logout, name='logout'),
    path('comments/', CommentListView.as_view(), name='comments_list'),
    path('search/', SearchListView.as_view(), name='search_list'),
    path('edit/<int:news_id>/', views.edit_news, name='edit_news'),
    path('delete/<int:news_id>/', views.delete_news, name='delete_news'),
    path('item/<int:news_id>/', views.item_detail, name='item_detail'),
    path('comment/edit/<int:comment_id>/', views.edit_comment, name='edit_comment'),
    path('comment/delete/<int:comment_id>/', views.delete_comment, name='delete_comment'),
    path('item/<int:news_id>/comment/<int:comment_id>/', views.comment_context, name='comment_context'),
]
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
