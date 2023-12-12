import spotipy, os
from spotipy.oauth2 import SpotifyOAuth
from flask import Flask, render_template, redirect, url_for, session, request

scope = "user-library-read user-top-read"

app = Flask(__name__)
app.secret_key = "Ilov3TayTay"  # Change this to a random secret key

SPOTIPY_CLIENT_ID = os.environ.get('SPOTIPY_CLIENT_ID')
SPOTIPY_CLIENT_SECRET = os.environ.get('SPOTIPY_CLIENT_SECRET')
SPOTIPY_REDIRECT_URI = os.environ.get('SPOTIPY_REDIRECT_URI')

print(SPOTIPY_CLIENT_ID, SPOTIPY_CLIENT_SECRET, SPOTIPY_REDIRECT_URI)

def get_spotify_object():
    return spotipy.Spotify(auth_manager=SpotifyOAuth(client_id=SPOTIPY_CLIENT_ID,
                                                     client_secret=SPOTIPY_CLIENT_SECRET,
                                                     redirect_uri=SPOTIPY_REDIRECT_URI,
                                                     scope=scope,
                                                     show_dialog=True))

@app.route('/')
def index():
    return render_template('index.html')

@app.route("/login")
def login():
    sp = get_spotify_object()
    session['token_info'] = sp.auth_manager.get_cached_token()
    print(sp.auth_manager.get_cached_token())
    return redirect(url_for('data'))

@app.route('/data')
def data():
    artistRange = request.args.get('artistDuration', 'medium_term')
    artistLimit = int(request.args.get('artistAmount', 10))
    songRange = request.args.get('songDuration', 'medium_term')
    songLimit = int(request.args.get('songAmount', 10))
    sp = spotipy.Spotify(auth=session['token_info']['access_token'])
    artistsResults = sp.current_user_top_artists(limit=artistLimit, time_range=artistRange)
    songResults = sp.current_user_top_tracks(limit=songLimit, time_range=songRange)
    artists = []
    songs = []

    print(f"Artist Range: {artistRange}, Artist Limit: {artistLimit}, Song Range: {songRange}, Song Limit: {songLimit}")

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
        songs.append({'name': songName, 'artist': songArtist, 'link': songLink, 'cover': cover})

    return render_template('artists.html', artists=artists, songs=songs)

if __name__ == '__main__':
    app.run()
