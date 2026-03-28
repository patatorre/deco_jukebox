#########
# Deco Jukebox
#
# A touchscreen jukebox in Python
# by Patrick Dumais, patatorre "at" proton.me
# Version 0.85
# March 2026
#
# sudo buy me a coffee:
# https://buymeacoffee.com/patrickdumais
#
# For user customizations of genres etc., have a look at the readme.txt in user_classifications/

import pyglet
#from pyglet.gl import *
import mutagen
import os
import math
import random
import time
from unidecode import unidecode
from mutagen.id3 import ID3TimeStamp
# import spotify_controller
# import audacity_controller
import vlc
from pathlib import Path


def is_windows():
    probably_windows = 0
    if os.path.exists("C:\\"):
        probably_windows = 1
    return(probably_windows)


def is_raspberry_pi():
    try:
        with open('/proc/device-tree/compatible', 'rb') as f:
            compatible_data = f.read().split(b'\0')
            for entry in compatible_data:
                if entry:
                    vendor, model = entry.decode('ascii').split(',', 1)
                    if vendor == 'raspberrypi':
                        return True
            return False
    except FileNotFoundError:
        return False


on_windows = is_windows()
if not on_windows:
    raspberrypi = is_raspberry_pi()
    if raspberrypi:
        pyglet.options['shadow_window'] = False
else:
    raspberrypi = False

from pyglet.gl import * # on a pi, the shadow_window = False must precede even this statement

# display is customized only for the resolutions listed below
resolutions = ['1600x900', '1920x1080', '1280x720', '1280x800']
resolutions_x = []
resolutions_y = []
for rez in resolutions:
    splitrez = rez.split('x')
    rez_x = int(splitrez[0])
    rez_y = int(splitrez[1])
    resolutions_x.append(rez_x)
    resolutions_y.append(rez_y)

print(resolutions_x, resolutions_y)

# Laptop 1920 x 1080
# Touchscreen 1600 x 900
# Get the default display
display = pyglet.display.get_display()
screen = display.get_default_screen()
pyg_config = screen.get_best_config()
if raspberrypi:
    pyg_config.opengl_api = 'gles'
    pyg_config.major_version = 3
    pyg_config.minor_version = 1

screen_width = screen.width
screen_height = screen.height

# test rez
# screen_width = 1280
# screen_height = 800

# find resolution in list

rez_idx = -1
idx = 0
for rez_x, rez_y in zip(resolutions_x, resolutions_y):
    if screen_width == rez_x and screen_height == rez_y:
        rez_idx = idx
        break
    idx += 1

if rez_idx >= 0:
    print(f"Screen resolution: {screen.width}x{screen.height} is one of the default, good")
else:
    print(f"Screen resolution: {screen.width}x{screen.height} is not one of the default, forcing to {resolutions[0]}")
    rez_idx = 0

# # rasp pi screen size, to try
# screen_width = 1280
# screen_height = 720

window_width = screen_width

if on_windows:
    window_height = screen_height
else:
    window_height = screen_height - 30 # not fullscreen, make room for the top bar

# print(f"Screen resolution: {screen.width}x{screen.height}")
# if not (screen.width == 1600) and not (screen.height == 900):
#     print("*** NOTE Layout parameters are optimized for 1600 x 900 resolution")
print(f"Window Size: {window_width}x{window_height}")

# Tab buttons Singles / Tracks / Albums
#top_buttons_x = [500, 500][rez_idx]  # DEPRECATED - NOW CENTERED
top_buttons_y = window_height - 50 #1030 or 850

# selection buttons pane
selection_buttons_panel_left = 0
selection_buttons_panel_right = window_width-320 #[window_width-320, window_width-320, window_width-320][rez_idx]
selection_buttons_panel_top = 100
selection_buttons_panel_bot = 0
selection_button_spacing_horz = 116 #120
selection_button_spacing_vert = 50

# Main selection pane/ labels
songlist_edge_left = 320
songlist_edge_right = window_width - 360
songlist_edge_top = top_buttons_y #1030
songlist_edge_bot = 200
songlist_label_width = 300
songlist_label_height = 93

songs_page_control_buttons_x = window_width - 630 #1250
songs_page_control_buttons_y = 110

# artists panel
artists_panel_edge_left = 0
artists_panel_edge_right = 300
artists_panel_edge_top = window_height - 10 #1070
artists_panel_edge_bot = 150
artists_panel_label_width = 300
artists_panel_label_height = 50
artists_panel_artist_max_length = 25  # Characters

artists_panel_page_buttons_x = 0
artists_panel_page_buttons_y = 140

# Playlist panel
playlist_panel_edge_left = window_width - 313 #1580
playlist_panel_edge_right = window_width # 1920
playlist_panel_edge_top = window_height - 10 #1070
playlist_panel_edge_bot = 190
playlist_panel_label_width = 300
playlist_panel_label_height = 93
playing_highlight_x = window_width - 323
playing_highlight_y = playlist_panel_edge_top - 103 #952

play_control_buttons_x = window_width - 320 #1550
play_control_buttons_y = 80

# Neon tube path
tube_waypoint_1 = (artists_panel_edge_right - 2, selection_buttons_panel_top+51)
tube_waypoint_2 = (artists_panel_edge_right - 2, top_buttons_y + 27)
tube_waypoint_3 = (playlist_panel_edge_left-27, top_buttons_y + 27)
tube_waypoint_4 = (playlist_panel_edge_left-27, selection_buttons_panel_top+51)
tube_waypoint_5 = (artists_panel_edge_right - 2, selection_buttons_panel_top+51)
tube_waypoint_is_corner = [False, True, True, True, True]
tube_corner_rotations = [2, 0, 3, 2, 1] #[180, 0, 90, 180, 270]

# grille
grille_top = selection_buttons_panel_top #+10
grille_bot = selection_buttons_panel_bot
grille_left = selection_buttons_panel_left
grille_right = selection_buttons_panel_right

LABEL_MAX_LENGTH_ARTIST = 25 # chars
LABEL_MAX_LENGTH_TITLE = 30
PROGBAR_TEXT_SIZE = 12
HANDLE_EOS_DELAY = 0.1 # seconds
LABEL_WIDTH = 300  # Eventually should use these to be smart about font sizes and text wrapping
BUTTON_WIDTH = 120


# Read configuration file
# should contain:
# music_path=/path/to/music/dir
#
def read_ini():
    config = {}
    config_file_name = 'jukebox.cfg'
    try:
        with open(config_file_name) as f:
            for line in f:
                line = line.strip()
                if line and not (line.startswith('#') or line.startswith(';')):
                    key, value = line.split('=', 1)
                    config[key.strip()] = value.strip()
                    print(f'{key.strip()} = {value.strip()}')
    except:
        print(f'Error config file {config_file_name}')

    # fill in missing options
    if not 'spotify_enable' in config:
        config['spotify_enable'] = 'off'

    return(config)

config = read_ini()

if config['spotify_enable'] == 'on':
    spotify_id = os.getenv('SPOTIFY_CLIENT_ID')
    spotify_secret = os.getenv('SPOTIFY_CLIENT_SECRET')
    spotify_playlist_id = os.getenv('SPOTIFY_PLAYLIST_ID')
    if spotify_id == None:
        print('*** WARNING *** SPOTIFY_CLIENT_ID environmental variable not set. Spotify disabled.')
        config['spotify_enable'] == 'off'
    if spotify_secret == None:
        print('*** WARNING *** SPOTIFY_CLIENT_SECRET environmental variable not set. Spotify disabled.')
        config['spotify_enable'] == 'off'
    if spotify_playlist_id == None:
        print('*** NOTE *** SPOTIFY_PLAYLIST_ID environmental variable not set.')


buttons_font_size = 20
buttons_font_size_smaller = 14
labels_artist_font_size = 14
labels_title_font_size = 12
labels_title_font_size_smaller = 9
big_album_label_size = 12


try:
    if config['scraping_enable'] == 'on':
        audacity_client = audacity_controller.AudacityPipeController()
except:
    config['scraping_enable'] = 'off'

#spotify_start_page_number
if not 'spotify_start_page_number' in config:
    spotify_start_page_number = 0

try:
    music_root_folders = config['music_root_folder'].split(',')
    print(music_root_folders)
except:
    print('*** ERROR: jukebox.cfg item missing : "music_root_folder"')

#app_folder = "/home/patrick/Python/jukebox/"
app_folder = os.getcwd()
graphics_folder = os.path.join(app_folder, "graphics")
album_art_folder = os.path.join(graphics_folder, 'album_covers')
seek_album_art_filename = os.path.join(album_art_folder,'requests.txt')

decor_folder = os.path.join(graphics_folder, "decor")
frame_corner_file = os.path.join(decor_folder, "frame_corner_topleft.png")
frame_segment_file = os.path.join(decor_folder, "frame_horz_line.png")
tube_horz_unlit_file = os.path.join(decor_folder, "tube_horz_unlit.png")
tube_horz_lit_file = os.path.join(decor_folder, "tube_horz_red.png")
tube_vert_unlit_file = os.path.join(decor_folder, "tube_vert_unlit.png")
tube_vert_lit_file = os.path.join(decor_folder, "tube_vert_red.png")
tube_corner_lit_file = os.path.join(decor_folder, "tube_corner_red.png")
tube_corner_unlit_file1 = os.path.join(decor_folder, "tube_corner_unlit_rot_0.png")
tube_corner_unlit_file2 = os.path.join(decor_folder, "tube_corner_unlit_rot_90.png")
tube_corner_unlit_file3 = os.path.join(decor_folder, "tube_corner_unlit_rot_180.png")
tube_corner_unlit_file4 = os.path.join(decor_folder, "tube_corner_unlit_rot_270.png")
grid_pattern_file = os.path.join(decor_folder, "grille.png")
grid_pattern_file2 = os.path.join(decor_folder, "grille300x234.png")
grid_pattern_file3 = os.path.join(decor_folder, "grille320x234.png")
#bar_file = os.path.join(decor_folder, "bar10x128.png")

labels_folder = os.path.join(graphics_folder, "labels")
label_file1 = os.path.join(labels_folder, "vividred1-300x93.png")
label_dimmed_file1 =  os.path.join(labels_folder, "vividred1_dimmed_300x93.png")
label_file2 = os.path.join(labels_folder, "powederblue300x93.png")
label_dimmed_file2 =  os.path.join(labels_folder, "powederblue_dimmed_300x93.png")
label_file3 = os.path.join(labels_folder, "green_300x93.png")
label_dimmed_file3 =  os.path.join(labels_folder, "green_dimmed_300x93.png")
label_files = [label_file1, label_file2, label_file3]
label_dimmed_files = [label_dimmed_file1, label_dimmed_file2, label_dimmed_file3]
label_highlight_file1 = os.path.join(labels_folder, "playing_frame1.png")
label_highlight_file2 = os.path.join(labels_folder, "playing_frame2.png")
label_highlight_file3 = os.path.join(labels_folder, "playing_frame3.png")

buttons_folder = os.path.join(graphics_folder, "buttons")
button_off_file = os.path.join(buttons_folder, "button_grey_120x48.png")
button_green_file = os.path.join(buttons_folder, "button_yellow_120x48.png")
button_blue_file = os.path.join(buttons_folder, "button_yellow_120x48.png")
play_button_file = os.path.join(buttons_folder, "play_symbol_button.png")
pause_button_file = os.path.join(buttons_folder, "button_pause.png")
skip_button_file = os.path.join(buttons_folder, "skip_symbol_button.png")
skip_button_juiced_file = os.path.join(buttons_folder, "skip_symbol_button_juiced.png")
shuffle_button_file = os.path.join(buttons_folder, "shuffle_button.png")
up_button_on_file = os.path.join(buttons_folder, "button_arrow_up_80x80.png")
down_button_on_file = os.path.join(buttons_folder, "button_arrow_down_80x80.png")
up_button_juiced_file = os.path.join(buttons_folder, "button_arrow_up_juiced_80x80.png")
down_button_juiced_file = os.path.join(buttons_folder, "button_arrow_down_juiced_80x80.png")
up_button_off_file = os.path.join(buttons_folder, "button_arrow_up_unlit_80x80.png")
down_button_off_file = os.path.join(buttons_folder, "button_arrow_down_unlit_80x80.png")
square_button_blue_on_file = os.path.join(buttons_folder, "square_button_blue_on.png")
square_button_blue_off_file = os.path.join(buttons_folder, "square_button_blue_off.png")
arrow_up_button_blue_on_file = os.path.join(buttons_folder, "arrow_up_button_blue_on.png")
arrow_up_button_blue_off_file = os.path.join(buttons_folder, "arrow_up_button_blue_off.png")
arrow_down_button_blue_on_file = os.path.join(buttons_folder, "arrow_down_button_blue_on.png")
arrow_down_button_blue_off_file = os.path.join(buttons_folder, "arrow_down_button_blue_off.png")
all_button_file = os.path.join(buttons_folder, "all_button_80x80.png")
#top_button_on_file = os.path.join(buttons_folder, "button_red.png")
#top_button_off_file = os.path.join(buttons_folder, "button_gray.png")
clear_button_file = os.path.join(buttons_folder, "clear_button_wide.png")
clear_button_unlit_file = os.path.join(buttons_folder, "clear_button_wide_unlit.png")
clear_button_juiced_file = os.path.join(buttons_folder, "clear_button_wide_juiced.png")
stop_button_file = os.path.join(buttons_folder, "stop_button_wide.png")
singles_button_on_file = os.path.join(buttons_folder, "singles_button_on.png")
singles_button_off_file = os.path.join(buttons_folder, "singles_button_off.png")
tracks_button_on_file = os.path.join(buttons_folder, "tracks_button_on.png")
tracks_button_off_file = os.path.join(buttons_folder, "tracks_button_off.png")
albums_button_on_file = os.path.join(buttons_folder, "albums_button_on.png")
albums_button_off_file = os.path.join(buttons_folder, "albums_button_off.png")
spotify_button_on_file = os.path.join(buttons_folder, "spotify_button_on.png")
spotify_button_off_file = os.path.join(buttons_folder, "spotify_button_off.png")
back_button_lit_file = os.path.join(buttons_folder, "back_button_160x80.png")
back_button_unlit_file = os.path.join(buttons_folder, "back_button_unlit_160x80.png")
default_cover_image_file = os.path.join(album_art_folder, "default_cover_100x100.png")



label_blanks = []
labels_dimmed = []
for label_file in label_files:
    label_blank = pyglet.image.load(label_file)
    label_blanks.append(label_blank)
for label_file in label_dimmed_files:
    label_dimmed = pyglet.image.load(label_file)
    labels_dimmed.append(label_dimmed)
label_highlight1 = pyglet.image.load(label_highlight_file1)
label_highlight2 = pyglet.image.load(label_highlight_file2)
label_highlight3 = pyglet.image.load(label_highlight_file3)
label_highlights = [label_highlight1, label_highlight2, label_highlight3]

frame_corner = pyglet.image.load(frame_corner_file)
frame_segment = pyglet.image.load(frame_segment_file)
tube_horz_lit_image = pyglet.image.load(tube_horz_lit_file)
tube_horz_unlit_image = pyglet.image.load(tube_horz_unlit_file)
tube_vert_lit_image = pyglet.image.load(tube_vert_lit_file)
tube_vert_unlit_image = pyglet.image.load(tube_vert_unlit_file)
tube_corner_lit_image = pyglet.image.load(tube_corner_lit_file)
tube_corner_unlit_image1 = pyglet.image.load(tube_corner_unlit_file1)
tube_corner_unlit_image2 = pyglet.image.load(tube_corner_unlit_file2)
tube_corner_unlit_image3 = pyglet.image.load(tube_corner_unlit_file3)
tube_corner_unlit_image4 = pyglet.image.load(tube_corner_unlit_file4)
tube_corner_unlit_images = [tube_corner_unlit_image1, tube_corner_unlit_image2,
                            tube_corner_unlit_image3, tube_corner_unlit_image4]
grid_image = pyglet.image.load(grid_pattern_file)
grid_image2 = pyglet.image.load(grid_pattern_file2)
grid_image3 = pyglet.image.load(grid_pattern_file3)
#bar_image = pyglet.image.load(bar_file)
# print(f'Grille image width = {grid_image.width} height = {grid_image.height}')
# print(f'Grille clip width = {(grille_right-grille_left)} height = {(grille_top-grille_bot)}')
#grid_clipped_image = grid_image.get_region(x=grille_left, y=grille_top, width = (grille_right-grille_left),
#                                           height=(grille_top-grille_bot))

button_off = pyglet.image.load(button_off_file)
button_on_epochs = pyglet.image.load(button_blue_file)
button_on_genre = pyglet.image.load(button_green_file)
play_button =  pyglet.image.load(play_button_file)
pause_button = pyglet.image.load(pause_button_file)
skip_button =  pyglet.image.load(skip_button_file)
skip_button_juiced =  pyglet.image.load(skip_button_juiced_file)
shuffle_button =  pyglet.image.load(shuffle_button_file)
up_button_on = pyglet.image.load(up_button_on_file)
down_button_on = pyglet.image.load(down_button_on_file)
up_button_juiced = pyglet.image.load(up_button_juiced_file)
down_button_juiced = pyglet.image.load(down_button_juiced_file)
up_button_off = pyglet.image.load(up_button_off_file)
down_button_off = pyglet.image.load(down_button_off_file)
small_up_button_on = pyglet.image.load(arrow_up_button_blue_on_file)
small_down_button_on = pyglet.image.load(arrow_down_button_blue_on_file)
small_up_button_off = pyglet.image.load(arrow_up_button_blue_off_file)
small_down_button_off = pyglet.image.load(arrow_down_button_blue_off_file)
all_button_80 = pyglet.image.load(all_button_file)
#top_button_off = pyglet.image.load(top_button_off_file)
#top_button_on = pyglet.image.load(top_button_on_file)
# default_cover_image = pyglet.image.load(default_cover_image_file)
# default_cover_texture = default_cover_image.get_texture()
artists_cell_selected = pyglet.image.load(square_button_blue_on_file)
artists_cell_unselected = pyglet.image.load(square_button_blue_off_file)
clear_button = pyglet.image.load(clear_button_file)
clear_button_unlit = pyglet.image.load(clear_button_unlit_file)
clear_button_juiced = pyglet.image.load(clear_button_juiced_file)
stop_button = pyglet.image.load(stop_button_file)

