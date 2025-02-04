# Plex Ripper & Converter

This program automates the process of ripping movies from optical drives, fetching metadata from TMDB, renaming files, and compressing them for use with Plex.

## Features

- Rip movies from optical drives using MakeMKV.
- Fetch movie and TV show metadata from TMDB.
- Rename or copy media files based on TMDB metadata.
- Compress movies using HandBrake CLI.
- Organize media files into folders named after the movie title and release year.
- Pause and resume the ripping and compression process using `Ctrl+P`.

## Requirements

- Python 3.x
- MakeMKV
- HandBrake CLI
- `requests` library
- `tqdm` library
- `keyboard` library

## Installation

1. Install Python 3.x from [python.org](https://www.python.org/).
2. Install MakeMKV from [makemkv.com](https://www.makemkv.com/).
3. Install HandBrake CLI from [handbrake.fr](https://handbrake.fr/).
4. Install the required Python libraries:
    ```sh
    pip install requests tqdm keyboard
    ```

## Configuration

1. Update the `MAKEMKV_PATH` and `HANDBRAKE_PATH` variables in `rip_n_compress.py` to point to the MakeMKV and HandBrake CLI executables on your system.
2. Replace the `TMDB_API_KEY` variable with your own TMDB API key.

## Usage

1. Place a movie disc in your optical drive.
2. Run the script:
    ```sh
    python rip_n_compress.py
    ```
3. The script will:
    - Rip the movie from the optical drive.
    - Identify the main movie file.
    - Fetch movie details from TMDB.
    - Rename and organize the media files.
    - Compress the main movie file.
4. Use `Ctrl+P` to pause and resume the ripping and compression process.

## Notes

- Ensure that the optical drive is properly connected and recognized by your system.
- The script assumes that the largest MKV file in the staging directory is the main movie file.
- The script will create a folder named after the movie title and release year in the output directory.