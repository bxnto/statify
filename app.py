import spotipy
from spotipy.oauth2 import SpotifyOAuth
from flask import Flask, render_template, redirect, url_for, session, request
from flask_session import Session
import os

scope = "user-library-read user-top-read"

app = Flask(__name__)
app.config['SECRET_KEY'] = os.urandom(64)
app.config['SESSION_TYPE'] = 'filesystem'
app.config['SESSION_FILE_DIR'] = './.flask_session/'
Session(app)

SPOTIPY_CLIENT_ID = os.environ.get('SPOTIPY_CLIENT_ID')
SPOTIPY_CLIENT_SECRET = os.environ.get('SPOTIPY_CLIENT_SECRET')
SPOTIPY_REDIRECT_URI = os.environ.get('SPOTIPY_REDIRECT_URI')

print(SPOTIPY_CLIENT_ID, SPOTIPY_CLIENT_SECRET, SPOTIPY_REDIRECT_URI)

@app.route('/')
def index():
    cache_handler = spotipy.cache_handler.FlaskSessionCacheHandler(session)
    auth_manager = spotipy.oauth2.SpotifyOAuth(
        scope='user-top-read user-library-read',
        cache_handler=cache_handler,
        show_dialog=True
    )

    if request.args.get("code"):
        # Step 2. Being redirected from Spotify auth page
        auth_manager.get_access_token(request.args.get("code"))
        return redirect(url_for('data'))

    if not auth_manager.validate_token(cache_handler.get_cached_token()):
        # Step 1. Display sign-in link when no token
        auth_url = auth_manager.get_authorize_url()
        return f'<h2><a href="{auth_url}">Sign in</a></h2>'

    # Step 3. Signed in, display data
    return redirect(url_for('data'))

@app.route('/sign_out')
def sign_out():
    session.pop("token_info", None)
    return redirect('/')

@app.route('/data')
def data():
    artistRange = request.args.get('artistDuration', 'medium_term')
    artistLimit = int(request.args.get('artistAmount', 10))
    songRange = request.args.get('songDuration', 'medium_term')
    songLimit = int(request.args.get('songAmount', 10))

    # Use the token from the session for Spotify API requests
    cache_handler = spotipy.cache_handler.FlaskSessionCacheHandler(session)
    auth_manager = spotipy.oauth2.SpotifyOAuth(cache_handler=cache_handler)
    sp = spotipy.Spotify(auth_manager=auth_manager)
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
    app.run(debug=True, port=5001)