definitions_folder = os.path.join(app_folder, "user_classifications")


class MediaPlayer:
    def __init__(self, config):
        self.this_player = vlc.MediaPlayer()
        self.play_progress_bar = ProgressBar(playlist_panel_edge_left, playing_highlight_y-15, playlist_panel_label_width)
        self.eos_flag = False
        self.eos_time = None
        self.is_spotify_track = 0
        self.playlist = []
        self.playing = 0  # 1 if actually playing, 0 if paused or stopped.
        self.stop_time = time.time()
        self.pause_start = time.time()

        if config['spotify_enable'] == 'on':
            self.spotify_enable = True
            self.spotify_client = spotify_controller.SpotifyDBusController()
            token = spotify_controller.get_user_token()
            tracks = spotify_controller.spotify_get_playlist(token, spotify_playlist_id)
            self.playlist = tracks


    def play(self):
        self.this_player.play()
        self.playing = 1

    def stop(self):
        self.this_player.stop()
        self.playing = 0
        self.flush_queue()

    def pause(self):
        self.this_player.pause()
        self.playing = 0

    def play_pause(self):
        if self.is_spotify_track:
            if self.spotify_client.play_pause(): # returns True0 if pause, 1 if depause
                self.play_progress_bar.depause()
            else:
                self.play_progress_bar.pause()
        else:
            if self.is_playing():
                self.pause()
                self.playing = 0
                self.pause_start = time.time()
                self.play_progress_bar.pause()
            else:
                self.playing = 1
                self.play()
                paused_time = time.time() - self.pause_start
                self.stop_time += paused_time
                self.play_progress_bar.depause()

    def queue(self, song_path):
        #media = vlc.Media(song_path)
        file_path = Path(song_path)
        media_uri = file_path.as_uri()
        self.this_player.set_media(vlc.Media(media_uri))

    def flush_queue(self):
        self.this_player.set_media(None)
        pass

    def is_playing(self):
        return(self.this_player.is_playing())

    def time(self):
        return(self.this_player.get_time())

    def source(self):
        ze_media = player.get_media()
        return(ze_media)

    def status(self):
            print('player_status() --')
            # Check if player is currently playing
            is_playing = self.is_playing()  # Returns True/False
            # Check if player has a source loaded
            has_source = player.source() is not None
            # Get current playback time (in seconds)
            current_time = self.time()
            print(f'is_playing:{is_playing}, has_source:{has_source}, current_time:{current_time}')

    def play_media(self, play_item):

        self.play_progress_bar.start_timer(play_item)

        if play_item['filepath'][0:7] == 'spotify':  # pass this on to the spotify app
            print(f'Spotify tune {play_item["filepath"]}')
            self.spotify_client.play(play_item['filepath'])
            self.spotify_client.set_stop_time(play_item['duration_s'])  # we need to check, it won't stop by itself
            self.is_spotify_track = 1
            if config['scraping_enable'] == 'on':
                audacity_client.stop()  # if song got skipped, audacity is still recording
                audacity_client.clearTrack()
                audacity_client.record()
        else:
            #music = get_media(play_item)
            self.queue(play_item['filepath'])
            self.set_stop_time(play_item['duration_s'])
            player.play()
            self.is_spotify_track = 0

    def is_track_done(self):
        if player.is_spotify_track > 0:
            return(self.spotify_client.is_track_done())
        else: # local
            if self.playing: # don't check is paused
                now = time.time()
                if now > self.stop_time:
                    return True
                else:
                    return False
            else:
                return False

    def set_stop_time(self, duration_s):
        now = time.time()
        self.stop_time = now + duration_s


class JuicedButton:
    def __init__(self, x, y, image_name_static, image_name_juiced):
        self.visible = 1
        self.juiced = 0
        self.juice_start_time = time.time()
        self.juice_duration = 0.2 # seconds
        image_static = pyglet.image.load(image_name_static)
        image_juiced = pyglet.image.load(image_name_juiced)
        self.width = image_static.width
        self.height = image_static.height
        self.sprite_static = pyglet.sprite.Sprite(image_static, x=x, y=y)
        self.sprite_juiced = pyglet.sprite.Sprite(image_juiced, x=x, y=y)
        self.button_x = x + self.width // 2
        self.button_y = y + self.height // 2


    def clicked(self, click_x, click_y):
        clicked = 0
        if (abs(self.button_x - click_x) < self.width / 2) and (abs(self.button_y - click_y) < self.height / 2):
            clicked = 1
            self.juice_start_time = time.time()
            self.juiced = 1
            print('JuicedButton clicked ----')

        return clicked

    def draw(self):
        time_now = time.time()
        if self.juiced and abs(self.juice_start_time - time_now) < self.juice_duration:
            self.sprite_juiced.draw()
        else:
            self.sprite_static.draw()
            self.juiced = 0 # reset the juice, though it may be already off


# Selector button panel: epochs and genres -----------------
class ButtonPanel:
    buttons_panel_left = selection_buttons_panel_left
    buttons_panel_right = selection_buttons_panel_right
    buttons_panel_top = selection_buttons_panel_top
    buttons_panel_bot = selection_buttons_panel_bot
    button_spacing_horz = selection_button_spacing_horz
    button_spacing_vert = selection_button_spacing_vert

    def __init__(self, epochs_lit_image, genres_lit_image, unlit_image, config_genres_list, buttons_font_stack):
        print(f'ButtonPanel __init__() config_genres_list = {config_genres_list}')
        self.epochs_list = ['60s', '70s', '80s', '90s', '2000s', '2010s', '2020s']
        if config_genres_list == []: # all genres except 'All' and 'Other'
            self.genres_list = ['Classical', 'Soundtrack', 'Folk', 'Rock', 'R&B', 'Altechnic', 'Franco', 'Christmas']
        else:
            self.genres_list = config_genres_list
        self.epoch_names = ['All'] + self.epochs_list + ['Other']
        self.genres_list = ['All'] + self.genres_list + ['Other']
        print(f'ButtonPanel __init__() self.genres_list = {self.genres_list}')
        self.all_years = []
        self.epoch_buttons = []
        self.genre_buttons = []

        self.buttons_batch = pyglet.graphics.Batch()
        self.epochs_lit_image = epochs_lit_image
        self.genres_lit_image = genres_lit_image
        self.unlit_image = unlit_image
        self.genre_button_sprites = []
        self.epoch_button_sprites = []

        # Background image
        self.background_sprite = pyglet.sprite.Sprite(img=grid_image, x=grille_left, y=grille_bot)
        # self.bar_batch = pyglet.graphics.Batch()
        # self.bar_sprites = []
        #
        # xpos = grille_left
        # bar_width = bar_image.width
        # while xpos < grille_right:
        #     sprite = pyglet.sprite.Sprite(img=bar_image, x=xpos, y=grille_top, batch=self.bar_batch)
        #     self.bar_sprites.append(sprite)
        #     xpos += bar_width

        # make a list of all possible years for the 'Other' option comparison
        for epoch in self.epochs_list:
            # print(epoch)
            epoch = epoch[:-1]  # strip the "s" out of epoch name
            if len(epoch) == 2:
                year = 1900 + int(epoch)
                years = range(year, year + 10)
            else:
                year = int(epoch)
                if year > 1999:
                    years = range(year, year + 10)
            self.all_years = self.all_years + list(years)

        # calculate button positions and set data structures

        xl = self.buttons_panel_left
        yl = self.buttons_panel_top - self.button_spacing_vert

        for epoch in self.epoch_names:
            button_label = format_button_label(epoch, 0, xl, yl, self.button_spacing_horz-20, buttons_font_stack)
            button = {'name':epoch, 'flag':0, 'pos':(xl, yl), 'label':button_label}
            self.epoch_buttons.append(button)

            sprite = pyglet.sprite.Sprite(self.unlit_image, x=xl, y=yl, batch=self.buttons_batch)
            self.epoch_button_sprites.append(sprite)

            xl = xl + self.button_spacing_horz
            if xl + self.button_spacing_horz > self.buttons_panel_right:
                break # just skip buttons that don't fit in a single line
                # xl = self.buttons_panel_left
                # yl = yl - self.button_spacing_vert

        # now do the genre buttons
        xl = self.buttons_panel_left
        yl = yl - self.button_spacing_vert

        for genre in self.genres_list:
            button_label = format_button_label(genre, 0, xl, yl, self.button_spacing_horz-20, buttons_font_stack)
            button = {'name': genre, 'flag': 0, 'pos': (xl, yl), 'label': button_label}
            self.genre_buttons.append(button)

            sprite = pyglet.sprite.Sprite(self.unlit_image, x=xl, y=yl, batch=self.buttons_batch)
            self.genre_button_sprites.append(sprite)

            xl = xl + self.button_spacing_horz
            if xl + self.button_spacing_horz > self.buttons_panel_right:
                break # just skip buttons that don't fit in a single line
                # xl = self.buttons_panel_left
                # yl = yl - self.button_spacing_vert

        print(self.genre_buttons)

        # startup: activate All/All
        self.genre_buttons[0]['flag'] = 1
        self.epoch_buttons[0]['flag'] = 1

    def draw_buttons(self):

        self.background_sprite.draw()
        # self.bar_batch.draw()

        # update sprite images lit / not lit
        for epoch_button, epoch_sprite in zip (self.epoch_buttons, self.epoch_button_sprites):
            epoch_flag = epoch_button['flag']
            if epoch_flag > 0:
                epoch_sprite.image = self.epochs_lit_image
            else:
                epoch_sprite.image = self.unlit_image
            button_label = epoch_button['label']
            button_label.draw()

        for genre_button, genre_sprite in zip(self.genre_buttons, self.genre_button_sprites):
            genre_flag = genre_button['flag']
            (xl, yl) = genre_button['pos']
            if genre_flag > 0:
                genre_sprite.image = self.genres_lit_image
            else:
                genre_sprite.image = self.unlit_image
            button_label = genre_button['label']
            button_label.draw()

        self.buttons_batch.draw()  # Draw the button images

        # now draw the text
        for epoch_button in self.epoch_buttons:
            button_label = epoch_button['label']
            button_label.draw()

        for genre_button in self.genre_buttons:
            button_label = genre_button['label']
            button_label.draw()

    # find if and which button has been clicked
    # using proximity to button label center coords
    def process_click(self, click_x, click_y):
        hit_flag = 0
        button_idx = 0
        for button in self.epoch_buttons:
            button_label = button['label']
            button_name = button['name']
            button_x = button_label.x
            button_y = button_label.y
            if (abs(button_x - click_x) < self.button_spacing_horz/2) and (abs(button_y - click_y) < self.button_spacing_vert/2):
                hit_flag = 1
                print(f'clicked button {button_name}')
                which_button = button
                break
            button_idx = button_idx + 1

        # If anything but 'all' is turned on, turn off 'all'
        if (hit_flag > 0):
            button['flag'] = not(button['flag'])
            print(f'button x y = {button_x}, {button_y}')
            self.epoch_buttons[button_idx] = button
            if not (button_name == 'All'):
                self.epoch_buttons[0]['flag'] = 0
        else: # not epoch, look in genres now
            button_idx = 0
            for button in self.genre_buttons:
                button_label = button['label']
                button_name = button['name']
                button_x = button_label.x
                button_y = button_label.y
                if (abs(button_x - click_x) < self.button_spacing_horz / 2) and (
                        abs(button_y - click_y) < self.button_spacing_vert / 2):
                    hit_flag = 1
                    which_button = button
                    break
                button_idx = button_idx + 1

            if (hit_flag > 0):
                button['flag'] = not (button['flag'])
                print(f'button x y = {button_x}, {button_y}')
                self.genre_buttons[button_idx] = button
                if not (button_name == 'All'):
                    self.genre_buttons[0]['flag'] = 0

        return(hit_flag)

    def find_genres_selected(self):
        genres_selected = []

        all_genres = 0
        other_genres = 0

        for button in self.genre_buttons:
            genre = button['name']
            if button['flag'] > 0:
                if genre == 'All':
                    all_genres = 1
                elif genre == 'Other':
                    other_genres = 1
                else:
                    genres_selected.append(genre)

        print(f'genres selected:{genres_selected}, all={all_genres}, other={other_genres}')
        return(genres_selected, all_genres, other_genres)

    def find_epochs_selected(self):
        epochs_selected = []
        all_epochs = 0
        other_epochs = 0

        for button in self.epoch_buttons:
            epoch = button['name']
            if button['flag'] > 0:
                if epoch == 'All':
                    all_epochs = 1
                elif epoch == 'Other':
                    other_epochs = 1
                else:
                    epochs_selected.append(epoch)

        print(f'epochs selected:{epochs_selected}, all={all_epochs}, other={other_epochs}')
        return(epochs_selected, all_epochs, other_epochs)


    # source is either all_music, all_singles, or all_albums
    def update_filtered(self, source):
        # make lists from the buttons currently active
        filtered_list = []
        epochs_selected, all_epochs, other_epochs = self.find_epochs_selected()
        genres_selected, all_genres, other_genres = self.find_genres_selected()
        lowercase_genres_list = [g.lower() for g in self.genres_list]
        #print(lowercase_genres_list)

        for this_record in source:
            genre_flag = 0  # genre match result
            epoch_flag = 0  # epoch match result
            song_year = this_record['year']
            song_genre = this_record['genre'].lower()
            # print(f'song genre: {song_genre}')
            # in or out?
            if all_genres:
                genre_flag = 1
            else:
                for genre in genres_selected:
                    genre = genre.lower()
                    # if genre == 'altechnic': # special label
                    #     if genre in ['electronic', 'alternative', 'techno']:
                    #         genre_flag = 1
                    if genre == song_genre:
                        genre_flag = 1
            if (song_genre not in lowercase_genres_list) and (other_genres == 1):
                genre_flag = 1

            if all_epochs:
                epoch_flag = 1
            else:
                for epoch in epochs_selected:
                    #print(epoch)
                    epoch = epoch[:-1] # strip the "s" out of epoch name
                    if len(epoch) == 2:
                        year = 1900 + int(epoch)
                        years = range(year, year+10)
                    else:
                        year = int(epoch) # should be a four digit year number
                        if year > 1999:
                            years = range(year, year+10)

                    if song_year in years:
                        epoch_flag = 1
                        # print(f'{song_year} found in {years}')

                if (song_year not in self.all_years) and (other_epochs == 1):
                    epoch_flag = 1

            if (epoch_flag and genre_flag): # ding!
                filtered_list.append(this_record)

        return(filtered_list)

    # web query a page worth of songs according to the button selection

    def get_spotify_page(self, songs_perpage, page_number):
        # make the list of genres for the query
        epochs_selected, all_epochs, other_epochs = self.find_epochs_selected()
        genres_selected, all_genres, other_genres = self.find_genres_selected()
        min_year = math.inf
        max_year = 0

        # format search fields
        if all_epochs > 0:
            year_range = "" # "all" selected, so don't specify
        else:
            for epoch_label in epochs_selected:
                epoch = int(epoch_label[:-1])  # strip the "s" out of epoch name
                if epoch < 100: # 70, 80, 90 ...
                    epoch = epoch + 1900
                if epoch < 2000:
                    epoch_toprange = epoch + 9
                else:
                    epoch_toprange = 2030
                if epoch < min_year:
                    min_year = epoch
                if epoch_toprange > max_year:
                    max_year = epoch_toprange
            year_range = f'year:{min_year}-{max_year}'

        genre_field = ""  # "all" selected, so don't specify
        if all_genres > 0:
            pass # already ok
        else:
            for genre in genres_selected:
                if genre == 'Altechnic': # eek, this is a custom genre, we'll need to tap into the genre user mappings later
                    genre_field += ' genre:electronic'
                elif genre == 'Franco':
                    genre_field += ' genre:french'
                else:
                    genre_field += f' genre:{genre}'

        spotify_tracks = spotify_controller.spotify_search_tracks(genre_field, year_range, songs_perpage, page_number)
        # transform results to our playlist format
        # print(f"{i:2d}. {track['name']}")
        # print(f"    Artist: {', '.join([artist['name'] for artist in track['artists']])}")
        # print(f"    Album: {track['album']['name']}")
        # print(f"    Release: {track['album']['release_date']}")
        # duration_s = track['duration_ms'] / 1000
        # print(f"    Duration: {duration_s} s")
        # print(f"    Popularity: {track['popularity']}/100")
        # print(f"    Preview: {track['preview_url'] or 'No preview available'}")
        # print(f"    Spotify URL: {track['external_urls']['spotify']}")
        # print(f"    Spotify URI: {track['uri']}")
        playlist_items = []
        dimmed_tracks = 0
        for track in spotify_tracks:
            album = track['album']['name']
            album_id = track['album']['id']
            title = track['name']
            artist = ', '.join([artist['name'] for artist in track['artists']])
            filepath = track['uri']
            duration_s = track['duration_ms'] / 1000
            year = track['album']['release_date'][0:4]
            if len(genres_selected) > 0:
                genre = genres_selected[0]
            else:
                genre = 'unknown'
            # See if we have this one already
            artist_sanitized = sanitize(artist)
            #album_sanitized = sanitize(album)
            artist_path = os.path.join(config['scraping_write_to_folder'], artist_sanitized)
            title_sanitized = sanitize(title) + ".mp3"
            # Search the whole artist directory for this particular song; it may exist in different albums
            dim_flag = 0
            music_files_list = list_files_in_nested_folders(artist_path)
            for music_file in music_files_list:
                filename = os.path.basename(music_file)
                if filename == title_sanitized:
                    dim_flag = 1 # found it
                    dimmed_tracks += 1
                    print(f'{title_sanitized} == {filename}')
                else:
                    print(f'{title_sanitized} != {filename}')
            #track_path = os.path.join(config['scraping_write_to_folder'], artist_sanitized, album_sanitized, title_sanitized)
            #print(f'testing path:{track_path}')
            # if os.path.exists(track_path): # have the label dimmed so we know we have it already
            #     dim_flag = 1

            this_playlist_item = {'album':album, 'artist':artist, 'title':title, 'filepath':filepath, 'duration_s':duration_s,
                                  'genre':genre, 'year':year, 'album_id':album_id, 'dim_flag':dim_flag, 'list_index':1}
            playlist_items.append(this_playlist_item)
        print(f'Should be {dimmed_tracks} dimmed tracks.')
        return(playlist_items)

