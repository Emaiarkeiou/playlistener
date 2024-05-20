import os
import base64
from requests import post,get
import json
from difflib import SequenceMatcher

def similar(a, b):
    return SequenceMatcher(None, a, b).ratio()

client_id = "6159386c92a9417aac8dee56ff9df305"
client_secret = "a901979879f048f9889c3c1933d2526b"

""" Authorization """

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
    return {"Authorization":"Bearer " + token}



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
            resolve["tracks"] = list(map(lambda d: dict((k, d[k]) for k in keys if k in d) 
                                         | {"album":{"id":d["album"]["id"],"name":d["album"]["name"],"image":d["album"]["images"][0]["url"]}}
                                         | {"artists":[{"id":a["id"],"name":a["name"]} for a in d["artists"]]},
                                         json_result["tracks"]["items"]))
            
        if albums:
            resolve["albums"] = [d["id"] for d in json_result["albums"]["items"] if "id" in d]
            resolve["albums"] = get_from_ids("albums",resolve["albums"]) #per prendere le popolarità
            resolve["albums"] = list(map(lambda d: dict((k, d[k]) for k in keys if k in d) | {"image":d["images"][0]["url"]},resolve["albums"]))
        if artists:
            resolve["artists"] = list(map(lambda d: dict((k, d[k]) for k in keys if k in d),json_result["artists"]["items"]))
    return resolve

def order_popularity(name,lista,sus,n):
    """ Sceglie le n opzioni più vicine al nome e le ordina per popolarità """
    lista = list(reversed(sorted(lista, key=lambda d: similar(name,d["name"]))))[:n]

    lista = list(reversed(sorted(lista, key=lambda d: d["popularity"])))[:n]
    sus = sus
    i=0
    while i < sus*5:
        if lista[i]["type"] == "artist":
            lista[i:i+sus-1] = get_artist_top_tracks(lista[i],sus)
            i += sus-1
        elif lista[i]["type"] == "album":
            lista[i:i+sus-1] = get_album_first_tracks(lista[i],sus)
            i += sus-1
        i += 1
        if i >= len(lista):
            break
    """ track: {id, nome, popularity, type,album{id,image,name},artists[{id,name }] } """
    lista = remove_duplicates_id(lista)
    n = n if n<len(lista) else len(lista)
    return lista[:n]

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
    keys = ["id","name"]
    return list(map(lambda d: dict((k, d[k]) for k in keys if k in d) 
                    | {"album":{"id":d["album"]["id"],"name":d["album"]["name"],"image":d["album"]["images"][0]["url"]}}
                    | {"artists":[{"id":a["id"],"name":a["name"]} for a in d["artists"]]},
                    json_result["tracks"][:n]))

def get_album_first_tracks(album,n):
    """ Get informazioni base delle prime canzoni di 1 album """
    url = "https://api.spotify.com/v1/albums/" + album["id"] + "/tracks?limit=" + str(n)
    headers = get_auth_header()
    result = get(url,headers=headers)
    json_result = json.loads(result.content)
    keys = ["id","name"]
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
        keys = ["id","acousticness","danceability","valence","loudness",   "eff_energy","closerability"]
        response = list(map(lambda d: dict((k, d[k]) for k in keys if k in d),response))
    return response



""" Ordinamenti """

def add_names_to_audiofeatures(audiofeatures,ids,names):
    diz = dict(zip(ids, names))
    response = list(map(lambda e: e | {"name":diz[e["id"]]},audiofeatures))
    return response

def order_playlist(tracks,feature,punti):
    punti = list(map(lambda x: x-min(punti),punti))
    rangey = max(punti)
    print(punti)
    perc = [0 for i in range(rangey)]       #perc Y
    print(perc)
    for i in range(len(punti)-1):
        diff = punti[i+1] - punti[i]        #diff Y
        if diff == 0:
            k = 0 if punti[i] == 0 else punti[i]-1
            perc[k] += 1
        elif diff > 0:                  #se crescente
            for j in range(diff):
                perc[punti[i]+j] += 1/diff
        elif diff < 0:                  #se decrescente
            for j in range(1,-diff+1):
                perc[punti[i]-j] += 1/(-diff)
    print(perc)
    lista = list(sorted(tracks, key=lambda d: d[feature]))
    # dividere in sezioni
    # ordinare ogni sezione per closerability
    # dividere in sottosezioni
    # ordinare ogni sottosezione crescente o decrescente, guardare anche i picchi
    return lista
    #print(f"Eff {e['eff_energy']:5.3f} | close {e['closerability']:5.3f}  | Acoustic {e['acousticness']:10} | Dance{e['danceability']:10} | Energy{e['energy']:10} | Tempo{e['tempo']:10} | Volume: {pow(22,((60+e['loudness'])/60)+1)/150:5.3f} | Felicità{e['valence']:10}")
    


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

token = get_token()


"""
names = ["guts spilled"]
size = 10

searched = get_search(names[0],tracks=True,albums=True,artists=True,n=size)
print(order_popularity(names[0],searched["tracks"]+searched["albums"]+searched["artists"],15))
"""


"""
for name in names:
    tracks += get_search(name,albums=True)["albums"][0]["tracks"]["items"]

print("Got")

ids = list(map(lambda track: track["id"],tracks))
names = list(map(lambda track: track["name"],tracks))

tracks_features = add_names_to_audiofeatures(get_from_ids("audio-features",ids),ids,names)
"""


"""
<option>Acustica</option>
print("\nacousticness")
order_tracks(tracks_features,"acousticness")

<option>Ballabilità</option>
print("\ndanceability")
order_tracks(tracks_features,"danceability")

<option>Felicità</option>
print("\nivalence")
order_tracks(tracks_features,"valence")

<option>Volume</option>
print("\nloudness")
order_tracks(tracks_features,"loudness")
"""

#<option selected>Energia</option>
#order_tracks_eff_energy(tracks_features)

