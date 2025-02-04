import requests
import os
import time
import shutil
import subprocess
from tqdm import tqdm
import keyboard

# TMDB API key (replace with your own)
TMDB_API_KEY = "ff7f21fbe33f56dc1eeae78455e3159d"

# Base URL for TMDB API
TMDB_API_URL = "https://api.themoviedb.org/3"

# Path to MakeMKV executable (update this for your system)
MAKEMKV_PATH = r"C:\Program Files (x86)\MakeMKV\makemkvcon.exe"

# Path to HandBrake CLI executable (update this for your system)
HANDBRAKE_PATH = r"C:C:\Program Files\HandBrake\HandBrakeCLI.exe"

# Rate limiting: TMDB allows 40 requests every 10 seconds
REQUEST_DELAY = 0.25  # Delay between API requests (in seconds)

# Global variable to control pausing
paused = False

def toggle_pause():
    global paused
    paused = not paused
    if paused:
        print("\nPausing process...")
    else:
        print("\nResuming process...")

# Register key listeners
keyboard.add_hotkey('ctrl+p', toggle_pause)

def search_movie(title):
    """Search for a movie by title using the TMDB API."""
    endpoint = f"{TMDB_API_URL}/search/movie"
    params = {
        "api_key": TMDB_API_KEY,
        "query": title,
        "include_adult": "false"
    }
    try:
        response = requests.get(endpoint, params=params)
        response.raise_for_status()  # Raise an error for bad status codes
        results = response.json().get("results", [])
        return results[0] if results else None
    except requests.exceptions.RequestException as e:
        print(f"Error searching for movie '{title}': {e}")
        return None

def search_tv_show(title):
    """Search for a TV show by title using the TMDB API."""
    endpoint = f"{TMDB_API_URL}/search/tv"
    params = {
        "api_key": TMDB_API_KEY,
        "query": title,
        "include_adult": "false"
    }
    try:
        response = requests.get(endpoint, params=params)
        response.raise_for_status()  # Raise an error for bad status codes
        results = response.json().get("results", [])
        return results[0] if results else None
    except requests.exceptions.RequestException as e:
        print(f"Error searching for TV show '{title}': {e}")
        return None

def get_media_details(media_type, media_id):
    """Get detailed metadata for a movie or TV show by its TMDB ID."""
    endpoint = f"{TMDB_API_URL}/{media_type}/{media_id}"
    params = {
        "api_key": TMDB_API_KEY,
        "append_to_response": "credits,videos"  # Optional: Add more details
    }
    try:
        response = requests.get(endpoint, params=params)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching details for {media_type} ID {media_id}: {e}")
        return None

def rename_media_file(file_path, metadata, media_type, output_dir=None):
    """
    Rename or copy a media file based on TMDB metadata without overwriting existing files.
    If `output_dir` is specified, files are copied to the new directory. Otherwise, they are renamed in place.
    """
    if not metadata:
        print("No metadata found. Skipping file.")
        return

    # Define the output directory (if not specified, use the input directory)
    if output_dir is None:
        output_dir = os.path.dirname(file_path)
    os.makedirs(output_dir, exist_ok=True)  # Create the directory if it doesn't exist

    title = metadata.get("title" if media_type == "movie" else "name", "Unknown")
    release_year = (
        metadata.get("release_date", "").split("-")[0]
        if media_type == "movie"
        else metadata.get("first_air_date", "").split("-")[0]
    )
    base_name = f"{title} ({release_year}).mkv" if release_year else f"{title}.mkv"
    new_file_path = os.path.join(output_dir, base_name)

    # Check if the file already exists and make the name unique if necessary
    counter = 1
    while os.path.exists(new_file_path):
        name, ext = os.path.splitext(base_name)
        new_file_path = os.path.join(output_dir, f"{name} ({counter}){ext}")
        counter += 1

    try:
        if output_dir == os.path.dirname(file_path):
            # Rename the file in place
            os.rename(file_path, new_file_path)
            print(f"Renamed '{os.path.basename(file_path)}' to '{os.path.basename(new_file_path)}'")
        else:
            # Copy the file to the new directory
            shutil.copy(file_path, new_file_path)
            print(f"Copied and renamed '{os.path.basename(file_path)}' to '{os.path.basename(new_file_path)}'")
    except OSError as e:
        print(f"Error processing file '{file_path}': {e}")

def rip_movie(output_dir):
    """Rip the movie from the optical drive using MakeMKV."""
    print("Ripping movie from optical drive...")
    command = [
        MAKEMKV_PATH, "mkv", "disc:0", "all", output_dir
    ]
    try:
        # Run MakeMKV and display a progress bar
        with tqdm(total=100, desc="Ripping Progress", unit="%") as pbar:
            process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True, bufsize=1)
            for line in iter(process.stdout.readline, ''):
                print(line, end="")  # Print MakeMKV output to the console
                if paused:
                    print("Process paused. Press Ctrl+P to resume.")
                    while paused:
                        time.sleep(1)
                if "PRGV" in line:  # MakeMKV progress lines contain "PRGV"
                    progress = int(line.split(",")[1])  # Extract progress percentage
                    pbar.n = progress
                    pbar.refresh()
            process.stdout.close()
            process.wait()
        print("Ripping complete.")
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error ripping movie: {e}")
        return False

