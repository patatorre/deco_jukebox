Deco Jukebox

This is a Python jukebox designed for a touch-screen interface. Just point it to your iTunes library and go! The top buttons changes the view between Singles / Tracks / Albums. The interface lets you sort by epochs, genres, and artists. The middle panel will contain a random selection of tracks, or show all the albums. In track view, add to the playlist by tapping a song label, or add all by tapping "add all".

Quick start:
1) Install Python (3.14 is current as of this writing) and the packages listed in requirements.txt. Windows: click-check "Add python.exe to PATH" during installation. install packages with "pip install whatever" on a command line, with whatever=pyglet, python-vlc, unidecode, mutagen, requests.
2) Install VLC. On Ubuntu do NOT use the snap install. Just "sudo apt install vlc". on Windows go to the official site: https://www.videolan.org/vlc/.
3) Clone this repo, unzip it if it's zipped.
4) In the repo files, edit the jukebox.cfg file. Change the "music_root_folder=" entry so it points to your music library.
5) Run it from the command line: "python3 jukebox.py" or "python.exe jukebox.py"

Your music library:
It should be organized like an iTunes library. That is, directory structure should be my_music/some_artist/some_album/some_songs.mp3. mp3's and m4a's will work. m4p's (which require DRM to play) will be ignored. The music is sorted from the music files metadata. The metadata can be a bit wonky, and that will cause trouble or confusion in navigating. For instance, Daft Punk could be tagged as 'french disco', which is a problem if you're expecting it to show up in 'electronica'.
To palliate this kind of problem, Deco Jukebox offers some features: custom genres, and genre assignments. Have a look at the "user_classifications" folder contents and the 'readme' in there. The second method consists in brute-forcing the metadata. A crude tool for this is "hard_remap_genres.py",
which is included in the project. One has to change the target directory path and de-comment the lines that change things and save the changes. I suggest using this on an album-to-album or artist-to-artist basis. Just don't put your library as the top path. Brute-forcing is not undoable.

Genres:
The 'genre' buttons are specified in "jukebox.cfg" (the "genres_list" item). I recommend not exceeding nine genres in the list. If you exceed this number, on the 1600x900 resolution you will start losing buttons. All of these genres can be custom genres, all you have to do is create a list of sub-genres and throw it in the user_classifications/genres/ folder. Any song that *matches* the genre or sub-genre therein will show up when that genre button is lit. See the readme in "user_classifications" for more details.

Album covers:
Once you've set your music library path, run 'discogs_album_cover_scraper.py' to retrieve at least some of the album art. The album art lives in graphics/album_covers/ and should be png format. File names need to match the album title as it is found in the music files metadata for that album (which can differ from the directory name). It is assumed all album titles are unique, and has not posed a problem for me except for 'Greatest Hits' which is all too common. Solution for that would be to force unique album titles in the metadata. I just let it ride.

Font:
The font that gives this jukebox its art-deco look is called 'Lavoir' and can be found here:
https://fontlibrary.org/en/font/lavoir
If this font is not installed (on Linux this means at root level), then the jukebox should default to one of the obvious fonts. But it won't look as cool.

Windows / Linux:
Deco Jukebox works in both. Note Windows and Linux paths use different slashes ("\" vs "/" respectively).

Raspberry pi:
Works on a Raspberry pi 5 running Ubuntu. Currently testing for raspberry os. The only weird difference is that the album cover art png's MUST have with RGBA channels. The scraper does take care of that, but if you're supplementing the album cover art yourself, you have to add an alpha channel to the image or the jukebox will crash.

If you enjoy this project, consider buying me a coffee: https://buymeacoffee.com/patrickdumais

Patrick Dumais
patatorre "at" proton.me