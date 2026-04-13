# Create missing metadata for mp3 files
# Using discogs to fill in the gaps
# WARNING: will try to guess artist/album from the directory path
#   if the flag below is set to 1 (and path is deep enough)
#
# Patrick Dumais
# patatorre "at" proton.me
# github.com/patatorre


ALLOW_NAME_GUESSING_FROM_PATH = 1 # set to 1 if library is organized like iTunes library music/artist/album/song.mp3

from unidecode import unidecode
import os
import mutagen.id3
import requests
import time


def read_ini(config_file_name):
    config = {}
    try:
        with open(config_file_name) as f:
            for line in f:
                line = line.strip()
                if line and not (line.startswith('#') or line.startswith(';')):
                    key, value = line.split('=', 1)
                    config[key.strip()] = value.strip()
                    #print(f'{key.strip()} = {value.strip()}')
    except:
        print(f'Error reading config file \"{config_file_name}\"')

    return(config)


# scans folder for music files, returns array of paths
def list_nested_mp3_files(start_folder):
    musics = []
    for dirpath, dirnames, filenames in os.walk(start_folder):
        # print(f"Folder: {dirpath}")
        for filename in filenames:
            #print(f"  File: {filename}")
            filepath = dirpath + "/" + filename
            audiotype = filename[-3:]
            if audiotype in ['mp3']:
                musics.append(filepath)
    return(musics)


def get_release_record_by_artist_and_album(artist_name, album_name, token):

    if token is not None:
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
                return None, 0

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
                # print(f"Selected release ID: {release_id}")
                # return release_id
                return best_match, 0 # return the whole dict so we don't need to fetch is again

            else:
                # print("No ID found in result")
                return None, 0

        except requests.exceptions.RequestException as e:
            print(f"API request failed: {e}")
            if e.response is not None:
                return None, e.response.status_code  # e.g., 404, 500, 429
            else:
                # No HTTP response (network error, DNS failure, timeout, etc.)
                return None, -1
        except Exception as e:
            print(f"Unexpected error: {e}")
            return None, -1
    else:
        return None, 0

def get_release_record_by_artist_and_song_title(artist_name, song_title, token):

    if token is not None:
        # Build search URL with filters
        url = "https://api.discogs.com/database/search"

        headers = {
            'User-Agent': 'YourGenreFetcher/1.0 +http://yourapp.example.com',  # Required!
            'Authorization': f'Discogs token={token}'
        }

        params = {
            'type': 'release',  # Only search releases
            'artist': artist_name,  # Filter by artist
            'track': song_title,  # Filter by album title
            'per_page': 5  # Get top 5 matches
        }

        try:
            response = requests.get(url, headers=headers, params=params)
            response.raise_for_status()
            data = response.json()

            results = data.get('results', [])

            if not results:
                print(f"No releases found for {artist_name} - {song_title}")
                return None, 0

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
                # print(f"Selected release ID: {release_id}")
                # return release_id
                return(best_match, 0) # return the whole dict so we don't need to fetch is again

            else:
                # print("No ID found in result")
                return None, 0

        except requests.exceptions.RequestException as e:
            print(f"API request failed: {e}")
            if e.response is not None:
                return None, e.response.status_code  # e.g., 404, 500, 429
            else:
                # No HTTP response (network error, DNS failure, timeout, etc.)
                return None, -1
        except Exception as e:
            print(f"Unexpected error: {e}")
            return None, -1
    else:
        return None, 0
    #     except requests.exceptions.RequestException as e:
    #         print(f"API request failed: {e}")
    #         return None
    #     except Exception as e:
    #         print(f"Unexpected error: {e}")
    #         return None
    # else:
    #     return None

# def get_release_genres_and_year(release_id, token):
#     url = f"https://api.discogs.com/releases/{release_id}"
#     headers = {
#         'User-Agent': 'YourApp/1.0',
#         'Authorization': f'Discogs token={token}'
#     }
#
#     response = requests.get(url, headers=headers)
#     data = response.json()
#
#     genres = data.get('genres', [])
#     #styles = data.get('styles', [])
#     year = data.get('year')  # may be None if not present
#     print(f'release id:{release_id}: year:{year} genres={genres}')
#
#     return genres, year


