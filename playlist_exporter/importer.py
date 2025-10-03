import sys
import os
import pandas as pd
import spotipy
from spotipy.oauth2 import SpotifyOAuth

# === CONFIG ===
CLIENT_ID = os.environ.get("SPOTIFY_CLIENT_ID")
CLIENT_SECRET = os.environ.get("SPOTIFY_CLIENT_SECRET")
REDIRECT_URI = os.environ.get("SPOTIFY_REDIRECT_URI")
SCOPE = "playlist-modify-public playlist-modify-private"

sp = spotipy.Spotify(auth_manager=SpotifyOAuth(
    client_id=CLIENT_ID,
    client_secret=CLIENT_SECRET,
    redirect_uri=REDIRECT_URI,
    scope=SCOPE
))

# === ARGUMENTOS ===
if len(sys.argv) < 2:
    print("❌ Por favor pasa el nombre de la playlist (CSV sin extensión) como parámetro")
    sys.exit(1)

playlist_name_param = sys.argv[1]
csv_path = os.path.join("exports", f"{playlist_name_param}.csv")

if not os.path.exists(csv_path):
    print(f"❌ No se encontró el archivo: {csv_path}")
    sys.exit(1)

# === LEER CSV ===
df = pd.read_csv(csv_path)
track_ids = df["id"].dropna().tolist()

if not track_ids:
    print("❌ No hay tracks en el CSV")
    sys.exit(1)

# === CREAR PLAYLIST EN SPOTIFY ===
user_id = sp.current_user()["id"]
playlist_name_spotify = playlist_name_param.replace("_", " ")  # limpieza mínima
playlist = sp.user_playlist_create(user=user_id, name=playlist_name_spotify, public=True)
print(f"✅ Playlist creada en Spotify: {playlist_name_spotify}")

# === AÑADIR TRACKS EN BATCHES DE 100 ===
for i in range(0, len(track_ids), 100):
    batch = track_ids[i:i+100]
    sp.playlist_add_items(playlist_id=playlist["id"], items=batch)
    print(f"✅ Añadidos tracks {i+1} a {i+len(batch)}")

print("🎉 Playlist completa!")
