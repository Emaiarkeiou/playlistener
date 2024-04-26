from django.shortcuts import render, HttpResponseRedirect
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout

# Create your views here.

from .models import Album, Artista, Canzone, Playlist


"""

GET PER I LINK/REDIRECT
POST PER LE FORM E BOTTONI SUBMIT(per input)


"""



def loginView(request):
    """View function for home page of site."""
    if request.method == 'GET':
        """ GET della pagina di login """
        return render(request, 'registration/login.html')
    elif request.method == 'POST':
        """ POST della form di login """
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(username=username, password=password)
        if user is not None:
            login(request, user)
            return HttpResponseRedirect('/playlistener/user/' + username) 
        else:
            return HttpResponseRedirect('/playlistener/login/')
    else:
        pass
    """ REDIRECT AD UNA PAGINA CHE DICE CHE HAI SBAGLIATO"""


def signupView(request):
    """View function for home page of site."""
    if request.method == 'GET':
        """ GET della pagina di singup """
        return render(request, 'registration/signup.html')
    elif request.method == 'POST':
        """ POST della form di sign up """
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(username=username, password=password)
        if user is not None:
            login(request, user)
            return HttpResponseRedirect('/playlistener/user/' + username) 
        else:
            return HttpResponseRedirect('/playlistener/login/')
    else:
        pass
    """ REDIRECT AD UNA PAGINA CHE DICE CHE HAI SBAGLIATO"""

def logoutView(request):
    if request.method == 'POST':
        logout(request)
        return HttpResponseRedirect('/')
    else:
        pass
        """ REDIRECT AD UNA PAGINA CHE DICE CHE HAI SBAGLIATO"""


def user(request,username):
    """View function for home page of site."""
    if request.method == 'GET':
        if request.user.is_authenticated:
            if request.user.username == username:
                utente = User.objects.get(username=username) 
                lista_playlist = Playlist.objects.filter(user_id=utente.id)
                return render(request, 'user.html', context={"username":username,"playlists":lista_playlist})
            else:
                """ REDIRECT AD UNA PAGINA CHE DICE CHE HAI SBAGLIATO"""
                return HttpResponseRedirect('/')
    else:
        pass
        """ REDIRECT AD UNA PAGINA CHE DICE CHE HAI SBAGLIATO"""