# Generated by Django 4.2.16 on 2024-11-11 22:31

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('News', '0007_customuser_favorite_comments_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='customuser',
            name='username',
            field=models.CharField(max_length=150, unique=True),
        ),
    ]
