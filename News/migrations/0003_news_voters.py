# Generated by Django 5.1.2 on 2024-11-10 15:20

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('News', '0002_thread'),
    ]

    operations = [
        migrations.AddField(
            model_name='news',
            name='voters',
            field=models.ManyToManyField(blank=True, related_name='voted_news', to='News.customuser'),
        ),
    ]
