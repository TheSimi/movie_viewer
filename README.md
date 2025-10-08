# movie_viewer

This program will make it easy, accessable and fun to watch movies and shows that you downloaded onto your PC

## Usage

When using for the first time the program and files might need some tweaking to work properly.

It is also recommanded that you use this program along with VLC media player, so download that if you don't have it already.

### Configuration

When opening the folder for the first time, go to the settings and configure the folders where you save your movies and shows.

### File names

The script uses file names to search on imdb, that means that in order for the program to work as intended you need to rename your movie files and show folders so that searching that term on imdb will result in the corresponding movie.

The script will also attempt to realise when running a show what the current episode is, so try and make it as easy to realise, best practice will be to save each episode as just a number.

There are special ways to name files so that the program will treat them differently:

For movies, if a movie is saved as more than one file or a file with subtitles, make a folder for it and have it's name start with a "-". Example: `-memento`. If there is a subtitle file, make the right one the same name as the video file. If there are more than one file that should be played in a row, make it as easy to understant the order as in shows.

For shows, unlike movies, they are folders by default and not files. if there is an internal folder with more shows on it, that isn't a show by itself, make that folder name start with a "-" to make the program recursivly search it. Example: `-star wars shows`

### Cache

The program will save things in a cache for easy loading when you later reopen the program. You can open the cache folder either from the settings menu or in your `C:\Users\<your user>\AppData\Local\movie_viewer` folder

### Usage

If you've done everything correctly, it should just work by running the .exe file or the `main.py` file.

Some of the setting you configured will be saved on a `.env` file that will be created automatically, make sure you don't delete it otherwise some settings will reset and need to be reconfigured