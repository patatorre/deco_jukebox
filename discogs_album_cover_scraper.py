
import requests
import os
import time
import mutagen

# retrieve metadata from the audio file: artist, album, genre, date
def get_tune_metadata(filename):
    audiofile = mutagen.File(filename)
    #print(filename)
    error_flag = 0
    audiotype = filename[-3:]
    # print(f"audiotype:{audiotype}")
    if audiotype == 'm4p':
        #print(f'skip m4p {filename}')
        pass
    if audiotype in ['m4a']: #, 'm4p']:
        try:
            title = audiofile["©nam"]
        except:
            title = "Unknown Title"
        try:
            artist = audiofile["©ART"]
        except:
            artist = ["Unknown Artist"]
        try:
            album = audiofile["©alb"]
        except:
            album = ['Unknown Album']
        try:
            date = audiofile['©day'] #'©day': ['1977-05-25T12:00:00Z'],
            year = int(date[0][0:4])
        except:
            year = 1066
        try:
            genre = audiofile['©gen']
        except:
            genre = 'Other'
            #error_flag = 1
        try:
            duration = audiofile.info.length
            #print(f'Duration: {duration}')
        except:
            duration = 0
        # blabla = f"title:{title[0]} by {artist[0]} on album {album[0]}"
        # print(blabla)
    elif audiotype == 'mp3':
        #print(audiofile)
        try:
            artist = audiofile['TPE1'].text
        except:
            artist = ['Unknown Artist']
        try:
            title = audiofile['TIT2'].text
        except:
            title = ["Unknown Title"]
        try:
            album = audiofile['TALB'].text
        except:
            album = ['Unknown Album']
        try:
            date = audiofile['TDRC'].text
            #print(date)
            if type(date) == mutagen.id3.ID3TimeStamp:
                #print('its a timestamp')
                date = date.text
                year = date[0][0:4]
            elif type(date) == str:
                #print('its a string')
                year = int(date[0:4]) # I found one example only. date was just the year
            elif type(date) == list: # prolly a list of timestamps, but let's hedge our bets
                ze_date = date[0]
                if type(ze_date) == mutagen.id3.ID3TimeStamp:
                # print('its a timestamp')
                    ze_date = ze_date.text
                    year = int(ze_date[0:4])
                else: # list of strings, then
                #print('its a list')
                #print(f'Date found not str is : {date}')
                    year = int(ze_date[0:4])
            else:
                print(f'Unexpected case, type = {type(date)} date={date}')
        except:
            year = 1066
        try:
            genre = audiofile['TCON'].text
            # blabla = f"title:{title[0]} by {artist[0]} on album {album[0]}"
            # print(blabla)
        except Exception as e:
            print(f'Error {e} parsing {filename}')
            keys = audiofile.keys()
            print(f'keys:{keys}')
            #error_flag = 1
            genre = 'Other'
        try:
            duration = audiofile.info.length
            #print(f'Duration: {duration}')
        except:
            duration = 0
            print(f'MP3 duration not found {filename}')

    else: # quite possibly not an audio file, not sure how it got in the list
        error_flag = 1

    # Fill in the missing metadata with dummy values just so we can return them
    # This would be for a non-audio file which gets ignored
    # error handling for missing metadata of otherwise valid file types is handled above here
    if (error_flag > 0): #
        try:
            title
        except NameError:
            title = [""]
        try:
            artist
        except NameError:
            artist = [""]
        try:
            album
        except NameError:
            album = ["Unknown Album"]
        try:
            genre
        except NameError:
            genre = [""]
        try:
            year
        except NameError:
            year = 1066
        try:
            duration
        except:
            duration = 0

    return(title[0], artist[0], album[0], year, genre[0], duration, error_flag)



def read_ini(config_file_name):
    config = {}
    try:
        with open(config_file_name) as f:
            for line in f:
                line = line.strip()
                if line and not (line.startswith('#') or line.startswith(';')):
                    key, value = line.split('=', 1)
                    config[key.strip()] = value.strip()
                    print(f'{key.strip()} = {value.strip()}')
    except:
        print(f'Error reading config file \"{config_file_name}\"')

    return(config)

def search_discogs_artist(artist_name, token):
    url = "https://api.discogs.com/database/search"
    headers = {
        'User-Agent': 'YourApp/1.0',
        'Authorization': f'Discogs token={token}'
    }
    params = {
        'q': artist_name,
        'type': 'artist',
        'per_page': 1
    }

    response = requests.get(url, headers=headers, params=params)
    return response.json()


