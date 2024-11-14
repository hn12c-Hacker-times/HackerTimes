from django.contrib import admin
from .models import News, CustomUser, Comments

# Register your models here.
@admin.register(News)
class Newsadmin(admin.ModelAdmin):
    pass
@admin.register(CustomUser)
class CustomUsersadmin(admin.ModelAdmin):
    pass
@admin.register(Comments)
class Comments(admin.ModelAdmin):
    pass