#### End class ButtonPanel

# top buttons / tabs  -----------------
class TopButtons:
    first_visible_index = 1 # which item on the list goes live at startup
    def __init__(self):
        self.tab_buttons = []
        self.tab_list = ['Singles', 'Tracks', 'Albums'] #, 'Playlists', 'Spotify'] # all genres except 'All' and 'Other'
        tab_files_off = [singles_button_off_file, tracks_button_off_file, albums_button_off_file, spotify_button_off_file]
        tab_files_on = [singles_button_on_file, tracks_button_on_file, albums_button_on_file, spotify_button_on_file]
        self.tab_images_off = []
        self.tab_images_on = []
        for file_on, file_off in zip(tab_files_on, tab_files_off):
            image_on = pyglet.image.load(file_on)
            image_off = pyglet.image.load(file_off)
            self.tab_images_on.append(image_on)
            self.tab_images_off.append(image_off)
        if config['spotify_enable'] == 'on':
            self.tab_list.append('Spotify')
        self.button_spacing_horz = 225
        self.button_width = 200 # clickable area rather than spacing
        self.button_height = 40
        self.visible_panel = self.tab_list[self.first_visible_index]
        #live_button_index = self.tab_list.index(self.visible_panel)  # global variable tells which panel starts off active
        # calculate button positions and set data structures
        n_tabs = len(self.tab_list)
        xl = window_width//2 - self.button_width//2 - n_tabs//2 * self.button_spacing_horz # finally, math centered!
        yl = top_buttons_y
        for tab_item, image in zip(self.tab_list, self.tab_images_off):
            #button_label = format_button_label(tab_item, 0, xl, yl)
            #button = {'name':tab_item, 'flag':0, 'pos':(xl, yl), 'label':button_label}
            sprite = pyglet.sprite.Sprite(image, x=xl, y=yl)
            button = {'name': tab_item, 'flag': 0, 'pos': (xl, yl), 'sprite': sprite}
            self.tab_buttons.append(button)
            xl = xl + self.button_spacing_horz
        self.tab_buttons[self.first_visible_index]['flag'] = 1


    def draw_buttons(self):
        for this_button, image_on, image_off in zip(self.tab_buttons, self.tab_images_on, self.tab_images_off):
            this_flag = this_button['flag']
            this_sprite = this_button['sprite']
            if this_flag > 0:
                this_button_image = image_on
            else:
                this_button_image = image_off
            this_sprite.image = this_button_image
            this_sprite.draw()


    # find if and which button has been clicked
    # using proximity to button label center coords
    def process_click(self, click_x, click_y):
        hit_flag = 0
        button_idx = 0
        for this_button in self.tab_buttons:
            #button_label = this_button['label']
            button_name = this_button['name']
            button_x = this_button['pos'][0]
            button_y = this_button['pos'][1]
            if (click_x > button_x) and (click_x < (button_x + self.button_width)):
                flag_x = 1
            else:
                flag_x = 0
            if (click_y > button_y) and (click_y < (button_y + self.button_height)):
                flag_y = 1
            else:
                flag_y = 0
            if flag_x and flag_y:
                hit_flag = button_idx + 1
                print(f'clicked button {button_name}')
                which_button = this_button
                break
            button_idx = button_idx + 1

        # switch select: this one on, everything else off
        if (hit_flag > 0):
            # turn off all
            for button in self.tab_buttons:
                button['flag'] = 0
            # turn on clicked one
            which_button['flag'] = 1

        return(hit_flag)
#### End class ButtonPanel


# "Selection" panel of jukebox labels ----- used for Singles and Tracks
class LabelPanel:
    edge_left = songlist_edge_left
    edge_right = songlist_edge_right
    edge_top = songlist_edge_top
    edge_bot = songlist_edge_bot
    label_width = songlist_label_width
    label_height = songlist_label_height

    def __init__(self, labels_font_stack):
        self.page_number = 0
        self.juice_duration = 0.2 # seconds
        labels_horz_space = self.edge_right - self.edge_left
        labels_vert_space = self.edge_top - self.edge_bot
        # self.n_labels_horz = 3 #4
        # self.n_labels_vert = 6 #9
        self.n_labels_horz = labels_horz_space // self.label_width
        self.n_labels_vert = labels_vert_space // self.label_height
        self.songs_per_page = self.n_labels_horz * self.n_labels_vert
        self.spacing_vert = math.floor((self.edge_top - self.edge_bot) / self.n_labels_vert)
        if self.n_labels_horz > 1:
            self.spacing_horz = math.floor((self.edge_right - self.edge_left - self.label_width) / (self.n_labels_horz - 1))
        else:
            self.spacing_horz = 100 # this won't be used, but if it is, we'll see it
        self.filtered_list = []
        self.double_filtered_list = []
        self.visible_labels = []
        # make a fixed set of labels
        x_label = self.edge_left
        y_label = self.edge_top - self.spacing_vert
        vert_count = 0
        now = time.time()
        for idx in range(self.songs_per_page):

            # Create placeholder text labels
            title = f'Title {idx}'
            artist = f'Artist {idx}'
            album = f'Album {idx}'
            title_labels, artist_label, album_label = format_labels(title, artist, album, x_label, y_label, labels_font_stack)
            #juiced_label = JuicedButton(x_label, y_label, )

            label_entry = {'x_label':x_label, 'y_label':y_label, 'title_label':title_labels, 'artist_label':artist_label, 'album_label':album_label,
                           'filepath': '', 'visible':0, 'genre':'', 'album_id':'', 'year':0, 'dim_flag':0, 'duration_s':0, 'list_index':0,
                           'juiced': 0, 'juice_start_time': now}
            self.visible_labels.append(label_entry)

            vert_count = vert_count + 1
            y_label = y_label - self.spacing_vert

            if vert_count >= self.n_labels_vert:
                vert_count = 0
                x_label = x_label + self.spacing_horz
                y_label = self.edge_top - self.spacing_vert

    # updates the content of visible list;
    # assumes filtered_list unchanged
    # should be the result of a page change
    def update_visible_list(self):
        duration_s = 0
        n_filtered = len(self.double_filtered_list)
        print(f'Double filtered list length={n_filtered}')
        start_index = self.page_number * self.songs_per_page
        # vert_count = 0
        range_end = start_index+self.songs_per_page
        print(f'Page number {self.page_number}')
        if range_end >= n_filtered:
            range_end = n_filtered
        print(f'visible range {start_index} to {range_end}')
        for idx in range(self.songs_per_page):
            label_entry = self.visible_labels[idx]
            if idx+start_index < n_filtered:
                song_record = self.double_filtered_list[idx + start_index]
                song_record_to_label_entry(song_record, label_entry)
            else:
                label_entry['visible'] = 0

        try:
            #first_filtered_song = self.filtered_list[0]
            first_filtered_song = self.double_filtered_list[0]
            #year = first_filtered_song['year']
            #print(f'First filtered song year = {year}')
        except Exception as e:
            print(f'update_visible_list error {e}')

    # Takes the filtered list (by selected genres, epochs) and filters by artists selected
    # Then shuffles list so we get a random selection on the Labels panel
    # the order should persist until some of the selections are altered
    # i.e. page up and page down will give reproducible results
    def update_double_filtered_list(self, artists_panel):
        self.double_filtered_list = []
        # {'filepath':music_file, 'title':title, 'artist':artist, 'album':album, 'year':year}
        artists_list = artists_panel.artists_list
        if len(artists_list) > 0:
            #all_entry = artists_list[0]
            #all_selected = artists_panel.all_selected #all_entry['selected']
            all_selected = artists_panel.artists_selected[0]
            for song_record in self.filtered_list:
                #this_title = song_record['title']
                #this_album = song_record['album']
                this_artist = song_record['artist']
                #filepath = song_record['filepath']
                #year = song_record['year']
                artist_list_idx = 0
                artist_selected = 0
                #print(f'first artist in artist_list is {artists_list[0]}')
                for artist_name, selected in zip(artists_list[1:], artists_panel.artists_selected[1:]):
                    #artist_name = artist_entry['artist']
                    #selected = artist_entry['selected']
                    if ((artist_name == this_artist) and (selected > 0)) or (all_selected > 0):
                        artist_selected = 1
                if artist_selected > 0:
                    self.double_filtered_list.append(song_record)
        random.shuffle(self.double_filtered_list)
        return(0)


    def draw_labels(self):
        for label_entry in self.visible_labels:
            x_label = label_entry['x_label']
            y_label = label_entry['y_label']
            title_labels = label_entry['title_label']
            artist_label = label_entry['artist_label']
            album_label = label_entry['album_label']
            dim_flag = label_entry['dim_flag']
            label_index = label_entry['list_index'] % len(label_blanks)

            if label_entry['visible'] > 0 :
                if dim_flag > 0:
                    #label_dimmed.blit(x_label, y_label)
                    labels_dimmed[label_index].blit(x_label, y_label)
                else:
                    #label_blank.blit(x_label, y_label)
                    if label_entry['juiced'] > 0:
                        now = time.time()
                        if abs(label_entry['juice_start_time'] - now) < self.juice_duration:
                            labels_dimmed[label_index].blit(x_label, y_label)
                        else:
                            label_entry['juiced'] = 0
                            label_blanks[label_index].blit(x_label, y_label)
                    else:
                        label_blanks[label_index].blit(x_label, y_label)

                for title_label in title_labels:
                    title_label.draw()
                artist_label.draw()
                album_label.draw()


    # handle the page change
    # returns 0 if neither up nor down was clicked (buttons 0 and 1)
    def page_change(self, down):
        if down > 1:
            return(0)
        else:
            if down > 0:
                last_page_number = math.ceil(len(self.double_filtered_list) / self.songs_per_page) - 1
                if (self.page_number < last_page_number):
                    self.page_number = self.page_number + 1
            else: # up
                if self.page_number > 0:
                    self.page_number = self.page_number - 1
            self.update_visible_list()
            return(1)


    # find if and which button has been clicked
    # using proximity to button label center coords
    def process_click(self, click_x, click_y):
        hit_flag = 0
        entry_idx = 0
        x_mid = 0
        y_mid = 0
        duration_s = 0

        for label_entry in self.visible_labels:
            artist_label = label_entry['artist_label']
            x_mid = artist_label.x
            y_mid = artist_label.y
            if (abs(x_mid - click_x) < self.label_width/2) and (abs(y_mid - click_y) < self.label_height/2):
                clicked_label = label_entry
                if clicked_label['visible']:
                    hit_flag = 1
                break
            entry_idx = entry_idx + 1

        if (hit_flag > 0):
            print(f'label x_mid y_mid = {x_mid}, {y_mid}')
            playlist_entry = label_to_playlist_item(clicked_label)
            print(f'adding to playlist: {playlist_entry["filepath"]}')
            # animate
            clicked_label['juiced'] = 1
            clicked_label['juice_start_time'] = time.time()
            # # Add song to playlist
            ze_playlist.add_to_playlist(playlist_entry)

        return(hit_flag)

    # add all tracks from visible list to playlist
    def add_all(self):
        for this_label in self.visible_labels:
            if this_label['visible'] > 0:
                playlist_entry = label_to_playlist_item(this_label)
                print(f'adding to playlist: {playlist_entry["filepath"]}')
                # # animate, somehow
                # # Add song to playlist
                player.playlist.append(playlist_entry)
                # Remove from visible list, otherwise it's still clickable **** DEPRECATED
                # clicked_label['visible'] = 0

#### End class LabelPanel


