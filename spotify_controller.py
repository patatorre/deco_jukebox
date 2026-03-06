# Spotify player app controller
# also spotify queries
#
# Patrick Dumais Jan 2026

import requests
import dbus
import base64
import time
import webbrowser
from urllib.parse import urlencode, parse_qs, urlparse
import threading
#from urllib.parse import urlparse, parse_qs
from http.server import HTTPServer, BaseHTTPRequestHandler
import os

# Python_jukebox app, see the developer dashboard
# https://developer.spotify.com/dashboard

CLIENT_ID = os.getenv('SPOTIFY_CLIENT_ID')
CLIENT_SECRET = os.getenv('SPOTIFY_CLIENT_SECRET')
PLAYLIST_ID = os.getenv('SPOTIFY_PLAYLIST_ID')
print(CLIENT_ID, CLIENT_SECRET, PLAYLIST_ID)

REDIRECT_URI = 'http://127.0.0.1:8888/callback'

spotify_client_token_filename = 'spotify_client_token.txt'
spotify_user_token_filename = 'spotify_user_token.txt'


class SpotifyDBusController:
    def __init__(self):
        self.bus = dbus.SessionBus()
        self.spotify = None
        self.connect()
        self.stop_time=time.time() + 315532800  # 10 years in the future
        self.playing = 0
        self.pause_start = time.time()

    def connect(self):
        """Connect to Spotify via DBus"""
        try:
            # Wait for Spotify to appear (max 30 seconds)
            for i in range(30):
                try:
                    self.spotify = self.bus.get_object(
                        'org.mpris.MediaPlayer2.spotify',
                        '/org/mpris/MediaPlayer2'
                    )
                    self.player = dbus.Interface(
                        self.spotify,
                        'org.mpris.MediaPlayer2.Player'
                    )
                    print("Connected to Spotify!")
                    return True
                except dbus.exceptions.DBusException:
                    if i == 0:
                        print("Waiting for Spotify... (start Spotify app)")
                    time.sleep(1)
            return False
        except Exception as e:
            print(f"Connection error: {e}")
            return False

    def play_pause(self):
        if self.spotify:
            self.player.PlayPause()
            if self.playing>0:
                self.playing = 0
                self.pause_start = time.time()
            else:
                self.playing = 1
                paused_time = time.time() - self.pause_start
                self.stop_time += paused_time
        return(self.playing)

    def play(self, spotify_uri):
        """Play a Spotify URI (e.g., spotify:track:123)"""
        if self.spotify:
            self.player.OpenUri(spotify_uri)
            self.playing = 1

    def get_current_track(self):
        if self.spotify:
            props = dbus.Interface(
                self.spotify,
                'org.freedesktop.DBus.Properties'
            )
            metadata = props.Get('org.mpris.MediaPlayer2.Player', 'Metadata')
            return {
                'title': str(metadata.get('xesam:title', 'Unknown')),
                'artist': ', '.join(metadata.get('xesam:artist', ['Unknown'])),
                'album': str(metadata.get('xesam:album', 'Unknown'))
            }
        return None

    def set_stop_time(self, duration_s):
        now = time.time()
        self.stop_time = now + duration_s

    def is_track_done(self):
        now = time.time()
        if now > self.stop_time:
            return True
        else:
            return False


def test_spotify_token(access_token):
    url = 'https://api.spotify.com/v1/search'
    headers = {
        'Authorization': f'Bearer {access_token}'
    }
    params = {
        'q': 'a',
        'type': 'track',
        'limit': 1
    }
    # we'll get an empty token if no previous token was found in the file
    if access_token == '':
        return False

    try:
        response = requests.get(url, headers=headers, params=params)
        if response.status_code == 200:
            print('Token is valid')
            return True
        elif response.status_code == 401:
            print('Token is invalid or expired')
            return False
        else:
            print(f'Unexpected status: {response.status_code}')
            return False
    except Exception as e:
        print(f'Error testing token: {e}')
        return False


def get_client_token():
    # get old token and test it before we request a new one
    try:
        f = open(spotify_client_token_filename)
        access_token = f.readline()
        f.close()
    except: # no file
        access_token = ''

    if not test_spotify_token(access_token): # Doesn't work, get a new one




        # Encode credentials for the Authorization header
        credentials = f"{CLIENT_ID}:{CLIENT_SECRET}"
        credentials_base64 = base64.b64encode(credentials.encode()).decode()

        # Request an access token
        auth_url = "https://accounts.spotify.com/api/token"
        auth_headers = {
            "Authorization": f"Basic {credentials_base64}",
        }
        auth_data = {
            "grant_type": "client_credentials",
        }

        response = requests.post(auth_url, headers=auth_headers, data=auth_data)
        access_token = response.json().get("access_token")

        if not access_token:
            raise Exception("Failed to retrieve access token") # I think we'll need to improve error handling

        print(access_token)

        # save it for subsequent use
        f = open(spotify_client_token_filename, 'w')
        f.write(access_token)

    return(access_token)


