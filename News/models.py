from datetime import date, datetime
from django.db import models
from django import forms
from django.contrib.auth.models import AbstractUser

# Modelo de usuario personalizado
class CustomUser(models.Model):
    username = models.CharField(max_length=150)  # Campo de nombre de usuario
    email = models.EmailField(primary_key=True, max_length=254)
    created_at = models.DateTimeField(auto_now_add=True)  # Fecha de creación
    karma = models.PositiveIntegerField(default=0)  # Karma del usuario
    about = models.TextField(blank=True, null=True)  # Información sobre el usuario
    banner = models.ImageField(default='banners/DefaultBanner.jpg', upload_to='banners/', blank=True, null=True)  # Banner del usuario
    avatar = models.ImageField(upload_to='avatars/', default='avatars/DefaultProfile.png',blank=True, null=True)  # Avatar del usuario
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
    published_date = models.DateTimeField(auto_now=True)
    points = models.IntegerField(default=0) 

    def __str__(self):
        return self.title
    
class Comments(models.Model):
    text = models.CharField(max_length=1000)
    author = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    published_date = models.DateTimeField(auto_now=True)
    New = models.ForeignKey(News, on_delete=models.CASCADE)
    parent = models.ForeignKey('self', null=True, blank=True, on_delete=models.CASCADE, related_name='replies')

class Search(models.Model):
    text = models.CharField(max_length=1000)
    author = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    published_date = models.DateTimeField(auto_now=True)
    New = models.ForeignKey(News, on_delete=models.CASCADE)


    def __str__(self):
        return self.text