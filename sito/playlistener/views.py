from django.shortcuts import render, redirect
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.db import IntegrityError
from django.views.decorators.cache import cache_control
from django.dispatch import receiver
from django.db.models.signals import post_delete

from .models import Album, Artista, Canzone, Playlist, Utente

from django.conf import settings
from .forms import *

from PIL import Image

def square_image(path, size):
    img = Image.open(path)
    if img.width != img.height:
        if img.width < img.height:      # When image height is greater than its width
            # make square by cutting off equal amounts top and bottom
            left = 0
            right = img.width
            top = (img.height - img.width)/2
            bottom = (img.height + img.width)/2
        
        elif img.width > img.height:    # When image width is greater than its height
            # make square by cutting off equal amounts left and right
            left = (img.width - img.height)/2
            right = (img.width + img.height)/2
            top = 0
            bottom = img.height
    
        img = img.crop((left, top, right, bottom))

    img.thumbnail((size,size))  # Resize the image to size x size resolution
    img.save(path)

""" 

FORSE NON SERVE 

def delete_file(path):
    if os.path.isfile(path):    # Controlla se esiste
        os.remove(path)         # Elimina

PROBLEMA REFRESH PAGINA ; GUARDA SALVATI

"""

"""

GET PER I LINK/REDIRECT
POST PER LE FORM E BOTTONI SUBMIT(per input)


"""


@cache_control(must_revalidate=True, no_store=True)
def loginView(request):
    context={}
    if request.method == 'GET':
        """ GET della pagina di login """
        if request.user.is_authenticated:
            return redirect(userView,request.user.get_username())
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
        context={"error":error,"username":username,"password":password}
    return render(request, 'registration/login.html',context=context)


@cache_control(must_revalidate=True, no_store=True)
def signupView(request):
    context={}
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
            if len(username)<3:
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
        context={"error":error,"first_name":nome,"last_name":cognome,"username":username,"password":password}
    return render(request, 'registration/signup.html',context=context)


@cache_control(must_revalidate=True, no_store=True)
def editView(request):
    context={}
    if request.method == 'POST':
        if request.POST['_method'] == 'GET':
            """ GET della pagina di edit """
            if request.user.check_password(request.POST['password']):
                context = {"first_name": request.user.first_name,
                        "last_name": request.user.last_name,
                        "username": request.user.get_username()}
            else:
                return redirect(userView,request.user.get_username())
        
        elif request.POST['_method'] == 'POST':
            """ POST della form di edit """
            error = ""
            nome = request.POST['first_name']
            cognome = request.POST['last_name']
            username = request.POST['username'].lower()
            password = request.POST['password']
            if username and len(username)<3:
                error = "Username troppo corto (min 3)"
            if password and len(password)<8:
                error = "Password troppo corta (min 8)"
            if not error:
                try:
                    user = User.objects.get(username=request.user.get_username())
                    if username:
                        user.username = username
                    if nome:
                        user.first_name = nome
                    if cognome:
                        user.last_name = cognome
                    if password:
                        user.set_password(password)
                    user.save()
                    user = authenticate(username=username, password=password)
                    login(request, user)
                    return redirect(userView, username=username)
                except IntegrityError:
                    error = username + " esiste già"
            context={"error":error,"first_name":nome,"last_name":cognome,"username":username}
        return render(request, 'registration/edit.html',context=context)
    return redirect(userView,request.user.get_username())




def logoutView(request):
    if request.method == 'POST':
        logout(request)
    return redirect(loginView)



@cache_control(must_revalidate=True, no_store=True)
def userView(request,username):
    """View function for home page of site."""
    if request.user.is_authenticated:
        if request.user.get_username() == username:
            user = User.objects.get(username=username)
            if request.method == 'GET':
                playlists = Playlist.objects.filter(user_id=user.id)
                form = ImageForm()
                return render(request, 'user.html', context={"form":form,"playlists":playlists,'media_root': settings.MEDIA_URL})
            elif request.method == 'POST':
                if request.POST['_method'] == 'PUT':
                    form = ImageForm(request.POST,request.FILES)
                    if form.is_valid():
                        image = request.FILES["pfp"]
                        user.utente.pfp.delete()
                        user.utente.pfp = image
                        user.utente.save()
                        square_image(user.utente.pfp.path, 300)
        
                elif request.POST['_method'] == 'DELETE':
                    user.utente.pfp.delete()
                    user.utente.save()
                return redirect(userView, username)
    return redirect(loginView)







@cache_control(must_revalidate=True, no_store=True)
def playlistView(request,username,id=None):
    if request.user.is_authenticated:
        if request.user.get_username() == username:
            user = User.objects.get(username=username)
            if request.method == 'GET':
                playlist = Playlist.objects.get(pk=id,user=user)
                return render(request, 'playlist.html', context={"playlist":playlist,'media_root': settings.MEDIA_URL})
            elif request.method == 'POST':
                if id is None:
                    playlist = Playlist.objects.create(user=user)
                    id = playlist.id
                
                return redirect(playlistView, username, id)
    return redirect(loginView)


