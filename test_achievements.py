"""
Test Achievement Fetching

Run this script to test achievement fetching for a specific Steam game.
Usage: python test_achievements.py <appid>
Example: python test_achievements.py 440
"""

import sys
import requests
import json
from consts import STEAM_API_KEY, STEAM_USERID_64


def test_achievements(appid):
    """
    Test fetching achievements for a specific game.

    Args:
        appid: Steam App ID to test
    """
    print(f"Testing achievements for App ID: {appid}")
    print("=" * 60)

    url = 'https://api.steampowered.com/ISteamUserStats/GetPlayerAchievements/v0001/'
    params = {
        'key': STEAM_API_KEY,
        'steamid': STEAM_USERID_64,
        'appid': appid
    }

    print(f"Request URL: {url}")
    print(f"Parameters: appid={appid}, steamid={STEAM_USERID_64}")
    print("\nFetching data from Steam API...")

    try:
        response = requests.get(url, params=params, timeout=10)
        print(f"Status Code: {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            print("\n" + "=" * 60)
            print("Raw API Response:")
            print("=" * 60)
            print(json.dumps(data, indent=2))

            # Parse achievements
            print("\n" + "=" * 60)
            print("Achievement Analysis:")
            print("=" * 60)

            playerstats = data.get('playerstats', {})
            success = playerstats.get('success')
            print(f"Success: {success}")

            if success:
                achievements = playerstats.get('achievements', [])
                print(f"Total achievements: {len(achievements)}")

                if achievements:
                    print("\nFirst 5 achievements (sample):")
                    for i, ach in enumerate(achievements[:5], 1):
                        achieved = ach.get('achieved')
                        apiname = ach.get('apiname', 'N/A')
                        unlocktime = ach.get('unlocktime', 0)
                        print(f"  {i}. {apiname}")
                        print(f"     achieved: {achieved} (type: {type(achieved).__name__})")
                        print(f"     unlocktime: {unlocktime}")

                    # Calculate statistics
                    unlocked = sum(1 for ach in achievements if ach.get('achieved'))
                    percentage = (unlocked / len(achievements) * 100) if achievements else 0

                    print(f"\n📊 Statistics:")
                    print(f"   Total: {len(achievements)}")
                    print(f"   Unlocked: {unlocked}")
                    print(f"   Percentage: {percentage:.2f}%")
                else:
                    print("No achievements found for this game")
            else:
                error = playerstats.get('error', 'Unknown error')
                print(f"Error: {error}")

        elif response.status_code == 400:
            print("ERROR: HTTP 400 - Game has no achievement schema")
        elif response.status_code == 403:
            print("ERROR: HTTP 403 - Invalid API key or profile is private")
            print("\nPossible solutions:")
            print("1. Check your Steam API key is correct in .env file")
            print("2. Make sure your Steam profile is set to PUBLIC")
            print("3. Go to: https://steamcommunity.com/my/edit/settings")
            print("   Set 'Game details' to PUBLIC")
        else:
            print(f"ERROR: HTTP {response.status_code} - Unexpected error")
            print(response.text[:500])

    except Exception as e:
        print(f"ERROR: Exception occurred: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python test_achievements.py <appid>")
        print("\nExample Steam App IDs:")
        print("  440 - Team Fortress 2")
        print("  620 - Portal 2")
        print("  1091500 - Cyberpunk 2077")
        print("  1145360 - Hades")
        sys.exit(1)

    appid = sys.argv[1]
    test_achievements(appid)
