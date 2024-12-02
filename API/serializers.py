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
        fields = ['id', 'title', 'url', 'urlDomain', 'text', 'author', 'points', 'is_hidden']
        read_only_fields = ['id', 'points', 'is_hidden', 'urlDomain', 'author']  # Incluir author aquí también
        
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
        fields = ['id', 'text', 'author', 'published_date', 'New', 'parent']


class CustomUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = [ 'username','email', 'created_at', 'karma', 'about', 'banner', 'avatar', 'show_dead', 'no_procrastinate', 'max_visit', 'min_away', 'delay', 'favorite_news', 'favorite_comments']


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
        fields = ['id', 'title', 'url', 'text', 'author']
        read_only_fields = ['id', 'author']  # El autor se asigna automáticamente

    def validate_url(self, value):
        """
        Validar el formato de la URL
        """
        if value:  # Solo validar si hay URL
            try:
                url_validator = URLValidator()
                url_validator(value)
            except ValidationError:
                raise serializers.ValidationError(
                    "Invalid URL format. Please provide a valid URL (e.g., https://example.com)"
                )
        return value
        
    def validate(self, data):
        """
        Validar los datos del submit
        """
        instance = getattr(self, 'instance', None)
        
        # Si estamos actualizando una instancia existente
        if instance:
            # Si es una ask (no tiene URL)
            if not instance.url:
                # No permitir añadir URL
                if data.get('url'):
                    raise serializers.ValidationError(
                        "Cannot add URL to an Ask submission"
                    )
            # Si es una news (tiene URL)
            else:
                # No permitir eliminar URL
                if 'url' in data and not data.get('url'):
                    raise serializers.ValidationError(
                        "News submissions must maintain a URL"
                    )
                
        # Para nuevas creaciones
        else:
            if not data.get('url') and not data.get('text'):
                raise serializers.ValidationError(
                    "Either URL or text must be provided"
                )

        return data
        
    def create(self, validated_data):
        """
        Crear una nueva noticia/ask con los datos validados
        """
        is_ask = not validated_data.get('url')

        if is_ask:
            validated_data['url'] = ''
            validated_data['urlDomain'] = ''
        else:

            if validated_data.get('url'):
                validated_data['urlDomain'] = tldextract.extract(validated_data['url']).domain
            else:
                validated_data['urlDomain'] = ''
            
        # Crear la noticia o ask
        news = News.objects.create(**validated_data)
        return news

    def update(self, instance, validated_data):
        """
        Actualizar una noticia/ask existente
        """
        # Actualizar los campos básicos
        instance.title = validated_data.get('title', instance.title)
        instance.text = validated_data.get('text', instance.text)
        
        # Manejar la URL y el dominio
        new_url = validated_data.get('url')
        if new_url is not None:  # Si se proporcionó una URL en la actualización
            if new_url:  # Si la URL no está vacía
                instance.url = new_url
                instance.urlDomain = tldextract.extract(new_url).domain
            else:  # Si la URL está vacía (convirtiendo en ask)
                instance.url = ''
                instance.urlDomain = ''
        
        instance.save()
        return instance