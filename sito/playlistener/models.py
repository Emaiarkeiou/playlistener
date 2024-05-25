from django.db import models
from django.contrib.auth.models import User
import uuid

# Create your models here.

class Utente(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    pfp = models.ImageField(null=True,blank=True)

    def __str__(self):
        return self.user.username

class Album(models.Model):
    """Album"""
    
    #Attributi
    id = models.CharField(max_length=22,primary_key=True)
    nome = models.CharField(max_length=100)
    image = models.TextField(null=True,blank=True)

    class Meta:
        ordering = ['nome']

    #Metodi
    def __str__(self):
        return self.nome
    
class Artista(models.Model):
    """Artista"""
    
    #Attributi
    id = models.CharField(max_length=22,primary_key=True)
    nome = models.CharField(max_length=100)

    class Meta:
        ordering = ['nome']

    #Metodi
    def __str__(self):
        return self.nome
    
class Canzone(models.Model):
    """Canzone"""
    
    #Attributi
    id = models.CharField(max_length=22,primary_key=True)
    nome = models.CharField(max_length=100)
    artista = models.ManyToManyField(Artista)
    album = models.ManyToManyField(Album)

    class Meta:
        ordering = ['nome']

    #Metodi
    def __str__(self):
        return self.nome

class Playlist(models.Model):
    """Playlist"""

    tags = {
        "libero":"libero",
        "sport":"sport",
        "viaggio":"viaggio",
    }
    #Attributi
    nome = models.CharField(max_length=100, default="Nuova Playlist")

    tag = models.CharField(max_length=14,choices=tags,default="libero")
    energia_min = models.FloatField(null=True,blank=True,default=0)
    durata_min = models.FloatField(null=True,blank=True)

    cover = models.ImageField(null=True,blank=True)
    desc = models.TextField(max_length=300,null=True,blank=True)
    canzone = models.ManyToManyField(Canzone,through='Ordine')

    user = models.ForeignKey(User, on_delete=models.CASCADE)  

    class Meta:
        ordering = ['nome']

    #Metodi
    def __str__(self):
        return self.nome
    
class Ordine(models.Model):
    """ Many to Many tra playlist e canzone """
    canzone = models.ForeignKey(Canzone, on_delete=models.CASCADE)
    playlist = models.ForeignKey(Playlist, on_delete=models.CASCADE)
    n = models.IntegerField()   # 0 a n-1
    def __str__(self):
        return str(self.playlist) + " - "+ str(self.n) +" - "+ str(self.canzone)