# def get_genres_for_album(artist_name, album_name, token):
#     """Get genres for a specific album by artist and title."""
#     release_id = get_release_id_by_artist_and_album(artist_name, album_name, token)
#
#     if release_id:
#         # Use your existing get_release_genres function
#         genres, year = get_release_genres_and_year(release_id, token)
#         return {
#             'artist': artist_name,
#             'album': album_name,
#             'genre': genres[0],
#             'year': year
#         }
#     return None


# def get_album_genre_and_year(artist_name, album_name):
#     discogs_token = os.getenv('DISCOGS_PERSONAL_TOKEN')
#     result = get_genres_for_album(artist_name, album_name, discogs_token)
#     if result:
#         return result['genre'], result['year']
#     else:
#         return 'unknown', '1066'

def get_release_genre_and_year(release_record):

    if release_record:
        genres = release_record.get('genre')
        year = release_record.get('year')
        return genres[0], year
    else:
        return 'unknown', '1066'

def get_release_album_title(release_record):
    album_name = release_record['title'].split(' - ', 1)[-1] if ' - ' in release_record['title'] else release_record['title']
    return(album_name)


def fix_TIT2(audiofile, file_title):
    try:
        this_data = audiofile['TIT2']
        this_fix_status = 2  # exists, valid or not remains to be seen
    except KeyError:
        this_data = mutagen.id3.TIT2(encoding=3, text='unknown')
        this_fix_status = 0

    this_title = this_data.text[0].lower()
    if this_title == 'unknown' or this_title == 'unknown title':
        audiofile['TIT2'] = mutagen.id3.TIT2(encoding=3, text=file_title)
        this_fix_status += 1

    return this_fix_status # 0:not found, not fixed, 1: not found, fixed, 2: found, not fixed, 3: found, but fixed

def fix_TPE1(audiofile, tentative_artist_name):
    this_fix_status = 0
    try:
        this_data = audiofile['TPE1']
        this_artist = this_data.text[0].lower()
        if this_artist[0:7] != 'unknown': # all good, exists and not 'unknown'
            this_fix_status = 2 # all good
        else: # exists, but is 'unknown'
            if (tentative_artist_name is not None):
                this_artist = tentative_artist_name.lower()
                if not (this_artist == 'unknown' or this_artist == 'unknown artist'):
                    audiofile['TPE1'] =  mutagen.id3.TPE1(encoding=3, text=tentative_artist_name)
                    this_fix_status = 3 # was there, was nonsense, was fixed
                else:
                    pass # it exists, is nonsense, but can't do anything. status is 0

    except KeyError: # no such tag
        # see if we have a tentative
        if tentative_artist_name is not None:
            this_artist = tentative_artist_name.lower()
            if not (this_artist == 'unknown' or this_artist == 'unknown artist'):
                audiofile['TPE1'] = mutagen.id3.TPE1(encoding=3, text=tentative_artist_name)
                this_fix_status = 1 # fixed
        else:
            pass # flag already 0

    return this_fix_status

def fix_TALB(audiofile, tentative_album_name, discogs_token):
    this_fix_status = 0
    lookup = 0
    release_record = None
    rate_exceeded = 0
    try:
        this_data = audiofile['TALB']
        this_album = this_data.text[0].lower()
        if not (this_album == 'unknown' or this_album == 'unknown album'):
            this_fix_status = 2 # all good
        else: # exists, but is 'unknown'
            if tentative_album_name is not None:
                this_album = tentative_album_name.lower()
                if not (this_album == 'unknown' or this_album == 'unknown album'):
                    print(f'fix_TALB tentative_album_name: "{tentative_album_name}" (len():{len(tentative_album_name)}')
                    audiofile['TALB'] =  mutagen.id3.TPE1(encoding=3, text=tentative_album_name)
                    this_fix_status = 3 # was there, was nonsense, was fixed
                else:
                    lookup = 1
            else:
                lookup = 1

    except KeyError:  # TALB does not exist
        if tentative_album_name is not None:
            this_album = tentative_album_name.lower()
            if not (this_album == 'unknown' or this_album == 'unknown album'):
                audiofile['TALB'] = mutagen.id3.TALB(encoding=3, text=tentative_album_name)
                this_fix_status = 1
            else:
                lookup = 1
        else:
            lookup = 1

    if lookup == 1: # look it up
        if discogs_token is not None:
            #print(f'fix_TALB: lookup')
            try:
                this_track = audiofile['TIT2'].text[0].lower()
                this_artist = audiofile['TPE1'].text[0].lower()
                print(f'fix_TALB: lookup {this_track} -> {this_artist}')
                release_record, error_code = get_release_record_by_artist_and_song_title(this_artist, this_track, discogs_token)
                if release_record is not None:  # found something
                    #genres, year = get_release_genre_and_year(release_record)
                    this_album = get_release_album_title(release_record)
                    if this_album is not None:
                        audiofile['TALB'] = mutagen.id3.TALB(encoding=3, text=this_album)
                        this_fix_status = 1
                else:
                    if error_code == 429:
                        rate_exceeded = 1
            except KeyError:
                print('fix_TALB: KeyError')
                pass

    return this_fix_status, release_record, rate_exceeded


