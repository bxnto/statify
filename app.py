import spotipy
from spotipy.oauth2 import SpotifyOAuth
from flask import Flask, render_template, redirect, url_for, session

scope = "user-library-read user-top-read"

app = Flask(__name__)
app.secret_key = "Ilov3TayTay"  # Change this to a random secret key

def get_spotify_object():
    return spotipy.Spotify(auth_manager=SpotifyOAuth(scope=scope, show_dialog=True))

@app.route('/')
def index():
    return render_template('index.html')

@app.route("/login")
def login():
    sp = get_spotify_object()
    session['token_info'] = sp.auth_manager.get_access_token(as_dict=True)
    return redirect(url_for('data'))

@app.route('/data')
def data():
    sp = spotipy.Spotify(auth_manager=SpotifyOAuth(scope=scope, show_dialog=True))
    artistsResults = sp.current_user_top_artists(limit=100, time_range="long_term")
    songResults = sp.current_user_top_tracks(limit=40, time_range='long_term')
    artists = []
    songs = []
    for artist in artistsResults['items']:
        name = artist['name']
        if artist['images']:
            image_url = artist['images'][0]['url']
        else:
            image_url = None
        artists.append({'name': name, 'image_url': image_url})

    for song in songResults['items']:
        songName = song['name']
        songArtist = song['artists'][0]['name']
        songLink = song['external_urls']['spotify']
        cover = song['album']['images'][1]['url']
        print(songName, songArtist, songLink, cover)
        songs.append({'name': songName, 'artist': songArtist, 'link': songLink, 'cover': cover})

    return render_template('artists.html', artists=artists, songs=songs)

if __name__ == '__main__':
    app.run(debug=True)
