from dotenv import load_dotenv
import os
import base64
from requests import post, get
import plotly.graph_objects as go
import json

load_dotenv()

client_id = os.getenv("CLIENT_ID")
client_secret = os.getenv("CLIENT_SECRET")
odkaz_api = "https://api.spotify.com/v1"

def get_token():
    auth_string = client_id + ":" + client_secret
    auth_bytes = auth_string.encode("utf-8")
    auth_base64 = str(base64.b64encode(auth_bytes), "utf-8")

    url = "https://accounts.spotify.com/api/token"
    headers = {
        "Authorization": "Basic " + auth_base64,
        "Content-Type": "application/x-www-form-urlencoded"
    }
    data = {"grant_type": "client_credentials"}
    result = post(url, headers=headers, data=data)
    json_result = json.loads(result.content)
    token = json_result["access_token"]
    return token


def get_auth_header(token):
    return {"Authorization": "Bearer " + token}


def search_for_artist(token, artist_name):
    url = odkaz_api+"/search"
    headers = get_auth_header(token)
    query = f"?q={artist_name}&type=artist&limit=1"

    query_url = url + query
    result = get(query_url, headers=headers)
    json_result = json.loads(result.content)["artists"]["items"]

    if len(json_result) == 0:
        print("No artists with this name exists...")
        return None

    return json_result[0]


def get_songs_by_artist(token, artist_id):
    url = f"{odkaz_api}/artists/{artist_id}/top-tracks?country=US"
    headers = get_auth_header(token)
    result = get(url, headers=headers)
    json_result = json.loads(result.content)["tracks"]
    songs = []
    song_names = []
    song_streams = []
    for track in json_result:
        track_id = track["id"]
        features_url = f"{odkaz_api}/audio-features/{track_id}"
        features_result = get(features_url, headers=headers)
        features_json = json.loads(features_result.content)
        song = {
            "name": track["name"],
            "popularity": track["popularity"],
            "duration": track["duration_ms"],
            "bpm": features_json["tempo"],
            "streams": track["popularity"] * 10000
        }
        songs.append(song)
        for track in json_result:
            song_names.append(track["name"])
            song_streams.append(track["popularity"])
    return songs, song_names, song_streams



def get_albums_by_artist(token, artist_id):
    url = f"{odkaz_api}/artists/{artist_id}/albums?include_groups=album,single&market=US&limit=5"
    headers = get_auth_header(token)
    result = get(url, headers=headers)
    json_result = json.loads(result.content)["items"]
    return json_result

def get_related_artists(token, artist_id):
    url = f"{odkaz_api}/artists/{artist_id}/related-artists"
    headers = get_auth_header(token)
    result = get(url, headers=headers)
    json_result = json.loads(result.content)["artists"]
    return json_result

def search_top_songs_by_genre(token, genre):
    url = f"{odkaz_api}/search?q=genre:{genre}&type=track&limit=10"
    headers = get_auth_header(token)
    result = get(url, headers=headers)
    json_result = json.loads(result.content)["tracks"]["items"]

    if len(json_result) == 0:
        print("No songs found for this genre.")
        return None

    top_songs = []
    for idx, track in enumerate(json_result):
        top_songs.append({
            "name": track["name"],
            "artist": track["artists"][0]["name"],
            "popularity": track["popularity"],
            "preview_url": track["preview_url"]
        })

    return top_songs


def search_top_albums_by_genre(token, genre):
    url = f"{odkaz_api}/search?q=genre:{genre}&type=album&limit=10"
    headers = get_auth_header(token)
    result = get(url, headers=headers)
    json_result = json.loads(result.content)["albums"]["items"]
    top_albums = []
    for idx, album in enumerate(json_result):
        top_albums.append({
            "name": album["name"],
            "artist": album["artists"]["name"]
        })
    return top_albums

def search_top_artists_by_genre(token, genre):
    url = f"{odkaz_api}/search?q=genre:{genre}&type=artist&limit=10"
    headers = get_auth_header(token)
    result = get(url, headers=headers)
    json_result = json.loads(result.content)["artists"]["items"]
    top_artists = []
    for idx, artist in enumerate(json_result):
        top_artists.append({
            "name": artist["name"],
            "followers": artist["followers"]["total"]
        })

    return top_artists