# Album panel has two modes: Album list (show album covers) and open album (zoom in album and contents)
class AlbumPanel:
    edge_left = songlist_edge_left
    edge_right = songlist_edge_right
    edge_top = songlist_edge_top
    edge_bot = songlist_edge_bot
    label_width = songlist_label_width
    label_height = songlist_label_height

    def __init__(self, labels_font_stack):
        self.album_cover_size = 120
        self.big_album_cover_size = 240
        self.big_album_image_x = self.edge_left
        self.big_album_image_y = self.edge_top - self.big_album_cover_size - 10
        self.album_title_size = 20
        self.page_number = 0
        self.album_open = 0 # 1 if we're looking inside an album
        self.open_album_entry = {}
        self.n_covers_horz = math.floor((self.edge_right-self.edge_left) / self.album_cover_size)
        self.n_covers_vert = math.floor((self.edge_top-self.edge_bot) / (self.album_cover_size + self.album_title_size))
        self.albums_per_page = self.n_covers_horz * self.n_covers_vert
        self.album_spacing_vert = math.floor((self.edge_top - self.edge_bot - self.album_title_size) / (self.n_covers_vert))
        self.album_spacing_horz = math.floor((self.edge_right - self.edge_left - self.album_cover_size) / (self.n_covers_horz-1))
        self.visible_albums = []
        self.filtered_list = []
        self.double_filtered_list = []
        self.big_album_label= pyglet.text.Label('Unknown Album',
                                           font_name=labels_font_stack,
                                           font_size=12,
                                           color=(255, 255, 255, 255),
                                           x=self.edge_left, y=self.big_album_image_y - 24,
                                           anchor_x='left', anchor_y='bottom')
        self.big_artist_label= pyglet.text.Label('Unknown Artist',
                                           font_name=labels_font_stack,
                                           font_size=12,
                                           color=(255, 255, 255, 255),
                                           x=self.edge_left, y=self.big_album_image_y - 48,
                                           anchor_x='left', anchor_y='bottom')
        self.big_year_label= pyglet.text.Label('1942',
                                           font_name=labels_font_stack,
                                           font_size=12,
                                           color=(255, 255, 255, 255),
                                           x=self.edge_left, y=self.big_album_image_y - 72,
                                           anchor_x='left', anchor_y='bottom')
        self.big_genre_label= pyglet.text.Label('Unknown genre',
                                           font_name=labels_font_stack,
                                           font_size=12,
                                           color=(255, 255, 255, 255),
                                           x=self.edge_left, y=self.big_album_image_y - 96,
                                           anchor_x='left', anchor_y='bottom')

        x_album_label = self.edge_left
        y_album_label = self.edge_top - self.album_spacing_vert
        this_album = 'Unknown Album'
        this_artist = 'Unknown Artist'
        this_cover_image, scale_x, scale_y = get_album_art(this_album, self.album_cover_size)
        vert_count = 0
        this_dir_path = ''
        for idx in range(self.albums_per_page):
            this_label = pyglet.text.Label(this_album,
                                           font_name=labels_font_stack,
                                           font_size=12,
                                           color=(255, 255, 255, 255),
                                           x=x_album_label, y=y_album_label,
                                           anchor_x='left', anchor_y='bottom')
            this_sprite = pyglet.sprite.Sprite(this_cover_image, x=x_album_label, y=y_album_label+self.album_title_size)
            this_sprite.scale_x = scale_x
            this_sprite.scale_y = scale_y
            this_album_entry = {'album': this_album, 'artist': this_artist, 'x_label': x_album_label, 'y_label': y_album_label,
                                'label': this_label, 'sprite': this_sprite, 'dir_path': this_dir_path, 'visible':0,
                                'year':'1066', 'genre':''}
            self.visible_albums.append(this_album_entry)
            vert_count = vert_count + 1
            y_album_label = y_album_label - self.album_spacing_vert
            if vert_count >= self.n_covers_vert:
                vert_count = 0
                x_album_label = x_album_label + self.album_spacing_horz
                y_album_label = self.edge_top - self.album_spacing_vert

        # make a fixed set of labels for in-album mode
        labels_horz_space = self.edge_right - self.edge_left - big_album_label_size - 40
        labels_vert_space = self.edge_top - self.edge_bot
        self.n_labels_horz = labels_horz_space // self.label_width
        self.n_labels_vert = labels_vert_space // self.label_height
        self.songs_per_page = self.n_labels_horz * self.n_labels_vert
        self.spacing_vert = math.floor((self.edge_top - self.edge_bot) / self.n_labels_vert)
        label_panel_width = self.edge_right - self.edge_left - self.label_width - self.big_album_cover_size - 40
        if self.n_labels_horz > 1:
            self.spacing_horz = math.floor((label_panel_width) / (self.n_labels_horz - 1))
        else:
            self.spacing_horz = 100 # this won't be used, but if it is, we'll see it
        self.visible_labels = []
        self.songlist = [] # for the open album
        
        x_label = self.edge_left + self.big_album_cover_size + 50
        y_label = self.edge_top - self.spacing_vert
        vert_count = 0
        for idx in range(self.songs_per_page): # 'album open' option has labels

            # Create placeholder text labels
            title = f'Title {idx}'
            artist = f'Artist {idx}'
            album = f'Album {idx}'
            title_labels, artist_label, album_label = format_labels(title, artist, album, x_label, y_label, labels_font_stack)

            label_entry = {'x_label':x_label, 'y_label':y_label, 'title_label':title_labels, 'artist_label':artist_label, 'album_label':album_label,
                           'filepath': '', 'visible':0, 'genre':'', 'album_id':'', 'year':0, 'dim_flag':0, 'duration_s':0, 'list_index':0}
            self.visible_labels.append(label_entry)

            vert_count = vert_count + 1
            y_label = y_label - self.spacing_vert
            if vert_count >= self.n_labels_vert:
                vert_count = 0
                x_label = x_label + self.spacing_horz
                y_label = self.edge_top - self.spacing_vert

        back_button_x = self.edge_left + 5
        back_button_y = self.edge_bot + 0
        self.back_button = JuicedButton(back_button_x, back_button_y, back_button_lit_file, back_button_unlit_file)
        big_album_cover_texture, scale_x, scale_y = get_album_art(default_cover_image_file, self.big_album_cover_size)
        this_sprite = pyglet.sprite.Sprite(big_album_cover_texture, x=self.big_album_image_x, y=self.big_album_image_y)
        this_sprite.scale_x = scale_x
        this_sprite.scale_y = scale_y
        self.big_album_cover_sprite = this_sprite

        # this_cover_image.blit(self.edge_left, self.edge_top - self.big_album_cover_size)

    # updates the content of visible list;
    # assumes filtered_list unchanged
    # should be the result of a page change
    def update_visible_list(self):
        if not self.album_open: # album covers page
            n_filtered = len(self.double_filtered_list)
            print(f'Album panel double filtered album list length={n_filtered}')
            start_index = self.page_number * self.albums_per_page
            range_end = start_index+self.albums_per_page
            print(f'Page number {self.page_number}')
            if range_end > n_filtered - 1:
                range_end = n_filtered - 1
            print(f'visible range {start_index} to {range_end}')
            for label_idx in range(self.albums_per_page):
                album_idx = label_idx + start_index
                if album_idx <=  range_end:
                    album_record = self.double_filtered_list[album_idx]
                    this_album = album_record['album']
                    if len(this_album) > 15:
                        this_album_short = this_album[0:15]
                    else:
                        this_album_short = this_album
                    this_artist = album_record['artist']
                    this_year = album_record['year']
                    this_genre = album_record['genre']
                    this_dir_path = album_record['dir_path']
                    this_cover_image, scale_x, scale_y  = get_album_art(this_album, self.album_cover_size)

                    self.visible_albums[label_idx]['visible'] = 1
                    self.visible_albums[label_idx]['dir_path'] = this_dir_path
                    self.visible_albums[label_idx]['label'].text = this_album_short
                    self.visible_albums[label_idx]['sprite'].image = this_cover_image
                    self.visible_albums[label_idx]['sprite'].scale_x = scale_x
                    self.visible_albums[label_idx]['sprite'].scale_y = scale_y
                    self.visible_albums[label_idx]['album'] = this_album
                    self.visible_albums[label_idx]['artist'] = this_artist # do we need this? YES
                    self.visible_albums[label_idx]['year'] = str(this_year)
                    self.visible_albums[label_idx]['genre'] = this_genre
                else:
                    #print(f'AlbumPanel.update_visible_list: label_idx = {label_idx}')
                    self.visible_albums[label_idx]['visible'] = 0
        else: # album open page: big cover, song labels
            n_album_songs = len(self.songlist)
            print(f'Songs in open album = {n_album_songs}')
            start_index = self.page_number * self.songs_per_page
            #this_cover_image, scale_x, scale_y = get_album_art(this_album, self.album_cover_size)
            #self.big_album_cover_sprite.image = this_cover_image
            for idx in range(self.songs_per_page):
                label_entry = self.visible_labels[idx]
                if idx + start_index < n_album_songs:
                    song_record = self.songlist[idx + start_index]
                    song_record_to_label_entry(song_record, label_entry)
                else:
                    label_entry['visible'] = 0

    def update_double_filtered_list(self, artists_panel):
        self.double_filtered_list = []
        # {'filepath':music_file, 'title':title, 'artist':artist, 'album':album, 'year':year}
        artists_list = artists_panel.artists_list
        if len(artists_list) > 0:
            all_selected = artists_panel.artists_selected[0] #all_selected #all_entry['selected']
            for album_record in self.filtered_list:
                this_artist = album_record['artist']
                artist_selected = 0
                for artist_name, selected in zip(artists_list, artists_panel.artists_selected):
                    if ((artist_name == this_artist) and (selected > 0)) or (all_selected > 0):
                        artist_selected = 1
                if artist_selected > 0:
                    self.double_filtered_list.append(album_record)
        return(0)


    # returns 0 if neither up nor down was clicked (buttons 0 and 1)
    def page_change(self, down):
        if down > 1: # means neither the up nor down button were clicked, but some other ('down' the actual button index)
            return(0)
        else:
            if self.album_open:
                last_page_number = math.ceil(len(self.songlist) / self.songs_per_page) - 1  # misnamed, it's a page index, starts from zero
            else:
                last_page_number = math.ceil(len(self.double_filtered_list) / self.albums_per_page) - 1
            if down > 0:
                if (self.page_number < last_page_number):
                    self.page_number = self.page_number + 1
            else: # up
                if self.page_number > 0:
                    self.page_number = self.page_number - 1
            self.update_visible_list()
            return(1)


    def draw(self):
        if self.album_open:
            self.draw_labels()
        else:
            self.draw_covers()


    # Draw song labels and big album cover and info
    def draw_labels(self):
        album_record = self.open_album_entry
        this_album = album_record['album']
        this_artist = album_record['artist']
        this_year = album_record['year']
        this_genre = album_record['genre']
        this_dir_path = album_record['dir_path']
        # this_cover_image = get_album_art(this_album, self.big_album_cover_size)
        # this_cover_image.blit(self.edge_left, self.edge_top - self.big_album_cover_size)
        #self.big_album_cover_image.blit(self.big_album_image_x, self.big_album_image_y)
        this_cover_texture, scale_x, scale_y = get_album_art(this_album, self.big_album_cover_size)
        self.big_album_cover_sprite.image = this_cover_texture
        self.big_album_cover_sprite.scale_x = scale_x
        self.big_album_cover_sprite.scale_y = scale_y
        self.big_album_cover_sprite.draw()
        self.big_album_label.text = this_album
        self.big_album_label.draw()
        self.big_artist_label.text = this_artist
        self.big_artist_label.draw()
        self.big_year_label.text = this_year
        self.big_year_label.draw()
        self.big_genre_label.text = this_genre
        self.big_genre_label.draw()

        self.back_button.draw()

        for label_entry in self.visible_labels:
            if label_entry['visible'] > 0 :
                x_label = label_entry['x_label']
                y_label = label_entry['y_label']
                title_labels = label_entry['title_label']
                artist_label = label_entry['artist_label']
                album_label = label_entry['album_label']
                dim_flag = label_entry['dim_flag']
                label_index = label_entry['list_index'] % len(label_blanks)

                if dim_flag > 0:
                    labels_dimmed[label_index].blit(x_label, y_label)
                else:
                    label_blanks[label_index].blit(x_label, y_label)
                for title_label in title_labels:
                    title_label.draw()
                artist_label.draw()
                album_label.draw()

    # Draw a collection of album covers
    def draw_covers(self):
        for album_entry in self.visible_albums:
            if album_entry['visible'] == 1:
                # x_label = album_entry['x_label']
                # y_label = album_entry['y_label']
                sprite = album_entry['sprite']
                #cover = album_entry['cover']
                #cover.blit(x_label, y_label+self.album_title_size+2)
                sprite.draw()
                album_label = album_entry['label']
                album_label.draw()


    # find if and which album or label has been clicked
    # using proximity to button label center coords
    def process_click(self, click_x, click_y):
        hit_flag = 0
        entry_idx = 0
        x_mid = 0
        y_mid = 0
        if self.album_open: # Clickable songs
            for label_entry in self.visible_labels:
                if label_entry['visible'] > 0:
                    artist_label = label_entry['artist_label']
                    x_mid = artist_label.x
                    y_mid = artist_label.y
                    if (abs(x_mid - click_x) < self.label_width / 2) and (abs(y_mid - click_y) < self.label_height / 2):
                        clicked_label = label_entry
                        # if clicked_label['visible']:
                        hit_flag = 1
                        break
                entry_idx = entry_idx + 1

            if (hit_flag > 0):
                print(f'label x_mid y_mid = {x_mid}, {y_mid}')
                playlist_entry = label_to_playlist_item(clicked_label)
                print(f'adding to playlist: {playlist_entry["filepath"]}')
                # # animate, somehow
                # # Add song to playlist
                player.playlist.append(playlist_entry)

            else: # no labels clicked, let's see the button
                if self.back_button.clicked(click_x, click_y): # "back" button clicked, revert view
                    self.album_open = 0
                    self.page_number = 0

        else:
            # Find which album was clicked
            for album_entry in self.visible_albums:
                if album_entry['visible'] > 0:
                    x = album_entry['x_label']
                    y = album_entry['y_label']
                    if (click_x > x) and (click_x < (x + self.album_cover_size)) and (click_y > y)  and (click_y < (y + self.album_cover_size + self.album_title_size)):
                        hit_flag = 1
                        clicked_album = album_entry
                        break
                entry_idx = entry_idx + 1

            if (hit_flag > 0):
                print(f'hit xy = {x}, {y}, album clicked is {clicked_album["album"]}')
                song_labels = find_album_songs(clicked_album['dir_path'], clicked_album['artist']) # artist will be ignored

                # album-open mode
                self.album_open = 1
                self.page_number = 0
                self.open_album_entry = clicked_album
                self.big_album_cover_image = get_album_art(clicked_album['album'], self.big_album_cover_size)
                # add album songs to local list
                self.songlist = []
                for song_label in song_labels:
                    self.songlist.append(song_label)

                self.update_visible_list()

        return(hit_flag)

    # add all tracks from visible list to playlist
    def add_all(self):
        print(f'AlbumPanel.add_all() --- album_open={self.album_open}, len(visible_labels) = {len(self.visible_labels)}')
        if self.album_open: # Add all not active for a page full of albums
            for this_song in self.songlist:
                player.playlist.append(this_song)

#### End class AlbumPanel


# "Selection" panel of jukebox labels ----------------------------------
class ArtistsPanel:
    edge_left = artists_panel_edge_left
    edge_right = artists_panel_edge_right
    edge_top = artists_panel_edge_top
    edge_bot = artists_panel_edge_bot
    label_width = artists_panel_label_width
    label_height = artists_panel_label_height
    artist_max_length = artists_panel_artist_max_length # string visible length

    def __init__(self, labels_font_stack):
        self.page_number = 0
        self.n_labels_horz = 1
        artists_vertical_space = self.edge_top - self.edge_bot
        self.n_labels_vert =  artists_vertical_space // self.label_height
        #self.songs_per_page = self.n_labels_horz * self.n_labels_vert
        self.spacing_vert = math.floor((self.edge_top - self.edge_bot - self.label_height) / (self.n_labels_vert))
        self.spacing_horz = math.floor((self.edge_right - self.edge_left - self.label_width) / (self.n_labels_horz))
        #self.visible_list = []
        self.artists_list = []
        self.artists_selected = [1] # first item in this list is dummy artist 'All'
        self.grid_batch = pyglet.graphics.Batch()
        self.grid_sprites = []

        ypos = grid_image.height
        grille_height = grid_image2.height
        while ypos < window_height:
            sprite = pyglet.sprite.Sprite(img=grid_image2, x=0, y=ypos, batch=self.grid_batch)
            self.grid_sprites.append(sprite)
            sprite = pyglet.sprite.Sprite(img=grid_image3, x=playlist_panel_edge_left, y=ypos, batch=self.grid_batch)
            self.grid_sprites.append(sprite)
            ypos += grille_height

        # create empty labels for later use
        x_label = self.edge_left
        y_label = self.edge_top - self.spacing_vert
        all_label = pyglet.text.Label('All',
                              font_name=labels_font_stack,
                              font_size=14,
                              color=(255, 255, 255, 255),
                              x=x_label+50, y=y_label+20,
                              anchor_x='left', anchor_y='center')
        all_label =  {'artist': 'All', 'artist_label':all_label, 'x_label':x_label, 'y_label':y_label, 'artist_idx':0, 'visible':1}
        self.visible_list = [all_label]
        y_label = y_label - self.spacing_vert

        for idx in range(1, self.n_labels_vert):
            artist_label = pyglet.text.Label('',
                              font_name=labels_font_stack,
                              font_size=14,
                              color=(255, 255, 255, 255),
                              x=x_label+50, y=y_label+20,
                              anchor_x='left', anchor_y='center')
            this_label_entry = {'artist': '', 'artist_label':artist_label, 'x_label':x_label, 'y_label':y_label, 'artist_idx':idx, 'visible':0}
            self.visible_list.append(this_label_entry)
            y_label = y_label - self.spacing_vert
        print(f'init len(visible_list) = {len(self.visible_list)}')

    # updates the content of visible list;
    # assumes filtered_list unchanged
    # should be the result of a page change
    def update_visible_list(self):

        n_filtered = len(self.artists_list)
        start_index = self.page_number * (self.n_labels_vert-1)

        range_end = start_index + self.n_labels_vert - 2
        if range_end >= n_filtered:
            range_end = n_filtered
        print(f'Artists Page number {self.page_number}')
        if range_end >= n_filtered:
            range_end = n_filtered
        print(f'visible range {start_index} to {range_end}')

        for idx in range(1, self.n_labels_vert): # idx 0 is 'All', always
            artist_idx = idx + (self.n_labels_vert-1)*self.page_number
            if (artist_idx < len(self.artists_list)):
                this_artist = self.artists_list[artist_idx]
                self.visible_list[idx]['visible'] = 1
                if len(this_artist) > self.artist_max_length:
                    this_artist_short = this_artist[0:25]
                else:
                    this_artist_short = this_artist
            else: # walked off the list
                this_artist_short = ''
                artist_idx = 0
                self.visible_list[idx]['visible'] = 0

            self.visible_list[idx]['artist_label'].text = this_artist_short
            self.visible_list[idx]['artist_idx'] = artist_idx

        #print(f'Artist visible list has {len(self.visible_list)}')

    def update_artists_list(self, filtered_list):
        self.artists_list = ['All'] # may need more fields
        self.artists_selected = [1]
        #print(f'update_artists_list() filtered_list = {filtered_list}')
        for list_item in filtered_list:
            #print(f'list item:{list_item}')
            this_artist = list_item['artist']
            if this_artist not in self.artists_list:
                self.artists_list.append(this_artist)
                self.artists_selected.append(0)

        self.artists_list[1:] = sorted(self.artists_list[1:])

        print(f'Artist list has {len(self.artists_list)} items')


    def draw_labels(self):
        self.grid_batch.draw()
        n_artists = len(self.artists_list)
        for label_entry in self.visible_list:
            x_label = label_entry['x_label']
            y_label = label_entry['y_label']
            #selected = label_entry['selected']
            artist_idx = label_entry['artist_idx']
            if artist_idx <= n_artists: # legit idx; 0 is 'all'
                selected = self.artists_selected[artist_idx]
            else:
                selected = 0
            if label_entry['visible']:
                if selected:
                    artists_cell_selected.blit(x_label, y_label)
                else:
                    artists_cell_unselected.blit(x_label, y_label)
                artist_label = label_entry['artist_label']
            artist_label.draw()


    def page_change(self, button_index):
        n_artists = len(self.artists_list)
        change_flag = 0
        if button_index == 0: # page up
            if self.page_number > 0:
                self.page_number = self.page_number - 1
                change_flag = 1
        else: # should be page down
            n_pages = math.ceil(n_artists / (self.n_labels_vert - 1))
            if self.page_number < n_pages - 1:
                self.page_number = self.page_number + 1
                change_flag = 1
        return(change_flag)

    # find if and which button has been clicked
    # using proximity to button label center coords
    # returns true if an artist was selected/deselected (?)
    def process_click(self, click_x, click_y):
        hit_flag = 0
        entry_idx = 0
        x_mid = 0
        y_mid = 0

        for label_entry in self.visible_list:
            artist_label = label_entry['artist_label']
            x_mid = artist_label.x
            y_mid = artist_label.y
            if (abs(x_mid - click_x) < self.label_width/2) and (abs(y_mid - click_y) < self.label_height/2):
                hit_flag = 1
                clicked_label = label_entry
                break
            entry_idx = entry_idx + 1

        if (hit_flag > 0):
            clicked_artist = clicked_label['artist']
            clicked_artist_idx = clicked_label['artist_idx']

            if clicked_artist == 'All':
                #self.all_selected = 1
                self.artists_selected[0] = 1
                # unselect all artists
                for idx in range(1, len(self.artists_list)):
                    self.artists_selected[idx] = 0

            else:
                #listindex = self.artists_list.index(clicked_artist) # index of artist in non-visible list

                self.artists_selected[0] = 0 # unselectm'All'
                # select what was clicked, or unselect it if it already was
                #already_selected = self.visible_list[entry_idx]['selected']
                already_selected = self.artists_selected[clicked_artist_idx]
                if already_selected:
                    #self.visible_list[entry_idx]['selected'] = 0
                    self.artists_selected[clicked_artist_idx] = 0
                else:
                    #self.visible_list[entry_idx]['selected'] = 1
                    self.artists_selected[clicked_artist_idx] = 1
                print(f'clicked {clicked_artist}')
                print(f'list record {self.visible_list[entry_idx]}')

        return(hit_flag)
#### End class LabelPanel


