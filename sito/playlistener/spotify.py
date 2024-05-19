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
    return response



""" Ordinamenti """

def add_names_to_audiofeatures(audiofeatures,ids,names):
    diz = dict(zip(ids, names))
    response = list(map(lambda e: e | {"name":diz[e["id"]]},audiofeatures))
    return response

def order_tracks(tracks_features,feature):
    lista = list(reversed(sorted(tracks_features, key=lambda d: d[feature])))
    for e in lista:
        print(f"{e['name']:30.30} | Eff {e['eff_energy']:5.3f} | close {e['closerability']:5.3f}  | Acoustic {e['acousticness']:10} | Dance{e['danceability']:10} | Energy{e['energy']:10} | Tempo{e['tempo']:10} | Volume: {pow(22,((60+e['loudness'])/60)+1)/150:5.3f} | Felicità{e['valence']:10}")

"""
Calcolo l'Energia contando 60% energy, 20% loudness, 15% valence(-0.15 a 0.15), 5% danceability, -5% acousticness
Energia per divisione verticale
Per divisione orizzonatale faccio per altri parametri (per decidere a stesso livello di Energia dove vanno le tracks, se alla fine o all'inizio)
es: loudness: all'inizio tracks basse verso la fine tracks alte
    valence: same all'inizio che alla fine, a gaussiana
// max = 5
"""

x = []
y = []

def order_tracks_eff_energy(tracks_features):
    features = [dict(track,
                     eff_energy = (.5*track["energy"] + 0.3*(pow(22,((60+track['loudness'])/60)+1)/150) + .4*(track["valence"]) + .25*track["danceability"]*track["valence"]*10
                            + 0.005*track["tempo"]*((60+track["loudness"])/60) - .5*track["acousticness"])*(5/4.7),
                     closerability = - .5*track["acousticness"] + .3*track["danceability"] - .3*track["energy"] + 0.8
                ) for track in tracks_features]
    listay = list(reversed(sorted(features, key=lambda d: d["eff_energy"])))
    i = 0
    for e in listay:
        print(f"{e['name']:30.30} | Eff {e['eff_energy']:5.3f} | close {e['closerability']:5.3f}  | Acoustic {e['acousticness']:10} | Dance{e['danceability']:10} | Energy{e['energy']:10} | Tempo{e['tempo']:10} | Volume: {pow(22,((60+e['loudness'])/60)+1)/150:5.3f} | Felicità{e['valence']:10}")
        y.append(e['eff_energy'])
        x.append(i)
        i +=1 

    listax = list(reversed(sorted(features, key=lambda d: d["closerability"])))
    print("\n\n Ordine per x")
    for e in listax:
        print(f"{e['name']:30.30} | Eff {e['eff_energy']:5.3f} | close {e['closerability']:5.3f}  | Acoustic {e['acousticness']:10} | Dance{e['danceability']:10} | Energy{e['energy']:10} | Tempo{e['tempo']:10} | Volume: {pow(22,((60+e['loudness'])/60)+1)/150:5.3f} | Felicità{e['valence']:10}")


token = get_token()

#"Midnights till dawn edition","red taylor's version","1989","lover","reputation","guts","sour","thank u, next","sweetener","future nostalgia","happier than ever","folklore"

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
print("\nacousticness")
order_tracks(tracks_features,"acousticness")

print("\ndanceability")
order_tracks(tracks_features,"danceability")

print("\nenergy")
order_tracks(tracks_features,"energy")

print("\ninstrumentalness")
order_tracks(tracks_features,"instrumentalness")

print("\nloudness")
order_tracks(tracks_features,"loudness")
"""


#order_tracks_eff_energy(tracks_features)

