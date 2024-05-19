from django.contrib import admin

from .models import Album, Artista, Canzone, Playlist, Utente, Ordine

admin.site.register(Album)
admin.site.register(Artista)
admin.site.register(Canzone)
admin.site.register(Playlist)
admin.site.register(Utente)
admin.site.register(Ordine)


