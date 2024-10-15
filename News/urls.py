from django.urls import path
from .views import NewListView


urlpatterns = [
    path('', NewListView.as_view(), name='News-list'),
]