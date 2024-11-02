from django import forms
from .models import News  # Asegúrate de importar tu modelo News

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