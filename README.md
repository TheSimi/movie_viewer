# movie_viewer

This program will make it easy, accessable and fun to watch movies and shows localy by scaning given movie/show folders and connecting to imdb

## Usage Notes

The program is only supported on windows as of now

The program takes a little time to scrape information from imdb about a movie/show when it first loads it. After intial loading, everything should be cached and loading should be quick.

It is recommanded that you use this program along with VLC media player, other media players might somewhat work but are not supported currently

## Setup

### Folder and files setup Setup

The program expects your files to be saved in a certain way when it scrapes your folders, so make sure you are saving all your file correctly to avoid issues.

#### Movie / Show folders

The program needs your movie and shows to be saved **seperatly**, make sure you have dedicated folders with either only movies or only shows

#### File names

The program will search imdb using the filenames, make sure you rename your files accordinly otherwise the program might find junk and link it to your movie / show.

It is best to just name your file as the movie / show name (e.g "Interstellar") or the name and the year the movie / show came out (e.g "Interstellar 2014")

#### Scanning for movies

When the program scans for movies it'll do it **recursivly** - that means that whatever folder you set up for movies could have subfolders with more movies in them and the program will find it.

Folders with names that start with the '-' charecter won't be searched inside, and will instead be treated as a single movie. This is useful if you have a movie split into multiple file, or a movie with a seprate subtitles file. Make sure to name it accordingly.

Example: I have the movie Interstellar and a seprate subtitle file, I could place them inside their own folder, and name that folder "-Interstellar". The program will then treat that whole folder as one movie.

#### Scanning for shows

Show scanning is kinf of the reverse of movie scanning, the program **does not search for shows recursivly**. The program expects by default that each folder in your show folder is **a single show** and won't search it for subfolder.

But just like with movie scanning, you can name any folder starting with a '-' to make an exception, and the program will search that folder recursivly.

Example: Say I want the program to have all my star wars shows on a single folder, and have the program search it recursivly, I will put all my star wars show folders in folder called **"-Star Wars"** and inside it make multiple subfolders: **Andor**, **The Mandalorian** etc.

### Program Setup

Download the program `.zip` file, put it somewhere and unzip it. Open the `.exe` file in there to start the program.

Once you open it, go to the settings and while on either `Movies` or `Shows` click on `Add Folder` and select to your movie/show folder to the list to scan.

When you close out of the settings menu, it should save your chagnes and start scanning those folders, and get info about them from the web. Give it some time to load.

### Wrong Search Results

Sometimes the search will get something wrong, and another movie will be found then what you wanted (for example, naming your show "one piece" could either pull the live action netflix version or the original anime).

If the program got some search wrong, right click that movie /show and press `Search Matches`. The program will re-seach that movie / show using the file name, allowing you to see all the results it got and choose the right one.

## Settings

Using the settings menu you can do several things:

- configure the movie / show folders
- configure the default playing speed
- configrue the media player being used
- open the cache folder

Most settings are saved to a `config.json` file upon closing the program. If you don't have one yet, the program should automatically create one when you open/close it.

### Media player notes

As mentioned before, the program currently only supports VLC Media player, and for the program to work as intended the media player setting needs to point to the actual VLC `.exe` file - if it doesn't by default, make sure to set it manually.

Non VLC players may work, but will surely be missing features. To try another player simply make the media player setting point to that player's `.exe` file

### Cache notes

The cache is stored on the `LOCALAPPDATA` folder, under `movie_viewer\.cache`.

## How to play

To play a movie or an episode of a show, you can just click it to play on default settings, or right click it and press `Play` to play with one-time settings (such as increased different speed then the default)

## Playing movies

If a movie is a media file the program will simply play that file, nothing more there.

If the program is not a file, but rather a folder (named starting with a '-') the program will act differently.

* **If you're not using VLC**, it'll simply open the folder with the file explorer.
* **If the folder contains multilple media files**, the program will try to figure out what order they should be played and play them on after the other using a VLC playlist.
* **If the folder contains a single media file & a single subtitle file**, the program will play the media file with the subtitle file.
* **If the folder contains a single media file and multile subtitle files**, the program will search for a subtitle file with the same filename as the movie, and if it exists will play them together.
* **For anything else**, the program will simply open the folder with file explorer for you

## Playing shows

Shows are assumed to be folder, and when you click to play the program will play a single media file from that folder (that should be a single episode).

When playing a file the program moves it into a subfolder called `watched` which will contain all the watched episodes so far. Media files in that `watched` folder will be ignored.

The program will choose the episode to play based on it's name, trying to find the earliest unwached episode. Note that this isn't perfect and sometimes makes mistakes and opens the wrong file if the names are in some wierd or non-consistant format.

To make it easy for the program to choose a file try and name all episodes with just the episode number (e.g "1.mkv") or in S_E_ format (e.g "S1E1.mkv"). At the very least, make sure you use a consistent format.

## Deletion notes

When deleting a movie or wached episodes using the program, those **will not move to the recycle bin**. They are just gone.

## Offline notes

If you open the programs without internet connection, the program cannot get info about your movies/shows that are not already in the cache. When you regain connection agian right click that movie/show and click "Reload" for the program to load that movie agian.

If all your movies / shows are already cached, the program should work just fine.

## Development notes

The program is made using these tools:
* **Python** - the main language
* **UV** - the package manager of choice
* **pyqt6** - the GUI framework
* **pyinstaller** - to make the program into an easy to use `.exe` file
* **pillow** - for image loading and editing
* **requests** - to fetch info about media from the web
* **ruff** - for linting

The program also uses some free-to use open APIs that don't require keys, these are:
* **FM-DB API** - default api for movie info. [website](https://imdb.iamidiotareyoutoo.com) [documentation](https://imdb.iamidiotareyoutoo.com/docs/index.html)
* **FM-DB API** - default api for movie info. [website](https://imdb.iamidiotareyoutoo.com) [documentation](https://imdb.iamidiotareyoutoo.com/docs/index.html)
* **TV Maze** - default api for show info (except for rating). [website](https://www.tvmaze.com) [documentation](https://www.tvmaze.com/api)
* **Imdb Dev** - default for show rating and fallback for everything else. [documentation](https://imdbapi.dev)

### Running localy

Make sure you have uv installed:

```
pip install uv
```

Clone the repository, then download dependecies and run:

```
uv sync

uv run main.py
```

### Building localy

Simply clone the repository, open it on `cmd` and run either one of those (or replace `.bat` with `.ps1` to run in powershell):
```
scripts/build_dev.bat
```
```
scripts/build_prd.bat
```

The dev script is just a little different, and builds a `.exe` where you can see the console and logs for yourself.

## Future additions

* GUI improvments
* Using libVLC
* Pydantic validations
* Scraping from imdb as fallback
* Additional settings
* Smarter cache
* Better error handling
* Much more...
