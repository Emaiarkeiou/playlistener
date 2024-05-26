from django.http import HttpResponseRedirect
import os
import re
import base64
from requests import post,get
import json
from difflib import SequenceMatcher
import math
from itertools import islice,chain

import random
import hashlib
from urllib.parse import urlencode

def similar(a, b):
    return SequenceMatcher(None, a, b).ratio()

client_id = "6159386c92a9417aac8dee56ff9df305"
client_secret = "a901979879f048f9889c3c1933d2526b"

""" Authorization """

def redirectToAuthCodeFlow(uri):
    verifier = base64.urlsafe_b64encode(os.urandom(40)).decode('utf-8')
    verifier = re.sub('[^a-zA-Z0-9]+', '', verifier)
    challenge = hashlib.sha256(verifier.encode('utf-8')).digest()
    challenge = base64.urlsafe_b64encode(challenge).decode('utf-8')
    challenge = challenge.replace('=', '')

    params = {"client_id":client_id,
              "response_type":"code",
              "redirect_uri":uri,
              "scope":"playlist-read-private playlist-modify-public playlist-modify-private ugc-image-upload user-read-private user-read-email",
              "code_challenge_method":"S256",
              "code_challenge":challenge}
    return verifier,urlencode(params)
    

def getAccessToken(code,verifier,uri):
    params = {"client_id":client_id,
              "grant_type":"authorization_code",
              "code":code,
              "redirect_uri":uri,
              "code_verifier":verifier}
    url = "https://accounts.spotify.com/api/token"
    headers = {
        "Content-Type": "application/x-www-form-urlencoded",
    }
    result = post(url,headers=headers, data=params)
    json_result = json.loads(result.content)
    return json_result["access_token"],json_result["refresh_token"]


def get_token():
    auth_string = client_id +":"+client_secret
    auth_bytes = auth_string.encode("utf-8")
    auth_base64= str(base64.b64encode(auth_bytes), "utf-8")

    url = "https://accounts.spotify.com/api/token"
    headers = {
        "Authorization":"Basic " +auth_base64,
        "Content-Type": "application/x-www-form-urlencoded",
    }
    data = {"grant_type":"client_credentials"}
    
    result = post(url,headers=headers, data=data)
    json_result = json.loads(result.content)
    token = json_result["access_token"]
    return token

def get_auth_header():
    return {"Authorization":"Bearer " + get_token()}



""" Search """

def get_search(string,tracks=False,albums=False,artists=False,n=1):
    """ Get di canzoni,album,artisti """
    """ id name e POPULARITY per ordinarli nella ricerca """
    resolve = {}
    if tracks or albums or artists:
        url = "https://api.spotify.com/v1/search"
        headers = get_auth_header()
        types = ["track" if tracks else "", "album" if albums else "", "artist" if artists else ""]
        types = "%2C".join(string for string in types if string)
        url += f"?q={string}&type={types}&limit={n}"
        result = get(url,headers=headers)
        json_result = json.loads(result.content)
        keys = ["id","name","popularity","type"]
        if tracks:
            resolve["tracks"] = list(map(lambda d: dict((k, d[k]) for k in keys+["duration_ms"] if k in d) 
                                         | {"album":{"id":d["album"]["id"],"name":d["album"]["name"],"image":d["album"]["images"][0]["url"]}}
                                         | {"artists":[{"id":a["id"],"name":a["name"]} for a in d["artists"]]},
                                         json_result["tracks"]["items"]))
        if albums:
            resolve["albums"] = [d["id"] for d in json_result["albums"]["items"] if "id" in d]
            resolve["albums"] = get_from_ids("albums",resolve["albums"]) #per prendere le popolarità
            albumss = []
            for a in resolve["albums"]:
                a = {k: a[k] for k in a.keys() - {'tracks'}}
                albumss.append(dict((k, a[k]) for k in keys if k in a) | {"image":a["images"][0]["url"]})
            resolve["albums"] = albumss
            
        if artists:
            resolve["artists"] = list(map(lambda d: dict((k, d[k]) for k in keys if k in d),json_result["artists"]["items"]))
    return resolve

