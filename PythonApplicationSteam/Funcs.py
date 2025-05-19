import requests
import tkinter as tk
from tkinter import messagebox, Scrollbar, Canvas, Frame
from PIL import Image, ImageTk
import io
import os
import threading
import logging
from queue import Queue, Empty

# Steam API key from environment variable
API_KEY = os.getenv('STEAM_API_KEY')
if not API_KEY:
    raise ValueError("STEAM_API_KEY environment variable not set")
# Security: Using environment variable prevents hardcoding sensitive API key.
# Design Rationale: Fail early if key is missing to avoid runtime issues.

def get_owned_games(steam_id):
    """Fetch list of games owned by the user."""
    url = "http://api.steampowered.com/IPlayerService/GetOwnedGames/v1/"
    params = {
        "key": API_KEY,
        "steamid": steam_id,
        "include_appinfo": True,
        "include_played_free_games": True
    }
    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json().get('response', {})
        if 'games' not in data:
            logging.warning(f"No games data for SteamID {steam_id}; profile may be private")
            return None
        games = data.get('games', [])
        logging.info(f"Fetched {len(games)} games for SteamID {steam_id}")
        return games
    except requests.RequestException as e:
        logging.error(f"Error fetching owned games: {e}")
        return None
# API: Checks for missing 'games' key to detect private profiles.
# Performance: Timeout of 10s accommodates large game libraries.

def get_player_achievements(steam_id, appid):
    """Fetch player achievements for a specific game."""
    url = "http://api.steampowered.com/ISteamUserStats/GetPlayerAchievements/v1/"
    params = {
        "key": API_KEY,
        "steamid": steam_id,
        "appid": appid
    }
    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json().get('playerstats', {})
        if data.get('success'):
            logging.info(f"Fetched achievements for appid {appid}")
            return data.get('achievements', [])
        return []
    except requests.RequestException as e:
        logging.error(f"Error fetching achievements for appid {appid}: {e}")
        return []
# Design Rationale: Empty list fallback ensures UI can handle failed or empty responses.

def get_global_achievements(appid):
    """Fetch global achievement percentages for a game."""
    url = "http://api.steampowered.com/ISteamUserStats/GetGlobalAchievementPercentagesForApp/v2/"
    params = {"gameid": appid}
    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json().get('achievementpercentages', {})
        return data.get('achievements', [])
    except requests.RequestException as e:
        logging.error(f"Error fetching global achievements for appid {appid}: {e}")
        return []
# Performance: Could cache global achievements to reduce API calls for repeated queries.