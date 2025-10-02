import sys
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import pandas as pd

# === CONFIG ===
CLIENT_ID = "YOUR_CLIENT_ID"
CLIENT_SECRET = "YOUR_CLIENT_SECRET"
REDIRECT_URI = "http://localhost:8888/callback"
SCOPE = "playlist-read-private user-library-read playlist-read-collaborative"

# === AUTHENTICATION ===
sp = spotipy.Spotify(auth_manager=SpotifyOAuth(
    client_id=CLIENT_ID,
    client_secret=CLIENT_SECRET,
    redirect_uri=REDIRECT_URI,
    scope=SCOPE
))

# === DETERMINE SOURCE ===
playlist_id = sys.argv[1] if len(sys.argv) > 1 else None

tracks = []
if playlist_id:
    print(f"Exporting playlist: {playlist_id}")
    results = sp.playlist_tracks(playlist_id, limit=100)
else:
    print("Exporting Liked Songs...")
    results = sp.current_user_saved_tracks(limit=50)

# === COLLECT TRACKS ===
while results:
    for item in results["items"]:
        track = item["track"]
        if track and track["id"]:
            tracks.append({
                "id": track["id"],
                "name": track["name"],
                "artist": ", ".join(a["name"] for a in track["artists"]),
                "album": track["album"]["name"],
                "release_date": track["album"]["release_date"]
            })
    if results["next"]:
        results = sp.next(results)
    else:
        results = None

# === GET AUDIO FEATURES ===
ids = [t["id"] for t in tracks]
features = []
for i in range(0, len(ids), 50):
    batch = ids[i:i+50]
    audio = sp.audio_features(batch)
    features.extend(audio)

# === MERGE AND EXPORT ===
df_tracks = pd.DataFrame(tracks)
df_features = pd.DataFrame(features)
df = df_tracks.merge(df_features, on="id")

output_file = "spotify_playlist_export.csv"
df.to_csv(output_file, index=False)

print(f"✅ Export completed: {output_file}")