# Playlist -----------------------------------------------------------
class PlayList:
    edge_left = playlist_panel_edge_left
    edge_right = playlist_panel_edge_right
    edge_top = playlist_panel_edge_top # affects the position of the topmost label
    edge_bot = playlist_panel_edge_bot
    label_width = playlist_panel_label_width
    label_height = playlist_panel_label_height

    headspace = 30  # extra space for the first item (space for progress bar)
    juice_duration = 0.2 # seconds

    def __init__(self, playlist_at_startup, labels_font_stack):
        n_songs_at_startup = len(playlist_at_startup)
        #self.label_start_index = 0 # Either 0 or 1 depending on play status
        self.topsong_index = 0 # playlist index of the song currently playing or 0 if not
        self.page_index = 0 # which page of the list should be showing
        self.n_labels_horz = 1

        playlist_verticalspace = playlist_panel_edge_top - playlist_panel_edge_bot - self.headspace
        self.n_labels_vert = playlist_verticalspace // playlist_panel_label_height
        print(f'playlist n_labels_vert={self.n_labels_vert}')
        self.songs_per_page = self.n_labels_horz * self.n_labels_vert
        self.spacing_vert = math.floor((self.edge_top - self.edge_bot - self.headspace) / self.n_labels_vert)
        self.spacing_horz = math.floor((self.edge_right - self.edge_left) / self.n_labels_horz)
        self.visible_labels = []
        now = time.time()

        # make a fixed set of labels
        x_label = self.edge_left
        y_label = self.edge_top - playlist_panel_label_height #- 8
        vert_count = 0
        for idx in range(self.n_labels_horz * self.n_labels_vert):

            if idx > n_songs_at_startup-1:
                # Create placeholder text labels
                title = f'Title {idx}'
                artist = f'Artist {idx}'
                album = f'Album {idx}'
                # this_genre = 'undefined'
                # filepath = ''
                # duration_s = 0
                # this_year = 1876
                # album_id = ''
                visible_flag = 0

            else:
                # print(playlist_at_startup[idx])
                title = playlist_at_startup[idx]['title']
                artist = playlist_at_startup[idx]['artist']
                album = playlist_at_startup[idx]['album']
                # this_genre = playlist_at_startup[idx]['genre']
                # filepath = playlist_at_startup[idx]['filepath']
                # duration_s = playlist_at_startup[idx]['duration_s']
                # this_year = playlist_at_startup[idx]['year']
                # album_id = playlist_at_startup[idx]['album_id']
                visible_flag = 1

            title_labels, artist_label, album_label = format_labels(title, artist, album, x_label, y_label, labels_font_stack)

            label_entry = {'x_label':x_label, 'y_label':y_label, 'title_label':title_labels, 'artist_label':artist_label, 'album_label':album_label,
                           'playlist_index': idx, 'visible':visible_flag, 'list_index':0, 'juiced': 0, 'juice_start_time': now}

            self.visible_labels.append(label_entry)

            y_label = y_label - self.spacing_vert
            if vert_count == 0:
                y_label = y_label - self.headspace
            vert_count = vert_count + 1

            if vert_count >= self.n_labels_vert:
                vert_count = 0
                x_label = x_label + self.spacing_horz
                y_label = self.edge_top - self.spacing_vert

        #self.play_list = []


    # called at player end-of-song
    # Move playlist to next song
    def scroll_down_one(self, this_control_buttons):
        #print('Before EOS - Current song:', this_player.source)
        #this_player.play() # had a problem with playback stopping after one song
        print(f'Scroll_down_one() topsong index is {self.topsong_index}')
        last_one = 0
        self.topsong_index = self.topsong_index + 1
        if self.topsong_index >= len(player.playlist):
            print("Queue is empty")
            this_control_buttons.playing = 0
            this_control_buttons.buttons[0]['active'] = 0
            self.topsong_index = 0
            last_one = 1
        else:
            print("Queue not empty, next song should be queued up")
            self.visible_index_start = self.topsong_index + 1
            self.page_index = 0

        return(last_one)


    # updates the content of visible list;
    # assumes filtered_list unchanged
    # should be the result of a page change
    def update_visible_list(self, show_list_end, juice_last_entry):
        print(f'PlayList.update_visible_list() playing = {play_control_buttons.playing}, show_list_end = {show_list_end}, juice_last_entry = {juice_last_entry}')
        len_playlist = len(player.playlist)
        label_idx_end = self.songs_per_page - 1
        if play_control_buttons.playing: # playing song is at top always
            playlist_entry = player.playlist[self.topsong_index] # topsong is playing song
            label_entry = self.visible_labels[0]
            playlist_to_label_entry(playlist_entry, label_entry)
            last_page_index = math.ceil((len_playlist - self.topsong_index - 1) / (self.songs_per_page - 1)) - 1
            if show_list_end:
                self.page_index = last_page_index
            label_idx_start = 1
            song_start_index = self.topsong_index + 1 + self.page_index * (self.songs_per_page - 1)

        else:
            label_idx_start = 0
            last_page_index = math.ceil(len_playlist / self.songs_per_page) - 1
            if show_list_end:
                self.page_index = last_page_index
            song_start_index =  self.page_index * self.songs_per_page

        print(f'PlayList.update_visible_list() len_playlist={len_playlist}, topsong_index={self.topsong_index}, last_page_index={last_page_index}')
        print(f'visible range {label_idx_start} to {label_idx_end}')
        last_visible_label_idx = 0
        for idx in range(label_idx_start, label_idx_end+1):
            label_entry = self.visible_labels[idx]
            song_index = song_start_index + idx - label_idx_start
            last_visible_label = label_entry
            if song_index < len_playlist:
                playlist_entry = player.playlist[song_index]
                playlist_to_label_entry(playlist_entry, label_entry)
                label_entry['visible'] = 1
                last_visible_label_idx = idx
            else:
                label_entry['visible'] = 0

        if juice_last_entry:
            #print("Playlist.update_visible_list() juice_last_entry=1")
            # last_visible_label['juiced'] = 1
            # last_visible_label['juice_start_time'] = time.time()
            # print(last_visible_label)
            self.visible_labels[last_visible_label_idx]['juiced'] = 1
            self.visible_labels[last_visible_label_idx]['juice_start_time'] = time.time()

    def draw_labels(self):
        #playlist_visible_entries = len(self.visible_list)
        #print(f'Playlist visible entries = {playlist_visible_entries}')
        #playlist_entries = len(playlist)
        #print(f'Playlist entries = {playlist_entries}')
        for label_entry in self.visible_labels:
            x_label = label_entry['x_label']
            y_label = label_entry['y_label']
            title_labels = label_entry['title_label']
            artist_label = label_entry['artist_label']
            album_label = label_entry['album_label']
            list_index = label_entry['list_index'] % len(label_blanks)

            if label_entry['visible'] > 0 :
                #print('draw_labels:', label_entry)
                if label_entry['juiced'] > 0:
                    #print('Playlist.draw_labels() juiced')
                    now = time.time()
                    if abs(label_entry['juice_start_time'] - now) < self.juice_duration:
                        labels_dimmed[list_index].blit(x_label, y_label)
                    else:
                        label_entry['juiced'] = 0
                        label_blanks[list_index].blit(x_label, y_label)
                else:
                    label_blanks[list_index].blit(x_label, y_label)

                for title_label in title_labels:
                    title_label.draw()
                artist_label.draw()
                album_label.draw()


    def page_change(self, down):
        if play_control_buttons.playing:  # playing song is at top always, don't touch it
            # page change on portion under top (playing) song
            len_playlist = len(player.playlist) - self.topsong_index - 1 # access only below the playing song not above
            n_pages = math.ceil((len_playlist) / (self.songs_per_page - 1))
        else:
            len_playlist = len(player.playlist)
            n_pages = math.ceil((len_playlist) / self.songs_per_page)

        if down > 0:
            if self.page_index < n_pages - 1:
                self.page_index += 1
        else: # up
            self.page_index -= 1
            if self.page_index < 0:
                self.page_index = 0

        self.update_visible_list(0,0)

    # find if and which button has been clicked
    # using proximity to button label center coords
    def process_click(self, click_x, click_y):
        hit_flag = 0
        button_idx = 0
        x_mid = 0
        y_mid = 0

        for label_entry in self.visible_list:
            # title_label = label_entry['title_label']
            # x_mid = title_label.x
            # y_mid = title_label.y
            artist_label = label_entry['artist_label']
            x_mid = artist_label.x
            y_mid = artist_label.y
            #y_label = label_entry['y_label']
            if (abs(x_mid - click_x) < self.label_width/2) and (abs(y_mid - click_y) < self.label_height/2):
                hit_flag = 1
                clicked_label = label_entry
                break
            button_idx = button_idx + 1

        if (hit_flag > 0):
            # we're already in the playlist, not sure what a click will do yet
            print(f'label x_mid y_mid = {x_mid}, {y_mid}')
            filepath = label_entry['filepath']
            #print(f'added {filepath}')
            # Add song to playlist
            #playlist.append(clicked_label)

        return(hit_flag)


    def add_to_playlist(self, playlist_entry):
        player.playlist.append(playlist_entry)
        self.update_visible_list(1, 1)
#### End class PlayList


# Control buttons: Play/pause, Skip, shuffle --------------------------------
class ControlButtonPanel:
    # there are multiple possible sets of buttons. Only one set per instance?
    button_widths = [100, 80, 40]
    button_heights = [100, 80, 40]
    button_types = ['play', 'skip', 'shuffle', 'up', 'down', 'all', 'clear']
    double_widths = [0,       0,      0,         0,      0,      0,       1]
    button_images_on = [[play_button, skip_button, shuffle_button, up_button_on, down_button_on, all_button_80, clear_button],
                        [play_button, skip_button, shuffle_button, up_button_on, down_button_on, all_button_80, clear_button],
                        [play_button, skip_button, shuffle_button, small_up_button_off, small_down_button_off, all_button_80, clear_button]]
    button_images_juiced = [[play_button, skip_button_juiced, shuffle_button, up_button_juiced, down_button_juiced, all_button_80, clear_button_juiced],
                        [play_button, skip_button_juiced, shuffle_button, up_button_juiced, down_button_juiced, all_button_80, clear_button_juiced],
                        [play_button, skip_button_juiced, shuffle_button, small_up_button_on, small_down_button_on, all_button_80, clear_button_juiced]]
    button_images_off = [[pause_button, skip_button, shuffle_button, up_button_off, down_button_off, all_button_80, stop_button],
                         [pause_button, skip_button, shuffle_button, up_button_off, down_button_off, all_button_80, stop_button],
                        [pause_button, skip_button, shuffle_button, small_up_button_off, small_down_button_off, all_button_80, stop_button]]

    def __init__(self, x, y, button_list, button_set):
        self.buttons = []
        self.playing = 0  # this is 1 if playlist is being played. it is still 1 if play is paused.
        self.paused = 0 # and this is how we keep track of pausing. maybe should fold this into player class.
        self.is_spotify_track = 0 # current track is being played on spotify client
        self.button_width = self.button_widths[button_set]
        self.button_height = self.button_heights[button_set]
        self.juice_duration = 0.2 # seconds
        now = time.time()
        button_x = x
        for button in button_list:
            double_width = self.double_widths[self.button_types.index(button)]
            this_button_width = self.button_width * (1 + double_width)
            image_index = self.button_types.index(button)
            if image_index < 0:
                print(f'WARNING button {button} not recognized')
            button_image_on = self.button_images_on[button_set][image_index]
            button_image_juiced = self.button_images_juiced[button_set][image_index]
            button_image_off = self.button_images_off[button_set][image_index]
            this_sprite = pyglet.sprite.Sprite(button_image_on, x=button_x, y=y)
            button_entry = {'type':button, 'image_on':button_image_on, 'image_off':button_image_off,
                            'image_juiced':button_image_juiced, 'active':1, 'juiced':0, 'juice_start_time':now,
                            'x':button_x, 'y':y, 'sprite':this_sprite, 'width':this_button_width}
            self.buttons.append(button_entry)
            button_x = button_x + self.button_widths[button_set]


    def draw_buttons(self):
        for button in self.buttons:
            # button_x = button['x']
            # button_y = button['y']
            active = button['active']
            juiced = button['juiced']
            button_image = button['image_off']  # 'off' contains alternate button for play/pause and clear/stop
            if active > 0:
                button_image = button['image_on']
                if juiced:
                    now = time.time()
                    if abs(now-button['juice_start_time']) < self.juice_duration:
                        button_image = button['image_juiced'] # clear_button
                        #print('Juice on')
                    else:
                        button['juiced'] = 0


            button_sprite = button['sprite']
            button_sprite.image = button_image
            #button_image.blit(button_x, button_y)
            button_sprite.draw()


    # find if and which button has been clicked
    # using proximity to button label center coords
    def process_click(self, click_x, click_y):
        hit_flag = 0
        button_idx = 0
        hit_button_index_plus_one = 0

        for button in self.buttons:
            button_x = button['x']
            button_y = button['y']
            #print(f'bx:{button_x}, by:{button_y}')
            yes_x = 0
            yes_y = 0
            if (click_x - button_x) < button['width'] and (click_x >= button_x):
                yes_x = 1
            if ((click_y - button_y) < self.button_height) and (click_y >= button_y):
                yes_y = 1
            if yes_x and yes_y:
                hit_flag = 1
                clicked_button_idx = button_idx
                button['juiced'] = 1
                button['juice_start_time'] = time.time() # now
                self.buttons[clicked_button_idx] = button
                break
            button_idx = button_idx + 1

        if (hit_flag > 0):
            print(f'Hit control button index {button_idx}')
            hit_button_index_plus_one = button_idx + 1

        return(hit_button_index_plus_one)

#### End class ControlButtonPanel`

class ProgressBar:

    def __init__(self, x0, y0, total_width):
        text_width = 50
        text_v_adj = 5
        self.xpos = x0
        self.ypos = y0
        self.bar_x0 = x0 + text_width
        self.bar_width = total_width - 2 * text_width # pixels
        dummy_time_str = '0:00'
        self.paused = 0
        self.pause_start = 0
        self.paused_time = 0
        self.start_time = 0
        self.end_time = 0
        self.played_time = 0
        self.played_time_label = pyglet.text.Label(dummy_time_str,
                                           font_name=labels_font_stack,
                                           font_size=PROGBAR_TEXT_SIZE,
                                           color=(255, 255, 255, 255),
                                           x=x0, y=y0-text_v_adj,anchor_x='left', anchor_y='bottom')
        self.end_time_label = pyglet.text.Label(dummy_time_str,
                                           font_name=labels_font_stack,
                                           font_size=PROGBAR_TEXT_SIZE,
                                           color=(255, 255, 255, 255),
                                           x=x0 + self.bar_width + text_width, y=y0-text_v_adj,anchor_x='left', anchor_y='bottom')

        self.bar_frame_rect = pyglet.shapes.BorderedRectangle(self.bar_x0, y0, width=self.bar_width, height=PROGBAR_TEXT_SIZE,
                                                         color=(0,0,0,255), border_color=(255, 255, 255), border=1)

        self.bar_prog_rect = pyglet.shapes.Rectangle(self.bar_x0, y0, width=self.bar_width, height=PROGBAR_TEXT_SIZE,
                                                color=(255,255,255,255))

    def draw(self):
        self.played_time_label.draw()
        self.end_time_label.draw()
        self.bar_frame_rect.draw()
        self.bar_prog_rect.draw()

    def format_mm_ss(self, seconds):
        minutes, seconds = divmod(int(seconds), 60)
        return f"{minutes:02d}:{seconds:02d}"

    def start_timer(self, playlist_item):
        now = time.time()
        self.start_time = now
        self.duration_s = playlist_item['duration_s']
        self.end_time = now + self.duration_s
        self.played_time = 0
        played_str = '00:00'
        print(f'ProgressBar start_timer self.duration_s = {self.duration_s}')
        end_str = self.format_mm_ss(self.duration_s)
        self.end_time_label.text = end_str
        self.played_time_label.text = played_str
        self.bar_prog_rect.width = 0
        self.paused_time = 0
        self.paused = 0


    def update_timer(self):
        if not self.paused:
            now = time.time()
            played_time = now - self.start_time - self.paused_time
            played_str = self.format_mm_ss(played_time)
            self.played_time_label.text = played_str
            frac_played = played_time / self.duration_s
            self.bar_prog_rect.width = math.floor(self.bar_width * frac_played)

    def pause(self):
        now = time.time()
        self.pause_start = now
        self.paused = 1

    def depause(self):
        now = time.time()
        self.paused_time += now - self.pause_start
        self.paused = 0
# end class ProgressBar


