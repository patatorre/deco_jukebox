
import pyglet
import time
import os

times_played = 0
app_path = os.getcwd()
print(f'app_path = {app_path}')
music_folder = 'musik/1980_1983/'
music_path = os.path.join(app_path, music_folder)
print(f'music_path = {music_path}')
file1 = os.path.join(music_path, '02 Echo Beach.m4a')
file2 = os.path.join(music_path, 'Sunday Bloody Sunday.mp3')
music_files = [file1, file2]

def get_media(music_file):
    print(f'Get_media({music_file})')
    directory_path = os.path.dirname(os.path.realpath(music_file))
    music_file_name = os.path.basename(music_file)
    pyglet.resource.path = [directory_path]
    pyglet.resource.reindex()
    music = pyglet.resource.media(music_file_name)
    print(music)
    return(music)


def play_media(play_item):
    music = get_media(play_item)
    player.queue(music)
    player.play()


def player_status(player):
    print('player_status() --')
    # Check if player is currently playing
    is_playing = player.playing  # Returns True/False

    # # Check if player is paused
    # is_paused = player.paused  # Returns True/False

    # Check if player has a source loaded
    has_source = player.source is not None

    # Get current playback time (in seconds)
    current_time = player.time

    # Get source duration (if loaded)
    if player.source:
        duration = player.source.duration

    print(f'is_playing:{is_playing}, has_source:{has_source}, current_time:{current_time}')


player = pyglet.media.Player()
audio_driver = pyglet.media.get_audio_driver()
print(f'Pyglet.options(audio) = {pyglet.options["audio"]}, driver = {audio_driver}')


@player.event
def on_eos(): # end of one song, when all of playlist was queued (TO BE DEPRECATED with spotify option,
    # because we need to check if the current song needs to be played by the spotify player)
    print('on_eos() ----')
    player_status(player)

    if player.playing:
        player.pause()
        #player.seek(0)
        time.sleep(0.1)
        print('on_eos() - made it to the try statement')
        try:
            player.next_source()
        except:
            print("on_eos() player.next_source() generated error")
            pass
        if player.source:
            player.seek(0)
    # BUG ALERT: sometimes we get on_eos() but not on_player_eos(). Gets stuck in a weird unreachable state.


@player.event
def on_player_eos(): # end of all songs
    global times_played

    times_played += 1
    print(f'on_player_eos(), times_played={times_played} ----')
    player_status(player)

    if player.playing:
        player.pause()

    #time.sleep(0.1)

    while player.source:
        player.next_source()
        time.sleep(0.05)

    if player.playing:
        player.pause()

    time.sleep(0.1) # attempt to resolve a race condition that results in "interrupted by signal 11:SIGSEGV" error
    music_file = music_files[times_played%2]
    print(f'on_player_eos() queuing up: {music_file}')
    play_media(music_file)

play_media(music_files[0])
pyglet.app.run()