def get_release_genres_and_year(release_id, token):
    url = f"https://api.discogs.com/releases/{release_id}"
    headers = {
        'User-Agent': 'YourApp/1.0',
        'Authorization': f'Discogs token={token}'
    }

    response = requests.get(url, headers=headers)
    data = response.json()

    genres = data.get('genres', [])
    #styles = data.get('styles', [])
    year = data.get('year')  # may be None if not present

    return genres, year


def get_release_cover_art_url(release_id, token):
    url = f"https://api.discogs.com/releases/{release_id}"
    headers = {
        'User-Agent': 'YourApp/1.0',
        'Authorization': f'Discogs token={token}'
    }

    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()  # Raise exception for 4xx/5xx status codes
        data = response.json()

        # The images array may contain one or more images
        images = data.get('images', [])
        if not images:
            print("No images found for this release.")
            return None

        # Try to find the primary image (type = 'primary')
        for img in images:
            if img.get('type') == 'primary':
                return img.get('uri') or img.get('resource_url')

        # If no primary image, return the first one as fallback
        first_img = images[0]
        return first_img.get('uri') or first_img.get('resource_url')

    except requests.exceptions.RequestException as e:
        print(f"Error fetching release data: {e}")
        return None
    except ValueError as e:
        print(f"Error parsing JSON response: {e}")
        return None


def get_artist_releases(artist_id, token, per_page=50):
    url = f"https://api.discogs.com/artists/{artist_id}/releases"
    headers = {
        'User-Agent': 'YourApp/1.0',
        'Authorization': f'Discogs token={token}'
    }
    params = {
        'per_page': per_page,
        'page': 1
    }
    all_releases = []
    while True:
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        data = response.json()
        releases = data.get('releases', [])
        all_releases.extend(releases)

        # Pagination: check if there's a next page
        if not data.get('pagination', {}).get('urls', {}).get('next'):
            break
        params['page'] += 1
        time.sleep(0.2)  # be kind to the API

    return all_releases


def get_release_id_by_artist_and_album(artist_name, album_name, token):

    # Build search URL with filters
    url = "https://api.discogs.com/database/search"

    headers = {
        'User-Agent': 'YourGenreFetcher/1.0 +http://yourapp.example.com',  # Required!
        'Authorization': f'Discogs token={token}'
    }

    params = {
        'type': 'release',  # Only search releases
        'artist': artist_name,  # Filter by artist
        'release_title': album_name,  # Filter by album title
        'per_page': 5  # Get top 5 matches
    }

    try:
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        data = response.json()

        results = data.get('results', [])

        if not results:
            print(f"No releases found for {artist_name} - {album_name}")
            return None

        # Display matches to help with selection
        print(f"Found {len(results)} potential matches:")
        for i, result in enumerate(results):  # Show first 3
            print(f"  {i + 1}. {result.get('id')}:{result.get('title')} (Year: {result.get('year', 'N/A')})")

        # Select a release that has the earliest release date
        earliest_release_date = 6666
        best_idx = 0
        for idx, result in enumerate(results):
            year = int(result.get('year', '0'))
            if year > 0 :
                if year < earliest_release_date:
                    earliest_release_date = year
                    best_idx = idx
        best_match = results[best_idx]
        release_id = best_match.get('id')

        if release_id:
            print(f"Selected release ID: {release_id}")
            return release_id
        else:
            print("No ID found in result")
            return None

    except requests.exceptions.RequestException as e:
        print(f"API request failed: {e}")
        return None
    except Exception as e:
        print(f"Unexpected error: {e}")
        return None


# Example usage with your existing genre-fetching function
def get_genres_for_album(artist_name, album_name, token):
    """Get genres for a specific album by artist and title."""
    release_id = get_release_id_by_artist_and_album(artist_name, album_name, token)

    if release_id:
        # Use your existing get_release_genres function
        genres, year = get_release_genres_and_year(release_id, token)
        return {
            'artist': artist_name,
            'album': album_name,
            'genre': genres[0],
            'year': year
        }
    return None


def get_album_genre_and_year(artist_name, album_name):
    discogs_token = os.getenv('DISCOGS_PERSONAL_TOKEN')
    result = get_genres_for_album(artist_name, album_name, discogs_token)
    if result:
        return result['genre'], result['year']
    else:
        return 'unknown', '1066'