class NeonTube:

    is_lit = False
    cell_size = 101
    center_pixel = 51
    lit_image_horz = tube_horz_lit_image
    lit_image_vert = tube_vert_lit_image
    lit_corner = tube_corner_lit_image
    unlit_image_horz = tube_horz_unlit_image
    unlit_image_vert = tube_vert_unlit_image
    unlit_corners = tube_corner_unlit_images

    # unlit_corner = test_pattern_image
    # unlit_image_horz = test_pattern_image
    # unlit_image_vert = test_pattern_image

    # lit_image_horz.anchor_x = center_pixel
    # lit_image_horz.anchor_y = center_pixel
    # unlit_image_horz.anchor_x = center_pixel
    # unlit_image_horz.anchor_y = center_pixel
    # lit_image_vert.anchor_x = center_pixel
    # lit_image_vert.anchor_y = center_pixel
    # unlit_image_vert.anchor_x = center_pixel
    # unlit_image_vert.anchor_y = center_pixel
    # lit_corner.anchor_x = center_pixel
    # lit_corner.anchor_y = center_pixel
    # for unlit_corner in unlit_corners:
    #     unlit_corner.anchor_x = center_pixel
    #     unlit_corner.anchor_y = center_pixel

    def __init__(self, waypoints, waypoint_is_corner, corner_rotations):
        print(f'NeonTube.init() with waypoints: {waypoints}')
        self.sprites_batch = pyglet.graphics.Batch()
        self.corners_unlit_batch = pyglet.graphics.Batch()
        self.corners_lit_batch = pyglet.graphics.Batch()
        self.sprites = []
        self.sprites_are_horz = []
        self.corners = []
        point_start = waypoints[0]
        start_tube = False # Hack - should be true if the first segment is at an edge
        n_pts = len(waypoints)
        for pt_idx in range(1, n_pts):
            point_end = waypoints[pt_idx]
            #print(f'pt_idx = {pt_idx}')
            x0, y0 = point_start
            x1, y1 = point_end
            x0 -= self.center_pixel
            x1 -= self.center_pixel
            y0 -= self.center_pixel
            y1 -= self.center_pixel
            delta_x = x1 - x0
            delta_y = y1 - y0
            start_segment = True

            if abs(delta_x) > abs(delta_y): # let's say it's horizontal
                is_horizontal = True # need this for last point
                if delta_x > 0:
                    inc_x = self.cell_size
                else:
                    inc_x = -1 * self.cell_size
                this_x = x0

                while abs(this_x - x1) > self.cell_size:
                    if not start_tube:
                        if start_segment:
                            this_x += inc_x
                            start_segment = False
                    else:
                        start_tube = False
                        start_segment = False

                    sprite = pyglet.sprite.Sprite(self.unlit_image_horz, x=this_x, y=y0,
                                                  batch=self.sprites_batch)
                    self.sprites.append(sprite)
                    self.sprites_are_horz.append(True)
                    this_x += inc_x

                # last cell special case
                scale_x = abs(this_x - x1) / self.cell_size
                scaled_width = int(this_x - x1)
                tweak_x = 0
                # if scaled_width%2 > 0 and scaled_width > 0: # tweak if odd and going negative way
                #     tweak_x = -1
                print(f'Last seg horz: scaled_width={scaled_width}, this_x = {this_x}, tweak_x = {tweak_x}')
                this_x += tweak_x
                if scaled_width > 0:
                    this_x += self.cell_size - scaled_width
                sprite = pyglet.sprite.Sprite(self.unlit_image_horz, x=this_x, y=y0, batch=self.sprites_batch)
                sprite.scale_x = scale_x

                self.sprites.append(sprite)
                self.sprites_are_horz.append(True)

            else: # let's say it's vertical
                is_horizontal = False
                if delta_y > 0:
                    inc_y = self.cell_size
                else:
                    inc_y = -1 * self.cell_size
                this_y = y0
                while abs(this_y - y1) > self.cell_size:
                    if not start_tube:
                        if start_segment:
                            this_y += inc_y
                            start_segment = False
                    else:
                        start_tube = False
                        start_segment = False

                    sprite = pyglet.sprite.Sprite(self.unlit_image_vert, x=x0, y=this_y, batch=self.sprites_batch)
                    self.sprites.append(sprite)
                    self.sprites_are_horz.append(False)
                    this_y += inc_y

                # last cell special case
                scaled_width = int(this_y - y1)
                scale_y = abs(scaled_width) / self.cell_size
                tweak_y = 0
                # if scaled_width%2 > 0: # tweak if odd
                #     tweak_y = (inc_y > 0) - (inc_y < 0)

                print(f'this_y = {this_y}, tweak_y = {tweak_y}')
                this_y += tweak_y
                if scaled_width > 0:
                    this_y += self.cell_size - scaled_width
                sprite = pyglet.sprite.Sprite(self.unlit_image_vert, x=x0, y=this_y, batch=self.sprites_batch)
                sprite.scale_y = scale_y
                #sprite.rotation = 90
                self.sprites.append(sprite)
                self.sprites_are_horz.append(False)

            point_start = point_end

        # last point special case

        # if is_horizontal:
        #     sprite = pyglet.sprite.Sprite(self.unlit_image_horz, x=x1, y=y1, batch=self.sprites_batch)
        # else:
        #     sprite = pyglet.sprite.Sprite(self.unlit_image_vert, x=x1, y=y1, batch=self.sprites_batch)
        # self.sprites.append(sprite)
        # self.sprites_are_horz.append(is_horizontal)

        # for idx, (sprite, is_horz) in enumerate(zip(self.sprites, self.sprites_are_horz)):
        #     print(f'{idx}:({sprite.x}, {sprite.y}) scale_x:{sprite.scale_x},scale_y:{sprite.scale_y}, horz:{is_horz}')

        # corners at all waypoints except ends
        for waypoint, is_corner, rotation_idx in zip(waypoints, waypoint_is_corner, corner_rotations):
            if is_corner:
                x0, y0 = waypoint
                # lit corners use the same image
                sprite = pyglet.sprite.Sprite(self.lit_corner, x=x0, y=y0, batch=self.corners_lit_batch)
                rotation = int(rotation_idx * 90)
                sprite.rotation = rotation
                # Rotate is wonky at pixel level
                # also, sprites rotation is clockwise, stupidly
                if rotation == 0:
                    sprite.x = x0 - self.center_pixel
                    sprite.y = y0 - self.center_pixel
                    # print(f'self.center_pixel = {self.center_pixel}, x0 = {x0}, sprite.x = {sprite.x}')
                if rotation == 270:
                    # sprite.scale_x = -1
                    sprite.rotation = 90
                    sprite.x = x0 - self.center_pixel + 1 - 1
                    sprite.y = y0 +  self.center_pixel - 1
                if rotation == 180:
                    # sprite.scale_x = -1
                    # sprite.scale_y = -1
                    sprite.rotation = 180
                    sprite.x = x0 + self.center_pixel - 1
                    sprite.y = y0 + self.center_pixel - 1
                if rotation == 90:
                    sprite.rotation = 270
                    sprite.x = x0 + self.center_pixel - 1
                    sprite.y = y0 - self.center_pixel
                self.corners.append(sprite)
                # print(f'rotation = {rotation}, sprite.rotation = {sprite.rotation}, scale_x = {sprite.scale_x}, scale_y = {sprite.scale_y}')
                #unlit corners - no muss, each is customized
                x0, y0 = waypoint
                x0 -= self.center_pixel
                y0 -= self.center_pixel
                sprite = pyglet.sprite.Sprite(self.unlit_corners[rotation_idx], x=x0, y=y0, batch=self.corners_unlit_batch)
                self.corners.append(sprite)

    def draw(self):
        self.sprites_batch.draw()
        if self.is_lit:
            self.corners_lit_batch.draw()
        else:
            self.corners_unlit_batch.draw()

    def light_on(self):
        for sprite, is_horz in zip(self.sprites, self.sprites_are_horz):
            if is_horz:
                sprite.image = self.lit_image_horz
            else:
                sprite.image = self.lit_image_vert

        self.is_lit = True
        # for sprite in self.corners:
        #     sprite.image = self.lit_corner

    def light_off(self):
        for sprite, is_horz in zip(self.sprites, self.sprites_are_horz):
            if is_horz:
                sprite.image = self.unlit_image_horz
            else:
                sprite.image = self.unlit_image_vert
        # for sprite in self.corners:
        #     sprite.image = self.unlit_corner
        self.is_lit = False


class FrameHighlight:
    # frame_delay = 0.2 # seconds between frames
    count_delay = 0

    def __init__(self, frames, x, y):
        self.n_frames = len(frames)
        self.frames = frames
        self.sprite_idx = 0
        self.count = 0
        self.sprites = []
        #self.last_time = time.time()

        for frame in frames:
            sprite = pyglet.sprite.Sprite(img = frame, x=x, y=y)
            self.sprites.append(sprite)

    def draw(self):
        self.sprites[self.sprite_idx].draw()
        self.count += 1
        # now = time.time()
        # if now - self.last_time > self.frame_delay:
        if self.count > self.count_delay:
            #self.last_time = now
            self.count = 0
            self.sprite_idx += 1
            if self.sprite_idx >= self.n_frames:
                self.sprite_idx = 0


def set_and_load_fonts(config, button_width, label_width):

    # see if config contains font names
    try:
        button_font_name = config['button_font_name']  # 'Lavoir'
    except:
        button_font_name = 'Lavoir'  # this is an art deco font
        print(f'*** WARNING jukebox.cfg missing "button_font_name" entry, defaulting to {button_font_name} ***')

    try:
        label_font_name = config['label_font_name']  # 'Lavoir'
    except:
        label_font_name = 'DINEngsschriftStd'
        print(f'*** WARNING jukebox.cfg missing "label_font_name" entry, defaulting to {label_font_name} ***')

    # build font stack with likely default fonts
    default_font_stack = ('Arial', 'Helvetica', 'sans-serif')
    label_font_stack = [label_font_name]
    button_font_stack = [button_font_name]

    for this_font_name in default_font_stack:
        have_this = pyglet.font.have_font(this_font_name)
        if have_this:
            label_font_stack.append(this_font_name)
            button_font_stack.append(this_font_name)

    labels_font_size = 12

    # see if the first choice fonts are present
    button_avail = pyglet.font.have_font(button_font_name)  # Check if specific font exists
    if button_avail:
        print(f'Font "{button_font_name}" available')
    else:
        print(f'*** WARNING Font "{button_font_name}" NOT available')
        print(f'*** Try and find it here: https://fontlibrary.org/')

    label_avail = pyglet.font.have_font(label_font_name)  # Check if specific font exists
    if label_avail:
        print(f'Font "{label_font_name}" available')
    else:
        print(f'*** WARNING Font "{label_font_name}" NOT available')
        print(f'*** Try and find it here: https://fontlibrary.org/')

    return(button_font_stack, label_font_stack)


def label_to_playlist_item(clicked_label):
    filepath = clicked_label['filepath']
    this_album = clicked_label['album_label'].text
    this_artist = clicked_label['artist_label'].text
    if len(clicked_label['title_label'][0].text) < 1:
        this_title = clicked_label['title_label'][1].text + clicked_label['title_label'][2].text
    else:
        this_title = clicked_label['title_label'][0].text
    this_genre = clicked_label['genre']
    this_year = clicked_label['year']
    album_id = clicked_label['album_id']
    duration_s = clicked_label['duration_s']
    list_index = clicked_label['list_index']

    playlist_entry = {'album': this_album, 'artist': this_artist, 'title': this_title, 'filepath': filepath,
                      'duration_s': duration_s,
                      'genre': this_genre, 'year': this_year, 'album_id': album_id, 'list_index':list_index}

    return(playlist_entry)

# scans folder for music files, returns array of paths
def list_files_in_nested_folders(root_folder):
    musics = []
    for dirpath, dirnames, filenames in os.walk(root_folder):
        #print(f"Folder: {dirpath}")
        filenames.sort()
        for filename in filenames:
            #print(f"  File: {filename}")
            filepath = os.path.join(dirpath, filename)
            audiotype = filename[-3:]
            if audiotype in ['m4a', 'm4p', 'mp3']:
                musics.append(filepath)
            else:
                pass
                #print("skipped")

    return(musics)


# retrieve metadata from the audio file: artist, album, genre, date
def get_tune_metadata(filename):
    #print(filename)
    try:
    	audiofile = mutagen.File(filename)
    except mutagen.MutagenError:
    	print("Error reading headers for ", filename)
    	return([""], [""], ["Unknown album"], 1600, [""], 0, 1)
    	
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


def remap_genre(music_record, map_artists_to_genre, map_albums_to_genre, map_custom_genres):
    # music_record = {'filepath':music_file, 'title':title, 'artist':artist, 'album':album, 'year':year, 'genre':genre}
    artist = unidecode(music_record['artist'].lower())
    album = unidecode(music_record['album'].lower())
    genre = unidecode(music_record['genre'].lower())
    remapped_flag = 0

    # hard remap John Rutter
    if 'john rutter' in artist:
        music_record['artist'] = 'John Rutter'

    # hard remap if album title contains 'christmas'
    if ('christmas' in album):
        music_record['genre'] = 'Christmas'

    # user defined sub-genres
    for map_entry in map_custom_genres:
        if genre in map_entry['sub_genres']:
            music_record['genre'] = map_entry['genre']
            remapped_flag = 1
            break

    # Hard remap, not user specified
    # if ('country' in genre):
    #     music_record['genre'] = 'Folk'
    # elif (('electron' in genre) or ('altern' in genre) or ('industrial' in genre) or ('techno' in genre)
    #       or ('new age' in genre) or ('dance' in genre) or ('house' in genre)):
    #     music_record['genre'] = 'Altechnic'
    #     #print(f'Remapped {artist} to Altechnic')
    # elif ('pop' in genre) or ('hip hop' in genre) or ('rock' in genre) or ('hip-hop' in genre):
    #     music_record['genre'] = 'Rock'
    # elif ('christmas' in album) or ('holiday' in genre) or ('xmas' in genre):
    #     music_record['genre'] = 'Christmas'
    # elif 'franco' in genre:
    #     music_record['genre'] = 'Franco'
    # elif 'score' in genre:
    #     music_record['genre'] = 'Soundtrack'

    # user-defined artists and albums
    # if not remapped_flag:
    for map_entry in map_artists_to_genre:
        if artist in map_entry['artists']:
            music_record['genre'] = map_entry['genre']
            break
    for map_entry in map_albums_to_genre:
        if album in map_entry['albums']:
            music_record['genre'] = map_entry['genre']
            break

    return(music_record)


# import raw music files, get metadata and make a big list
def import_music(start_folders, map_artists_to_genre, map_albums_to_genre, map_custom_genres):
    # first, find all the music files
    global n_visited, n_read
    all_paths = []
    all_music = []
    list_idx = 0 # keep track of which list we got the files from
    for start_folder in start_folders:
        this_list = list_files_in_nested_folders(start_folder)
        #all_paths = all_paths + this_list

        # now, make a proper list with the metadata
        # for music_file in all_paths:
        for music_file in this_list:
            title, artist, album, year, genre, duration_s, error_flag = get_tune_metadata(music_file)
            # print(f'Error flag:{error_flag}')
            if not(error_flag):
                #dir_path = os.path.dirname(music_file)

                music_record = {'filepath':music_file, 'title':title, 'artist':artist, 'album':album, 'year':year,
                                'genre':genre, 'duration_s':duration_s, 'list_index':list_idx}
                music_record = remap_genre(music_record, map_artists_to_genre, map_albums_to_genre, map_custom_genres)
                all_music.append(music_record)
                n_read += 1

            n_visited += 1

            if n_visited % 100 == 0:
                # pump events (untested)
                pyglet.clock.tick()
                window.switch_to()
                window.dispatch_events()
                window.dispatch_event('on_draw')
                window.flip()

        list_idx += 1

    print(f"{n_visited} files examined.")

    return(all_music)


# From source list, make a list of all the albums that contain more than one song
# Also, put songs from single-song albums into the a 'singles' list
# also treat Compilations as special case
def build_albums_list(all_music):
    local_albums_list = []
    singles_list = []

    for music_record in all_music:
        #music_record = {'filepath':music_file, 'title':title, 'artist':artist, 'album':album, 'year':year, 'genre':genre}
        found_album = None
        this_album = music_record['album']
        this_year = music_record['year']
        this_genre = music_record['genre']
        this_artist = music_record['artist']
        this_music_file = music_record['filepath']
        dir_path = os.path.dirname(this_music_file)
        for album_record in local_albums_list:
            #if (album_record['album'] == this_album) and ((album_record['artist'] == this_artist) or ('Compilations' in this_music_file))
            # The directory path 'makes' the album -- all files in this directory should end up in this album
            # Caveat: only the first artist appearing in a collection will be listed
            # Therefore the other artists in a compilation will not be searchable by name
            #if (album_record['album'] == this_album) and (dir_path == album_record['dir_path']):
            # this modification should allow multiple discs to be listed as one
            if (dir_path == album_record['dir_path']):
                found_album = album_record
                break
        if found_album:
            found_album['count'] += 1
            #print(f'Found album {this_album} by {this_artist}, count {found_album["count"]}')
        else:
            album_record = {'album':this_album, 'count':1, 'year': this_year, 'genre':this_genre, 'artist':this_artist, 'dir_path':dir_path}
            local_albums_list.append(album_record)

    triaged_album_list = []
    singles_list = []
    # find singlet albums - discard album, add to singles list
    for album_record in local_albums_list:
        if album_record['count'] > 1:
            triaged_album_list.append(album_record)
            #print(f'Added to triaged list with {album_record["count"]} album intitled {album_record["album"]}')
        else:#
            # welp, now gotta find that song from the song list, 'case we shed some info on the way
            # Since we've established there's only one song in the album, shouldn't be a problem
            for music_record in all_music:
                if music_record['album'] == album_record['album']:
                    singles_list.append(music_record)
                    break

    # for album_record in triaged_album_list:
    #     append_fetch_cover_art_list(album_record['album']) # adds a to-fetch item, if not exists


    return(triaged_album_list, singles_list)


def read_list(filename):
    this_list = []
    f = open(filename, 'r')
    for line in f:
        stripped = line.rstrip()
        stripped = unidecode(stripped.lower())
        if not stripped == "":
            this_list.append(stripped)
    return(this_list)


def split_string_no_truncate_word(this_string, line_maxlength) :
    split_string = this_string.split(' ')
    short_string = ""
    short_len = 0
    split_index = 0
    n_splits = len(split_string)
    while (short_len < line_maxlength) and (split_index < n_splits):
        short_string = short_string + split_string[split_index] + ' '
        short_len = short_len + len(split_string[split_index]) + 1
        split_index = split_index + 1
    leftover = ""
    short_len = 0
    while (short_len < line_maxlength) and (split_index < n_splits):
        leftover = leftover + split_string[split_index] + ' '
        short_len = short_len + len(split_string[split_index]) + 1
        split_index = split_index + 1

    return(short_string, leftover)


# genre definitions and overrides
def read_genre_mappings(genres_list):
    #files_list = []
    map_artists_to_genre = []
    map_albums_to_genre = []
    map_subgenres_to_genre = []
    genres_files_path = os.path.join(definitions_folder,  "genres")
    file_names = os.listdir(genres_files_path)
    print(f'file names in genres folder: {file_names}')
    for filename in file_names:
        splitname = filename.split("_")
        first_word = splitname[0]
        second_word = splitname[1]
        filetype = second_word[-4:]
        print(f'First word={first_word}, second={second_word}, filetype={filetype}')
        stop_idx = len(second_word)-4
        if filetype == '.txt':
            datatype = second_word[0:stop_idx]
            #print(f'datatype={datatype}')
            if datatype in ['artists', 'albums', 'genres']:
                destination_genre = first_word
                file_path = os.path.join(genres_files_path, filename)
                if datatype == 'artists':
                    artists_list = read_list(file_path)
                    map_entry = {'genre':destination_genre, 'artists':artists_list}
                    map_artists_to_genre.append(map_entry)
                elif datatype == 'albums':
                    albums_list = read_list(file_path)
                    map_entry = {'genre':destination_genre, 'albums':albums_list}
                    map_albums_to_genre.append(map_entry)
                elif datatype == 'genres':
                    genres_list = read_list(file_path)
                    map_entry = {'genre': destination_genre, 'sub_genres': genres_list}
                    map_subgenres_to_genre.append(map_entry)
    return(map_artists_to_genre, map_albums_to_genre, map_subgenres_to_genre)


def format_button_label(button_label, button_flag, x_button, y_button, max_width_pixels, buttons_font_stack):
    this_button_label = pyglet.text.Label(button_label,
                              font_name=buttons_font_stack,
                              font_size=buttons_font_size,
                              color=(0,0,0,255),
                              x=x_button+60, y=y_button+22,
                              anchor_x='center', anchor_y='center')
    if this_button_label.content_width > max_width_pixels:
        this_button_label.font_size = buttons_font_size_smaller
    #print(this_button_label.text)
    return(this_button_label)


def format_label_text(this_album, this_artist, this_title):
    album_short, leftover = split_string_no_truncate_word(this_album, 25)

    # Shorten artist name
    if len(this_artist) > LABEL_MAX_LENGTH_ARTIST:
        split_artist = this_artist.split(' ')
        if len(split_artist) > 2:
            artist_short = split_artist[0] + ' ' + split_artist[1] + ' ' + split_artist[2]
        else:
            artist_short = this_artist[0:LABEL_MAX_LENGTH_ARTIST]
    else:
        artist_short = this_artist

    # split track title in two lines if necessary
    top_part, bot_part = split_string_no_truncate_word(this_title, LABEL_MAX_LENGTH_TITLE)
    # print(f'format label top_part:{top_part}, bot_part:{bot_part}')
    if len(bot_part) > 0:
        mid_title = ''
    else:
        mid_title = top_part
        top_part = ''
        bot_part = ''

    return(album_short, artist_short, mid_title, bot_part, top_part)


