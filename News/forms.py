from django import forms
from .models import News, CustomUser  # Asegúrate de importar tu modelo News

class NewsForm(forms.ModelForm):
    class Meta:
        model = News
        fields = ['title', 'url', 'text']  # Especifica los campos que quieres incluir en el formulario

class AskNewsForm(forms.ModelForm):
    class Meta:
        model = News
        fields = ['title', 'text']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Añadir una etiqueta "url" sin campo de entrada
        self.url_label = "url:"
        
class UserForm(forms.ModelForm):
    banner_file = forms.ImageField(required=False)
    avatar_file = forms.ImageField(required=False)
    class Meta:
        model = CustomUser
        fields = ['about']  # Especifica los campos que quieres incluir en el formulario
