from django import forms
from .models import News  # Asegúrate de importar tu modelo News

class NewsForm(forms.ModelForm):
    class Meta:
        model = News
        fields = ['title', 'url', 'text']  # Especifica los campos que quieres incluir en el formulario