def format_labels(this_title, this_artist, this_album, x_label, y_label, labels_font_stack):
    # Shorten the album title to something with 20+ letters but don't cut words

    album_short, artist_short, mid_title, bot_part, top_part = format_label_text(this_album, this_artist, this_title)

    title_label_top = pyglet.text.Label(top_part,
                              font_name=labels_font_stack,
                              font_size=9,
                              color=(0,0,0,255),
                              x=x_label+150, y=y_label+78,
                              anchor_x='center', anchor_y='center')
    title_label_bot = pyglet.text.Label(bot_part,
                              font_name=labels_font_stack,
                              font_size=9,
                              color=(0,0,0,255),
                              x=x_label+150, y=y_label+66,
                              anchor_x='center', anchor_y='center')

    title_label_mid = pyglet.text.Label(mid_title,
                              font_name=labels_font_stack,
                              font_size=12,
                              color=(0,0,0,255),
                              x=x_label+150, y=y_label+70,
                              anchor_x='center', anchor_y='center')
    # title_labels = [title_label]

    title_labels = [title_label_mid, title_label_top, title_label_bot]

    artist_label = pyglet.text.Label(artist_short,
                              font_name=labels_font_stack,
                              font_size=14,
                              color=(0, 0, 0, 255),
                              x=x_label+150, y=y_label+46,
                              anchor_x='center', anchor_y='center')
    album_label = pyglet.text.Label(album_short,
                              font_name=labels_font_stack,
                              font_size=12,
                              color=(0, 0, 0, 255),
                              x=x_label+150, y=y_label+23,
                              anchor_x='center', anchor_y='center')

    return(title_labels, artist_label, album_label)


def playlist_to_label_entry(playlist_entry, label_entry):
    #print(f'playlist_entry {playlist_entry}')
    title_labels = label_entry['title_label']
    artist_label = label_entry['artist_label']
    album_label = label_entry['album_label']
    list_index = playlist_entry['list_index']
    label_entry['list_index'] = list_index

    album_short, artist_short, mid_title, bot_part, top_part = format_label_text(playlist_entry['album'],
                                                                                 playlist_entry['artist'],
                                                                                 playlist_entry['title'])
    title_labels[0].text = mid_title
    title_labels[1].text = top_part
    title_labels[2].text = bot_part
    #print(f'Playlist title_labels={title_labels[0].text}, {title_labels[1].text}, {title_labels[2].text}')
    artist_label.text = artist_short
    album_label.text = album_short


def song_record_to_label_entry(song_record, label_entry):
    #print('song_record_to_label_entry() ----')
    #print(song_record)
    filepath = song_record['filepath']
    year = song_record['year']
    genre = song_record['genre']
    try:
        album_id = song_record['album_id']
    except:
        album_id = ''
        # print('No album ID in this song record')
    if 'dim_flag' in song_record:
        dim_flag = song_record['dim_flag']
    else:
        dim_flag = 0  # regular Music library won't have this flag
    # if filepath[0:7] == 'spotify':
    #     duration_s = song_record['duration_s']
    duration_s = song_record['duration_s']
    title_labels = label_entry['title_label']
    artist_label = label_entry['artist_label']
    album_label = label_entry['album_label']
    # print(f'Label text is {title_label.text}')

    album_short, artist_short, mid_title, bot_part, top_part = format_label_text(song_record['album'],
                                                                                 song_record['artist'],
                                                                                 song_record['title'])
    title_labels[0].text = mid_title
    title_labels[1].text = top_part
    title_labels[2].text = bot_part

    artist_label.text = artist_short
    album_label.text = album_short
    label_entry['filepath'] = filepath
    label_entry['duration_s'] = duration_s
    label_entry['visible'] = 1
    label_entry['year'] = year
    label_entry['genre'] = genre
    label_entry['album_id'] = album_id
    label_entry['dim_flag'] = dim_flag
    label_entry['list_index'] = song_record['list_index']


def get_media(play_item):
    music_file = play_item['filepath']
    print(f'Get_media({play_item})')
    # music_file = '/home/patrick/Python/jukebox/musik/1977_1979/16 We Will Rock You.m4a'
    directory_path = os.path.dirname(os.path.realpath(music_file))
    music_file_name = os.path.basename(music_file)
    pyglet.resource.path = [directory_path]
    pyglet.resource.reindex()
    # print("Resource Path:", pyglet.resource.path)
    #music = pyglet.resource.media(music_file_name)
    file_path = Path(music_file)
    media_uri = file_path.as_uri()
    music = vlc.Media(media_uri)
    print(music)
    return(music)

def shuffle_playlist(this_playlist, topsong_index, playing):
    n_songs = len(this_playlist)
    print(f'len(playlist) = {n_songs}')
    # make a list containing numbers 0 to n_songs-1
    if playing:
        nums = list(range(topsong_index+1, n_songs))
        shuffled_playlist = this_playlist[0:topsong_index+1]  # keep already played songs as-is
    else:
        nums = list(range(0, n_songs))
        shuffled_playlist = []
    print(f'playing={playing}, init shuffled_playlist={shuffled_playlist}')
    print(f'nums = {nums}')

    # if playing: # pull that song from randomizer list, put it on top of the shuffled list
    #     del(nums[topsong_index])
    #     shuffled_playlist.append(this_playlist[topsong_index])
    while len(nums) > 0:
        randindex = random.randint(0,len(nums)-1)
        print(f'rand = {randindex}, song there = {this_playlist[nums[randindex]]}')
        shuffled_playlist.append(this_playlist[nums[randindex]])
        del(nums[randindex])
        print(f'nums = {nums}')
    #shuffled_playlist.append(this_playlist[0]) # check this one, not sure
    n_songs = len(shuffled_playlist)
    print(f'len(shuffled_playlist) = {n_songs}')
    return(shuffled_playlist)


def requeue(this_player, this_playlist, topsong_index):
    n_songs = len(this_playlist)
    print(f'requeue playlist={this_playlist}')
    if topsong_index < n_songs - 1: # no need to do anything if the last item is playing
        current_source = this_player.source
        current_song_time = this_player.time
        player.stop()
        player.queue = None # purge queue
        player.queue(current_source)
        player.seek(current_song_time)
        for idx in range(topsong_index+1, n_songs):
            music = get_media(this_playlist[idx])
            this_player.queue(music)

    return(0)


def is_central_panel_click(x, y):
    if (x > songlist_edge_left) and (x < songlist_edge_right):
        flag_x = 1
    else:
        flag_x = 0
    if (y > songlist_edge_bot) and (y < songlist_edge_top):
        flag_y = 1
    else:
        flag_y = 0
    return(flag_x and flag_y)


#song_labels = find_album_songs(clicked_label['album'], clicked_label['artist'])
def find_album_songs(dir_path, artist):
    song_list = []

    for song_record in all_music:
        this_dir_path = os.path.dirname(song_record['filepath'])
        if (dir_path == this_dir_path):
            song_list.append(song_record)

    return(song_list)


#song_labels = find_album_songs(clicked_label['album'], clicked_label['artist'])
def find_album_songs_deprecated(dir_path, artist):
    playlist_entries = []

    for song_record in all_music:
        this_album = song_record['album']
        this_artist = song_record['artist']
        this_dir_path = os.path.dirname(song_record['filepath'])
        this_duration = song_record['duration_s']
        list_index = song_record['list_index']
        # this_year = song_record['year']
        # this_genre = song_record['genre']
        #if (album == this_album) and ((artist == this_artist)):
        if (dir_path == this_dir_path):
            this_title = song_record['title']
            # this_artist = song_record['artist']
            filepath = song_record['filepath']

            playlist_entry = {'filepath': filepath, 'album': this_album, 'artist': this_artist, 'title': this_title,
                              'duration_s':this_duration, 'list_index':list_index}

            playlist_entries.append(playlist_entry)

    return(playlist_entries)

def get_album_art(album_title, new_width):
    cover_art = None
    path = os.path.join(album_art_folder, album_title + '.png')
    new_height = new_width
    try:
        cover_art_image =pyglet.image.load(path)
        #print(f'image width={cover_art_image.width}, height={cover_art_image.height}')
        #image_rgba = add_alpha_channel(cover_art_image)
        #cover_art_texture = cover_art_image.get_texture(image_rgba)
        #scaled_image = texture.get_texture().get_region(0, 0, cover_art.width, cover_art.height)
        #scaled_image.width = new_width
        #scaled_image.height = new_height
        #sprite = pyglet.sprite.Sprite(texture)
        scale_x = new_width / cover_art_image.width
        scale_y =  new_height / cover_art_image.height
        #print(f'texture width={texture.width}, height={texture.height}, target width={new_width}, height={new_height}')
        #cover_art = sprite
    except Exception as e:
        print(e)
        #texture = default_cover_texture
        cover_art_image = default_cover_image
        scale_x = new_width / default_cover_image.width
        scale_y =  new_height / default_cover_image.height
        # # make note of missing album art
        # write_line = album_title + '\n'
        # fp = open(seek_album_art_filename, 'a')
        # fp.write(write_line)
        # fp.close()
    return(cover_art_image, scale_x, scale_y)


def append_fetch_cover_art_list(album_title):
    cover_art = get_album_art(album_title)
    if cover_art == default_cover_image:
        write_line =album_title + '\n'
        fp = open(seek_album_art_filename, 'a')
        fp.write(write_line)
        fp.close()

def sanitize(ze_string):
    sanitized_string = ze_string.replace('/', '-')
    #sanitized_string = sanitized_string.replace('"', '\\"')
    return(sanitized_string)

# Special case for putting a pathname in a command pipe
def sanitize_dequote(ze_string):
    sanitized_string = ze_string.replace('"', '\\"')
    return(sanitized_string)


# write out track recorded in audacity with the appropriate metadata
def export_track(playlist_item):
    maxwait = 30 # max seconds to give to audacity to export before giving up
    wait_interval = 3
    title = playlist_item['title']
    artist = playlist_item['artist']
    album = playlist_item['album']
    genre = playlist_item['genre']
    year = playlist_item['year']
    album_id = playlist_item['album_id']
    #album_cover_addrs = playlist_item['album_cover']

    # Sanitize
    artist = sanitize(artist)
    album = sanitize(album)
    title = sanitize(title)

    # Check and/or create artist directory
    artist_path = os.path.join(config['scraping_write_to_folder'], artist)
    if not os.path.exists(artist_path):
        os.mkdir(artist_path)

    # Check and/or create album directory
    album_path = os.path.join(artist_path, album)
    if not os.path.exists(album_path):
        os.mkdir(album_path)
    title_mp3 = title + '.mp3'
    track_path = os.path.join(album_path, title_mp3)

    # export track from audacity client
    print(f'track_path={track_path}')
    audacity_client.saveTo(sanitize_dequote(track_path))

    # wait until the export is good and done
    waited = 0
    while (not os.path.exists(track_path)) and (waited < maxwait):
        time.sleep(wait_interval)
        waited += wait_interval

    # File exists, but may still be in writing mode; wait a bit more
    time.sleep(2*wait_interval)

    # Now change metadata on the file
    audiofile = mutagen.File(track_path)
    keys = audiofile.keys()
    audiofile['TCON'] = mutagen.id3.TCON(encoding=3, text=genre)
    audiofile['TDRC'] = mutagen.id3.TDRC(encoding=3, text=str(year))
    audiofile['TALB'] = mutagen.id3.TALB(encoding=3, text=album)
    audiofile['TPE1'] = mutagen.id3.TPE1(encoding=3, text=artist)
    audiofile['TIT2'] = mutagen.id3.TIT2(encoding=3, text=title)
    audiofile.save()

    # Now scrape album art
    album_art_path = os.path.join(config['scraping_write_to_folder'], 'album_covers', album + '.jpg')
    album_cover_image = spotify_controller.get_album_art(album_id)
    if not album_cover_image == None:
        with open(album_art_path, "wb") as file:
            file.write(album_cover_image)



# ============================================ Main ========================================


n_visited = 0
n_read = 0
eos_flag = 0 # set to 1 whenever get get on_eos or on_player_eos
eos_time = time.time()
# window = pyglet.window.Window(width=screen_width, height=screen_height, fullscreen=True)

window = pyglet.window.Window(width=window_width, height=window_height, fullscreen=False,
                              style=pyglet.window.Window.WINDOW_STYLE_BORDERLESS, config=pyg_config)
#window.switch_to()
glEnable(GL_BLEND)
glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)

buttons_font_stack, labels_font_stack = set_and_load_fonts(config, BUTTON_WIDTH, LABEL_WIDTH)
#label_highlight_sprite = pyglet.sprite.Sprite(img=label_highlight, x=playing_highlight_x, y=playing_highlight_y)
#label_highlight.blit(playing_highlight_x, playing_highlight_y)

