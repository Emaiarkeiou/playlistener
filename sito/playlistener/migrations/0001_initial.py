# Generated by Django 5.0.4 on 2024-04-26 16:22

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Album',
            fields=[
                ('id', models.CharField(max_length=22, primary_key=True, serialize=False)),
                ('nome', models.CharField(max_length=100)),
            ],
            options={
                'ordering': ['nome'],
            },
        ),
        migrations.CreateModel(
            name='Artista',
            fields=[
                ('id', models.CharField(max_length=22, primary_key=True, serialize=False)),
                ('nome', models.CharField(max_length=100)),
            ],
            options={
                'ordering': ['nome'],
            },
        ),
        migrations.CreateModel(
            name='Canzone',
            fields=[
                ('id', models.CharField(max_length=22, primary_key=True, serialize=False)),
                ('nome', models.CharField(max_length=100)),
                ('album', models.ManyToManyField(to='playlistener.album')),
                ('artista', models.ManyToManyField(to='playlistener.artista')),
            ],
            options={
                'ordering': ['nome'],
            },
        ),
        migrations.CreateModel(
            name='Playlist',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nome', models.CharField(max_length=100)),
                ('tag', models.CharField(blank=True, choices=[('sp', 'sport'), ('vg', 'viaggio'), ('fr', '')], max_length=2, null=True)),
                ('cover', models.ImageField(blank=True, null=True, upload_to='')),
                ('desc', models.TextField(blank=True, max_length=300, null=True)),
                ('canzone', models.ManyToManyField(to='playlistener.canzone')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['nome'],
            },
        ),
        migrations.CreateModel(
            name='Utente',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('pfp', models.ImageField(blank=True, null=True, upload_to='')),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]