# Spotify Playlist Exporter & Upbeat Sublist Generator

This Python script allows you to export Spotify playlists or your Liked Songs to CSV, and optionally generate a “high-energy” sublist based on song genres and a target duration.

## Features

- Export any Spotify playlist by ID or your entire Liked Songs collection.
- Fetch song metadata: track ID, name, artists, album, release date, duration, and genres.
- Generate an **upbeat sublist** for running, workouts, or events, maintaining genre proportions while prioritizing “energetic” genres.
- Customizable target duration in minutes for the upbeat sublist.
- Extended genre support including EDM, pop, hip hop, reggaeton, dance, trap, rock, indie, Latin, classical, jazz, and more.
- CSV output stored in an `exports` folder, including both full playlist and upbeat sublist if requested.

## Requirements

- Python 3.8+
- Spotipy (`pip install spotipy`)
- Pandas (`pip install pandas`)
- Spotify account (Premium recommended for full playlist access)
- Spotify developer credentials (client ID, client secret, and redirect URI)

## Setup

1. Create a Spotify application at [Spotify Developer Dashboard](https://developer.spotify.com/dashboard/applications).
2. Set your environment variables:

```bash
export SPOTIPY_CLIENT_ID="your_client_id"
export SPOTIPY_CLIENT_SECRET="your_client_secret"
export SPOTIPY_REDIRECT_URI="http://127.0.0.1:8000/callback"
```

(Windows PowerShell example: `setx SPOTIPY_CLIENT_ID "your_client_id"` etc.)

3. Install required Python packages:

```bash
pip install spotipy pandas
```

## Usage

Run the script with different combinations of parameters:

```bash
# Export Liked Songs only
python exporter.py

# Export a playlist by ID
python exporter.py <playlist_id>

# Export Liked Songs and generate upbeat sublist of 120 minutes
python exporter.py 120

# Export a playlist and generate upbeat sublist of 90 minutes
python exporter.py <playlist_id> 90
```

### Output

- The full playlist is exported as `exports/<playlist_name>.csv`.
- The upbeat sublist (if generated) is exported as `exports/<playlist_name>_upbeat_<target_minutes>min.csv`.

CSV columns:

- `id`: Spotify track ID
- `name`: Track name
- `artist_ids`: Artist IDs (pipe-separated)
- `artist_names`: Artist names
- `album`: Album name
- `release_date`: Album release date
- `duration_ms`: Track duration in milliseconds
- `genres`: Track genres (pipe-separated)
- `duration_min`: Duration in minutes
- `genre_score`: Calculated “energy” score based on genre
- `genre_weight`: Weight of genre proportion in the playlist
- `upbeat_score`: Final score used to generate the sublist

## How it Works

1. Collect tracks from a playlist or Liked Songs.
2. Fetch artist genres in batches to avoid API rate limits.
3. Assign genre-based scores to each track.
4. Calculate a weighted upbeat score for each track.
5. Sort tracks by upbeat score and select enough tracks to match the target duration while maintaining genre proportions.

## Notes

- If no playlist ID is provided, the script defaults to Liked Songs.
- If no target duration is provided, only the full playlist is exported.
- Adjust the `assign_genre_scores` function to tweak the energy weighting of specific genres.