# TDRC : release date
def fix_TDRC(audiofile, release_record, discogs_token):
    this_fix_status = 0
    rate_exceeded = 0
    #release_id = None
    try:
        this_data = audiofile['TDRC']
        this_fix_status = 2
    except KeyError:
        this_data = mutagen.id3.TDRC(encoding=3, text='1066')

    this_date_thing = this_data.text[0]
    this_date_string = str(this_date_thing)
    this_date = this_date_string[0:4]

    # if discogs_token is not None:
    #     print(f'fix_TDRC: date="{this_date}"')

    if this_date == '1066':
        # we can fix this by looking it up, if we have an album and artist name
        try:
            this_album  = audiofile['TALB'].text[0].lower()
            this_artist = audiofile['TPE1'].text[0].lower()
            if not(this_album[0:7] == 'unknown' and this_artist[0:7] == 'unknown'):
                this_fix_status = 3
                #print(f'fix_TDRC() this_album:{this_album} this_artist:{this_artist}')
                # ok, got some data, so try
                if release_record is None:
                    # try search by artist and album
                    #print(f'fix_TDRC() this_album:{this_album} this_artist:{this_artist}')
                    release_record, error_code = get_release_record_by_artist_and_album(this_artist, this_album, discogs_token)
                    if (release_record is None) and (error_code==0): # try again with a shortened album name, if we can
                        this_album_cleaned = remove_album_qualifiers(this_album)
                        if this_album_cleaned != this_album :
                            release_record, error_code = get_release_record_by_artist_and_album(this_artist, this_album_cleaned, discogs_token)
                    if release_record is None: # that didn't work, try search track
                        this_track = audiofile['TIT2'].text[0].lower()
                        #print(f'fix_TDRC() this_album:{this_album} this_artist:{this_artist} this_track:{this_track}')
                        #if (release_record is None):  # Haven't been provided with a release id, so look it up
                        release_record, error_code = get_release_record_by_artist_and_song_title(this_artist, this_track,
                                                                                         discogs_token)
                    # if release_record is not None:  # found something
                    #     genres, year = get_release_genre_and_year(release_record)
                    #     if year is not None:
                    #         audiofile['TDRC'] = mutagen.id3.TDRC(encoding=3, text=year)
                    #         this_fix_status = 1
                if release_record is not None:
                    genre, year = get_release_genre_and_year(release_record)
                    if year is not None:
                        audiofile['TDRC'] = mutagen.id3.TDRC(encoding=3, text=str(year))
                        this_fix_status = 1
                else:
                    pass # no fix, but see if we exceeded the query rate
                    if error_code == 429:
                        rate_exceeded = 1

        except KeyError:
            #print('fix_TDRC: KeyError')
            # if TALB is still undefined, it means lookup failed and it's pointless to try again with the same information
            pass # no fix

    return this_fix_status, release_record, rate_exceeded

