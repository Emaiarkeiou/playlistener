from django.shortcuts import render, HttpResponseRedirect
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout

# Create your views here.

from .models import Album, Artista, Canzone, Playlist

def loginView(request):
    """View function for home page of site."""
    return render(request, 'login.html', context={"a":2})

def loginReq(request):
    username = request.POST['username']
    password = request.POST['password']
    user = authenticate(username=username, password=password)
    if user is not None:
        login(request, user)
        return HttpResponseRedirect('/playlistener/user/' + username) 
    else:
        return render(request, 'login.html', context={"a":2})

def logoutReq(request):
    logout(request)
    return HttpResponseRedirect('/')

def signup(request):
    """View function for home page of site."""
    return render(request, 'login.html', context={"a":2})

def user(request,username):
    """View function for home page of site."""
    if not request.user.is_authenticated:
        return HttpResponseRedirect('/')
    else:
        """ 
        
        
        DEVO AGGIUNGERE SE POSSIBILE LE IMMAGINI NEL DATABASEEEEEEEEEEE
        EEEEEEEEEEEEEE
        EEEE
        E

        
        
        """
        utente = User.objects.get(username=username) 
        lista_playlist = Playlist.objects.filter(user_id=utente.id)
        return render(request, 'user.html', context={"username":username,"playlists":lista_playlist,"prova":lista_playlist[0].user})