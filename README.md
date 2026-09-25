# movie_viewer

This program makes it easy, accessible, and fun to watch locally stored movies and shows by scanning your movie/show folders and matching them with IMDb.

## Usage Notes

The program is only supported on Windows as of now.

Loading a movie/show for the first time takes a little while because info is fetched from the web. After the initial load, everything is cached and loading should be quick.

It is recommended to use this program along with VLC media player. Other media players might partially work but are not currently supported.

A Chrome / Edge / Helium installation is required, since IMDb info is scraped with a headless browser (Selenium). Make sure one of them is installed and up to date.

## Setup

### Folder and file setup

The program expects your files to be saved in a certain way when it scans your folders, so make sure you save everything correctly to avoid issues.

#### Movie / show folders

The program needs your movies and shows to be saved **separately**. Make sure you have dedicated folders containing only movies or only shows.

#### File names

The program searches IMDb using the file names, so rename your files accordingly, otherwise it might match the wrong title.

It is best to name your file as just the movie / show name (e.g. `Interstellar`) or the name plus the release year (e.g. `Interstellar 2014`).

#### Scanning for movies

When the program scans for movies it does so **recursively** - whatever folder you configure for movies may contain subfolders with more movies and the program will find them.

Folders with names starting with the `-` character won't be searched inside, and will instead be treated as a single movie. This is useful if you have a movie split into multiple files, or a movie with a separate subtitle file. Make sure to name it accordingly.

Example: I have the movie Interstellar plus a separate subtitle file. I can place them inside their own folder named `-Interstellar`, and the program will treat that whole folder as one movie.

#### Scanning for shows

Show scanning is kind of the reverse of movie scanning: the program **does not search for shows recursively**. By default it expects each folder inside your show folder to be **a single show**, and won't look for subfolders inside it.

Just like with movie scanning, you can name a folder starting with `-` to make an exception, and the program will search that folder recursively.

Example: say I want all my Star Wars shows under a single folder and have the program search it recursively. I'll put all my Star Wars show folders inside a folder called `-Star Wars`, with subfolders like `Andor`, `The Mandalorian`, etc.

### Program setup

Download the program `.zip` file, put it somewhere and unzip it. Open the `.exe` file inside to start the program.

Once open, go to settings and, while on either `Movies` or `Shows`, click `Add Folder` and add your movie/show folder to the list.

When you close the settings menu it should save your changes and start scanning those folders, fetching info about them from the web. Give it some time to load.

### Wrong search results

Sometimes the search gets it wrong and matches a different title than the one you wanted (for example, naming your show `One Piece` could match either the live-action Netflix version or the original anime).

If the program matched the wrong title, right click that movie / show and press `Search Matches`. The program will re-search using the file name, showing all results so you can pick the right one.

## Settings

Using the settings menu you can:

- configure the movie / show folders
- configure the default playing speed
- configure the media player being used
- open the cache folder

Most settings are saved to a `config.json` file when the program closes. If you don't have one yet, the program automatically creates one with default values when you open/close it.

### Media player notes

As mentioned above, the program currently only supports VLC media player. The media player setting needs to point to the actual VLC `.exe` file - if it doesn't by default, set it manually.

Non-VLC players may work, but will be missing features. To try another player, simply point the media player setting to that player's `.exe` file.

### Cache notes

The cache is stored in the `LOCALAPPDATA` folder, under `movie_viewer\.cache`.

## How to play

To play a movie or an episode of a show, click it to play with default settings, or right click it and press `Play` to play with one-time settings (such as a different speed than the default).

Right clicking a title also gives you `Details`, `Open in files`, `Reload`, `Search Matches`, and delete options (`Delete movie` / `Delete show` / `Delete watched`). Shows additionally have an `Episodes` view.

## Playing movies

If a movie is a media file, the program will simply play that file.

If the movie is a folder (named starting with `-`), the program acts differently:

