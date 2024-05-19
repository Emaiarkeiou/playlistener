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

from .spotify import *

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



@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def userView(request,username):
    """View function for home page of site."""
    if request.user.is_authenticated:
        if request.user.get_username() == username:
            user = User.objects.get(username=username)
            if request.method == 'GET':
                playlists = Playlist.objects.filter(user_id=user.id).order_by("id")
                form = PfpForm()
                return render(request, 'user.html', context={"form":form,"playlists":playlists,'media_root': settings.MEDIA_URL})
            elif request.method == 'POST':
                if request.POST['_method'] == 'PUT':
                    form = PfpForm(request.POST,request.FILES)
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



@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def playlistView(request,username,id=None):
    if request.user.is_authenticated:
        if request.user.get_username() == username:
            user = User.objects.get(username=username)
            if request.method == 'GET':
                context = {'media_root': settings.MEDIA_URL}
                if request.GET.get('name') == "song":
                    if request.GET.get('search'):
                        context["search"] = request.GET.get('search')
                        searched = get_search(context["search"],tracks=True,albums=True,artists=True,n=10)
                        context["searched"] = order_popularity(context["search"],searched["tracks"]+searched["albums"]+searched["artists"],10,30)
                        request.session["search"] = context["search"]
                        request.session["searched"] = context["searched"]
                    else:
                        context["search"] = request.session["search"]
                        context["searched"] = request.session["searched"]
                    for i in range(len(context["searched"])):
                        if "artists" in context["searched"][i]:
                            artists_string = [d["name"] for d in context["searched"][i]["artists"] if "name" in d]
                            context["searched"][i]["artists_string"] = ", ".join(artists_string)
                        #if track id in object get playlist tracks
                    """ track: {id, nome, popularity, type,album{id,image,name},artists[{id,name }],artists_string } """
                context["playlist"] = Playlist.objects.get(pk=id,user=user)
                print(context["playlist"].canzone.all())
                context["form"] = CoverForm()
                return render(request, 'playlist.html', context=context)
            
            elif request.method == 'POST':
                if id is None:
                    playlist = Playlist.objects.create(user=user)
                    id = playlist.id

                elif request.POST['_method'] == 'POST':
                    playlist = Playlist.objects.get(pk=id,user=user)
                    if request.POST['_name'] == 'song':
                        """ track: {id, nome, popularity, type,album{id,image,name},artists[{id,name }],artists_string } """
                        track = eval(request.POST['_track'])
                        album,artisti = track["album"],[]
                        album,created = Album.objects.update_or_create(id=album["id"],nome=album["name"],image=album["image"])
                        for artist in track["artists"]:
                            artista,created = Artista.objects.update_or_create(id=artist["id"],nome=artist["name"])
                            artisti.append(artista)
                        canzone,created = Canzone.objects.update_or_create(id=track["id"],nome=track["name"])
                        print(canzone)
                        canzone.album.add(album.id)
                        canzone.artista.add(*[a.id for a in artisti])
                        playlist.canzone.add(canzone.id)
                        return redirect(request.path_info+"?name=song")

                elif request.POST['_method'] == 'PUT':
                    playlist = Playlist.objects.get(pk=id,user=user)
                    if request.POST['_name'] == 'nome':
                        playlist.nome = request.POST['nome']
                    elif request.POST['_name'] == 'desc':
                        playlist.desc = request.POST['desc']
                    elif request.POST['_name'] == 'cover':
                        form = CoverForm(request.POST,request.FILES)
                        if form.is_valid():
                            image = request.FILES['cover']
                            playlist.cover.delete()
                            playlist.cover = image
                            playlist.save()
                            square_image(playlist.cover.path, 300)
                    
                elif request.POST['_method'] == 'DELETE':
                    playlist = Playlist.objects.get(pk=id,user=user)
                    if request.POST['_name'] == 'playlist':
                        playlist.delete()
                        return redirect(userView, username)
                    if request.POST['_name'] == 'cover':
                        playlist.cover.delete()
                
                    playlist.save()
                return redirect(playlistView, username, id)
    return redirect(loginView)


