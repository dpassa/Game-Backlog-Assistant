import requests
import time
import json
import os
from datetime import datetime, timedelta
from store_integration_protocol import StoreIntegrationProtocol
from consts import NOTION_STORE_STEAM_ID, STEAM_API_KEY, STEAM_USERID_64

class SteamIntegration(StoreIntegrationProtocol):
    def __init__(self, api_key, steamid, cache_enabled=True, cache_ttl_hours=24):
        self.api_key = api_key
        self.steamid = steamid

        # Smart rate limiting based on Steam Web API Terms: 100,000 calls/day
        # Reference: https://steamcommunity.com/dev/apiterms
        self.daily_limit = 100000  # Official Steam API limit
        self.rate_limit_file = '.steam_api_usage.json'
        self.last_request_time = 0
        self.requests_today = self._load_daily_usage()
        self.current_date = datetime.now().date()

        # Adaptive rate limiting - only slow down when needed
        self.min_interval_when_limited = 1.0  # Fallback interval after 429 errors

        # Caching configuration
        self.cache_enabled = cache_enabled
        self.cache_ttl_hours = cache_ttl_hours
        self.cache_file = '.steam_api_cache.json'
        self.cache = self._load_cache() if cache_enabled else {}
        
    def _load_daily_usage(self):
        """Load today's API usage count from file"""
        try:
            if os.path.exists(self.rate_limit_file):
                with open(self.rate_limit_file, 'r') as f:
                    data = json.load(f)
                    file_date = datetime.fromisoformat(data.get('date', '1900-01-01')).date()
                    current_date = datetime.now().date()
                    
                    if file_date == current_date:
                        return data.get('requests', 0)
                    else:
                        # New day, reset counter
                        return 0
            return 0
        except (json.JSONDecodeError, KeyError):
            return 0
    
    def _save_daily_usage(self):
        """Save current usage count to file"""
        try:
            data = {
                'date': datetime.now().date().isoformat(),
                'requests': self.requests_today
            }
            with open(self.rate_limit_file, 'w') as f:
                json.dump(data, f)
        except Exception as e:
            print(f"Warning: Could not save API usage data: {e}")

    def _load_cache(self):
        """Load cached API responses from file"""
        try:
            if os.path.exists(self.cache_file):
                with open(self.cache_file, 'r', encoding='utf-8') as f:
                    cache_data = json.load(f)
                    # Clean up expired entries
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
        """Save cache to file"""
        try:
            with open(self.cache_file, 'w', encoding='utf-8') as f:
                json.dump(self.cache, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Warning: Could not save cache: {e}")

    def _get_from_cache(self, cache_key):
        """Get data from cache if available and not expired"""
        if not self.cache_enabled:
            return None

        cached_entry = self.cache.get(cache_key)
        if cached_entry:
            expires_at = cached_entry.get('expires_at', '1900-01-01')
            if expires_at > datetime.now().isoformat():
                print(f"📦 Using cached data for {cache_key}")
                return cached_entry.get('data')
            else:
                # Remove expired entry
                del self.cache[cache_key]

        return None

    def _save_to_cache(self, cache_key, data):
        """Save data to cache with TTL"""
        if not self.cache_enabled:
            return

        expires_at = (datetime.now() + timedelta(hours=self.cache_ttl_hours)).isoformat()
        self.cache[cache_key] = {
            'data': data,
            'cached_at': datetime.now().isoformat(),
            'expires_at': expires_at
        }
        self._save_cache()
    
    def _increment_request_count(self):
        """Increment request counter and save to file"""
        # Check if we've rolled over to a new day
        current_date = datetime.now().date()
        if current_date != self.current_date:
            self.current_date = current_date
            self.requests_today = 0
        
        self.requests_today += 1
        self._save_daily_usage()

    def get_owned_games(self):
        print(f"🎮 Starting Steam library fetch for user ID: {self.steamid}")
        games = self.get_games_from_api()
        print(f"📥 Retrieved {len(games)} games from Steam API")
        print("🔄 Normalizing games and fetching detailed information...")
        print("⚡ Using smart adaptive rate limiting (Steam official: 100k/day)")
        normalized_games = self.normalize_games_list(games)
        print(f"✅ Completed Steam library processing: {len(normalized_games)} games ready")
        return normalized_games
    
    def get_games_from_api(self):
        print("🌐 Fetching owned games from Steam API...")
        url = f'https://api.steampowered.com/IPlayerService/GetOwnedGames/v1/?key={self.api_key}&steamid={self.steamid}&include_appinfo=true'
        response = requests.get(url)
        data = response.json()
        games = data['response']['games']
        print(f"📋 Found {len(games)} games in Steam library")
        return games

    def _smart_rate_limit(self, estimated_remaining_requests=1):
        """
        Smart adaptive rate limiting for Steam Store API.
        Steam Web API Terms: "You are limited to one hundred thousand (100,000) calls to the Steam Web API per day"
        Reference: https://steamcommunity.com/dev/apiterms
        
        Only applies delays when:
        1. Approaching daily limit (90%+ usage)
        2. After receiving HTTP 429 errors
        3. Making requests too fast (>2 req/sec sustained)
        """
        current_usage_percent = (self.requests_today / self.daily_limit) * 100
        
        # Check if we're approaching the daily limit
        if self.requests_today + estimated_remaining_requests >= self.daily_limit:
            print(f"🚫 Daily API limit reached ({self.requests_today}/{self.daily_limit}). Stopping requests.")
            raise RuntimeError(f"Steam API daily limit of {self.daily_limit} requests exceeded")
        
        # Only enforce delays if usage is high (90%+) or after 429 errors
        if current_usage_percent >= 90:
            elapsed = time.time() - self.last_request_time
            if elapsed < self.min_interval_when_limited:
                sleep_time = self.min_interval_when_limited - elapsed
                print(f"⏳ High API usage ({current_usage_percent:.1f}%), rate limiting: {sleep_time:.1f}s")
                time.sleep(sleep_time)
        
        # Very light throttling for sustained high-frequency requests (>2 req/sec)
        elif time.time() - self.last_request_time < 0.5:  # Less than 500ms
            time.sleep(0.1)  # Minimal 100ms delay
        
        self.last_request_time = time.time()
        self._increment_request_count()
        
        # Status logging every 100 requests
        if self.requests_today % 100 == 0:
            print(f"📊 Steam API usage: {self.requests_today}/{self.daily_limit} ({current_usage_percent:.1f}%)")

    def get_game_info(self, appid):
        """
        Get detailed game information from Steam store API with caching,
        smart rate limiting and exponential backoff retry logic.
        """
        # Check cache first
        cache_key = f"appid_{appid}"
        cached_data = self._get_from_cache(cache_key)
        if cached_data is not None:
            return cached_data

        # Not in cache, fetch from API
        self._smart_rate_limit()

        url = f'https://store.steampowered.com/api/appdetails?appids={appid}'
        max_retries = 3
        base_delay = 5  # Base delay in seconds

        for attempt in range(max_retries):
            try:
                response = requests.get(url, timeout=10)

                # Handle rate limiting with exponential backoff
                if response.status_code == 429:
                    # Calculate exponential backoff delay: base_delay * (2 ^ attempt)
                    retry_delay = base_delay * (2 ** attempt)
                    print(f"🚨 HTTP 429 Rate Limited by Steam API (attempt {attempt + 1}/{max_retries})")

                    # Increase rate limiting for all future requests
                    self.min_interval_when_limited = min(3.0, self.min_interval_when_limited * 1.5)

                    if attempt < max_retries - 1:
                        print(f"⏳ Exponential backoff: waiting {retry_delay}s before retry...")
                        time.sleep(retry_delay)
                        continue
                    else:
                        print(f"❌ Max retries reached for appid {appid}")
                        return None

                # Handle successful response
                if response.status_code == 200:
                    data = response.json()
                    if data and str(appid) in data:
                        app_data = data[str(appid)]
                        if app_data.get('success') and 'data' in app_data:
                            game_data = app_data['data']
                            print(f"✅ Retrieved detailed info for appid {appid}")
                            # Save to cache
                            self._save_to_cache(cache_key, game_data)
                            return game_data
                        else:
                            print(f"❌ No valid data for appid {appid}")

                    print(f"⚠️ No response data for appid {appid}")
                    return None

                # Handle other HTTP errors
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
    
    def normalize_games_list(self, games):
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
                'external_id': str(game['appid']),  # Steam App ID as external_id
                'store_name': 'Steam',  # Store identifier
            }

            # Extract all available metadata to skip IGDB calls
            extracted_fields = []
            if game_info:
                # Extract platforms
                platforms = self._extract_platforms(game_info)
                if platforms:
                    normalized_game['platforms'] = platforms
                    extracted_fields.append('platforms')

                # Extract cover URL
                if 'header_image' in game_info:
                    normalized_game['cover_url'] = game_info['header_image']
                    extracted_fields.append('cover')

                # Extract release date
                release_date = self._extract_release_date(game_info)
                if release_date:
                    normalized_game['release_date'] = release_date
                    extracted_fields.append('release_date')

                # Extract genres
                genres = self._extract_genres(game_info)
                if genres:
                    normalized_game['genres'] = genres
                    extracted_fields.append('genres')

                # Extract game modes
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

    def _extract_platforms(self, game_info):
        """Extract platform names from Steam game info"""
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
        """Extract release date in YYYY-MM-DD format"""
        if not game_info or 'release_date' not in game_info:
            return None

        release_info = game_info['release_date']
        if release_info.get('coming_soon', True):
            return None

        date_str = release_info.get('date')
        if not date_str:
            return None

        try:
            from datetime import datetime
            # Steam formats: "Jan 1, 2020", "1 Jan, 2020", "2020-01-01"
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
        """Extract genre names from Steam game info"""
        if not game_info or 'genres' not in game_info:
            return None

        genres = [genre['description'] for genre in game_info['genres'] if 'description' in genre]
        return genres if genres else None

    def _extract_game_modes(self, game_info):
        """Extract game modes from Steam categories"""
        if not game_info or 'categories' not in game_info:
            return None

        game_modes = []
        categories = {cat['id']: cat.get('description', '') for cat in game_info['categories']}

        # Steam category IDs
        if 2 in categories:  # Single-player
            game_modes.append('Single player')
        if 1 in categories:  # Multi-player
            game_modes.append('Multiplayer')
        if 9 in categories or 38 in categories:  # Co-op or Online Co-op
            game_modes.append('Co-operative')
        if 24 in categories:  # Shared/Split Screen
            game_modes.append('Split screen')
        if 20 in categories:  # MMO
            game_modes.append('Massively Multiplayer Online (MMO)')

        return game_modes if game_modes else None
    