# genre field may contain more than one genre, must be in format
# 'genre:electronic genre:soundtrack' etc
# Valid genres are: rock, electronic, soundtrack, jazz, R&B, classical, french
def spotify_search_tracks(genre_field, year_range, limit, page_number):
    access_token = get_client_token()
    # Spotify API search endpoint
    print(f'Searching for {genre_field} in {year_range}')
    search_url = "https://api.spotify.com/v1/search"
    search_params = {
        "q": f"{genre_field} {year_range}",  # Search query
        "type": "track",  # Search for albums
        "limit": {limit},  # number of tracks returned
        "offset": {limit*page_number} # "page 2" results etc
    }

    # Make the request
    headers = {
        "Authorization": f"Bearer {access_token}",
    }
    response = requests.get(search_url, headers=headers, params=search_params)

    if response.status_code != 200:
        print(f"Failed to search: {response.status_code}")
        return []
    else:
    # Parse the response
        search_results = response.json()
        tracks = search_results['tracks']['items']

    if not tracks:
        print(f"No tracks found for {genre_field} {year_range}")
        return []

    # Display results
    for i, track in enumerate(tracks, 1):
        print(f"{i:2d}. {track['name']}")
        print(f"    Artist: {', '.join([artist['name'] for artist in track['artists']])}")
        print(f"    Album: {track['album']['name']} (album ID {track['album']['id']})")
        print(f"    Release: {track['album']['release_date']}")
        duration_s = track['duration_ms'] / 1000
        print(f"    Duration: {duration_s} s")
        print(f"    Popularity: {track['popularity']}/100")
        #print(f"    Preview: {track['preview_url'] or 'No preview available'}")
        print(f"    Spotify URL: {track['external_urls']['spotify']}")
        print(f"    Spotify URI: {track['uri']}")

        print()

    #print(tracks[0])

    return tracks


def get_album_art(album_id):

    access_token = get_client_token()

    # Spotify API endpoint for album information
    album_url = f"https://api.spotify.com/v1/albums/{album_id}"

    # Make the request
    headers = {
        "Authorization": f"Bearer {access_token}",
    }
    response = requests.get(album_url, headers=headers)

    if response.status_code != 200:
        raise Exception(f"Failed to retrieve album information: {response.status_code}")

    # Parse the response
    album_data = response.json()
    album_name = album_data["name"]
    artist_name = album_data["artists"][0]["name"]
    album_cover_url = album_data["images"][0]["url"]  # Highest resolution image

    print(f"Album: {album_name} by {artist_name}")
    print(f"Album Cover URL: {album_cover_url}")

    # Download the album cover image
    response = requests.get(album_cover_url)
    if response.status_code == 200:
        return(response.content)
    else:
        return None

    #     with open(filepath, "wb") as file:
    #         file.write(response.content)
    #     print("Album cover downloaded successfully!")
    # else:
    #     print("Failed to download album cover.")


def fetch_artist_genre(access_token, artist_ids):
    """
    Get genres for multiple artists at once (max 50 IDs)
    """
    url = "https://api.spotify.com/v1/artists"

    headers = {
        "Authorization": f"Bearer {access_token}"
    }

    params = {
        "ids": ",".join(artist_ids[:50])  # Spotify allows max 50 IDs per call
    }

    response = requests.get(url, headers=headers, params=params)

    if response.status_code == 200:
        artists_data = response.json()
        genres_dict = {}

        for artist in artists_data.get('artists', []):
            if artist:  # Check if artist exists
                genres = artist.get('genres', [])
                #print(genres)
                if len(genres) > 0:
                    first_genre = genres[0]
                else:
                    first_genre = 'unknown'
                genres_dict[artist['id']] = first_genre

        return genres_dict
    else:
        print(f"Error getting artists info: {response.status_code}")
        return {}


# Reads tracks off a specified playlist and returns them in a 'playlist' format
# ... should be able to pop those straight in the jukebox playlist
def spotify_get_playlist(access_token, playlist_id):
    #access_token = get_client_token()
    # Spotify API search endpoint
    #print(f'Searching for {genre_field} in {year_range}')
    search_url = f"https://api.spotify.com/v1/playlists/{playlist_id}/tracks"
    #print(search_url)
    # Make the request
    headers = {
        "Authorization": f"Bearer {access_token}",
    }
    # params = {
    #     "limit": 30,
    #     "offset": 0
    # }
    #response = requests.get(search_url, headers=headers, params=params)
    response = requests.get(search_url, headers=headers)

    if response.status_code != 200:
        print(f"Failed to search: {response.status_code}")
        return []
    else:
    # Parse the response
        tracks = response.json()
        #print(tracks)

    if not tracks:
        #print(f"No tracks found for {genre_field} {year_range}")
        return []


    artist_ids = []
    # Print all track names and artists; collate artist id list
    print("Tracks in playlist:")
    for i, item in enumerate(tracks['items'], 1):
        track = item['track']
        artists = ', '.join([artist['name'] for artist in track['artists']])
        print(f"{i}. {track['uri']}:{track['name']} - {artists}")
        artists = track['artists']
        #print(artists)
        first_artist = artists[0]['name']
        first_artist_id = artists[0]['id']
        artist_ids.append(first_artist_id)

    artist_genres_dict = fetch_artist_genre(access_token, artist_ids)

    tracks_list = []
    # massage a bit and fetch the genres from (first) artist name
    idx = 0
    for item in tracks['items']:
        print(item)
        track = item['track']
        this_album = track['album']['name']
        #print(this_album)
        album_id = track['album']['id']
        this_title = track['name']
        uri =  track['uri']
        duration_s = track['duration_ms'] / 1000
        this_year = track['album']['release_date']
        artists = track['artists']
        this_artist = artists[0]['name']
        this_artist_id = artist_ids[idx]
        this_genre = artist_genres_dict[this_artist_id]
        playlist_entry = {'album': this_album, 'artist': this_artist, 'title': this_title, 'filepath': uri,
                          'duration_s': duration_s,
                          'genre': this_genre, 'year': this_year, 'album_id': album_id, 'list_index':0}

        tracks_list.append(playlist_entry)
        idx += 1

    return tracks_list

