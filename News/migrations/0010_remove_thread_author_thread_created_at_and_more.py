# Generated by Django 4.2.16 on 2024-11-12 01:08

from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('News', '0009_remove_thread_created_at_remove_thread_description_and_more'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='thread',
            name='author',
        ),
        migrations.AddField(
            model_name='thread',
            name='created_at',
            field=models.DateTimeField(auto_now_add=True, default=django.utils.timezone.now),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='thread',
            name='updated_at',
            field=models.DateTimeField(auto_now=True),
        ),
        migrations.AlterField(
            model_name='thread',
            name='comments',
            field=models.ManyToManyField(to='News.comments'),
        ),
        migrations.AlterField(
            model_name='thread',
            name='title',
            field=models.CharField(max_length=200),
        ),
    ]