if __name__ == "__main__":
    print("🚀 Starting Steam Integration Test")
    print("=" * 60)
    
    steam_api = SteamIntegration(STEAM_API_KEY, STEAM_USERID_64)
    print(f"🔑 Initialized Steam API with user ID: {STEAM_USERID_64}")
    
    owned_games = steam_api.get_owned_games()
    print(f"\n📈 Final Result: Found {len(owned_games)} games on Steam")

    # Test first 3 games to see what data we're getting
    print("\n🔍 Showing sample data for first 3 games:")
    for i, game in enumerate(owned_games[:3], 1):
        print(f"\n{'='*60}")
        print(f"Game {i}: {game['name']} (AppID: {game['appid']})")
        print(f"{'='*60}")

        # Show what fields we extracted
        print(f"Notion Store ID: {game.get('notion_store_id', 'N/A')}")
        print(f"Platforms: {game.get('platforms', 'NOT EXTRACTED')}")
        print(f"Cover URL: {game.get('cover_url', 'NOT EXTRACTED')}")
        print(f"Release Date: {game.get('release_date', 'NOT EXTRACTED')}")
        print(f"Genres: {game.get('genres', 'NOT EXTRACTED')}")
        print(f"Game Modes: {game.get('game_modes', 'NOT EXTRACTED')}")
    
    print("\n✅ Steam Integration Test Complete")