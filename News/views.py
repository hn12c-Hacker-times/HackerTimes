from django.shortcuts import render
from django.views.generic import ListView
from .models import News, Comments 

# Create your views here.
class NewListView(ListView):
    model = News
    template_name = 'Newslist.html'
    context_object_name = 'New'

class CommentListView(ListView):
    model = Comments
    template_name = 'Comments_list.html'
    context_object_name = 'books'