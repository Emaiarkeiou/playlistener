from django.shortcuts import render, redirect
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.db import IntegrityError
from django.views.decorators.cache import cache_control
from django.conf import settings
from django.core.files.storage import FileSystemStorage

# Create your views here.

from .models import Album, Artista, Canzone, Playlist, Utente


"""

GET PER I LINK/REDIRECT
POST PER LE FORM E BOTTONI SUBMIT(per input)


"""


@cache_control(must_revalidate=True, no_store=True)
def loginView(request):
    """View function for home page of site."""
    if request.method == 'GET':
        """ GET della pagina di login """
        if request.user.is_authenticated:
            return redirect(userView,request.user.username)
        else:
            return render(request, 'registration/login.html')
    elif request.method == 'POST':
        """ POST della form di login """
        username = request.POST['username'].lower()
        password = request.POST['password']
        if username and password:
            try:
                user = User.objects.get(username=username)
                user = authenticate(username=username, password=password)
                if user is not None:
                    login(request, user)
                    return redirect(userView, username=username) 
                else:
                    error = "Password errata"
            except User.DoesNotExist:
                error = "Credenziali errate"
        else:
            error = "Riempi tutti i campi"
        return render(request, 'registration/login.html',context={"error":error,"username":username,"password":password})
    else:
        pass
    """ REDIRECT AD UNA PAGINA CHE DICE CHE HAI SBAGLIATO"""

@cache_control(must_revalidate=True, no_store=True)
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
            if len(username<3):
                error = "Username troppo corto (min 3)"
            elif len(password)>=8:
                try:
                    User.objects.create_user(username=username, password=password, first_name=nome, last_name=cognome)
                    user = authenticate(username=username, password=password)
                    Utente.objects.create(user=user)
                    login(request, user)                                                            
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


@cache_control(must_revalidate=True, no_store=True)
def userView(request,username):
    """View function for home page of site."""
    if request.user.is_authenticated:
        if request.user.username == username:
            user = User.objects.get(username=username)
            lista_playlist = Playlist.objects.filter(user_id=user.id)
            if request.method == 'GET':
                return render(request, 'user.html', context={"playlists":lista_playlist,'media_root': settings.MEDIA_URL})
            elif request.method == 'POST':

                if request.POST['_method'] == 'PUT':
                    image = request.POST['image']
                    user.utente.pfp = image                 
                    
                    
                    """PROBLEMA REFRESH PAGINA ; GUARDA SALVATI"""

                    """ UPLOAD IMMAGINE CON FORM AS CLASS ; GUARDA VIDEO SALVATO"""

                    user.utente.save()
                    return render(request, 'user.html', context={"playlists":lista_playlist,"prova":image,'media_root': settings.MEDIA_URL})
                
                elif request.POST['_method'] == 'DELETE':
                    user.utente.pfp = ""
                    user.utente.save()
                    return render(request, 'user.html', context={"playlists":lista_playlist,'media_root': settings.MEDIA_URL,"prova":"zzz"})
                
    return redirect(loginView)