* **If you're not using VLC**, it'll simply open the folder with the file explorer.
* **If the folder contains multiple media files**, the program will try to figure out their order and play them one after another using a VLC playlist.
* **If the folder contains a single media file and a single subtitle file**, it will play the media file with that subtitle file.
* **If the folder contains a single media file and multiple subtitle files**, it will look for a subtitle file with the same file name as the movie and play them together if found.
* **For anything else**, it will simply open the folder with the file explorer.

## Playing shows

Shows are assumed to be folders. Clicking play will play a single media file from that folder (a single episode).

When playing a file, the program moves it into a subfolder called `watched`, which holds all watched episodes so far. Media files in `watched` are ignored when picking the next episode.

The program picks the episode to play based on its name, trying to find the earliest unwatched episode. This isn't perfect and can pick the wrong file if names use a weird or inconsistent format.

To make picking reliable, name episodes with just the episode number (e.g. `1.mkv`) or in season/episode format (e.g. `S1E1.mkv`). At the very least, use a consistent format.

You could also play a specific episode, mark episodes as watched / unwached and more by right clicking a show and opening the `Episodes` menu.

## Deletion notes

When deleting a movie or watched episodes using the program, they **will not move to the recycle bin**. They are just gone.

## Offline notes

If you open the program without an internet connection, it cannot fetch info for movies/shows that aren't already cached. Once you're back online, right click that movie/show and click `Reload` to load it again.

If all your movies / shows are already cached, the program should work just fine offline.

## Data sources

The program fetches info from these sources:

* **Official IMDb website** - the default source for movie and show info, scraped directly from [imdb.com](https://www.imdb.com) with a headless Chrome/Edge browser via Selenium. This is also where posters and ratings come from.
* **Wikidata** - fallback source for movie info when IMDb scraping fails. [website](https://www.wikidata.org) [documentation](https://www.wikidata.org/wiki/Wikidata:Data_access)
* **TV Maze** - fallback source for show info when IMDb scraping fails. Show search starts with TV Maze because a single lookup returns both the TV Maze id and the IMDb id. [website](https://www.tvmaze.com) [documentation](https://www.tvmaze.com/api)

Only IMDb ratings are ever shown. When a fallback source is used, the rating is left at `0` instead of showing a non-IMDb rating.

## Development notes

The program is made using these tools:

* **Python** - the main language
* **UV** - the package manager of choice
* **PyQt6** - the GUI framework
* **PyInstaller** - to bundle the program into an easy to use `.exe` file
* **Pillow** - for image loading and editing
* **Requests** - to fetch info about media from the web
* **Selenium** - to scrape info from IMDb in a headless browser
* **BeautifulSoup4 / lxml** - to parse scraped IMDb pages
* **Ruff** - for linting
* **mypy** - for static type checking
* **pre-commit** - for running lint and typing checks on commits

### Running locally

Make sure you have uv installed:

```
pip install uv
```

Clone the repository, then download dependencies and run:

```
uv sync

uv run main.py
```

Before committing any changes, it is recommended that you also run:

```
uv run pre-commit install
```

### Building locally

Clone the repository, open it in `cmd` and run either one of these (replace `.bat` with `.ps1` to run in PowerShell):

```
scripts/build_dev.bat
```

```
scripts/build_prd.bat
```

The dev script is only slightly different: it builds an `.exe` where you can see the console and logs.

#### Building script flow

1. downloading / verifying download of uv via pip
2. downloading / syncing dependencies via uv
3. removing old build and dist folders if they exist
4. using pyinstaller to build the `.exe` into the `dist/movie_viewer/` folder
5. copying `config.json` if it exists into the `dist/movie_viewer/_internal/` folder

## Future additions

* GUI improvements
* Adding a movie or show via the program itself
* Pydantic validations
* Additional settings
* Smarter cache
* Tests
* Bug fixes
* Much more...

See issues in the github repository
