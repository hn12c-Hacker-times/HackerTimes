# Generated by Django 4.2.16 on 2024-11-10 19:35

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('News', '0003_hiddennews'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='hiddennews',
            unique_together={('user', 'news')},
        ),
    ]
