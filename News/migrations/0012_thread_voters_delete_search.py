# Generated by Django 5.1.2 on 2024-11-13 12:44

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('News', '0011_remove_thread_created_at'),
    ]

    operations = [
        migrations.AddField(
            model_name='thread',
            name='voters',
            field=models.ManyToManyField(blank=True, related_name='voted_comment_thread', to='News.customuser'),
        ),
        migrations.DeleteModel(
            name='Search',
        ),
    ]
