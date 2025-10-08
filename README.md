# movie_viewer

This program will make it easy, accessable and fun to watch movies and shows localy by scaning given movie/show folders and connecting to imdb

## Usage Notes

The program is only supported on windows as of now

The program takes a little to scrape information about a movie/show when it first loads it, give it a little time

It is also recommanded that you use this program along with VLC media player, other media players might somewhat work but are not supported currently

## Setup

### Folder Setup

The program expects your files to be saved in a certain way, so make sure you are saving all your file correctly to avoid issues.

#### Movie / Show folders

The program needs your movie and shows to be saved in different folders, make sure you have folders with only movies and folders with only shows

#### File names

The program will search imdb using the filenames just as they are, make sure you rename your files accordinly otherwise the program might find junk and link it to your movie

#### Scanning for movies

When the program scans for movies it'll do it **recursivly** - that means that whatever folder you set up for movies could have subfolders with more movies in them and the program will find it :)

Sometimes you'll have a movie split into multiple files, or a movie and a subtitles file, in which case you can put it in a folder and make sure the folder name starts with the '-' charecter, that'll tell the program to **not recursivly search it** and instead **tread the whole folder as a single movie**

Example: say I have the movie **Memento** and a sub file, I will put it in folder and name it **"-Memento"**

#### Scanning for shows

Show scanning is the reverse of movies, the program **does not search for shows recursivly**

If you do what the program to search recursivly on a single folder, make that folder start with the '-' charecter

Example: Say I want the program to have all my star wars shows on a single folder, and have the program search it recursivly, I will put all my star wars show folders in folder called **"-Star Wars"**

### Program Setup

Download and open the program, once you do go to the settings and while on either 'Movies' or 'Shows' click on "Add Folder" and add your movie/show folder to the list.

When you close out of the settings menu it should scan those folders, and scrape info about them. Give it a little time.

### Configuration

When opening the folder for the first time, go to the settings and configure the folders where you save your movies and shows.

## Settings

Using the settings menu you can do several things:

- configure the movie / show folders
- configure the default playing speed
- configrue the media player being used
- open the cache folder

### Media player notes

As mentioned before the program currently only supports VLC Media player currently, and for the program to work as intended the media player setting needs to point to the actual VLC .exe file - if it doesn't by default, make sure to set it manually

## How to play

To play a movie or an episode of a show, you can just click it to play on default settings or right click it and press "Play" to play with one-time settings (such as increased speed just this once)

## Playing movies

If a movie is a media file the program will just play it.

If a movie is a folder containing multilple meida files, the program will play them one after the other.

If a movie is a folder containing a single media file and a single subtitle file, the program will the media file with the subtitle file.

If a movie is a folder containing a single media file and multile subtitle files, the program will search for a subtitle file with the same filename as the movie, and if it exists will play them together.

## Playing shows

Shows are assumed to be folder, the program will play each time a single media file (that should be an episode).

When playing a file the program moves it into a subfolder called "watched" which will contain all the watched episodes so far.

The program will choose the episode to play based on it's name, trying to find the earliest unwached episode. Note that this algorithm isn't perfect and sometimes makes mistakes and opens the wrong file.

To make it easy for the program to choose a file try and name all episodes just the episode number or in S?E? format and have all episodes the same kind of files (all .mkv for example)

## Shows length notes

The amount of episodes the program says a show has is taken from imdb (not what you downloaded), and may not be accurate.

## Deletion notes

When deleting a movie or wached episodes using the program, those will not move to the recycle bin. They are just gone.

## Offline notes

If you open the programs without internet connection, the program cannot get info about your movies/shows that are not already in the cache. When you regain connection agian right click that movie/show and click "Reload" for the program to load that movie agian
