from django.shortcuts import render,redirect
from django.views.generic import ListView
from django.utils import timezone
from .models import News, Comments
from .forms import NewsForm  

# Create your views here.

# Vista de la lista de news
class NewListView(ListView):
    model = News
    template_name = 'Newslist.html'
    context_object_name = 'New'

# Vista de la lista de comments
class CommentListView(ListView):
    model = Comments
    template_name = 'Comments_list.html'
    context_object_name = 'books'

# Vista para crear una nueva News
def create_news(request):
    if request.method == "POST":
        form = NewsForm(request.POST)
        if form.is_valid():
            news = form.save(commit=False) 
            news.author = 'default_author'  # Establece el autor hardcoded
            news.published_date = timezone.now()
            news.save()
            return redirect('news:news_list')  # Redirige a la página 'newest'
    else:
        form = NewsForm()
    return render(request, 'submit.html', {'form': form})