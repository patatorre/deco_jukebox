# Looks at mp3 files in target folder to weed out invalid files
# Patrick Dumais
# patatorre "at" proton.me
# Feb 2026

import os


# scans folder for music files, returns array of paths
def list_files_in_nested_folders(root_folder):
    musics = []
    for dirpath, dirnames, filenames in os.walk(root_folder):
        #print(f"Folder: {dirpath}")
        for filename in filenames:
            #print(f"  File: {filename}")
            filepath = dirpath + "/" + filename
            audiotype = filename[-3:]
            if audiotype in ['m4a', 'm4p', 'mp3']:
                musics.append(filepath)
            else:
                pass
                #print("skipped")

    return(musics)


# get all files paths from start directory, includind nested
def import_music(start_folders):
    # first, find all the music files
    all_paths = []
    all_music = []
    for start_folder in start_folders:
        this_list = list_files_in_nested_folders(start_folder)
        #print(this_list)
        all_paths = all_paths + this_list

    return(all_paths)


##### MAIN ######################################################################

target_album_path_list = ["/home/patrick/Music/spotify_tracks/"]  # must be a list
album_music = import_music(target_album_path_list)

for music_file in album_music:
    #print(music_file)
    audiotype = music_file[-3:]

    if audiotype == 'mp3':
        try:
            file_size = os.path.getsize(music_file)
            if file_size < 20 * 1024:
                print(f'{music_file} is too small to be valid, probably')
        except:
            print(f'error checking file: {music_file}')