def order_popularity(name,exact,lista,n_artist,tot):
    """ Sceglie le n opzioni più vicine al nome e le ordina per popolarità """
    if exact:
        lista = [t for t in lista if name.lower() in t["name"].lower()][:tot]
    else:
        lista = list(reversed(sorted(lista, key=lambda d: similar(name,d["name"]))))[:tot]
    lista = list(reversed(sorted(lista, key=lambda d: d["popularity"])))[:tot]
    tracks = []
    for t in lista:
        if t["type"] == "artist":
            tracks += get_artist_top_tracks(t,n_artist)
        elif t["type"] == "album":
            tracks += get_album_first_tracks(t)
        else:
            tracks.append(t)
    """ track: {id, nome, popularity, type, duration_ms, album{id,image,name},artists[{id,name }] } """
    tracks = remove_duplicates_id(tracks)
    tot = tot if tot<len(tracks) else len(tracks)
    tracks = [t for t in tracks if ("album" in t.keys() and "artists" in t.keys())]
    return tracks[:tot]

def remove_duplicates_id(lista):
    ids = []
    new = []
    for el in lista:
        if el["id"] not in ids:
            ids.append(el["id"])
            new.append(el)
    return new


""" Get """

def get_artist_top_tracks(artist,n):
    """ Get informazioni base delle top canzoni di 1 artista """
    url = "https://api.spotify.com/v1/artists/" + artist["id"] + "/top-tracks"
    headers = get_auth_header()
    result = get(url,headers=headers)
    json_result = json.loads(result.content)
    keys = ["id","name","duration_ms"]
    return list(map(lambda d: dict((k, d[k]) for k in keys if k in d) 
                    | {"album":{"id":d["album"]["id"],"name":d["album"]["name"],"image":d["album"]["images"][0]["url"]}}
                    | {"artists":[{"id":a["id"],"name":a["name"]} for a in d["artists"]]},
                    json_result["tracks"][:n]))

def get_album_first_tracks(album):
    """ Get informazioni base delle prime canzoni di 1 album """
    url = "https://api.spotify.com/v1/albums/" + album["id"] + "/tracks"
    headers = get_auth_header()
    result = get(url,headers=headers)
    json_result = json.loads(result.content)
    keys = ["id","name","duration_ms"]
    return list(map(lambda d: dict((k, d[k]) for k in keys if k in d)
                    | {"album":{"id":album["id"],"name":album["name"],"image":album["image"]}}
                    | {"artists":[{"id":a["id"],"name":a["name"]} for a in d["artists"]]},
                    json_result["items"]))


def get_from_id(param,id):
    """ Get informazioni base di canzoni,album,artisti """
    """ param = tracks,albums,artists,audio-features,... """
    url = "https://api.spotify.com/v1/" + param + "/" + id
    headers = get_auth_header()
    result = get(url,headers=headers)
    json_result = json.loads(result.content)
    return json_result

def get_from_ids(param,ids):
    """ Get informazioni base di più canzoni,album,artisti con una lista di id """
    """ param = tracks,albums,artists,audio-features,... """
    def max_chunks(list, n=100): 
        for i in range(0, len(list), n):  
            yield list[i:i + n]
    chunks = list(max_chunks(ids))

    response = []
    for chunk in chunks:
        url = "https://api.spotify.com/v1/" + param + "?ids=" + "%2C".join(chunk)
        headers = get_auth_header()
        result = get(url,headers=headers)
        response += json.loads(result.content)[param.replace("-","_")]
    
    if param == "audio-features":
        response = calculate_eff_energy_closerability(response)
        keys = ["id","acousticness","danceability","valence","loudness","duration_ms",   "eff_energy","closerability"]
        response = list(map(lambda d: dict((k, d[k]) for k in keys if k in d),response))
    return response



""" Ordinamenti """

def add_names_to_audiofeatures(audiofeatures,ids,names):
    diz = dict(zip(ids, names))
    response = list(map(lambda e: e | {"name":diz[e["id"]]},audiofeatures))
    return response

