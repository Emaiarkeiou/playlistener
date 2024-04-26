from django.db import models
from django.contrib.auth.models import User

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

    #Playlist ha 2 attributi nel DB per indicare lo user collegato:
    # user: serve per fare un collegamento con Utente, es: con user.utente.cover riesco a prendere l'immagine
    # user_id: serve per confrontare solo l'id dello user collegato
    user = models.ForeignKey(User, on_delete=models.CASCADE)  
    """
    
    AGGIUNGERE METODO CHE ELIMINA LA FOTO
    
    
    """
    class Meta:
        ordering = ['nome']

    #Metodi
    def __str__(self):
        return self.nome
    
