# Generated by Django 5.0.4 on 2024-04-21 19:30

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('playlistener', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='playlist',
            name='cover',
            field=models.ImageField(blank=True, null=True, upload_to=''),
        ),
    ]