def order_playlist(tracks,feature,punti):
    if len(set(punti)) <= 1:  #se i punti sono tutti uguali
        return list(sorted(tracks, key=lambda t: t['closerability']))
    else:
        punti = list(map(lambda x: x-min(punti),punti))
        tratti = [] 
        # tratto = {y:,lun:,dir:}
        """
        y: n sezione verticale (0-rangey)
        lun: lunghezza tratto in terimini di numero di canzoni
        dir: andamento (cresc/decres) (-1/0/+1)
        """
        for i in range(len(punti)-1):   #creazione tratti
            diff = punti[i+1] - punti[i]        #diff Y
            if diff == 0:
                k = 0 if punti[i] == 0 else punti[i]-1
                tratti.append({"y":k,"lun":len(tracks)/(len(punti)-1),"dir":0})
            elif diff > 0:                  #se crescente
                for j in range(diff):
                    tratti.append({"y":punti[i]+j,"lun":(len(tracks)/diff)/(len(punti)-1),"dir":diff})
            elif diff < 0:                  #se decrescente
                for j in range(1,-diff+1):
                    tratti.append({"y":punti[i]-j,"lun":(len(tracks)/(-diff))/(len(punti)-1),"dir":diff})

        for i in range(len(tratti)):    #eliminazione dei tratti ne crescenti ne decrescenti
            if tratti[i]["dir"] == 0:
                indexes = []
                j = i
                while j>0 and tratti[j]["dir"] == 0:
                    j-=1
                if tratti[j]["dir"] != 0:
                    indexes.append(j)
                j = i
                while j<len(tratti)-1 and tratti[j]["dir"] == 0:
                    j+=1
                if tratti[j]["dir"] != 0:
                    indexes.append(j)
                for j in indexes:
                    tratti[j]["lun"] += tratti[i]["lun"]/len(indexes)
        tratti = [t for t in tratti if t["dir"] != 0]

        lista = list(sorted(tracks, key=lambda d: d[feature]))  #lista canzoni ordinate per feature
        perc = [i for i in range(max(punti))] # [[ {y:0,lun:,dir:},{y:0,lun:,dir:} ] , [{y:1,lun:,dir:},{y:1,lun:,dir:}],...]
        for i in perc:
            perc[i] = sum([d["lun"] for d in tratti if d["y"] == i])
        
        lunghezze = divide(len(tracks),perc)
        lista = iter(lista) #tracks
        divisi = [list(islice(lista, elem)) for elem in lunghezze] # dividere in sezioni
        divisi = list(map(lambda x: sorted(x, key=lambda d: d['closerability']),divisi)) # ordinare ogni sezione per closerability

        tracks = [i for i in range(len(tratti))]
        for i in range(max(punti)): #per ogni sezione_y
            perc = []
            trattiy = []
            for j in range(len(tratti)):
                if tratti[j]["y"] == i:
                    trattiy.append(j)
            #indici dei tracci
            perc = [tratti[j]["lun"] for j in trattiy] #percentuali di ogni tratto
            lunghezze = divide(len(divisi[i]),perc)
            lista = iter(divisi[i]) #tracks di una sezioni
            divisi_y = [list(islice(lista, elem)) for elem in lunghezze] # dividere in tratti 
            for j,y in zip(trattiy,divisi_y):  #per ogni indice del tratto
                if tratti[j]["dir"] > 0:
                    tracks[j] = list(sorted(y, key=lambda d: d[feature]))
                elif tratti[j]["dir"] < 0:
                    tracks[j] = list(reversed(list(sorted(y, key=lambda d: d[feature]))))

        return list(chain.from_iterable(tracks))  
    


def divide(n,perc):
    floored = list(map(math.floor,perc))
    if n-sum(floored):
        resti = list(map(lambda x: x%1,perc))
        indexes = sorted(range(len(resti)), key = lambda sub: resti[sub])[-(n-sum(floored)):]   #indice di chi ha i resti maggiori
        for i in indexes:
            floored[i] += 1
    return floored

"""
Calcolo l'Energia contando 60% energy, 20% loudness, 15% valence(-0.15 a 0.15), 5% danceability, -5% acousticness
Energia per divisione verticale
Per divisione orizzonatale faccio per altri parametri (per decidere a stesso livello di Energia dove vanno le tracks, se alla fine o all'inizio)
es: loudness: all'inizio tracks basse verso la fine tracks alte
    valence: same all'inizio che alla fine, a gaussiana
// max = 5
"""

def calculate_eff_energy_closerability(tracks_features):
    features = [dict(track,
                     eff_energy = (.5*track["energy"] + 0.3*(pow(22,((60+track['loudness'])/60)+1)/150) + .4*(track["valence"]) + .25*track["danceability"]*track["valence"]*10
                            + 0.005*track["tempo"]*((60+track["loudness"])/60) - .5*track["acousticness"])*(5/4.7),
                     closerability = - .5*track["acousticness"] + .3*track["danceability"] - .3*track["energy"] + 0.8
                ) for track in tracks_features]
    return features
