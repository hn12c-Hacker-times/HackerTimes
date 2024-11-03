from django import forms
from .models import News, CustomUser  # Asegúrate de importar tu modelo News

class NewsForm(forms.ModelForm):
    class Meta:
        model = News
        fields = ['title', 'url', 'text']  # Especifica los campos que quieres incluir en el formulario

class UserForm(forms.ModelForm):
    banner_file = forms.ImageField(required=False)
    avatar_file = forms.ImageField(required=False)
    class Meta:
        model = CustomUser
        fields = ['about']  # Especifica los campos que quieres incluir en el formulario