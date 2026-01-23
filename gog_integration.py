import requests
import json
from store_integration_protocol import StoreIntegrationProtocol
from consts import GOG_PUBLIC_USERNAME, GOG_PROFILE_URL, NOTION_STORE_GOG_ID


class GogIntegration(StoreIntegrationProtocol):
    """Integration class for GOG.com API operations."""

    # ========== INITIALIZATION ==========

    def __init__(self, username):
        """
        Initialize GOG client.

        Args:
            username: GOG public profile username
        """
        self.username = username
        self.session = requests.Session()
        self.session.get('https://www.gog.com/')

    # ========== PUBLIC API - MAIN METHODS ==========

    def get_owned_games(self):
        """
        Get all owned games from GOG library, normalized for Notion.

        Returns:
            List of normalized game dictionaries
        """
        print(f"🎮 Starting GOG library fetch for user: {self.username}")
        all_games = self.get_all_games_from_public_profile()
        print(f"📥 Retrieved {len(all_games)} games from GOG public profile")
        print("🔄 Normalizing GOG games data...")
        normalized_games = self.normalize_games_list(all_games)
        print(f"✅ Completed GOG library processing: {len(normalized_games)} games ready")
        return normalized_games

    def get_game_info(self, appid):
        """
        Get detailed game information from GOG API.

        Args:
            appid: GOG game ID

        Returns:
            Game details dictionary or None if not found
        """
        print(f"🔍 Fetching detailed info for GOG game ID: {appid}")
        url = f'https://www.gog.com/account/gameDetails/{appid}.json'

        response = self.session.get(url)
        try:
            data = response.json()
            if data and 'game' in data:
                print(f"✅ Successfully retrieved game details for ID: {appid}")
                return data['game']
            else:
                print(f"❌ 'game' key not found in response for appid {appid}")
                return None
        except ValueError:
            print(f"🚨 Unable to parse JSON response for appid {appid}")
            return None
        except TypeError:
            print(f"🚨 Response for appid {appid} is not JSON")
            return None

    def get_all_games_from_public_profile(self):
        """
        Fetch all games from GOG public profile with pagination.

        Returns:
            List of all game dictionaries from profile
        """
        print("📚 Starting paginated fetch of all GOG games...")
        all_games = []
        page = 1
        total_pages = None

        while True:
            data = self.get_games_from_public_profile(page)
            if data and '_embedded' in data and 'items' in data['_embedded']:
                games_on_page = data['_embedded']['items']
                all_games.extend(games_on_page)

                if total_pages is None and 'pages' in data:
                    total_pages = data['pages']
                    print(f"📊 Found {total_pages} total pages to process")

                print(f"📖 Page {page}/{total_pages or '?'}: Added {len(games_on_page)} games (total: {len(all_games)})")

                if 'page' in data and 'pages' in data and data['page'] < data['pages']:
                    page += 1
                else:
                    print(f"🏁 Reached final page. Total games collected: {len(all_games)}")
                    break
            else:
                print(f"⚠️ No valid data on page {page}, stopping pagination")
                break

        return all_games

    def get_games_from_public_profile(self, page=1):
        """
        Fetch a single page of games from GOG public profile.

        Args:
            page: Page number to fetch (default: 1)

        Returns:
            Response data dictionary or None on error
        """
        print(f"🌐 Fetching GOG games page {page} for user: {self.username}")
        url = GOG_PROFILE_URL.format(username=self.username)
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:140.0) Gecko/20100101 Firefox/140.0",
            "Accept": "application/hal+json, application/json, */*",
            "Referer": f"https://www.gog.com/u/{self.username}/games",
            "X-Requested-With": "XMLHttpRequest"
        }

        params = {
            "sort": "recent_playtime",
            "order": "desc",
            "page": page
        }
        try:
            response = self.session.get(url, headers=headers, params=params, timeout=10)

            if response.status_code == 200:
                data = response.json()
                games_on_page = len(data.get('_embedded', {}).get('items', []))
                print(f"✅ Retrieved page {page} with {games_on_page} games")
                return data
            else:
                print(f"🚨 HTTP Error {response.status_code} for page {page}")
                return None

        except json.JSONDecodeError as e:
            print(f"❌ JSON parsing error on page {page}: {e}")
            print(f"Response content (first 500 chars): {response.text[:500]}")
            return None
        except Exception as e:
            print(f"🚨 General error on page {page}: {e}")
            return None

    def normalize_games_list(self, games):
        """
        Normalize raw GOG games data into standardized format.

        Args:
            games: List of raw game dictionaries from GOG API

        Returns:
            List of normalized game dictionaries
        """
        print(f"🔍 Normalizing {len(games)} GOG games...")
        normalized_games = []
        games_with_covers = 0

        for i, game in enumerate(games, 1):
            game_data = game.get('game', {})
            game_title = game_data.get('title', game.get('title', 'Unknown'))

            if i % 50 == 0 or i == len(games):
                print(f"📊 Progress: {i}/{len(games)} games normalized ({(i/len(games))*100:.1f}%)")

            game_id = game_data.get('id', game.get('id'))
            normalized_game = {
                'appid': game_id,
                'name': game_title,
                'notion_store_id': NOTION_STORE_GOG_ID,
                'external_id': str(game_id),
                'store_name': 'GOG',
            }

            # GOG is primarily PC-only
            normalized_game['platforms'] = ['PC (Microsoft Windows)']

            extracted_fields = []
            if 'image' in game_data:
                normalized_game['cover_url'] = game_data['image']
                games_with_covers += 1
                extracted_fields.append('cover')

            if extracted_fields:
                print(f"📝 {game_title}: extracted {', '.join(extracted_fields)}")

            normalized_games.append(normalized_game)

        print(f"📈 Normalization stats: {games_with_covers}/{len(games)} games have cover images")
        print(f"🏁 Normalization complete: {len(normalized_games)} games ready")
        return normalized_games


if __name__ == "__main__":
    print("🚀 Starting GOG Integration Test")
    print("=" * 60)

    username = GOG_PUBLIC_USERNAME
    print(f"👤 Testing with GOG username: {username}")

    gog_api = GogIntegration(username)
    print(f"🔧 Initialized GOG API for user: {username}")

    print("\n🔍 Testing get_owned_games() method:")
    owned_games = gog_api.get_owned_games()
    print(f"\n📈 Final Result: Found {len(owned_games)} normalized games")

    print("\n🔍 Testing raw get_all_games_from_public_profile() method:")
    raw_games = gog_api.get_all_games_from_public_profile()
    print(f"\n📋 Raw games retrieved: {len(raw_games)}")

    print("\n🎮 Sample of first 3 games:")
    for i, item in enumerate(raw_games[:3], 1):
        game = item['game']
        print(f"\n--- Game {i}: {game['title']} ---")
        print(f"ID: {game.get('id', 'N/A')}")
        print(f"Image: {game.get('image', 'No image')}")

    print("\n✅ GOG Integration Test Complete")
