from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.db import IntegrityError
from django.views.decorators.cache import cache_control
from django.dispatch import receiver
from django.db.models.signals import post_delete,pre_delete
from django.db.models import F
from .models import Album, Artista, Canzone, Playlist, Utente, Ordine
from django.conf import settings
from .forms import *
from PIL import Image

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from .spotify import *
from urllib.parse import urlparse

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
    img = img.resize((size,size))
    img.save(path)

""" 

FORSE NON SERVE 

def delete_file(path):
    if os.path.isfile(path):    # Controlla se esiste
        os.remove(path)         # Elimina

PROBLEMA REFRESH PAGINA ; GUARDA SALVATI

"""

@receiver(pre_delete, sender=Playlist)
def delete_song(sender, instance, **kwargs):
    #ELIMINAZIONE CANZONI NON PRESENTI IN NESSUNA PLAYLIST
    i = 0
    while i < instance.canzone.all().count():
        if Playlist.objects.filter(canzone=instance.canzone.all()[i]).count() <= 1: #se non ci sono playlist con quella canzone
            instance.canzone.all()[i].delete()                                      #elimina la canzone
            i -= 1
        i += 1
        if i >= len(instance.canzone.all()):
            break
    instance.canzone.clear()

@receiver(pre_delete, sender=Canzone)
def delete_song_related(sender, instance, **kwargs):
    #ELIMINAZIONE ALBUM NON AVENTI NESSUNA CANZONE SALVATA
    i = 0
    while i < instance.album.all().count():
        if Canzone.objects.filter(album=instance.album.all()[i]).count() <= 1:      #se non ci sono canzoni quell'album
            instance.album.all()[i].delete()                                        #elimina l'album
            i -= 1
        i += 1
        if i >= len(instance.album.all()):
            break
    instance.album.clear()
    
    #ELIMINAZIONE ARTISTI NON AVENTI NESSUNA CANZONE SALVATA
    i = 0
    while i < instance.artista.all().count():
        if Canzone.objects.filter(artista=instance.artista.all()[i]).count() <= 1:  #se non ci sono canzoni quell'artista
            instance.artista.all()[i].delete()                                      #elimina l'album
            i -= 1
        i += 1
        if i >= len(instance.artista.all()):
            break
    instance.artista.clear()

code,verifier = "",""

"""

GET PER I LINK/REDIRECT
POST PER LE FORM E BOTTONI SUBMIT(per input)


"""


@cache_control(must_revalidate=True, no_store=True)
def loginView(request):
    global code
    context={}
    if request.method == 'GET':
        """ GET della pagina di login """
        if request.user.is_authenticated:
            if request.GET.get('code'):
                code = request.GET.get('code')
                return redirect(loginSpotifyView,request.user.get_username())
            else:
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
    global code
    response = redirect(loginView)
    if request.method == 'POST':
        code = ""
        response.delete_cookie("access_token")
        response.delete_cookie("refresh_token")
        logout(request)
    return response



@cache_control(must_revalidate=True, no_store=True)
def loginSpotifyView(request,username):
    global code,verifier
    response = redirect(loginView)
    if request.method == 'GET':
        if request.user.is_authenticated:
            if request.user.get_username() == username:
                print("code: "+code)
                if not code:
                    verifier,querystring = redirectToAuthCodeFlow("http://"+urlparse(request.build_absolute_uri()).netloc+"/playlistener/login/")
                    return redirect("https://accounts.spotify.com/authorize?"+querystring)
                else:
                    access_token,refresh_token = getAccessToken(code,verifier,"http://"+urlparse(request.build_absolute_uri()).netloc+"/playlistener/login/")
                    response.set_cookie("access_token", access_token)
                    response.set_cookie("refresh_token", refresh_token)

    return response

@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def userView(request,username,param="all"):
    """View function for home page of site."""
    global code
    if request.user.is_authenticated:
        if request.user.get_username() == username:
            user = User.objects.get(username=username)
            if request.method == 'GET':
                context = {'media_root': settings.MEDIA_URL}
                access_token = request.COOKIES.get("access_token","")
                if access_token:
                    context["access_token"] = True
                    try:
                        spotify_user = get_spotify_user(access_token)
                        context["display_name"] = spotify_user["display_name"]
                        context["spotify_email"] = spotify_user["email"]
                    except:
                        print("ERRORE ACCESS_TOKEN")
                        code = ""
                        response = redirect(loginSpotifyView,request.user.get_username())
                        response.delete_cookie("access_token")
                        response.delete_cookie("refresh_token")
                        return response
                else:
                    context["access_token"] = False
                search = request.GET.get("name","")
                context["search"] = search
                if search:
                    if param == "all":
                        playlists = Playlist.objects.filter(user_id=user.id, nome__contains = search).order_by("-id")
                    else:
                        playlists = Playlist.objects.filter(user_id=user.id, nome__contains = search, tag=param).order_by("-id")
                else:
                    if param == "all":
                        playlists = Playlist.objects.filter(user_id=user.id).order_by("-id") 
                    else:
                        playlists = Playlist.objects.filter(user_id=user.id, tag=param).order_by("-id")
                context["playlists"] = playlists
                context["param"] = {param:True}
                context["form"] = CoverForm()
                form = PfpForm()
                
                return render(request, 'user.html', context=context)
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
                return redirect(userView, username,param)
    return redirect(loginView)