# genre field may contain more than one genre, must be in format
# 'genre:electronic genre:soundtrack' etc
# Valid genres are: rock, electronic, soundtrack, jazz, R&B, classical, french
def spotify_get_playlist_id(access_token, playlist_name):
    #access_token = get_user_token()
    # Spotify API search endpoint
    #print(f'Searching for {genre_field} in {year_range}')
    search_url = "https://api.spotify.com/v1/me/playlists"

    # Make the request
    headers = {
        "Authorization": f"Bearer {access_token}",
    }
    print(headers)
    response = requests.get(search_url, headers=headers)
    search_results = response.json()
    print(search_results)
    playlist_id = search_results['items'][0]['id']
    print(f'Playlist ID is:{playlist_id}')

    return playlist_id


class SpotifyHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        # Parse the callback
        query = urlparse(self.path).query
        params = parse_qs(query)

        if 'code' in params:
            self.server.auth_code = params['code'][0]
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b'Authorization successful! You can close this window.')
        else:
            self.send_response(400)
            self.end_headers()
            self.wfile.write(b'No authorization code received')

    def log_message(self, format, *args):
        pass  # Suppress default logging


# get higher priority token for interrogating user playlist
def get_user_token():

    # get old token and test it before we request a new one
    try:
        f = open(spotify_user_token_filename)
        user_token = f.readline()
        f.close()
    except: # no file
        user_token = ''

    if not test_spotify_token(user_token): # Doesn't work, get a new one

        # Start HTTP server
        server = HTTPServer(('127.0.0.1', 8888), SpotifyHandler)
        server.auth_code = None

        thread = threading.Thread(target=server.serve_forever)
        thread.daemon = True
        thread.start()

        # Build auth URL
        auth_url = 'https://accounts.spotify.com/authorize'
        params = {
            'client_id': CLIENT_ID,
            'response_type': 'code',
            'redirect_uri': REDIRECT_URI,
            'scope': 'playlist-read-private'
        }

        auth_request = f"{auth_url}?{'&'.join(f'{k}={v}' for k, v in params.items())}"

        print("Opening browser for Spotify login...")
        webbrowser.open(auth_request)

        # Wait for callback
        print("Waiting for authorization...")
        while server.auth_code is None:
            import time
            time.sleep(0.1)

        auth_code = server.auth_code
        print(f'Success! code is {auth_code}')

        # Got the code, shutdown server
        server.shutdown()

        # Step 3: Exchange for token
        #print("Exchanging code for token...")
        token_url = 'https://accounts.spotify.com/api/token'
        token_data = {
            'grant_type': 'authorization_code',
            'code': auth_code,
            'redirect_uri': REDIRECT_URI,
            'client_id': CLIENT_ID,
            'client_secret': CLIENT_SECRET
        }

        response = requests.post(token_url, data=token_data, timeout=10)
        print(f"   Status code: {response.status_code}")

        if response.status_code != 200:
            print(f"   ✗ Error: {response.text}")
            return None

        token_info = response.json()
        print(f"   ✓ Token response received")

        # Check all fields
        # print(f"\n4. Token details:")
        # print(f"   - access_token: {'Present' if 'access_token' in token_info else 'Missing'}")
        # print(f"   - token_type: {token_info.get('token_type', 'Missing')}")
        # print(f"   - expires_in: {token_info.get('expires_in', 'Missing')}")
        # print(f"   - scope: {token_info.get('scope', 'Missing')}")
        # print(f"   - refresh_token: {'Present' if 'refresh_token' in token_info else 'Missing'}")

        user_token = token_info.get('access_token')
        if not user_token:
            print("   ✗ No access_token in response!")
            return None

        print(f"got token:{user_token}")

        # save it for subsequent use
        f = open(spotify_user_token_filename, 'w')
        f.write(user_token)
        f.close()

    return user_token


# Test routine if run as main
if __name__ == "__main__":

    token = get_user_token()
    tracklist = spotify_get_playlist(token, PLAYLIST_ID)
    for i, item in enumerate(tracklist, 1):
        print(f'i:{item}')


