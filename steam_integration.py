import requests
import time
import json
import os
from datetime import datetime, timedelta
from store_integration_protocol import StoreIntegrationProtocol
from consts import NOTION_STORE_STEAM_ID, STEAM_API_KEY, STEAM_USERID_64


class SteamIntegration(StoreIntegrationProtocol):
    """Integration class for Steam Web API operations."""

    # ========== INITIALIZATION ==========

    def __init__(self, api_key, steamid, cache_enabled=True, cache_ttl_hours=24):
        """
        Initialize Steam API client.

        Args:
            api_key: Steam Web API key
            steamid: Steam user ID (64-bit)
            cache_enabled: Enable file-based caching (default: True)
            cache_ttl_hours: Cache time-to-live in hours (default: 24)
        """
        self.api_key = api_key
        self.steamid = steamid

        # Smart rate limiting based on Steam Web API Terms: 100,000 calls/day
        self.daily_limit = 100000
        self.rate_limit_file = '.steam_api_usage.json'
        self.last_request_time = 0
        self.requests_today = self._load_daily_usage()
        self.current_date = datetime.now().date()
        self.min_interval_when_limited = 1.0

        # Caching configuration
        self.cache_enabled = cache_enabled
        self.cache_ttl_hours = cache_ttl_hours
        self.cache_file = '.steam_api_cache.json'
        self.cache = self._load_cache() if cache_enabled else {}

        # In-memory cache for owned games
        self._owned_games_cache = None

    # ========== PUBLIC API - MAIN METHODS ==========

    def get_owned_games(self):
        """
        Get all owned games from Steam library, normalized for Notion.

        Returns:
            List of normalized game dictionaries
        """
        print(f"🎮 Starting Steam library fetch for user ID: {self.steamid}")
        games = self.get_games_from_api()
        print(f"📥 Retrieved {len(games)} games from Steam API")
        print("🔄 Normalizing games and fetching detailed information...")
        print("⚡ Using smart adaptive rate limiting (Steam official: 100k/day)")
        normalized_games = self.normalize_games_list(games)
        print(f"✅ Completed Steam library processing: {len(normalized_games)} games ready")
        return normalized_games

    def get_games_from_api(self, force_refresh=False):
        """
        Fetch owned games from Steam API with in-memory caching.

        Args:
            force_refresh: Force a fresh API call, ignoring cache (default: False)

        Returns:
            List of owned games from Steam API
        """
        if self._owned_games_cache is not None and not force_refresh:
            print(f"📦 Using cached owned games ({len(self._owned_games_cache)} games)")
            return self._owned_games_cache

        print("🌐 Fetching owned games from Steam API...")
        url = f'https://api.steampowered.com/IPlayerService/GetOwnedGames/v1/?key={self.api_key}&steamid={self.steamid}&include_appinfo=true'
        response = requests.get(url)
        data = response.json()
        games = data['response']['games']
        print(f"📋 Found {len(games)} games in Steam library")

        self._owned_games_cache = games
        return games

    def get_game_info(self, appid):
        """
        Get detailed game information from Steam store API with caching and retry logic.

        Args:
            appid: Steam App ID

        Returns:
            Game details dictionary or None if not found
        """
        cache_key = f"appid_{appid}"
        cached_data = self._get_from_cache(cache_key)
        if cached_data is not None:
            return cached_data

        self._smart_rate_limit()

        url = f'https://store.steampowered.com/api/appdetails?appids={appid}'
        max_retries = 3
        base_delay = 5

        for attempt in range(max_retries):
            try:
                response = requests.get(url, timeout=10)

                if response.status_code == 429:
                    retry_delay = base_delay * (2 ** attempt)
                    print(f"🚨 HTTP 429 Rate Limited by Steam API (attempt {attempt + 1}/{max_retries})")
                    self.min_interval_when_limited = min(3.0, self.min_interval_when_limited * 1.5)

                    if attempt < max_retries - 1:
                        print(f"⏳ Exponential backoff: waiting {retry_delay}s before retry...")
                        time.sleep(retry_delay)
                        continue
                    else:
                        print(f"❌ Max retries reached for appid {appid}")
                        return None

                if response.status_code == 200:
                    data = response.json()
                    if data and str(appid) in data:
                        app_data = data[str(appid)]
                        if app_data.get('success') and 'data' in app_data:
                            game_data = app_data['data']
                            print(f"✅ Retrieved detailed info for appid {appid}")
                            self._save_to_cache(cache_key, game_data)
                            return game_data
                        else:
                            print(f"❌ No valid data for appid {appid}")

                    print(f"⚠️ No response data for appid {appid}")
                    return None

                print(f"⚠️ HTTP {response.status_code} for appid {appid}")
                if attempt < max_retries - 1:
                    retry_delay = base_delay * (2 ** attempt)
                    print(f"⏳ Retrying in {retry_delay}s...")
                    time.sleep(retry_delay)
                    continue

                return None

            except (ValueError, TypeError, requests.RequestException) as e:
                print(f"🚨 Error fetching info for appid {appid} (attempt {attempt + 1}/{max_retries}): {str(e)}")

                if attempt < max_retries - 1:
                    retry_delay = base_delay * (2 ** attempt)
                    print(f"⏳ Retrying in {retry_delay}s...")
                    time.sleep(retry_delay)
                    continue

                return None

        return None

    def get_player_achievements(self, appid):
        """
        Get player achievements for a specific game using GetUserStatsForGame API.

        Args:
            appid: Steam App ID

        Returns:
            Dictionary with achievement data including percentage completion,
            or None if game has no achievements or API call fails
        """
        cache_key = f"achievements_{appid}"
        cached_data = self._get_from_cache(cache_key)
        if cached_data is not None:
            print(f"📦 Cached achievements for {appid}: {cached_data.get('percentage', 0)}%")
            return cached_data

        self._smart_rate_limit()

        url = f'https://api.steampowered.com/ISteamUserStats/GetUserStatsForGame/v0002/'
        params = {
            'key': self.api_key,
            'steamid': self.steamid,
            'appid': appid
        }

        max_retries = 2
        base_delay = 2

        for attempt in range(max_retries):
            try:
                response = requests.get(url, params=params, timeout=10)

                if response.status_code == 200:
                    data = response.json()
                    playerstats = data.get('playerstats', {})
                    achievements = playerstats.get('achievements', [])

                    if not achievements:
                        result = {'has_achievements': False, 'percentage': 0}
                        self._save_to_cache(cache_key, result)
                        return result

                    total = len(achievements)
                    unlocked = sum(1 for ach in achievements if ach.get('achieved', 0) == 1)
                    percentage = (unlocked / total * 100) if total > 0 else 0

                    result = {
                        'has_achievements': True,
                        'total': total,
                        'unlocked': unlocked,
                        'percentage': round(percentage, 2)
                    }
                    self._save_to_cache(cache_key, result)
                    print(f"✅ Achievements for appid {appid}: {unlocked}/{total} ({percentage:.1f}%)")
                    return result

                elif response.status_code == 400:
                    result = {'has_achievements': False, 'percentage': 0}
                    self._save_to_cache(cache_key, result)
                    return result

                elif response.status_code == 403:
                    print(f"⚠️ Achievements private or unavailable for appid {appid}")
                    result = {'has_achievements': False, 'percentage': 0}
                    self._save_to_cache(cache_key, result)
                    return result

                elif response.status_code == 429:
                    retry_delay = base_delay * (2 ** attempt)
                    self.min_interval_when_limited = min(3.0, self.min_interval_when_limited * 1.5)

                    if attempt < max_retries - 1:
                        print(f"⏳ Rate limited, waiting {retry_delay}s...")
                        time.sleep(retry_delay)
                        continue

            except Exception as e:
                print(f"⚠️ Error fetching achievements for appid {appid}: {e}")
                if attempt < max_retries - 1:
                    time.sleep(base_delay)
                    continue

        return None

    def get_recently_played_games(self):
        """
        Get recently played games with playtime information.

        Returns:
            Dictionary mapping appid to last played timestamp and playtime
        """
        cache_key = "recently_played"
        cached_data = self._get_from_cache(cache_key)
        if cached_data is not None:
            return cached_data

        self._smart_rate_limit()

        url = f'https://api.steampowered.com/IPlayerService/GetRecentlyPlayedGames/v1/'
        params = {
            'key': self.api_key,
            'steamid': self.steamid,
            'count': 0
        }

        try:
            response = requests.get(url, params=params, timeout=10)
            if response.status_code == 200:
                data = response.json()
                games = data.get('response', {}).get('games', [])

                result = {}
                for game in games:
                    appid = game.get('appid')
                    if appid:
                        result[str(appid)] = {
                            'playtime_forever': game.get('playtime_forever', 0),
                            'playtime_2weeks': game.get('playtime_2weeks', 0)
                        }

                self._save_to_cache(cache_key, result)
                print(f"✅ Retrieved recently played data for {len(result)} games")
                return result

        except Exception as e:
            print(f"⚠️ Error fetching recently played games: {e}")

        return {}

    def get_enriched_game_data(self, appid, include_achievements=True):
        """
        Get enriched game data including achievements and status for a specific game.

        Args:
            appid: Steam App ID
            include_achievements: Whether to fetch achievement data (default: True)

        Returns:
            Dictionary with achievement_percentage and status, or empty dict if game not found
        """
        result = {}

        if include_achievements:
            achievement_data = self.get_player_achievements(appid)
            if achievement_data and achievement_data.get('has_achievements'):
                result['achievement_percentage'] = achievement_data.get('percentage', 0)
                print(f"🎮 Game {appid} has achievements: {result['achievement_percentage']}%")
            else:
                result['achievement_percentage'] = 0
                print(f"🎮 Game {appid} has no achievements or data unavailable")

            games = self.get_games_from_api()
            game_data = next((g for g in games if g['appid'] == int(appid)), None)

            last_played = None
            if game_data and game_data.get('rtime_last_played', 0) > 0:
                last_played = datetime.fromtimestamp(game_data['rtime_last_played'])

            status = self.calculate_status(last_played, result.get('achievement_percentage', 0))
            result['status'] = status

        return result

    def calculate_status(self, last_played_date, achievement_percentage):
        """
        Calculate game status based on last played date and achievement completion.

        Args:
            last_played_date: Last played date as datetime object or None
            achievement_percentage: Achievement completion percentage (0-100)

        Returns:
            Status string: Currently Playing, Backlog, Complete, On Hold, or Abandoned
        """
        if achievement_percentage == 100:
            return "Complete"

        if last_played_date is None:
            return "Backlog"

        now = datetime.now()
        time_since_played = now - last_played_date

        if time_since_played <= timedelta(days=30):
            return "Currently Playing"

        if time_since_played <= timedelta(days=365):
            return "On Hold"

        if time_since_played > timedelta(days=730):
            return "Abandoned"

        return "On Hold"

    def normalize_games_list(self, games):
        """
        Normalize raw Steam games data into standardized format.

        Args:
            games: List of raw game dictionaries from Steam API

        Returns:
            List of normalized game dictionaries
        """
        normalized_games = []
        total_games = len(games)
        print(f"🔍 Processing {total_games} games for detailed information...")

        for i, game in enumerate(games, 1):
            if i % 10 == 0 or i == total_games:
                print(f"📊 Progress: {i}/{total_games} games processed ({(i/total_games)*100:.1f}%)")

            print(f"🎯 Processing: {game['name']} (AppID: {game['appid']})")
            game_info = self.get_game_info(game['appid'])
            normalized_game = {
                'appid': game['appid'],
                'name': game['name'],
                'notion_store_id': NOTION_STORE_STEAM_ID,
                'external_id': str(game['appid']),
                'store_name': 'Steam',
            }

            extracted_fields = []
            if game_info:
                platforms = self._extract_platforms(game_info)
                if platforms:
                    normalized_game['platforms'] = platforms
                    extracted_fields.append('platforms')

                if 'header_image' in game_info:
                    normalized_game['cover_url'] = game_info['header_image']
                    extracted_fields.append('cover')

                release_date = self._extract_release_date(game_info)
                if release_date:
                    normalized_game['release_date'] = release_date
                    extracted_fields.append('release_date')

                genres = self._extract_genres(game_info)
                if genres:
                    normalized_game['genres'] = genres
                    extracted_fields.append('genres')

                game_modes = self._extract_game_modes(game_info)
                if game_modes:
                    normalized_game['game_modes'] = game_modes
                    extracted_fields.append('game_modes')

                if extracted_fields:
                    print(f"📝 Extracted: {', '.join(extracted_fields)}")
                else:
                    print("⚠️ No additional metadata extracted")
            else:
                print("❌ No detailed info available")

            normalized_games.append(normalized_game)

        print(f"🏁 Normalization complete: {len(normalized_games)} games ready for processing")
        return normalized_games

    # ========== PRIVATE METHODS - CACHE ==========

    def _load_cache(self):
        """Load cached API responses from file."""
        try:
            if os.path.exists(self.cache_file):
                with open(self.cache_file, 'r', encoding='utf-8') as f:
                    cache_data = json.load(f)
                    current_time = datetime.now().isoformat()
                    cleaned_cache = {
                        k: v for k, v in cache_data.items()
                        if v.get('expires_at', '1900-01-01') > current_time
                    }
                    return cleaned_cache
            return {}
        except (json.JSONDecodeError, Exception) as e:
            print(f"Warning: Could not load cache, starting fresh: {e}")
            return {}

    def _save_cache(self):
        """Save cache to file."""
        try:
            with open(self.cache_file, 'w', encoding='utf-8') as f:
                json.dump(self.cache, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Warning: Could not save cache: {e}")

    def _get_from_cache(self, cache_key):
        """Get data from cache if available and not expired."""
        if not self.cache_enabled:
            return None

        cached_entry = self.cache.get(cache_key)
        if cached_entry:
            expires_at = cached_entry.get('expires_at', '1900-01-01')
            if expires_at > datetime.now().isoformat():
                print(f"📦 Using cached data for {cache_key}")
                return cached_entry.get('data')
            else:
                del self.cache[cache_key]

        return None

    def _save_to_cache(self, cache_key, data):
        """Save data to cache with TTL."""
        if not self.cache_enabled:
            return

        expires_at = (datetime.now() + timedelta(hours=self.cache_ttl_hours)).isoformat()
        self.cache[cache_key] = {
            'data': data,
            'cached_at': datetime.now().isoformat(),
            'expires_at': expires_at
        }
        self._save_cache()

    # ========== PRIVATE METHODS - RATE LIMITING ==========

    def _load_daily_usage(self):
        """Load today's API usage count from file."""
        try:
            if os.path.exists(self.rate_limit_file):
                with open(self.rate_limit_file, 'r') as f:
                    data = json.load(f)
                    file_date = datetime.fromisoformat(data.get('date', '1900-01-01')).date()
                    current_date = datetime.now().date()

                    if file_date == current_date:
                        return data.get('requests', 0)
                    else:
                        return 0
            return 0
        except (json.JSONDecodeError, KeyError):
            return 0

    def _save_daily_usage(self):
        """Save current usage count to file."""
        try:
            data = {
                'date': datetime.now().date().isoformat(),
                'requests': self.requests_today
            }
            with open(self.rate_limit_file, 'w') as f:
                json.dump(data, f)
        except Exception as e:
            print(f"Warning: Could not save API usage data: {e}")

    def _increment_request_count(self):
        """Increment request counter and save to file."""
        current_date = datetime.now().date()
        if current_date != self.current_date:
            self.current_date = current_date
            self.requests_today = 0

        self.requests_today += 1
        self._save_daily_usage()

    def _smart_rate_limit(self, estimated_remaining_requests=1):
        """
        Smart adaptive rate limiting for Steam Store API.

        Only applies delays when approaching daily limit or after 429 errors.
        """
        current_usage_percent = (self.requests_today / self.daily_limit) * 100

        if self.requests_today + estimated_remaining_requests >= self.daily_limit:
            print(f"🚫 Daily API limit reached ({self.requests_today}/{self.daily_limit}). Stopping requests.")
            raise RuntimeError(f"Steam API daily limit of {self.daily_limit} requests exceeded")

        if current_usage_percent >= 90:
            elapsed = time.time() - self.last_request_time
            if elapsed < self.min_interval_when_limited:
                sleep_time = self.min_interval_when_limited - elapsed
                print(f"⏳ High API usage ({current_usage_percent:.1f}%), rate limiting: {sleep_time:.1f}s")
                time.sleep(sleep_time)

        elif time.time() - self.last_request_time < 0.5:
            time.sleep(0.1)

        self.last_request_time = time.time()
        self._increment_request_count()

        if self.requests_today % 100 == 0:
            print(f"📊 Steam API usage: {self.requests_today}/{self.daily_limit} ({current_usage_percent:.1f}%)")

    # ========== PRIVATE METHODS - DATA EXTRACTION ==========

    def _extract_platforms(self, game_info):
        """Extract platform names from Steam game info."""
        if not game_info or 'platforms' not in game_info:
            return None

        platforms = []
        steam_platforms = game_info['platforms']

        if steam_platforms.get('windows'):
            platforms.append('PC (Microsoft Windows)')
        if steam_platforms.get('mac'):
            platforms.append('Mac')
        if steam_platforms.get('linux'):
            platforms.append('Linux')

        return platforms if platforms else None

    def _extract_release_date(self, game_info):
        """Extract release date in YYYY-MM-DD format."""
        if not game_info or 'release_date' not in game_info:
            return None

        release_info = game_info['release_date']
        if release_info.get('coming_soon', True):
            return None

        date_str = release_info.get('date')
        if not date_str:
            return None

        try:
            for fmt in ["%b %d, %Y", "%d %b, %Y", "%Y-%m-%d", "%d %b %Y"]:
                try:
                    date_obj = datetime.strptime(date_str, fmt)
                    return date_obj.strftime("%Y-%m-%d")
                except ValueError:
                    continue
        except Exception:
            pass

        return None

    def _extract_genres(self, game_info):
        """Extract genre names from Steam game info."""
        if not game_info or 'genres' not in game_info:
            return None

        genres = [genre['description'] for genre in game_info['genres'] if 'description' in genre]
        return genres if genres else None

    def _extract_game_modes(self, game_info):
        """Extract game modes from Steam categories."""
        if not game_info or 'categories' not in game_info:
            return None

        game_modes = []
        categories = {cat['id']: cat.get('description', '') for cat in game_info['categories']}

        if 2 in categories:
            game_modes.append('Single player')
        if 1 in categories:
            game_modes.append('Multiplayer')
        if 9 in categories or 38 in categories:
            game_modes.append('Co-operative')
        if 24 in categories:
            game_modes.append('Split screen')
        if 20 in categories:
            game_modes.append('Massively Multiplayer Online (MMO)')

        return game_modes if game_modes else None


if __name__ == "__main__":
    print("🚀 Starting Steam Integration Test")
    print("=" * 60)

    steam_api = SteamIntegration(STEAM_API_KEY, STEAM_USERID_64)
    print(f"🔑 Initialized Steam API with user ID: {STEAM_USERID_64}")

    owned_games = steam_api.get_owned_games()
    print(f"\n📈 Final Result: Found {len(owned_games)} games on Steam")

    print("\n🔍 Showing sample data for first 3 games:")
    for i, game in enumerate(owned_games[:3], 1):
        print(f"\n{'='*60}")
        print(f"Game {i}: {game['name']} (AppID: {game['appid']})")
        print(f"{'='*60}")

        print(f"Notion Store ID: {game.get('notion_store_id', 'N/A')}")
        print(f"Platforms: {game.get('platforms', 'NOT EXTRACTED')}")
        print(f"Cover URL: {game.get('cover_url', 'NOT EXTRACTED')}")
        print(f"Release Date: {game.get('release_date', 'NOT EXTRACTED')}")
        print(f"Genres: {game.get('genres', 'NOT EXTRACTED')}")
        print(f"Game Modes: {game.get('game_modes', 'NOT EXTRACTED')}")

    print("\n✅ Steam Integration Test Complete")
