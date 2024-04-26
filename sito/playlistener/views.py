from django.shortcuts import render, redirect
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.db import IntegrityError

# Create your views here.

from .models import Album, Artista, Canzone, Playlist, Utente

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
        username = request.POST['username'].lower()
        password = request.POST['password']
        user = authenticate(username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect(userView, username=username) 
        else:
            return redirect(loginView)
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
        nome = request.POST['first_name']
        cognome = request.POST['last_name']
        username = request.POST['username'].lower()
        password = request.POST['password']
        if nome and cognome and username and password:
            if len(password)>=8:
                try:
                    User.objects.create_user(username=username, password=password, first_name=nome, last_name=cognome)
                    user = authenticate(username=username, password=password)
                    Utente.objects.create(user=user)
                    login(request, user)                                                            




                    """ GUARDARE COME TOGLIERE BACK BUTTON"""#AAAAAAAAAAAAAAAAAAAAA







                    return redirect(userView, username=username)
                except IntegrityError:
                    error = username + " esiste già"
            else:
                error = "Password troppo corta (min 8)"
        else:
            error = "Riempi tutti i campi"
        return render(request, 'registration/signup.html',context={"error":error,"first_name":nome,"last_name":cognome,"username":username,"password":password})

    else:
        pass
    """ REDIRECT AD UNA PAGINA CHE DICE CHE HAI SBAGLIATO"""

def logoutView(request):
    if request.method == 'POST':
        logout(request)
        return redirect(loginView)
    else:
        pass
        """ REDIRECT AD UNA PAGINA CHE DICE CHE HAI SBAGLIATO"""


def userView(request,username):
    """View function for home page of site."""
    if request.method == 'GET': #get_object_or_404(MyModel, pk=1)
        if request.user.is_authenticated:
            if request.user.username == username:
                utente = User.objects.get(username=username) 
                lista_playlist = Playlist.objects.filter(user_id=utente.id)
                return render(request, 'user.html', context={"username":username,"playlists":lista_playlist})
            else:
                """ REDIRECT AD UNA PAGINA CHE DICE CHE HAI SBAGLIATO"""
                return redirect(loginView)
        else:
            return redirect(loginView)
    else:
        pass
        """ REDIRECT AD UNA PAGINA CHE DICE CHE HAI SBAGLIATO"""