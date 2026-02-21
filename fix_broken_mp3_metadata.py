# Force some changes on some music files

from unidecode import unidecode
import os
import mutagen.id3
import spotify_controller
import requests



# scans folder for music files, returns array of paths
def list_files_in_nested_folders(root_folder):
    musics = []
    for dirpath, dirnames, filenames in os.walk(root_folder):
        print(f"Folder: {dirpath}")
        for filename in filenames:
            print(f"  File: {filename}")
            filepath = dirpath + "/" + filename
            audiotype = filename[-3:]
            if audiotype in ['m4a', 'm4p', 'mp3']:
                musics.append(filepath)
            else:
                print("skipped")

    return(musics)


# import raw music files, get metadata and make a big list
def import_music(start_folders):
    # first, find all the music files
    all_paths = []
    all_music = []
    for start_folder in start_folders:
        this_list = list_files_in_nested_folders(start_folder)
        #print(this_list)
        all_paths = all_paths + this_list

    return(all_paths)


def spotify_search_artist(access_token, artist_name):

    url = 'https://api.spotify.com/v1/search'
    headers = {'Authorization': f'Bearer {access_token}'}
    params = {
        'q': artist_name,
        'type': 'artist',
        'limit': 1
    }

    response = requests.get(url, headers=headers, params=params)
    data = response.json()

    if data['artists']['items']:
        artist = data['artists']['items'][0]
        print(f"Artist: {artist['name']}")
        print(f"ID: {artist['id']}")
        print(f"Popularity: {artist['popularity']}")
        return artist['id']
    else:
        print("Artist not found")
        return None


def spotify_get_track_info(access_token, track_name, artist_name=None):

    # Build query
    query = f"track:{track_name}"
    if artist_name:
        query += f" artist:{artist_name}"

    url = "https://api.spotify.com/v1/search"
    headers = {"Authorization": f"Bearer {access_token}"}
    params = {
        "q": query,
        "type": "track",
        "limit": 1
    }

    response = requests.get(url, headers=headers, params=params)
    #print(response)
    data = response.json()
    #print(f'Data is {data}')
    if data["tracks"]["items"]:
        track = data["tracks"]["items"][0]
        return {
            "track": track["name"],
            "artists": [artist["name"] for artist in track["artists"]],
            "album": track["album"]["name"],
            "release_date": track["album"]["release_date"],
            "release_date_precision": track["album"]["release_date_precision"],
            "track_id": track["id"],
            "album_id": track["album"]["id"],
            "album_type": track["album"]["album_type"]
        }
    return None


# Test routine if run as main
if __name__ == "__main__":
    # Run this with your current token

    token = spotify_controller.get_user_token()

    target_album_path_list = ["/home/patrick/Music/spotify_tracks/"]
    album_music = import_music(target_album_path_list)
    print(album_music)
    #album_music = ["/home/patrick/Music/iTunes/iTunes Media/Music/Foreigner/Agent Provocateur/"]
    for music_file in album_music:
        #print(music_file)
        audiotype = music_file[-3:]
        audiofile = mutagen.File(music_file)
        keys = audiofile.keys()
        print(keys)

        if audiotype == 'mp3':
            trunc_path = music_file[:-4]  # remove type from filename
            split_string = trunc_path.split('/')
            n_words = len(split_string)
            filename = split_string[n_words - 1]
            album_name = split_string[n_words - 2]
            artist_name = split_string[n_words - 3]
            print(f'filename:{filename}, album:{album_name}, artist:{artist_name}')
            already_clean = 1

            try:
                print('TPE1:', audiofile['TPE1']) # Artist
            except:
                audiofile['TPE1'] = mutagen.id3.TPE1(encoding=3, text=artist_name)
                print(f'Set TPE1 to {artist_name}')
                already_clean = 0

            try:
                print('TCON:',audiofile['TCON']) # Type
            except:
                artist_id = spotify_search_artist(token, artist_name)
                genre_dict = spotify_controller.fetch_artist_genre(token, [artist_id])
                genre_found = genre_dict[artist_id]
                audiofile['TCON'] = mutagen.id3.TCON(encoding=3, text="Soundtrack")
                print(f'Artist {artist_name} ({artist_id}) assigned genre is {genre_found}')
                already_clean = 0

            try:
                print('TDRC:',audiofile['TDRC']) # date
            except:
                track_info = spotify_get_track_info(token, filename, artist_name)
                #print(track_info)
                if track_info:
                    date = track_info['release_date']
                    year = date[0:4]
                    print(f'Set TDRC to {year}')
                    audiofile['TDRC'] = mutagen.id3.TDRC(encoding=3, text=year)
                    already_clean = 0
                else:
                    print(f'Date not found for {artist_name}\'s {filename}')

            try:
                print('TIT2:',audiofile['TIT2'])
            except:
                audiofile['TIT2'] = mutagen.id3.TIT2(encoding=3, text=filename)
                print(f'Set TIT2 to {filename}')
                already_clean = 0

            try:
                print('TALB:', audiofile['TALB'])
            except:
                audiofile['TALB'] = mutagen.id3.TALB(encoding=3, text=album_name)
                print(f'Set TALB to {album_name}')
                already_clean = 0

                # audiofile['TIT2'] = mutagen.id3.TIT2(encoding=3, text=last_word)
                # audiofile['TDRC'] = mutagen.id3.TDRC(encoding=3, text="2001")
                # audiofile['TCON'] = mutagen.id3.TCON(encoding=3, text="Alternative")

                # audiofile['TCON'] = mutagen.id3.TCON(encoding=3, text="Soundtrack")
                # audiofile['TDRC'] = mutagen.id3.TDRC(encoding=3, text="1995")
                #audiofile['TALB'] = mutagen.id3.TALB(encoding=3, text="Tank Girl Soundtrack")
                # audiofile['TPE1'] = mutagen.id3.TPE1(encoding=3, text="Various artists")
                # audiofile['TIT2'] = mutagen.id3.TIT2(encoding=3, text=last_word)

            if not already_clean:
                #pass
                audiofile.save()
            else:
                print(f'Already clean: {artist_name}\'s {filename}')