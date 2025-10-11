"""Test Steam API appdetails endpoint"""
import requests
import json
import time

# Test with a well-known game
test_games = [
    (440, "Team Fortress 2"),
    (570, "Dota 2"),
    (730, "Counter-Strike: Global Offensive"),
]

for appid, expected_name in test_games:
    print(f"\n{'='*80}")
    print(f"Testing AppID {appid} ({expected_name})")
    print("="*80)

    url = f'https://store.steampowered.com/api/appdetails?appids={appid}'

    try:
        response = requests.get(url, timeout=10)
        print(f"Status Code: {response.status_code}")

        if response.status_code == 200:
            data = response.json()

            if str(appid) in data:
                app_data = data[str(appid)]
                print(f"Success: {app_data.get('success', False)}")

                if app_data.get('success') and 'data' in app_data:
                    game_data = app_data['data']

                    print(f"\nGame Name: {game_data.get('name')}")
                    print(f"Type: {game_data.get('type')}")

                    # Platforms
                    platforms = game_data.get('platforms', {})
                    print(f"\nPlatforms:")
                    print(f"  Windows: {platforms.get('windows', False)}")
                    print(f"  Mac: {platforms.get('mac', False)}")
                    print(f"  Linux: {platforms.get('linux', False)}")

                    # Header image
                    print(f"\nHeader Image: {game_data.get('header_image', 'N/A')[:80]}...")

                    # Release date
                    release = game_data.get('release_date', {})
                    print(f"\nRelease Date:")
                    print(f"  Coming Soon: {release.get('coming_soon', 'N/A')}")
                    print(f"  Date: {release.get('date', 'N/A')}")

                    # Genres
                    genres = game_data.get('genres', [])
                    print(f"\nGenres ({len(genres)}):")
                    for genre in genres:
                        print(f"  - {genre.get('description')} (id: {genre.get('id')})")

                    # Categories (game modes)
                    categories = game_data.get('categories', [])
                    print(f"\nCategories ({len(categories)}):")
                    for cat in categories[:10]:  # Show first 10
                        print(f"  - {cat.get('id')}: {cat.get('description')}")

                    # Developers/Publishers
                    print(f"\nDevelopers: {game_data.get('developers', 'N/A')}")
                    print(f"Publishers: {game_data.get('publishers', 'N/A')}")

                    # Show what we could extract
                    print(f"\n{'-'*80}")
                    print("EXTRACTABLE DATA SUMMARY:")
                    print(f"{'-'*80}")

                    extracted_platforms = []
                    if platforms.get('windows'): extracted_platforms.append('PC (Microsoft Windows)')
                    if platforms.get('mac'): extracted_platforms.append('Mac')
                    if platforms.get('linux'): extracted_platforms.append('Linux')
                    print(f"✓ Platforms: {extracted_platforms}")

                    print(f"✓ Cover URL: {bool(game_data.get('header_image'))}")
                    print(f"✓ Release Date: {release.get('date', 'MISSING')}")

                    genre_names = [g.get('description') for g in genres]
                    print(f"✓ Genres: {genre_names}")

                    # Detect game modes
                    game_modes = []
                    cat_ids = {cat['id']: cat.get('description') for cat in categories}
                    if 2 in cat_ids: game_modes.append('Single player')
                    if 1 in cat_ids: game_modes.append('Multiplayer')
                    if 9 in cat_ids or 38 in cat_ids: game_modes.append('Co-operative')
                    if 24 in cat_ids: game_modes.append('Split screen')
                    if 20 in cat_ids: game_modes.append('MMO')
                    print(f"✓ Game Modes: {game_modes}")

                    break  # Success, no need to test more
                else:
                    print(f"ERROR: No data or not successful")
            else:
                print(f"ERROR: appid {appid} not in response keys: {list(data.keys())}")
        else:
            print(f"ERROR: HTTP {response.status_code}")

    except Exception as e:
        print(f"ERROR: {e}")

    time.sleep(2)  # Rate limit