frame_batch = pyglet.graphics.Batch()
frame_size_vertical = 300
frame_size_horizontal = 800
corner_size = 100
frame_x_left = (window.width - frame_size_horizontal) // 2
frame_x_right = (window.width + frame_size_horizontal) // 2
frame_y_top = (window.height + frame_size_vertical) // 2
frame_y_bot = (window.height - frame_size_vertical) // 2
sprite_topleft  = pyglet.sprite.Sprite(frame_corner, x=frame_x_left - corner_size//2,
                                       y=frame_y_top - corner_size//2, batch=frame_batch)
sprite_topright  = pyglet.sprite.Sprite(frame_corner, x=frame_x_right - corner_size//2,
                                       y=frame_y_top + corner_size//2, batch=frame_batch)
sprite_botleft  = pyglet.sprite.Sprite(frame_corner, x=frame_x_left + corner_size//2,
                                       y=frame_y_bot-corner_size//2, batch=frame_batch)
sprite_botright  = pyglet.sprite.Sprite(frame_corner, x=frame_x_right + corner_size//2,
                                       y=frame_y_bot+corner_size//2 , batch=frame_batch)

frame_sprites = []
frame_x = frame_x_left + corner_size//2
while frame_x < (frame_x_right - corner_size):
    frame_sprite = pyglet.sprite.Sprite(frame_segment, x=frame_x, y=frame_y_top-corner_size// 2, batch=frame_batch)
    frame_sprites.append(frame_sprite)
    frame_sprite2 = pyglet.sprite.Sprite(frame_segment, x=frame_x+corner_size, y=frame_y_bot + corner_size // 2, batch=frame_batch)
    frame_sprite2.rotation = 180
    frame_sprites.append(frame_sprite2)
    frame_x += corner_size # frame cell size also

frame_y = frame_y_bot + corner_size//2
while frame_y < (frame_y_top - corner_size):
    frame_sprite = pyglet.sprite.Sprite(frame_segment, x=frame_x_left+corner_size//2, y=frame_y, batch=frame_batch)
    frame_sprite.rotation = 270
    frame_sprites.append(frame_sprite)
    frame_sprite2 = pyglet.sprite.Sprite(frame_segment, x=frame_x_right-corner_size//2, y=frame_y+corner_size, batch=frame_batch)
    frame_sprite2.rotation = 90
    frame_sprites.append(frame_sprite2)
    frame_y += corner_size # frame cell size also

sprite_topright.rotation = 90
sprite_botright.rotation = 180
sprite_botleft.rotation=270

label1 = pyglet.text.Label('Loading music, please wait...',
                          font_name=buttons_font_stack,
                          font_size=24,
                          x=window.width // 2, y=window.height // 2 + 25,
                          anchor_x='center', anchor_y='center')
label1_width = label1.content_width
# label1.x = window.width // 2
print(f'label content width = {label1_width}')
label2 = pyglet.text.Label('Loaded 0 files from 0 in directory',
                          font_name=buttons_font_stack,
                          font_size=20,
                          x=window.width // 2, y=window.height // 2 - 10,
                          anchor_x='center', anchor_y='center')
label2_width = label2.content_width
# label2.x = (window.width - label2_width) // 2

#global draw_its
draw_its = 0

@window.event
def on_draw():
    global draw_its
    window.clear()
    stringue = f'Loaded {n_read} files from {n_visited} in directory'
    label2.text = stringue
    # label1.x = (window.width - label1_width) // 2 + draw_its
    label1.draw()
    label2.draw()
    frame_batch.draw()
    # sprite1.x = draw_its
    # if draw_its % 2 > 0:
    #     sprite1.image = up_button_juiced
    # else:
    #     sprite1.image = up_button_off
    # sprite1.draw()
    draw_its +=1

try:
    #print(f'Genres_list before = {config["genres_list"]}')
    genres_list = config['genres_list'].split(',')
    print(f'Genres_list = {genres_list}')
except:
    genres_list = []

default_cover_image = pyglet.image.load(default_cover_image_file)
#default_cover_texture = default_cover_image_rgba.get_texture()
# all_tunes_paths = list_files_in_nested_folders(music_root_folder)
map_artists_to_genre, map_albums_to_genre, map_custom_genres = read_genre_mappings(genres_list)
print(map_custom_genres)
all_music = import_music(music_root_folders, map_artists_to_genre, map_albums_to_genre, map_custom_genres)

all_music_n_tracks = len(all_music)
print(f'{all_music_n_tracks} tracks loaded')
print(map_albums_to_genre)
print(map_artists_to_genre)
albums_list, all_singles_list = build_albums_list(all_music)

tab_buttons = TopButtons()
button_panel = ButtonPanel(button_on_epochs, button_on_genre, button_off, genres_list, buttons_font_stack)
tracks_panel = LabelPanel(labels_font_stack)
singles_panel = LabelPanel(labels_font_stack)
spotify_panel = LabelPanel(labels_font_stack)
albums_panel = AlbumPanel(labels_font_stack)

artist_list = ArtistsPanel(labels_font_stack)
# play_progress_bar = ProgressBar(playlist_panel_edge_left, playing_highlight_y-15, playlist_panel_label_width)
#play_control_buttons = ControlButtonPanel(play_control_buttons_x, play_control_buttons_y, button_list=['play', 'skip', 'shuffle'], button_set=0)
play_control_buttons = ControlButtonPanel(play_control_buttons_x, play_control_buttons_y, button_list=['play', 'skip'], button_set=0)
songs_page_buttons = ControlButtonPanel(songs_page_control_buttons_x, songs_page_control_buttons_y, button_list=['up', 'down', 'all'], button_set=1)
artists_page_buttons = ControlButtonPanel(artists_panel_page_buttons_x, artists_panel_page_buttons_y, button_list=['up', 'down'], button_set=2)
playlist_page_buttons = ControlButtonPanel(play_control_buttons_x, play_control_buttons_y - 80, button_list=['up', 'down', 'clear'], button_set=1)

player = MediaPlayer(config)
ze_playlist = PlayList(player.playlist, labels_font_stack)

# starting lineup
singles_panel.filtered_list = button_panel.update_filtered(all_singles_list)
tracks_panel.filtered_list = button_panel.update_filtered(all_music)
albums_panel.filtered_list = button_panel.update_filtered(albums_list)

artist_list.update_artists_list(tracks_panel.filtered_list)
tracks_panel.page_number = 0  # contents has changed, just go to top
tracks_panel.update_visible_list()

artist_list.page_number = 0
artist_list.all_selected = 1
artist_list.update_visible_list()
tracks_panel.update_double_filtered_list(artist_list)
albums_panel.update_double_filtered_list(artist_list)
singles_panel.update_double_filtered_list(artist_list)
# spotify_panel.update_double_filtered_list(artist_list)
tracks_panel.page_number = 0  # contents has changed, just go to top
albums_panel.page_number = 0
singles_panel.page_number = 0
spotify_panel.page_number = 0
tracks_panel.update_visible_list()
albums_panel.update_visible_list()
singles_panel.update_visible_list()

tube_waypoints = [tube_waypoint_1, tube_waypoint_2, tube_waypoint_3, tube_waypoint_4, tube_waypoint_5]
neon_tube = NeonTube(tube_waypoints, tube_waypoint_is_corner, tube_corner_rotations)
highlight_frame = FrameHighlight(label_highlights, playing_highlight_x, playing_highlight_y)
frame_count = 0
frame_count_start = time.time()

@window.event
def on_mouse_scroll(x, y, scroll_x, scroll_y):
    print(f"scroll_x: {scroll_x}, scroll_y: {scroll_y}")

# spotify_panel.update_visible_list()
@window.event
def on_mouse_press(x, y, button, modifiers):
    #global playlist
    #global eos_flag, eos_time, player
    global player

    pause_start = time.time() # init this var
    print(f"mouse press at {x}, {y}")
    play_control_button_click = play_control_buttons.process_click(x, y)
    playlist_page_button_click = playlist_page_buttons.process_click(x, y)
    artists_control_panel_click = artists_page_buttons.process_click(x, y)
    songs_page_control_button_click = songs_page_buttons.process_click(x, y)
    tab_buttons_click = tab_buttons.process_click(x, y)
    buttons_panel_click = button_panel.process_click(x, y)
    central_panel_click = is_central_panel_click(x, y)
    print(f'click play:{play_control_button_click} artist:{artists_control_panel_click} songs:{songs_page_control_button_click}, tabs:{tab_buttons_click}, buttons:{buttons_panel_click}, central_panel_click:{central_panel_click}')
    if central_panel_click:
        #print(f'Central panel click, visible panel is: {tab_buttons.visible_panel}')
        if tab_buttons.visible_panel == 'Tracks':
            if tracks_panel.process_click(x, y):
                ze_playlist.update_visible_list(0,0)
                # if play_control_buttons.playing: # need to add what was clicked to the player queue
                #     play_item = playlist[-1] # This works as long as click to add is the only possible action
                #     music = get_media(play_item)
                #     player.queue(music)
        elif tab_buttons.visible_panel == 'Singles':
            if singles_panel.process_click(x, y):
                ze_playlist.update_visible_list(0,0)
                # if play_control_buttons.playing: # need to add what was clicked to the player queue
                #     play_item = playlist[-1] # This works as long as click to add is the only possible action
                #     music = get_media(play_item)
                #     player.queue(music)
        elif tab_buttons.visible_panel == 'Albums':
            #print('Add album to playlist not yet defined')
            if albums_panel.process_click(x, y):
                ze_playlist.update_visible_list(0,0)
                # if play_control_buttons.playing: # need to add what was clicked to the player queue
                #     play_item = playlist[-1] # This works as long as click to add is the only possible action
                #     music = get_media(play_item)
                #     player.queue(music)
        elif tab_buttons.visible_panel == 'Spotify':
            if spotify_panel.process_click(x, y):
                ze_playlist.update_visible_list(0,0)


    elif tab_buttons_click:
        tab_buttons.visible_panel = tab_buttons.tab_list[tab_buttons_click-1]
        print('visible panel:' + tab_buttons.visible_panel)
        # update artist list, as singles/tracks/albums are all different
        if tab_buttons.visible_panel == 'Tracks':
            artist_list.update_artists_list(tracks_panel.filtered_list)
            tracks_panel.page_number = 0
            tracks_panel.update_visible_list()
            tracks_panel.update_double_filtered_list(artist_list)
        elif tab_buttons.visible_panel == 'Albums':
            artist_list.update_artists_list(albums_panel.filtered_list)
            albums_panel.page_number = 0
            albums_panel.update_visible_list()
            albums_panel.update_double_filtered_list(artist_list)
        elif tab_buttons.visible_panel == 'Singles':
            artist_list.update_artists_list(singles_panel.filtered_list)
            singles_panel.page_number = 0
            singles_panel.update_visible_list()
            singles_panel.update_double_filtered_list(artist_list)
        elif tab_buttons.visible_panel == 'Spotify':
            artist_list.update_artists_list(spotify_panel.filtered_list)
            spotify_panel.page_number = 0
            spotify_panel.update_visible_list()
            spotify_panel.update_double_filtered_list(artist_list)
        # go to top of artist list, reset 'all' flag
        artist_list.page_number = 0
        #artist_list.all_selected = 1
        artist_list.artists_selected[0] = 1
        artist_list.update_visible_list()

    elif buttons_panel_click: # i.e. selection of genres and epochs has changed
        print('Button panel click')
        albums_panel.album_open = 0 # force closure of open album
        singles_panel.filtered_list = button_panel.update_filtered(all_singles_list)
        tracks_panel.filtered_list = button_panel.update_filtered(all_music)
        albums_panel.filtered_list = button_panel.update_filtered(albums_list)
        if config['spotify_enable'] == 'on': # don't make web queries if not active option. Other local stuff we don't care about
            spotify_panel.filtered_list = button_panel.get_spotify_page(spotify_panel.songs_per_page, int(config['spotify_start_page_number']))
            print('Spotify panel filtered list :', spotify_panel.filtered_list)
            if tab_buttons.visible_panel == 'Spotify':
                artist_list.update_artists_list(spotify_panel.filtered_list)
                spotify_panel.update_double_filtered_list(artist_list)
                spotify_panel.update_visible_list()
        n_in_filtered = len(tracks_panel.filtered_list)
        print(f'Filtered tracks list now contains {n_in_filtered} entries')
        n_in_filtered = len(albums_panel.filtered_list)
        print(f'Filtered Albums list now contains {n_in_filtered} entries')
        if tab_buttons.visible_panel == 'Tracks':
            artist_list.update_artists_list(tracks_panel.filtered_list)
        elif tab_buttons.visible_panel == 'Albums':
            artist_list.update_artists_list(albums_panel.filtered_list)
        elif tab_buttons.visible_panel == 'Singles':
            artist_list.update_artists_list(singles_panel.filtered_list)

        artist_list.page_number = 0
        artist_list.all_selected = 1
        artist_list.update_artists_list(tracks_panel.filtered_list)
        artist_list.update_visible_list()
        tracks_panel.update_double_filtered_list(artist_list)
        albums_panel.update_double_filtered_list(artist_list)
        singles_panel.update_double_filtered_list(artist_list)
        # spotify_panel.update_double_filtered_list(artist_list)
        tracks_panel.page_number = 0 # contents has changed, just go to top
        albums_panel.page_number = 0
        singles_panel.page_number = 0
        spotify_panel.page_number = 0
        tracks_panel.update_visible_list()
        albums_panel.update_visible_list()
        singles_panel.update_visible_list()
        # spotify_panel.update_visible_list()
    elif artist_list.process_click(x,y): # artist was selected or deselected
        print('artist_list.process_click: yes')
        tracks_panel.page_number = 0
        albums_panel.page_number = 0
        singles_panel.page_number = 0
        spotify_panel.page_number = 0
        tracks_panel.update_double_filtered_list(artist_list)
        tracks_panel.update_visible_list()
        albums_panel.update_double_filtered_list(artist_list)
        albums_panel.update_visible_list()
        singles_panel.update_double_filtered_list(artist_list)
        singles_panel.update_visible_list()
        spotify_panel.update_double_filtered_list(artist_list)
        spotify_panel.update_visible_list()
        #artist_list.draw_labels() # not sure this is needed
    elif artists_control_panel_click:
        print('artists_control_panel_click: yes')
        button_index = artists_control_panel_click - 1
        artists_page_buttons.buttons[button_index]['active'] = 1
        artists_page_buttons.draw_buttons() # the "on" should appear brielfy
        if (artist_list.page_change(button_index)):
            artist_list.update_visible_list()
        else: # list changed, goto top, whichever panel we're at
            pass # actually no selections changes in this part, just page up down so I commented out the stuff below
            # tracks_panel.page_number = 0
            # albums_panel.page_number = 0
            # singles_panel.page_number = 0
            # spotify_panel.page_number = 0
            # singles_panel.update_visible_list()
            # albums_panel.update_visible_list()
            # tracks_panel.update_visible_list()
            # spotify_panel.update_visible_list()
        artists_page_buttons.buttons[button_index]['active'] = 0
    elif playlist_page_button_click:
        if playlist_page_button_click in [1, 2]:
            ze_playlist.page_change(playlist_page_button_click-1)
        if playlist_page_button_click == 3: # clear/stop pressed
            if play_control_buttons.playing: # stop, don't clear
                play_control_buttons.playing = 0
                neon_tube.light_off()
                player.stop()
                player.flush_queue()
                # while not (player.source == None): # flush queue
                #     player.next_source()
                playlist_page_buttons.buttons[2]['active'] = 1  # flip to 'clear' again
                play_control_buttons.buttons[0]['active'] = 1  # turn 'pause' button into 'play' button
                if play_control_buttons.is_spotify_track > 0:
                    player.spotify_client.play_pause()
            else: # clear playlist
                player.playlist = []
                player.stop()
                play_control_buttons.playing = 0
            ze_playlist.page_index = 0  # reset position
            ze_playlist.topsong_index = 0
            ze_playlist.update_visible_list(0,0)

    elif play_control_button_click:
            button_index = play_control_button_click-1

            if button_index == 0: # play / pause
                if len(player.playlist) > 0: # only do stuff if there's a playlist
                    if not (play_control_buttons.playing): # start Play
                        print(f'len(player.playlist) = {len(player.playlist)}')
                        play_control_buttons.playing = 1
                        neon_tube.light_on()
                        play_control_buttons.buttons[0]['active'] = 0 # turn 'play' button into 'pause' button
                        play_control_buttons.buttons[0]['juiced'] = 1
                        play_control_buttons.buttons[0]['juice_start_time'] = time.time()
                        playlist_page_buttons.buttons[2]['active'] = 0  # Turn 'clear' into "stop" button
                        play_item = player.playlist[0]
                        print(play_item)
                        #play_progress_bar.start_timer(play_item)
                        player.play_media(play_item)
                        ze_playlist.topsong_index = 0
                        ze_playlist.page_index = 0
                        ze_playlist.update_visible_list(0,0)
                    else:
                        if not play_control_buttons.paused: # playing, so pause
                            play_control_buttons.paused = 1
                            # player.play_progress_bar.pause()
                            player.play_pause()
                            #control_buttons.buttons[0]['flag'] = 0
                            play_control_buttons.buttons[0]['active'] = 1 # switch to 'play' button
                            print('Pause')
                        else: # paused, so depause
                            print('Play')
                            play_control_buttons.paused = 0
                            # player.play_progress_bar.depause()
                            play_control_buttons.buttons[0]['active'] = 0
                            player.play_pause()

            elif button_index == 1: # skip
                print("skip button pressed")
                if play_control_buttons.playing: # skip
                    if play_control_buttons.is_spotify_track > 0:
                        # need to pause current track because if it's not a spotify track next, it will play in parallel with the local track
                        player.spotify_client.play_pause()
                        if ze_playlist.scroll_down_one(play_control_buttons) < 1: # not last
                            play_item = player.playlist[ze_playlist.topsong_index]
                            player.play_media(play_item)
                        else: # Player finished playing, Turn 'stop' button back into 'clear'
                            playlist_page_buttons.buttons[2]['active'] = 1
                        ze_playlist.update_visible_list(0,0)
                    else:
                        if player.is_playing():
                            if ze_playlist.scroll_down_one(play_control_buttons) > 0:
                                player.stop()
                                play_control_buttons.buttons[0]['active'] = 1
                                play_control_buttons.playing = 0
                                playlist_page_buttons.buttons[2]['active'] = 1
                                neon_tube.light_off()
                            else:  # cue up next song
                                play_item = player.playlist[ze_playlist.topsong_index]
                                print(f'on_draw() queuing up: {play_item["filepath"]}')
                                player.play_media(play_item)
                            ze_playlist.update_visible_list(0, 0)

            # elif button_index == 2: # shuffle
            #     playlist = shuffle_playlist(playlist, ze_playlist.topsong_index, play_control_buttons.playing)
            #     print(f'play_control_buttons.playing={play_control_buttons.playing}')
            #     if play_control_buttons.playing: # need to reset the queue now
            #         #requeue(player, playlist, ze_playlist.topsong_index)
            #         n_songs = len(playlist)
            #         print(f'requeue playlist={playlist}')
            #         if ze_playlist.topsong_index < n_songs - 1:  # no need to do anything if the last item is playing
            #             current_source = player.source
            #             current_song_time = player.time
            #             #player.stop()
            #             #player.queue = None  # purge queue
            #             for idx in range(ze_playlist.topsong_index, n_songs):
            #                 player.next_source()
            #             player.queue(current_source)
            #             player.play()
            #             play_control_buttons.playing = 1 # eos was triggered when we emptied the queue, and reset this
            #             player.seek(current_song_time)
            #             for idx in range(ze_playlist.topsong_index + 1, n_songs):
            #                 music = get_media(playlist[idx])
            #                 player.queue(music)
            #     #ze_playlist.topsong_index = 0
            #     ze_playlist.update_visible_list(0,0)
            #     play_control_buttons.buttons[2]['flag'] = 0

    elif songs_page_control_button_click:
        button_index = songs_page_control_button_click - 1
        print(f'song page button {button_index} clicked')
        if tab_buttons.visible_panel == 'Singles':
            if not singles_panel.page_change(button_index): # "all" clicked
                singles_panel.add_all()
                ze_playlist.update_visible_list(0,0)
        elif tab_buttons.visible_panel == 'Tracks':
            if not tracks_panel.page_change(button_index):
                tracks_panel.add_all()
                ze_playlist.update_visible_list(0,0)
            #tracks_panel.update_visible_list()
        elif tab_buttons.visible_panel == 'Albums':
            if not albums_panel.page_change(button_index):
                albums_panel.add_all()
                ze_playlist.update_visible_list(0,0)
        elif tab_buttons.visible_panel == 'Spotify':
            # LabelPanel class does not know how to get more tracks, handle here.
            if button_index > 0: # page down, add to list if we were at the last page already
                # if no artists are selected, then the filtered_list and double_filtered_list are the same
                pages_available = math.ceil(len(spotify_panel.filtered_list) / spotify_panel.songs_per_page)
                page_start = pages_available + int(config['spotify_start_page_number'])
                filtered_pages_available = math.ceil(len(spotify_panel.double_filtered_list) / spotify_panel.songs_per_page)
                if (spotify_panel.page_number+1) > (filtered_pages_available-1): # MORE!
                    # add to non filtered list and then filter it.
                    # we might just end up with more items on the same page
                    spotify_panel.filtered_list += button_panel.get_spotify_page(spotify_panel.songs_per_page, page_start)
                    artist_list.update_artists_list(spotify_panel.filtered_list)
                    spotify_panel.update_double_filtered_list(artist_list)

            spotify_panel.page_change(button_index)


@window.event
def on_draw():
    #global eos_flag, eos_time
    global player
    global neon_tube
    # global frame_count
    # global frame_count_start
    window.clear()
    artist_list.draw_labels()
    neon_tube.draw()
    tab_buttons.draw_buttons()
    if tab_buttons.visible_panel == 'Tracks':
        tracks_panel.draw_labels()
    elif tab_buttons.visible_panel == 'Albums':
        albums_panel.draw()

    elif tab_buttons.visible_panel == 'Singles':
        singles_panel.draw_labels()
    elif tab_buttons.visible_panel == 'Spotify':
        spotify_panel.draw_labels()
    button_panel.draw_buttons()
    play_control_buttons.draw_buttons()
    songs_page_buttons.draw_buttons()
    artists_page_buttons.draw_buttons()
    playlist_page_buttons.draw_buttons()
    if play_control_buttons.playing:
        #label_highlight.blit(playing_highlight_x, playing_highlight_y)
        #label_highlight_sprite.draw()
        highlight_frame.draw()
        player.play_progress_bar.update_timer()
        player.play_progress_bar.draw()
        if player.is_track_done():
            if player.is_spotify_track > 0:
                player.spotify_client.play_pause() # pause
                if config['scraping_enable'] == 'on':
                    export_track(player.playlist[ze_playlist.topsong_index])
            if ze_playlist.scroll_down_one(play_control_buttons) > 0:
                play_control_buttons.buttons[0]['active'] = 1
                play_control_buttons.playing = 0
                playlist_page_buttons.buttons[2]['active'] = 1
                neon_tube.light_off()

            else:  # cue up next song
                play_item = player.playlist[ze_playlist.topsong_index]
                print(f'on_draw() queuing up: {play_item["filepath"]}')
                player.play_media(play_item)
            ze_playlist.update_visible_list(0,0)
    ze_playlist.draw_labels()
    # frame_count += 1
    # if frame_count > 100:
    #     now = time.time()
    #     delta_time = now - frame_count_start
    #     fps = frame_count / delta_time
    #     print(f'{fps:.1f} fps')
    #     frame_count = 0
    #     frame_count_start = now


pyglet.app.run(interval=0.2) # 0.2 <=> run at 5 fps, which should allow cpu to not max out -- adjust as necessary
