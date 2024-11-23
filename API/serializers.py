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


class SubmitSerializer(serializers.ModelSerializer):
    class Meta:
        model = News
        fields = ['title', 'url', 'text', 'author']
        read_only_fields = ['author']  # El autor se asigna automáticamente
        
    def validate(self, data):
        """
        Validar los datos del submit
        """
        # Verificar que hay URL o texto, pero no necesariamente ambos
        if not data.get('url') and not data.get('text'):
            raise serializers.ValidationError(
                "Either URL or text must be provided"
            )
            
        return data
        
    def create(self, validated_data):
        """
        Crear una nueva noticia con los datos validados
        """
        # Extraer el dominio de la URL si existe
        if validated_data.get('url'):
            validated_data['urlDomain'] = tldextract.extract(validated_data['url']).domain
        else:
            validated_data['urlDomain'] = ''
            
        return super().create(validated_data)