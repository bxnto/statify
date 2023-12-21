import spotipy
from spotipy.oauth2 import SpotifyOAuth
from flask import Flask, render_template, redirect, url_for, session, request
from flask_session import Session
import os

scopes = "user-library-read user-top-read playlist-modify-public playlist-modify-private playlist-read-private"

app = Flask(__name__)
app.config['SECRET_KEY'] = os.urandom(64)
app.config['SESSION_TYPE'] = 'filesystem'
app.config['SESSION_FILE_DIR'] = './.flask_session/'
Session(app)

SPOTIPY_CLIENT_ID = os.environ.get('SPOTIPY_CLIENT_ID')
SPOTIPY_CLIENT_SECRET = os.environ.get('SPOTIPY_CLIENT_SECRET')
SPOTIPY_REDIRECT_URI = os.environ.get('SPOTIPY_REDIRECT_URI')

@app.route('/')
def index():
    cache_handler = spotipy.cache_handler.FlaskSessionCacheHandler(session)
    auth_manager = spotipy.oauth2.SpotifyOAuth(
        scope=scopes,
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
        return render_template("index.html", auth_url = auth_url)

    # Step 3. Signed in, display data
    return redirect(url_for('data'))

@app.route('/sign_out')
def sign_out():
    session.pop("token_info", None)
    return redirect('/')

@app.route('/top/<time_range>')
def makeTopPlaylist(time_range):
    cache_handler = spotipy.cache_handler.FlaskSessionCacheHandler(session)
    auth_manager = spotipy.oauth2.SpotifyOAuth(cache_handler=cache_handler)
    sp = spotipy.Spotify(auth_manager=auth_manager)
    userInfoResults = sp.current_user()
    userName = userInfoResults['display_name']
    userID = userInfoResults['id']
    sp.user_playlist_create(user = userID,name = f"{userName}'s Top Tracks", public = False, description = "Top 100 tracks generated by Harmonify")
    playlist = sp.current_user_playlists(limit=1)['items'][0]
    playlistID = playlist['id']
    playlistLink = playlist['external_urls']['spotify']
    allSongs = list()
    for i in range(2):
        if i == 0:
            try:    
                songs = sp.current_user_top_tracks(limit = 50, time_range = time_range)
                allSongs.append(songs)
            except:
                return "<h2>Unable to access the data, are you whitelisted?</h2><br><a href='/sign_out'>Sign Out</a>"
        elif i == 1:
            try:
                songs = sp.current_user_top_tracks(offset=49, limit = 50, time_range = time_range)
                allSongs.append(songs)

            except:
                return "<h2>Unable to access the data, are you whitelisted?</h2><br><a href='/sign_out'>Sign Out</a>"
    songIDs = []
    for i in allSongs:
        for song in i['items']:
            songIDs.append(song['id'])

    try:
        sp.user_playlist_add_tracks(user= userID, playlist_id=playlistID, tracks=songIDs)
    except:
        return render_template('error.html')

    newURL = f'{url_for("data")}?playlistURL={playlistLink}'
    return redirect(newURL)

def openURL(urlToOpen):
    return render_template('openPlaylist.html', urlToOpen = urlToOpen)

    
@app.route('/data')
def data():
    if request.args.get('playlistURL') != None:
        playlistURL = request.args.get('playlistURL')
        return render_template('openPlaylist.html', urlToOpen = playlistURL)
    
    artistRange = request.args.get('artistRange', 'medium_term')
    artistLimit = int(request.args.get('artistLimit', 10))
    songRange = request.args.get('songRange', 'medium_term')
    songLimit = int(request.args.get('songLimit', 10))

    # Use the token from the session for Spotify API requests
    cache_handler = spotipy.cache_handler.FlaskSessionCacheHandler(session)
    auth_manager = spotipy.oauth2.SpotifyOAuth(cache_handler=cache_handler)
    sp = spotipy.Spotify(auth_manager=auth_manager)
    try:
        artistsResults = sp.current_user_top_artists(limit=artistLimit, time_range=artistRange)
        songResults = sp.current_user_top_tracks(limit=songLimit, time_range=songRange)
        userInfoResults = sp.current_user()
    except:
        return "<h2>Unable to access the data, are you whitelisted?</h2><br><a href='/sign_out'>Sign Out</a>"
    artists = []
    songs = []
    
    userName = userInfoResults['display_name']
    try:
        userPic = userInfoResults['images'][0]['url']
    except:
        userPic = url_for('static', filename = 'default.jpg')
    profileURL = userInfoResults['external_urls']['spotify']

    for artist in artistsResults['items']:
        name = artist['name']
        artistLink = artist['external_urls']['spotify']
        if artist['images']:
            image_url = artist['images'][0]['url']
        else:
            image_url = None
        artists.append({'name': name, 'image_url': image_url, 'link': artistLink})

    for song in songResults['items']:
        songName = song['name']
        songArtist = song['artists'][0]['name']
        songLink = song['external_urls']['spotify']
        cover = song['album']['images'][1]['url']
        songs.append({'name': songName, 'artist': songArtist, 'link': songLink, 'cover': cover})
    

    return render_template('artists.html', artists=artists, songs=songs, uName = userName, uPic = userPic, url = profileURL)

if __name__ == '__main__':
    app.run(debug=True)
