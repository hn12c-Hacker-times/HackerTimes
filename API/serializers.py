from rest_framework import serializers
from News.models import News, Comments, CustomUser, HiddenNews, Thread

class NewsSerializer(serializers.ModelSerializer):
    class Meta:
        model = News
        fields = [ 'title', 'url', 'urlDomain', 'text', 'author', 'published_date', 'points', 'is_hidden']

class CommentsSerializer(serializers.ModelSerializer):
    class Meta:
        model = Comments
        fields = [ 'text', 'author', 'published_date', 'New', 'parent']


class CustomUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = [ 'username','email', 'created_at', 'karma', 'about', 'banner', 'avatar', 'show_dead', 'no_procrastinate', 'max_visit', 'min_away', 'delay', 'favorite_news', 'favorite_comments']
        extra_kwargs = {
            'password': {'write_only': True}
        }

class HiddenNewsSerializer(serializers.ModelSerializer):
    class Meta:
        model = HiddenNews
        fields = [ 'user', 'news', 'hidden_at']

        
class ThreadSerializer(serializers.ModelSerializer):
    class Meta:
        model = Thread
        fields = [ 'title', 'comments', 'updated_at']


class AskSerializer(serializers.ModelSerializer):
    class Meta:
        model = News
        fields = ['title', 'text', 'author', 'published_date', 'points']