def format_playlist(playlist,songs,values,feature):
    maxs = max([v[feature] for v in values])
    formatted = []
    for song,value in zip(songs,values):
        canzone = song.__dict__
        canzone["image"] = song.album.all().values()[0]["image"]
        artists_string = [d["nome"] for d in song.artista.all().values() if "nome" in d]
        canzone["artists_string"] = ", ".join(artists_string)
        canzone["duration"] = value["duration_ms"] / 1000
        ordine = Ordine.objects.get(canzone=song,playlist=playlist)
        canzone["ordine"] = ordine.n + 1
        canzone["feature"] = value[feature]
        if feature == "loudness":
            canzone["feature_perc"] = value[feature]+100+maxs
        else:
            canzone["feature_perc"] = (value[feature]/maxs)*100
        formatted.append(canzone)
    return formatted

def format_search(songs,values,feature):
    maxs = max([v[feature] for v in values])
    formatted = []
    for song,value in zip(songs,values):
        canzone = song
        canzone["image"] = song["album"]["image"]
        artists_string = [d["name"] for d in song["artists"] if "name" in d]
        canzone["artists_string"] = ", ".join(artists_string)
        canzone["duration"] = value["duration_ms"] / 1000
        canzone["feature"] = value[feature]
        if feature == "loudness":
            canzone["feature_perc"] = value[feature]+100+maxs
        else:
            canzone["feature_perc"] = (value[feature]/maxs)*100
        formatted.append(canzone)
    return formatted

def get_ordine(playlist):
    ids = []
    ordini = Ordine.objects.filter(playlist=playlist).order_by("n")
    for o in ordini:
        ids.append(o.canzone_id)
    return ids


def ordina(playlist,ordini,feature):
    for i in range(len(ordini)):
        canzone = Canzone.objects.get(id=ordini[i]["id"])
        ordine = Ordine.objects.get(canzone=canzone,playlist=playlist)
        ordine.n = i
        ordine.save()


def scala_ordini(n,playlist):
    Ordine.objects.filter(playlist=playlist,n__gt=n).update(n=F('n') - 1)