# TCON: Genre
def fix_TCON(audiofile, release_record, discogs_token):
    this_fix_status = 0
    rate_exceeded = 0
    try:
        this_data = audiofile['TCON']
        this_fix_status = 2
    except:
        this_data = mutagen.id3.TCON(encoding=3, text='unknown')

    this_genre = this_data.text[0].lower()
    # if discogs_token is not None:
    #     print(f'fix_TCON: {this_genre}')
    if this_genre == 'unknown' or len(this_genre) < 2: # special broken caused by me
        # we can fix this by looking it up, if we have an album and artist name
        try:
            this_album  = audiofile['TALB'].text[0].lower()
            this_artist = audiofile['TPE1'].text[0].lower()
            if not(this_album[0:7] == 'unknown' and this_artist[0:7] == 'unknown'):
                if release_record is None:
                    # try search by artist and album
                    #print(f'fix_TCON() this_album:{this_album} this_artist:{this_artist}')
                    release_record, error_code = get_release_record_by_artist_and_album(this_artist, this_album, discogs_token)
                    if (release_record is None) and (error_code == 0): # try again with a shortened album name, if we can
                        this_album_cleaned = remove_album_qualifiers(this_album)
                        if this_album_cleaned != this_album:
                            release_record, error_code = get_release_record_by_artist_and_album(this_artist, this_album_cleaned, discogs_token)
                    if (release_record is None) and (error_code==0): # that didn't work, try search track
                        this_track = audiofile['TIT2'].text[0].lower()
                        #print(f'fix_TCON() this_album:{this_album} this_artist:{this_artist} this_track:{this_track}')
                        if release_record is None:  # Haven't been provided with a release id, so look it up
                            release_record, error_code = get_release_record_by_artist_and_song_title(this_artist, this_track,
                                                                                         discogs_token)

                if release_record is not None: # found something
                    this_genre, year = get_release_genre_and_year(release_record)
                    audiofile['TCON'] = mutagen.id3.TCON(encoding=3, text=this_genre)
                    this_fix_status = 1
                else:
                    #pass # no fix possible
                    if error_code == 429:
                        rate_exceeded = 1

        except KeyError:
            pass # no fix

    return this_fix_status, release_record, rate_exceeded


def clean_up_mp3_metadata(music_root_folder, music_file_path, which_tags, discogs_token, write):
    audiotype = music_file_path[-3:]
    # report flags: 0: not found, no fix; 1:not found, fixed 2:found, no fix 3:found, fixed anyway ('Unknown' and such)
    fix_status = []
    rate_exceeded = 0
    for tag in which_tags:
        fix_status.append(0)

    this_album = 'unknown'
    this_artist = 'unknown'

    if audiotype == 'mp3':
        audiofile = mutagen.File(music_file_path)
        keys = audiofile.keys()
        split_root = music_root_folder.split(os.path.sep)
        root_path_depth = len(split_root)
        split_path = music_file_path.split(os.path.sep)
        music_path_depth = len(split_path)
        filename = split_path[music_path_depth - 1]
        # filename_split = filename.split('.') # will fail for filenames with dots, it happens
        file_title = filename[:-4]

        release_id = None
        #print(f'path: {music_file_path}, n_words: {n_words}, file_title: {file_title}')
        #print(f'music_path_depth={music_path_depth}, root_path_depth={root_path_depth}, split_path={split_path}')
        if music_path_depth - root_path_depth >= 2 and ALLOW_NAME_GUESSING_FROM_PATH > 0: # Appears to be an iTunes-style library
            tentative_artist_name = split_path[music_path_depth - 3]
            tentative_album_name = split_path[music_path_depth - 2]
            #print(f'tentative_artist_name: {tentative_artist_name}, tentative_album_name: {tentative_album_name}')
        else:
            tentative_artist_name = None
            tentative_album_name = None

        for tag_idx, which_tag in enumerate(which_tags):
            # print(which_tag)
            # this_fix_status = 0

            if which_tag == 'TIT2': # track title
                this_fix_status = fix_TIT2(audiofile, file_title)

            if which_tag == 'TPE1': # artist name
                this_fix_status = fix_TPE1(audiofile, tentative_artist_name)

            if which_tag == 'TALB': # Album title
                this_fix_status, release_rec, rate_exceeded = fix_TALB(audiofile, tentative_album_name, discogs_token)

            if which_tag == 'TDRC': # Release date
                this_fix_status, release_rec, rate_exceeded = fix_TDRC(audiofile, release_rec, discogs_token)

            if which_tag == 'TCON': # Genre(s) - deco jukebox does not do lists of genres yet
                this_fix_status, release_rec, rate_exceeded = fix_TCON(audiofile, release_rec, discogs_token)

            fix_status[tag_idx] = this_fix_status

        if write:
            audiofile.save()

    return fix_status, rate_exceeded

