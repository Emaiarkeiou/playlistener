from django.db import models
from django.contrib.auth.models import User

# Create your models here.

class Album(models.Model):
    """Album"""
    
    #Attributi
    id = models.CharField(max_length=22,primary_key=True)
    nome = models.CharField(max_length=100)

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
        "sp":"sport",
        "vg":"viaggio",
        "fr":""
    }
    #Attributi
    nome = models.CharField(max_length=100)
    tag = models.CharField(max_length=2,choices=tags,null=True,blank=True)
    cover = models.ImageField(null=True,blank=True)
    desc = models.TextField(max_length=300,null=True,blank=True)
    canzone = models.ManyToManyField(Canzone)
    utente = models.ForeignKey(User, on_delete=models.CASCADE)  

    class Meta:
        ordering = ['nome']

    #Metodi
    def __str__(self):
        return self.nome
