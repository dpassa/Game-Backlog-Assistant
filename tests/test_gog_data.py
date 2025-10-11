"""Test GOG API data structure"""
import requests
import json
from consts import GOG_PUBLIC_USERNAME, GOG_PROFILE_URL

print("Testing GOG API data structure...\n")

session = requests.Session()
session.get('https://www.gog.com/')

url = GOG_PROFILE_URL.format(username=GOG_PUBLIC_USERNAME)
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:140.0) Gecko/20100101 Firefox/140.0",
    "Accept": "application/hal+json, application/json, */*",
    "X-Requested-With": "XMLHttpRequest"
}

params = {
    "sort": "recent_playtime",
    "order": "desc",
    "page": 1
}

try:
    print("Fetching GOG profile games...")
    response = session.get(url, headers=headers, params=params, timeout=10)

    print(f"Status Code: {response.status_code}\n")

    if response.status_code == 200:
        data = response.json()

        # Show structure
        print("Response structure:")
        print(f"  Keys: {list(data.keys())}\n")

        if '_embedded' in data and 'items' in data['_embedded']:
            games = data['_embedded']['items']
            print(f"Found {len(games)} games on current page")
            print(f"Current page: {data.get('page', 'N/A')}")
            print(f"Total pages: {data.get('pages', 'N/A')}\n")

            if games:
                print("="*80)
                print("FIRST GAME STRUCTURE:")
                print("="*80)
                print(json.dumps(games[0], indent=2))

                # Analyze what data is available
                first_game = games[0]
                print(f"\n{'='*80}")
                print("AVAILABLE FIELDS ANALYSIS:")
                print("="*80)

                print(f"\nGame ID: {first_game.get('id', 'N/A')}")
                print(f"Title: {first_game.get('title', 'N/A')}")

                # Check for metadata
                print(f"\nAvailable metadata fields:")
                for key in first_game.keys():
                    value = first_game[key]
                    if isinstance(value, dict):
                        print(f"  - {key}: {{dict with {len(value)} keys}}")
                        print(f"    Keys: {list(value.keys())[:5]}...")  # Show first 5 keys
                    elif isinstance(value, list):
                        print(f"  - {key}: [list with {len(value)} items]")
                        if value and isinstance(value[0], dict):
                            print(f"    First item keys: {list(value[0].keys())[:5]}")
                    else:
                        print(f"  - {key}: {type(value).__name__} = {str(value)[:100]}")

                # Check specific fields we're interested in
                print(f"\n{'='*80}")
                print("EXTRACTABLE DATA:")
                print("="*80)

                if 'image' in first_game:
                    print(f"[YES] Cover Image: {first_game['image']}")
                else:
                    print(f"[NO] Cover Image: NOT AVAILABLE at top level")

                # Check in 'game' object
                if 'game' in first_game and 'image' in first_game['game']:
                    print(f"[YES] Cover Image (from game object): {first_game['game']['image']}")

                # Check if there's additional game info
                if 'game' in first_game:
                    game_obj = first_game['game']
                    print(f"\n'game' object available with keys: {list(game_obj.keys())}")

                    # Look for useful fields
                    useful_fields = ['title', 'image', 'url', 'releaseDate', 'developers', 'publishers', 'genres']
                    for field in useful_fields:
                        if field in game_obj:
                            value = game_obj[field]
                            if isinstance(value, (str, int)):
                                print(f"  [YES] {field}: {value}")
                            else:
                                print(f"  [YES] {field}: {type(value).__name__}")
                        else:
                            print(f"  [NO] {field}: not available")

                if 'stats' in first_game:
                    stats = first_game['stats']
                    print(f"\n'stats' object available with keys: {list(stats.keys())}")

        else:
            print("ERROR: No '_embedded' or 'items' in response")

    else:
        print(f"ERROR: HTTP {response.status_code}")
        print(f"Response: {response.text[:500]}")

except Exception as e:
    print(f"ERROR: {e}")
    import traceback
    traceback.print_exc()