# just report on existence or non-existence of tags, including stuff marked as 'unknown'
def survey_mp3_metadata(music_file_path, which_tags):
    audiotype = music_file_path[-3:]

    # report flags:
    # 0: not found, unfixable (red);
    # 1: not found, fixable; (yellow/orange)
    # 2: exists and valid, no fix needed; (green)
    # 3: exists, but 'unknown', fixable (blue)

    fix_status = []
    for tag in which_tags:
        fix_status.append(0)

    this_album = 'unknown'
    this_artist = 'unknown'

    if audiotype == 'mp3':
        audiofile = mutagen.File(music_file_path)
        keys = audiofile.keys()
        split_root = music_root_folder.split(os.path.sep)
        root_path_depth = len(split_root)
        split_path = music_file_path.split(os.path.sep)
        music_path_depth = len(split_path)
        filename = split_path[music_path_depth - 1]
        # filename_split = filename.split('.') # will fail for filenames with dots, it happens
        file_title = filename[:-4]

        release_id = None
        #print(f'path: {music_file_path}, n_words: {n_words}, file_title: {file_title}')

        if (music_path_depth - root_path_depth >= 2) and ALLOW_NAME_GUESSING_FROM_PATH > 0:
            tentative_artist_name = split_path[music_path_depth - 3]
            tentative_album_name = split_path[music_path_depth - 2]
        else:
            tentative_artist_name = None
            tentative_album_name = None

        for tag_idx, which_tag in enumerate(which_tags):
            # print(which_tag)
            # this_fix_status = 0

            if which_tag == 'TIT2': # track title
                this_fix_status = fix_TIT2(audiofile, file_title)

            if which_tag == 'TPE1': # artist name
                this_fix_status = fix_TPE1(audiofile, tentative_artist_name)

            if which_tag == 'TALB': # Album title
                this_fix_status, release_rec = fix_TALB(audiofile, tentative_album_name, discogs_token)

            if which_tag == 'TDRC': # Release date
                this_fix_status, release_rec = fix_TDRC(audiofile, None, None)

            if which_tag == 'TCON': # Genre(s) - deco jukebox does not do lists of genres yet
                this_fix_status, release_rec = fix_TCON(audiofile, None, None)

            fix_status[tag_idx] = this_fix_status

    return fix_status


def report_string(tags, flags):
    red_text = '\033[31m'
    green_text = '\033[32m'
    yellow_text = '\033[33m'
    blue_text = '\033[34m'
    def_text = '\033[0m'
    flag_color = [red_text, yellow_text, green_text, blue_text]

    report_string = ''
    for this_tag, this_flag in zip(tags, flags):
        colorcode = flag_color[this_flag]
        report_string += colorcode + this_tag + ' '

    report_string += def_text
    return report_string


def clean_up_folder(music_root_folder, discogs_token):
    which_tags = ['TIT2', 'TPE1', 'TALB', 'TDRC', 'TCON']
    music_file_paths = list_nested_mp3_files(music_root_folder)
    broken_files_count = 0
    for music_file_path in music_file_paths:
        fixes, rate_exceeded = clean_up_mp3_metadata(music_file_path,  which_tags, discogs_token,0)
        if not rate_exceeded:
            this_report = report_string(which_tags, fixes)
            if sum(fixes) != 8:
                print(this_report, music_file_path)
                broken_files_count += 1
        else:
            print("Rate exceeded, try again in a minute.")
            break

    print(f'Broken files count: {broken_files_count}')


def fix_broken_file(music_root_folder, mp3_file_path, discogs_token):
    which_tags = ['TIT2', 'TPE1', 'TALB', 'TDRC', 'TCON']
    fixes, rate_exceeded = clean_up_mp3_metadata(music_root_folder, mp3_file_path, which_tags, discogs_token, 1)
    this_report = report_string(which_tags, fixes)
    print(this_report, mp3_file_path)


