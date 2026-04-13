# Force some changes on some music files

from unidecode import unidecode
import os
import mutagen.id3

app_folder = "/home/patrick/Python/jukebox/"
definitions_folder = app_folder + "user_classifications/"

def get_metadata_keys(filename):
    audiofile = mutagen.File(filename)
    #print(audiofile)
    keys = audiofile.keys()

    return keys

# Eventually, recruit the likes of spotify to fill in the gaps
# Meanwhile, look at what's there
def get_tune_metadata(filename):
    #filename = '01 Live Is Life (Digitally Remastere.m4a'
    audiofile = mutagen.File(filename)
    #print(audiofile)
    error_flag = 0
    audiotype = filename[-3:]
    # print(f"audiotype:{audiotype}")
    if audiotype == 'm4p':
        print(f'skip m4p {filename}')
    if audiotype in ['m4a']: #, 'm4p']:
        try:
            title = audiofile["©nam"]
        except:
            title = "Unknown Title"
        try:
            artist = audiofile["©ART"]
        except:
            artist = "Unknown Artist"
        try:
            album = audiofile["©alb"]
        except:
            album = "Unknown Album"
        try:
            date = audiofile['©day'] #'©day': ['1977-05-25T12:00:00Z'],
            year = int(date[0][0:4])
        except:
            year = 1066
        try:
            genre = audiofile['©gen']
        except:
            error_flag = 1
        # blabla = f"title:{title[0]} by {artist[0]} on album {album[0]}"
        # print(blabla)
    elif audiotype == 'mp3':
        #print(audiofile)
        try:
            artist = audiofile['TPE1'].text
            title = audiofile['TIT2'].text
            album = audiofile['TALB'].text
            date = audiofile['TDRC'].text
            year = date[0:4] # I found one example only. date was just the year
            genre = audiofile['TCON'].text

            # blabla = f"title:{title[0]} by {artist[0]} on album {album[0]}"
            # print(blabla)
        except Exception as e:
            print(f'Error {e} parsing {filename}')
            error_flag = 1

    else: # quite possibly not an audio file, not sure how it got in the list
        error_flag = 1

    if (error_flag > 0): # put blanks where stuff didn't get retrieved
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

    return(title[0], artist[0], album[0], year, genre[0], error_flag)


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


def read_list(filename):
    this_list = []
    f = open(filename, 'r')
    for line in f:
        stripped = line.rstrip()
        stripped = unidecode(stripped.lower())
        if not stripped == "":
            this_list.append(stripped)
    return(this_list)


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


if __name__ == '__main__':
    #target_album_path_list = ["/home/patrick/Music/spotify_tracks/Joe Hisaishi/"]
    target_album_path_list = ["/home/patrick/Music/iTunes/iTunes Media/Music/Donna Summer/"]
    album_music = import_music(target_album_path_list)
    print(album_music)
    #album_music = ["/home/patrick/Music/iTunes/iTunes Media/Music/Foreigner/Agent Provocateur/"]
    for music_file in album_music:
        #print(music_file)
        audiotype = music_file[-3:]
        audiofile = mutagen.File(music_file)
        keys = audiofile.keys()
        print(keys)
        if audiotype == 'm4a':
            try:
                print('m4a nam', audiofile['©nam'])
                print('m4a alb', audiofile['©alb'])
                print('m4a gen', audiofile['\xa9gen'])
                print('m4a ART', audiofile["©ART"])
                print('m4a ©wrt', audiofile["©wrt"])
                print('m4a day', audiofile['©day'])

            except:
                pass

            # audiofile['©day'] = ['1963']
            # audiofile["©ART"] = ['Vivaldi, Antonio']
            # audiofile['©alb'] = ['Hungry Ghosts']
            # audiofile['\xa9gen'] = ['francophone']
            # audiofile.save()

        if audiotype == 'mp3':
            try:
                print('TPE1:', audiofile['TPE1']) # Artist
                print('TIT2:', audiofile['TIT2'])
                print('TALB:', audiofile['TALB'])
                print('TCON:',audiofile['TCON'])
                print('TDRC:',audiofile['TDRC'])

            except KeyError:
                trunc_path = music_file[:-4] # remove type from filename
                split_string = trunc_path.split('/')
                n_words = len(split_string)
                last_word = split_string[n_words-1]
                print(f'filename:{last_word}')

            # audiofile['TIT2'] = mutagen.id3.TIT2(encoding=3, text="I Feel Love")
            # audiofile['TDRC'] = mutagen.id3.TDRC(encoding=3, text="1979")
            # audiofile['TALB'] = mutagen.id3.TALB(encoding=3, text="Unknown")
            # audiofile['TPE1'] = mutagen.id3.TPE1(encoding=3, text="Donna Summer")
            # audiofile['TCON'] = mutagen.id3.TCON(encoding=3, text="disco")
            # audiofile.save()