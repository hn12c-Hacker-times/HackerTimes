from django.contrib import admin
from .models import News

# Register your models here.
@admin.register(News)
class Newsadmin(admin.ModelAdmin):
    pass