from datetime import date, datetime
from django.db import models
from django import forms
from django.contrib.auth.models import AbstractUser

# Modelo de usuario personalizado
class CustomUser(models.Model):
    username = models.CharField(max_length=150, unique=True)  # Campo de nombre de usuario
    email = models.EmailField(primary_key=True, max_length=254)
    created_at = models.DateTimeField(auto_now_add=True)  # Fecha de creación
    karma = models.PositiveIntegerField(default=0)  # Karma del usuario
    about = models.TextField(blank=True, null=True)  # Información sobre el usuario
    banner = models.URLField(default='https://hn12c-hackertimes.s3.us-east-1.amazonaws.com/banners/DefaultBanner.jpg')  # Banner del usuario
    avatar = models.URLField(default = 'https://hn12c-hackertimes.s3.us-east-1.amazonaws.com/avatars/DefaultProfile.png')  # Avatar del usuario
    show_dead = models.BooleanField(default=True)  # Mostrar elementos "muertos"
    no_procrastinate = models.BooleanField(default=False)  # Opción de "no procrastinar"
    max_visit = models.PositiveIntegerField(default=20)  # Máximo de visitas
    min_away = models.PositiveIntegerField(default=180)  # Tiempo mínimo de ausencia (en segundos)
    delay = models.PositiveIntegerField(default=0)  # Retraso en la actividad

    def __str__(self):
        return self.email

class News(models.Model):
    title = models.CharField(max_length=200)
    url = models.URLField(max_length=200, blank=True)
    urlDomain = models.CharField(max_length=200)
    text = models.TextField(max_length=200, blank=True)
    author = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    published_date = models.DateTimeField(auto_now_add=True)
    points = models.IntegerField(default=0) 
    is_hidden = models.BooleanField(default=False)
    voters = models.ManyToManyField(CustomUser, related_name='voted_news', blank=True)

    def __str__(self):
        return self.title
    
class Comments(models.Model):
    text = models.CharField(max_length=1000)
    author = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    published_date = models.DateTimeField(auto_now_add=True)
    New = models.ForeignKey(News, on_delete=models.CASCADE)
    parent = models.ForeignKey('self', null=True, blank=True, on_delete=models.CASCADE, related_name='replies')
    voters = models.ManyToManyField(CustomUser, related_name='voted_comments', blank=True)

class Search(models.Model):
    text = models.CharField(max_length=1000)
    author = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    published_date = models.DateTimeField(auto_now=True)
    New = models.ForeignKey(News, on_delete=models.CASCADE)


    def __str__(self):
        return self.text
    
class Thread(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    author = models.ForeignKey(CustomUser, on_delete=models.CASCADE)

    def __str__(self):
        return self.title


class HiddenNews(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    news = models.ForeignKey(News, on_delete=models.CASCADE)
    hidden_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'news')  # Para asegurarnos de que un usuario no pueda ocultar la misma noticia varias veces
    
    def __str__(self):
        return f"News {self.news.title} hidden by {self.user.email}"