def get_unarted_albums_list(music_root_folder, album_cover_dir):

    albums = []
    music = []

    for dirpath, dirnames, filenames in os.walk(music_root_folder):
        filenames.sort()
        for filename in filenames:
            filepath = os.path.join(dirpath, filename)
            audiotype = filename[-3:]
            if audiotype in ['m4a', 'mp3']:
                music.append(filepath)

    processed_dirs = set()
    full_albums = set()
    for music_file in music:
        album_dir = os.path.dirname(music_file)
        if album_dir not in processed_dirs:
            processed_dirs.add(album_dir)
        else: # already there, so this is the second track found
            if album_dir not in full_albums:
                full_albums.add(album_dir)
                title, artist, album, year, genre, duration_s, error_flag = get_tune_metadata(music_file)
                if album == 'Unknown Album':
                    pass # tbd
                album_art_path = os.path.join(album_cover_dir, album + '.jpg')
                if not os.path.isfile(album_art_path):
                    print(f'Missing art file for {album} by {artist}')
                    albums.append((album, artist))
            else:
                pass
    return(albums)


def download_cover_image(image_url, output_path):
    """
    Download an image from a URL and save it to a file.

    Args:
        image_url (str): The URL of the image to download.
        output_path (str): Local file path where the image will be saved.
        user_agent (str, optional): User-Agent string to use. If None, a default is used.

    Returns:
        bool: True if successful, False otherwise.
    """
    headers = {
        'User-Agent': 'YourGenreFetcher/1.0 +http://yourapp.example.com'  # Required!
    }
    try:
        # Stream the download to handle large files efficiently
        with requests.get(image_url, headers=headers, stream=True) as r:
            r.raise_for_status()
            # Ensure the output directory exists
            os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
            with open(output_path, 'wb') as f:
                for chunk in r.iter_content(chunk_size=8192):
                    f.write(chunk)
        print(f"Image successfully saved to {output_path}")
        return True
    except requests.exceptions.RequestException as e:
        print(f"Error downloading image: {e}")
        return False
    except IOError as e:
        print(f"Error writing file: {e}")
        return False


def discogs_scrape_album_covers(albums_missing_art, album_cover_dir, discogs_token):
    for album_name, artist_name in albums_missing_art:
        if album_name != 'Unknown Album': # if the album title is unknown, then we can't retrieve the art, now can we?
            release_id = get_release_id_by_artist_and_album(artist_name, album_name, discogs_token)
            if release_id is not None:
                art_url = get_release_cover_art_url(release_id, discogs_token)
                if art_url is not None:
                    save_file_path = os.path.join(album_cover_dir, album_name + '.jpg')
                    download_cover_image(art_url, save_file_path)
                else:
                    print(f'Album {album_name} -- no art found.')



# ========================== Main Automatic Scraper =======================================
if __name__ == "__main__":
    album_cover_dir = os.path.join('graphics', 'album_covers')
    config_file_name = 'jukebox.cfg'
    discogs_token = os.getenv('DISCOGS_PERSONAL_TOKEN')
    if discogs_token is not None:
        config = read_ini(config_file_name) # retrieves jukebox.cfg info to find out where the library is
        if not 'music_root_folder' in config:
            print(f'Invalid config file \"{config_file_name}\", does not specify music_root_folder')
        else:
            music_root_folders = config['music_root_folder'].split(',')
            albums_missing_art = []
            for music_root_folder in music_root_folders:
                if not os.path.isdir(music_root_folder):
                    print(f'Music root folder \"{music_root_folder}\" does not exist')
                    if os.path.exists("C:\\"):
                        if music_root_folder.find('\\') == -1:
                            print('It looks like your path does not contain the right kind of slash ("\\")')
                        #print("Probably Windows (has C:\\)")
                    else:
                        #print("Probably not Windows")
                        if music_root_folder.find('/') == -1:
                            print('It looks like your path does not contain the right kind of slash ("/")')
                else:
                    this_albums_missing_art = get_unarted_albums_list(music_root_folder, album_cover_dir)
                    print(f'{len(this_albums_missing_art)} album art missing from {music_root_folder}')
                    albums_missing_art += this_albums_missing_art

            # now go scrape
            discogs_scrape_album_covers(albums_missing_art, album_cover_dir, discogs_token)


    else:
        print("Discogs Personal Token not found. You need to do the following:")
        print("1) Go to https://www.discogs.com/settings/developers")
        print("2) Login or create an account")
        print("3) click on \"Generate new token\" (personal access token)")
        print("4) create an environmental variable called DISCOGS_PERSONAL_TOKEN, put the token as its value")
        print("5) Reboot so it kicks in")




    # artist_name = 'Daft Punk'
    # album_name = 'Random Access Memories'
    #
    # result = get_genres_for_album('Daft Punk', 'Random Access Memories', discogs_token)
    # if result:
    #     print(f"Genre: {result['genre']}")
    #     print(f"year: {result['year']}")


