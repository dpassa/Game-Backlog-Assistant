"""Test script to inspect actual Steam API responses"""
import requests
from consts import STEAM_API_KEY, STEAM_USERID_64
import json

print("Testing Steam API data structure...\n")

# Test 1: Get owned games list
print("="*60)
print("TEST 1: GetOwnedGames API")
print("="*60)
url = f'https://api.steampowered.com/IPlayerService/GetOwnedGames/v1/?key={STEAM_API_KEY}&steamid={STEAM_USERID_64}&include_appinfo=true'
response = requests.get(url)
data = response.json()

if 'response' in data and 'games' in data['response']:
    games = data['response']['games']
    print(f"Found {len(games)} games\n")

    # Show first game structure
    if games:
        print("First game from GetOwnedGames:")
        print(json.dumps(games[0], indent=2))
        test_appid = games[0]['appid']
else:
    print("ERROR: Could not fetch games")
    test_appid = 440  # Team Fortress 2 as fallback

# Test 2: Get detailed game info
print(f"\n{'='*60}")
print(f"TEST 2: appdetails API for appid {test_appid}")
print("="*60)
url = f'https://store.steampowered.com/api/appdetails?appids={test_appid}'
response = requests.get(url)

try:
    data = response.json()
    if data and str(test_appid) in data:
        app_data = data[str(test_appid)]

        if app_data.get('success') and 'data' in app_data:
            game_data = app_data['data']

            print(f"\nGame: {game_data.get('name', 'N/A')}")
            print(f"\nAvailable fields:")
            print(f"  - type: {game_data.get('type', 'N/A')}")
            print(f"  - platforms: {game_data.get('platforms', 'N/A')}")
            print(f"  - header_image: {game_data.get('header_image', 'N/A')}")

            # Release date
            release_date = game_data.get('release_date', {})
            print(f"  - release_date: {release_date}")

            # Genres
            genres = game_data.get('genres', [])
            print(f"  - genres: {[g.get('description') for g in genres]}")

            # Categories (for game modes)
            categories = game_data.get('categories', [])
            print(f"  - categories (count): {len(categories)}")
            if categories:
                print(f"    Sample categories:")
                for cat in categories[:5]:
                    print(f"      {cat.get('id')}: {cat.get('description')}")

            # Show full structure of useful fields
            print(f"\n{'='*60}")
            print("FULL DATA STRUCTURE (useful fields):")
            print("="*60)
            useful_fields = {
                'name': game_data.get('name'),
                'type': game_data.get('type'),
                'platforms': game_data.get('platforms'),
                'header_image': game_data.get('header_image'),
                'release_date': game_data.get('release_date'),
                'genres': game_data.get('genres'),
                'categories': game_data.get('categories'),
                'developers': game_data.get('developers'),
                'publishers': game_data.get('publishers'),
            }
            print(json.dumps(useful_fields, indent=2))
        else:
            print(f"ERROR: No data in response. Success: {app_data.get('success')}")
    else:
        print(f"ERROR: appid {test_appid} not in response")

except Exception as e:
    print(f"ERROR parsing response: {e}")
    print(f"Response text: {response.text[:500]}")
