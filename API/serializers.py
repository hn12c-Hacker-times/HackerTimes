from rest_framework import serializers
from News.models import News, Comments, CustomUser, HiddenNews, Thread

class NewsSerializer(serializers.ModelSerializer):
    # Hacer que author sea de solo lectura
    author = serializers.PrimaryKeyRelatedField(
        read_only=True,
        default=serializers.CurrentUserDefault()
    )

    class Meta:
        model = News
        fields = ['title', 'url', 'urlDomain', 'text', 'author', 'points', 'is_hidden']
        read_only_fields = ['points', 'is_hidden', 'urlDomain', 'author']  # Incluir author aquí también
        
    def create(self, validated_data):
        request = self.context.get('request')
        if not request or not hasattr(request, 'user'):
            raise serializers.ValidationError("No authenticated user found")
            
        validated_data['author'] = request.user
        
        # Manejar la URL y el dominio
        url = validated_data.get('url', '')
        if url:
            try:
                extracted = tldextract.extract(url)
                validated_data['urlDomain'] = extracted.domain
            except:
                validated_data['urlDomain'] = ''
        else:
            validated_data['urlDomain'] = ''
            
        return super().create(validated_data)
        
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
    comments = CommentsSerializer(many=True)  # Anidamos los comentarios en el thread

    class Meta:
        model = Thread
        fields = ['title', 'comments', 'updated_at']
        read_only_fields = ['updated_at']  # El campo `updated_at` es solo de lectura


class AskSerializer(serializers.ModelSerializer):
    class Meta:
        model = News
        fields = ['title', 'text', 'author', 'published_date', 'points']


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