def compress_movie(input_file, output_file):
    """Compress the movie using HandBrake CLI."""
    print(f"Starting compression for: {input_file}")
    print(f"Compressing {input_file}...")
    command = [
        HANDBRAKE_PATH,
        "-i", input_file,
        "-o", output_file,
        "--preset", "Fast 1080p30"  # Adjust preset as needed
    ]
    try:
        # Run HandBrake and display a progress bar
        with tqdm(total=100, desc="Compression Progress", unit="%") as pbar:
            process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True, bufsize=1)
            for line in iter(process.stdout.readline, ''):
                if paused:
                    print("Process paused. Press Ctrl+P to resume.")
                    while paused:
                        time.sleep(1)
                if "Encoding" in line and "%" in line:  # HandBrake progress lines contain "Encoding" and "%"
                    progress = float(line.split(" ")[-1].replace("%", ""))  # Extract progress percentage
                    pbar.n = progress
                    pbar.refresh()
            process.stdout.close()
            process.wait()
        print(f"Compression complete. Output: {output_file}")
    except subprocess.CalledProcessError as e:
        print(f"Error compressing movie: {e}")

def process_media_directory(staging_dir, movie_folder):
    """
    Process all media files in the staging directory, identifying the main movie file and moving extras.
    All files are stored in a folder named after the main movie title.
    """
    # Get a list of all MKV files in the staging directory
    mkv_files = [f for f in os.listdir(staging_dir) if f.endswith(".mkv")]

    if not mkv_files:
        print("No MKV files found in the directory.")
        return

    # Identify the main movie file (largest file by size)
    main_file = max(mkv_files, key=lambda f: os.path.getsize(os.path.join(staging_dir, f)))
    print(f"Main movie file identified: {main_file}")

    # Create a 'Behind the Scenes' directory for extras
    behind_the_scenes_dir = os.path.join(movie_folder, "Behind the Scenes")
    os.makedirs(behind_the_scenes_dir, exist_ok=True)

    # Process each file
    for file in mkv_files:
        file_path = os.path.join(staging_dir, file)

        if file == main_file:
            # Process the main movie file
            print(f"\nProcessing main movie file: {file}")
            new_file_path = os.path.join(movie_folder, file)
            shutil.move(file_path, new_file_path)
            print(f"Moved and renamed '{file}' to '{new_file_path}'.")

            # Compress the main movie file
            compressed_file = os.path.join(movie_folder, f"compressed_{file}")
            compress_movie(new_file_path, compressed_file)
        else:
            # Move extras to the 'Behind the Scenes' directory
            new_file_path = os.path.join(behind_the_scenes_dir, file)
            try:
                shutil.move(file_path, new_file_path)
                print(f"Moved '{file}' to 'Behind the Scenes' directory.")
            except OSError as e:
                print(f"Error moving file '{file}': {e}")

def main():
    # Directory to save ripped files
    base_output_dir = r"D:\Plex Ripper_Converter\media"
    staging_dir = os.path.join(base_output_dir, "staging")

    # Create the staging directory
    os.makedirs(staging_dir, exist_ok=True)
    print(f"Created staging directory: {staging_dir}")

    # Step 1: Rip the movie from the optical drive
    print("Starting the ripping process...")
    if not rip_movie(staging_dir):
        print("Ripping failed. Exiting.")
        return  # Stop if ripping fails

    # Step 2: Identify the main movie file
    print("Identifying the main movie file...")
    mkv_files = [f for f in os.listdir(staging_dir) if f.endswith(".mkv")]
    if not mkv_files:
        print("No MKV files found in the directory.")
        return

    # Assume the largest file is the main movie
    main_file = max(mkv_files, key=lambda f: os.path.getsize(os.path.join(staging_dir, f)))
    main_movie_title = os.path.splitext(main_file)[0]  # Use the filename as the title
    print(f"Main movie file: {main_file}")

    # Step 3: Fetch movie details from TMDB
    print("Fetching movie details from TMDB...")
    movie_details = search_movie(main_movie_title)
    if not movie_details:
        print(f"Could not find details for movie: {main_movie_title}. Trying TV show search.")
        movie_details = search_tv_show(main_movie_title)
        if not movie_details:
            print(f"Could not find details for TV show: {main_movie_title}")
            return

    # Extract title and release year from the TMDB response
    title = movie_details.get("title" if "title" in movie_details else "name", "Unknown")
    release_year = movie_details.get("release_date" if "release_date" in movie_details else "first_air_date", "").split("-")[0]
    movie_folder_name = f"{title} ({release_year})" if release_year else title
    print(f"Movie folder name: {movie_folder_name}")

    # Create a folder named after the TMDB title and release year
    movie_folder = os.path.join(base_output_dir, movie_folder_name)
    os.makedirs(movie_folder, exist_ok=True)
    print(f"Created movie folder: {movie_folder}")

    # Step 4: Process the ripped files
    print("Processing the ripped files...")
    process_media_directory(staging_dir, movie_folder)

    # Step 5: Delete the staging directory
    print("Deleting the staging directory...")
    shutil.rmtree(staging_dir)
    print(f"Deleted staging directory: {staging_dir}")

if __name__ == "__main__":
    main()