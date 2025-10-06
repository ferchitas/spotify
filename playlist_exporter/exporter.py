import sys
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import pandas as pd
import os
import re
import time
from collections import defaultdict

# === CONFIG ===
CLIENT_ID = os.environ.get("SPOTIPY_CLIENT_ID")
CLIENT_SECRET = os.environ.get("SPOTIPY_CLIENT_SECRET")
REDIRECT_URI = os.environ.get("SPOTIPY_REDIRECT_URI")
SCOPE = "playlist-read-private user-library-read playlist-read-collaborative"
EXPORT_FOLDER = "exports"

# === CREATE EXPORT FOLDER ===
os.makedirs(EXPORT_FOLDER, exist_ok=True)

# === AUTHENTICATION ===
sp = spotipy.Spotify(auth_manager=SpotifyOAuth(
    client_id=CLIENT_ID,
    client_secret=CLIENT_SECRET,
    redirect_uri=REDIRECT_URI,
    scope=SCOPE
))

# === HELPER FUNCTIONS ===
def assign_genre_scores(genres_list):
    """Assign a 'upbeat' score to each genre (0-1). Adjust as needed."""
    score_map = {
        "edm": 1.0,
        "dance": 0.9,
        "pop": 0.8,
        "hip hop": 0.6,
        "rap": 0.6,
        "reggaeton": 0.1,
        "trap": 0.4,
        "latin": 0.5,
        "rock": 0.7,
        "indie": 0.55,
        "folk": 0.3,
        "country": 0.3,
        "classical": 0.1,
        "jazz": 0.2,
        "blues": 0.2,
        "salsa": 0.6,
        "merengue": 0.5,
        "bachata": 0.6,
        "k-pop": 0.1,
        "reggae": 0.3,
        "metal": 0.9,
        "punk": 0.65,
        "alternative": 0.55,
        "r&b": 0.6,
        "grunge": 0.7,
        "ska": 0.6,
        "funk": 0.7,
        "disco": 0.9,
        "soul": 0.5,
        "gospel": 0.2,
        "ambient": 0.1,
        "new age": 0.7,
        "techno": 1.0,
        "house": 1.0,
        "trance": 1.0,
        "dubstep": 0.9,
        "drum and bass": 0.9,
        "bluegrass": 0.3,
        "punk rock": 0.7,
        "emo": 0.2,
        "post-hardcore": 0.4
        # Add more genres if needed
    }
    scores = [score_map.get(g.lower(), 0.5) for g in genres_list]
    return max(scores) if scores else 0.5

def generate_upbeat_sublist(df, target_minutes):
    """Generate an upbeat sublist keeping genre proportion and target duration."""
    df = df.copy()
    df["duration_min"] = df["duration_ms"] / 60000
    # Calculate genre score
    df["genre_score"] = df["genres"].apply(lambda g: assign_genre_scores(g.split(", ")) if g else 0.5)
    
    # Calculate genre proportions
    genre_counts = defaultdict(int)
    for g_list in df["genres"].dropna():
        for g in g_list.split(", "):
            genre_counts[g] += 1
    
    total_tracks = len(df)
    df["genre_weight"] = df["genres"].apply(
        lambda g: max([genre_counts.get(gen, 1)/total_tracks for gen in g.split(", ")]) if g else 0.5
    )
    
    # Final score = 70% genre, 30% relative duration weight
    df["upbeat_score"] = df["genre_score"] * 0.7 + df["genre_weight"] * 0.3
    
    # Sort by score descending
    df_sorted = df.sort_values("upbeat_score", ascending=False)
    
    # Build sublist until target_minutes
    playlist = []
    total_time = 0
    for _, row in df_sorted.iterrows():
        if total_time + row["duration_min"] <= target_minutes:
            playlist.append(row)
            total_time += row["duration_min"]
        if total_time >= target_minutes:
            break

    sub_df = pd.DataFrame(playlist)
    print(f"✅ Upbeat sub-playlist: {len(sub_df)} songs, {total_time:.1f} minutes")
    return sub_df

# === DETERMINE SOURCE ===
playlist_id = None
target_minutes = None

# Handle arguments safely
if len(sys.argv) == 2:
    # Could be either playlist ID or target minutes
    try:
        target_minutes = int(sys.argv[1])
    except ValueError:
        playlist_id = sys.argv[1]
elif len(sys.argv) >= 3:
    playlist_id = sys.argv[1]
    try:
        target_minutes = int(sys.argv[2])
    except ValueError:
        target_minutes = None

tracks = []
playlist_name = "Liked_Songs"

if playlist_id:
    playlist_info = sp.playlist(playlist_id)
    playlist_name = playlist_info.get("name", playlist_id)
    print(f"Exporting playlist: {playlist_name} ({playlist_id})")
    results = sp.playlist_tracks(playlist_id, limit=100)
else:
    print("Exporting all Liked Songs...")
    results = sp.current_user_saved_tracks(limit=50)

# === COLLECT TRACKS ===
while results:
    for item in results["items"]:
        track = item["track"]
        if track and track.get("id"):
            tracks.append({
                "id": track["id"].strip(),
                "name": track["name"],
                "artist_ids": [a["id"] for a in track["artists"]],
                "artist_names": ", ".join(a["name"] for a in track["artists"]),
                "album": track["album"]["name"],
                "release_date": track["album"]["release_date"],
                "duration_ms": track["duration_ms"]
            })
            print(f"✅ Added track {track['id']}")
    if results.get("next"):
        results = sp.next(results)
    else:
        results = None

# === FETCH ARTIST GENRES IN BATCH ===
artist_ids = set(a_id for t in tracks for a_id in t["artist_ids"])
artist_genres_map = {}
artist_ids = list(artist_ids)
print(f"Fetching genres for {len(artist_ids)} artists...")

for i in range(0, len(artist_ids), 50):
    batch_ids = artist_ids[i:i+50]
    artists_data = sp.artists(batch_ids)["artists"]
    for artist in artists_data:
        artist_genres_map[artist["id"]] = artist.get("genres", [])
    time.sleep(0.1)

# === ASSIGN GENRES TO TRACKS ===
for track in tracks:
    genres_set = set()
    for a_id in track["artist_ids"]:
        genres_set.update(artist_genres_map.get(a_id, []))
    track["genres"] = ", ".join(genres_set) if genres_set else None

# === CLEAN PLAYLIST NAME FOR FILE ===
safe_name = re.sub(r'[^a-zA-Z0-9_-]', '_', playlist_name)

# === EXPORT TO CSV ===
df_tracks = pd.DataFrame(tracks)

# Convert lists to strings for CSV
for col in ['artist_ids', 'genres']:
    if col in df_tracks.columns:
        df_tracks[col] = df_tracks[col].apply(lambda x: '|'.join(x) if isinstance(x, list) else x)

output_file = os.path.join(EXPORT_FOLDER, f"{safe_name}.csv")
df_tracks.to_csv(output_file, index=False)
print(f"✅ Export completed: {output_file}")

# === GENERATE UPBEAT SUBLIST IF TARGET TIME PASSED ===
if target_minutes:
    upbeat_df = generate_upbeat_sublist(df_tracks, target_minutes=target_minutes)
    upbeat_file = os.path.join(EXPORT_FOLDER, f"{safe_name}_upbeat_{target_minutes}min.csv")
    upbeat_df.to_csv(upbeat_file, index=False)
    print(f"🎶 Upbeat playlist exported: {upbeat_file}")