@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def playlistView(request,username,id=None,param="eff_energy",exported = False):
    global code
    if request.user.is_authenticated:
        if request.user.get_username() == username:
            user = User.objects.get(username=username)
            if request.method == 'GET':
                context = {'media_root': settings.MEDIA_URL,"exported":exported}
                context["playlist"] = Playlist.objects.get(pk=id,user=user)
                context["canzoni"] = context["playlist"].canzone.all()
                ids = list(map(lambda canzone: canzone["id"],context["canzoni"].values()))

                if request.GET.get('name') == "song":
                    if request.GET.get('search'):
                        context["search"] = request.GET.get('search')
                        if context["search"].startswith(("\"", "\'")) and context["search"].endswith(("\"", "\'")): #Se la stringa è compresa tra virgolette
                            searched = get_search(context["search"][1:-1].rstrip(),tracks=True,n=20)                         #Cerca SOLO canzoni con QUEL titolo
                            context["searched"] = order_popularity(context["search"][1:-1].rstrip(),True,searched["tracks"],10,50)
                        else:
                            searched = get_search(context["search"].rstrip(),tracks=True,albums=True,artists=True,n=5)
                            context["searched"] = order_popularity(context["search"].rstrip(),False,searched["tracks"]+searched["albums"]+searched["artists"],10,50)
                        context["searched"] = [c for c in context["searched"] if c["id"] not in ids]
                        ids_searched = [c["id"] for c in context["searched"]]
                        track_features = get_from_ids("audio-features",ids_searched)
                        try:
                            context["searched"] = format_search(context["searched"],track_features,"eff_energy")
                        except:
                            print("ERRORE FORMAT")
                        request.session["search"] = context["search"].rstrip()
                        request.session["searched"] = context["searched"]
                    else:
                        context["search"] = request.session["search"].rstrip()
                        context["searched"] = [c for c in request.session["searched"] if c["id"] not in ids]

                duration,context["hours"],context["minutes"],context["seconds"] = 0,0,0,0
                if ids:
                    track_features = get_from_ids("audio-features",ids)
                    context["canzoni"] = format_playlist(context["playlist"],context["canzoni"],track_features,param)
                    context["canzoni"] = sorted(context["canzoni"], key=lambda d: d["ordine"])
                    duration = sum([c["duration"] for c in context["canzoni"]])
                    m, context["seconds"] = divmod(duration, 60)
                    h, m = divmod(m, 60)
                    context["hours"], context["minutes"] = int(h), int(m)
                    context["features"] = [c["feature"] for c in context["canzoni"]]
                    context["labels"] = ["" for c in context["canzoni"]]

                if context["playlist"].durata_min is not None:
                    m, s = divmod(context["playlist"].durata_min, 60)
                    h, m = divmod(m, 60)
                    context["hours_min"], context["minutes_min"] = int(h), int(m)
                    if duration >= context["playlist"].durata_min:
                        context["superata"] = True
                context["param"] = {param:True}
                context["tag"] = {context["playlist"].tag:True}
                context["form"] = CoverForm()
                return render(request, 'playlist.html', context=context)
            
            elif request.method == 'POST':
                if id is None:
                    playlist = Playlist.objects.create(user=user)
                    id = playlist.id

                elif request.POST['_method'] == 'POST':
                    playlist = Playlist.objects.get(pk=id,user=user)
                    if request.POST['_name'] == 'song':
                        #ADD song to playlist
                        """ track: {id, nome, popularity, type,album{id,image,name},artists[{id,name }],artists_string } """
                        track = eval(request.POST['_track'])
                        if track["album"]["image"] and track["artists"]:
                            album,artisti = track["album"],[]
                            album,created = Album.objects.update_or_create(id=album["id"],nome=album["name"],image=album["image"])
                            for artist in track["artists"]:
                                artista,created = Artista.objects.update_or_create(id=artist["id"],nome=artist["name"])
                                artisti.append(artista)
                            canzone,created = Canzone.objects.update_or_create(id=track["id"],nome=track["name"])
                            canzone.album.add(album.id)
                            canzone.artista.add(*[a.id for a in artisti])
                            playlist.canzone.add(canzone.id,through_defaults={'n': playlist.canzone.all().count()})
                        return redirect(request.path_info+"?name=song")
                    elif request.POST['_name'] == 'playlist':
                        #Export playlist
                        access_token = request.COOKIES.get("access_token","")
                        if access_token:
                            try:
                                ids = get_ordine(playlist)
                                spotify_user = get_spotify_user(access_token)
                                resp = export_playlist(access_token,spotify_user["id"],playlist,ids)
                                return redirect(playlistView, username, id, param,resp)
                            except:
                                print("ERRORE ACCESS_TOKEN Export")
                                code = ""
                                response = redirect(loginSpotifyView,request.user.get_username())
                                response.delete_cookie("access_token")
                                response.delete_cookie("refresh_token")
                                return response
                        else:
                            return redirect(loginSpotifyView,request.user.get_username())

                elif request.POST['_method'] == 'PUT':
                    playlist = Playlist.objects.get(pk=id,user=user)
                    if request.POST['_name'] == 'nome':
                        playlist.nome = request.POST['nome']
                    elif request.POST['_name'] == 'desc':
                        playlist.desc = request.POST['desc']
                    elif request.POST['_name'] == 'tag':
                        playlist.tag = request.POST['tag']
                        if request.POST['tag'] != "sport":
                            playlist.energia_min = 0
                        else:
                            playlist.energia_min = 3
                        if request.POST['tag'] != "viaggio":
                            playlist.durata_min = None
                    elif request.POST['_name'] == 'energy_min':
                        playlist.energia_min = float(request.POST['_energy'] or 0)
                    elif request.POST['_name'] == 'duration_min':
                        playlist.durata_min = 3600 * int(request.POST['_hours'] or 0) + 60 * int(request.POST['_minutes'] or 0)
                    elif request.POST['_name'] == 'cover':
                        form = CoverForm(request.POST,request.FILES)
                        if form.is_valid():
                            image = request.FILES['cover']
                            playlist.cover.delete()
                            playlist.cover = image
                            playlist.save()
                            square_image(playlist.cover.path, 300)
                    elif request.POST['_name'] == 'playlist':
                        ids = list(map(lambda canzone: canzone["id"],playlist.canzone.all().values()))
                        track_features = get_from_ids("audio-features",ids)
                        feature = request.POST['_param']
                        punti = [int(request.POST['_p'+str(i)])-1 for i in range(1,6)] #0 - len-1
                        ordered = order_playlist(track_features,feature,punti)
                        ordina(playlist,ordered,feature)
                        return redirect(playlistView, username, id, feature)
                    
                elif request.POST['_method'] == 'DELETE':
                    playlist = Playlist.objects.get(pk=id,user=user)
                    if request.POST['_name'] == 'playlist':
                        #Prima elimina tutte le canzoni,album,artisti senza references
                        playlist.delete()
                        return redirect(userView, username)
                    elif request.POST['_name'] == 'cover':
                        playlist.cover.delete()
                    
                    elif request.POST['_name'] == 'song':
                        track_id = request.POST['_track']
                        canzone = Canzone.objects.get(id=track_id)
                        n = int(request.POST['_ordine']) - 1
                        scala_ordini(n,playlist)
                        playlist.canzone.remove(canzone)
                        if Playlist.objects.filter(canzone=canzone).count() <= 0: #se non ci sono playlist con quella canzone
                            canzone.delete()
                        
                playlist.save()
                return redirect(playlistView, username, id, param)
    return redirect(loginView)