# just look at what's broken
def survey_folder(music_root_folder):
    which_tags = ['TIT2', 'TPE1', 'TALB', 'TDRC', 'TCON']
    music_file_paths = list_nested_mp3_files(music_root_folder)
    #print(f'{len(music_file_paths)} mp3 files')
    broken_files_count = 0
    broken_files = []
    for music_file_path in music_file_paths:
        fixes, rate_exceeded = clean_up_mp3_metadata(music_root_folder, music_file_path,  which_tags, None,0)
        this_report = report_string(which_tags, fixes)

        all_good_flag = 1
        for this_fix in fixes:
            if this_fix != 2:
                all_good_flag = 0
        #print(fixes)
        if all_good_flag == 0:
            print(this_report, music_file_path)
            broken_files_count += 1
            broken_files.append(music_file_path)

    print(f'Broken files count: {broken_files_count}')

    return broken_files

def remove_album_qualifiers(album_name):
    indices = [album_name.find(c) for c in '([']
    indices = [i for i in indices if i != -1]
    first_index = min(indices) if indices else -1
    if first_index > 0:
        clean_name = album_name[:first_index]
    else:
        clean_name = album_name
    return clean_name



# Main routine - find broken things and fix them
if __name__ == "__main__":
    config_file_name = 'jukebox.cfg'
    fixed_files_log = 'fix_broken_mp3_metadata.log' # keep track of what we fixed or tried fixing, so we don't do it over and over
    # discogs_token = None
    discogs_token = os.getenv('DISCOGS_PERSONAL_TOKEN')
    MAX_FIXES = 25 # max number of fixes in one go - try to comply with rate limits for discogs

    config = read_ini(config_file_name) # retrieves jukebox.cfg info to find out where the library is
    if not 'music_root_folder' in config:
        print(f'Invalid config file \"{config_file_name}\", does not specify music_root_folder')
    else:
        # read log
        if os.path.exists(fixed_files_log):
            print("reading log...", end='', flush=True)
            with open(fixed_files_log) as f:
                fixed_files = [line.rstrip('\r\n') for line in f]
            print(f'{len(fixed_files)} previous fixes found')
        else:
            fixed_files = []
        logfile = open(fixed_files_log, 'a')

        music_root_folders = config['music_root_folder'].split(',')
        for music_root_folder in music_root_folders:
            if not os.path.isdir(music_root_folder):
                print(f'Music root folder \"{music_root_folder}\" does not exist')
            else:
                print(f'Looking at {music_root_folder}')
                print('Titl Arti Albm Date Genr \033[32mis_OK \033[33mFixable \033[31mBroken\033[m')
                broken_files = survey_folder(music_root_folder)

                if discogs_token is not None:
                    if len(broken_files) > 0:
                        yesno = input(f"Try to fix mp3 file metadata ({MAX_FIXES} max fixes per run) ? WARNING: This operation is not undoable. (y/n): ")
                        if len(yesno) > 0:
                            if yesno[0].lower() == 'y': # go for it
                                n_fixes = 0
                                n_already_fixed = 0
                                for broken_file in broken_files:
                                    # check log to see if fix was already tried
                                    found_fixed = 0
                                    for already_fixed in fixed_files:
                                        if broken_file == already_fixed:
                                            found_fixed += 1
                                            break
                                    if not found_fixed:
                                        fix_broken_file(music_root_folder, broken_file, discogs_token)
                                        n_fixes += 1
                                        logfile.write(broken_file + os.linesep)
                                        if n_fixes >= MAX_FIXES:
                                            break
                                    else:
                                        n_already_fixed += 1
                                print(f'End run, {n_fixes} fixed, {n_already_fixed} already fixed found in log.')
                                print('----------------------------------')

                else:
                    if len(broken_files) > 0:
                        print("Discogs Personal Token not found. You need to do the following:")
                        print("1) Go to https://www.discogs.com/settings/developers")
                        print("2) Login or create an account")
                        print("3) click on \"Generate new token\" (personal access token)")
                        print("4) create an environmental variable called DISCOGS_PERSONAL_TOKEN, put the token as its value")
                        print("5) Reboot so it kicks in")



