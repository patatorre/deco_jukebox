import vlc
import os
import time

os.environ['VLC_PLUGIN_PATH'] = '/usr/lib/x86_64-linux-gnu/vlc/plugins'

app_path = os.getcwd()
print(f'app_path = {app_path}')
music_folder = 'musik/1980_1983/'
music_path = os.path.join(app_path, music_folder)
print(f'music_path = {music_path}')
file1 = os.path.join(music_path, '02 Echo Beach.m4a')
file2 = os.path.join(music_path, 'Sunday Bloody Sunday.mp3')

player = vlc.MediaPlayer(file2)
player.play()
time.sleep(10)