def search_artist():
    co_chci = input("Welcome to Datify\nAre you going to search by artist or genre? (A/G): ")
    object_name = input("Enter the name you are searching for: ")
    token = get_token()
    result = search_for_artist(token, object_name)
    if result is None:
        return
    if co_chci == "A":
        search_type = input("Do you want to search for songs, albums, related artists? \nEnter 'songs', 'albums', 'related': ")
        if search_type == "songs":
            artist_id = result["id"]
            songs, song_names, song_streams = get_songs_by_artist(token, artist_id)
            print(f"\nHere are the top songs by {result['name']}:")
            for idx, song in enumerate(songs):
                print(f"{idx+1}. {song['name']} (BPM: {song['bpm']}, Streams: {song['streams']})")
            fig = go.Figure(data=[go.Bar(x=song_names, y=song_streams)])
            fig.update_layout(title=f"Popularity of the top songs by {result['name']}",
                              xaxis_title="Song Name",
                              yaxis_title="Popularity")
            fig.show()
        elif search_type == "albums":
            artist_id = result["id"]
            albums = get_albums_by_artist(token, artist_id)
            album_names = [album["name"] for album in albums]
            album_track_counts = [album["total_tracks"] for album in albums]
            print(f"\nHere are the top albums by {result['name']}:")
            for idx, album in enumerate(albums):
                print(f"{idx+1}. {album['name']}")
            fig = go.Figure(data=[go.Bar(x=album_names, y=album_track_counts)])
            fig.update_layout(title=f"Albums and track counts by {result['name']}",
                              xaxis_title="Album Name",
                              yaxis_title="Number of Tracks")
            fig.show()
        elif search_type == "related":
            artist_id = result["id"]
            related_artists = get_related_artists(token, artist_id)
            artist_names = [artist["name"] for artist in related_artists]
            artist_followers = [artist["followers"]["total"] for artist in related_artists]
            print(f"\nHere are some related artists to {result['name']}:")
            for idx, artist in enumerate(related_artists):
                print(f"{idx+1}. {artist['name']}")
            fig = go.Figure(data=[go.Bar(x=artist_names, y=artist_followers)])
            fig.update_layout(title=f"Number of followers for related artists of {result['name']}",
                              xaxis_title="Artist Name",
                              yaxis_title="Number of Followers")
            fig.show()
    if co_chci == "G":
        search_type = input("Do you want to search for top songs by genre? \nEnter 'songs' 'albums' 'artists': ")
        if search_type == "songs":
            genre = object_name
            top_songs = search_top_songs_by_genre(token, genre)
            song_names = [song['name'] for song in top_songs]
            song_popularity = [song['popularity'] for song in top_songs]
            print(f"\nHere are the top 10 songs in the genre\n'{genre}':")
            for idx, song in enumerate(top_songs):
                print(f"{idx+1}. {song['name']} by {song['artist']}")
            fig = go.Figure(data=[go.Bar(x=song_names, y=song_popularity)])
            fig.update_layout(title=f"Top songs in the genre '{genre}'",
                              xaxis_title="Song Name",
                              yaxis_title="Popularity")
            fig.show()
        if search_type == "albums":
            genre = object_name
            top_albums = search_top_albums_by_genre(token, genre)
            print(f"\nHere are the top 10 albums in the genre\n'{genre}':")
            for idx, album in enumerate(top_albums):
                print(f"{idx + 1}. {album['name']} by {album['artist']}")
            else:
                print("There are no albums for this genre")
        if search_type == "artists":
            genre = object_name
            top_artists = search_top_artists_by_genre(token, genre)
            artist_names = [artist['name'] for artist in top_artists]
            artist_followers = [artist['followers'] for artist in top_artists]
            print(f"\nHere are the top 10 artists in the genre\n'{genre}':")
            for idx, artist in enumerate(top_artists):
                print(f"{idx + 1}. {artist['name']}")
            fig = go.Figure(data=[go.Bar(x=artist_names, y=artist_followers)])
            fig.update_layout(title=f"Top artists in the genre '{genre}'",
                              xaxis_title="Artist Name",
                              yaxis_title="Number of followers")
            fig.show()
    else:
        print("Invalid search type. Please enter 'songs', 'albums', 'related', or 'top'.")
        return

search_artist()