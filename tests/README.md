# Tests

This folder contains all test files for the Game Backlog Assistant.

## Test Types

### Unit Tests
Standard unit tests for individual integrations:
- **[test_steam_integration.py](test_steam_integration.py)** - Tests for Steam integration
- **[test_gog_integration.py](test_gog_integration.py)** - Tests for GOG integration
- **[test_howlongtobeat_integration.py](test_howlongtobeat_integration.py)** - Tests for HowLongToBeat integration

### API Exploration Tests
These tests explore actual API responses to understand data structures:
- **[test_steam_data.py](test_steam_data.py)** - Explores Steam GetOwnedGames API structure
- **[test_steam_detailed.py](test_steam_detailed.py)** - Explores Steam appdetails API with rate limit handling
- **[test_gog_data.py](test_gog_data.py)** - Explores GOG public profile API structure

## Running Tests

### Run All Unit Tests
```bash
python -m pytest tests/ -v
```

### Run Specific Test File
```bash
python -m pytest tests/test_steam_integration.py -v
```

### Run API Exploration Tests

**Important**: These tests make real API calls and may take time due to rate limiting (Steam: 100k calls/day - [Terms](https://steamcommunity.com/dev/apiterms)).

**Test Steam API**:
```bash
cd tests
python test_steam_data.py
python test_steam_detailed.py
```

**Test GOG API**:
```bash
cd tests
python test_gog_data.py
```

## Test Results

See **[../API_TESTING_RESULTS.md](../API_TESTING_RESULTS.md)** for detailed results of API testing including:
- Available fields from each API
- Rate limiting behavior
- Data structure analysis
- Optimization impact measurements

## Requirements

Make sure you have configured your `.env` file with:
- `STEAM_API_KEY` and `STEAM_USERID_64` for Steam tests
- `GOG_PUBLIC_USERNAME` for GOG tests
- `IGDB_CLIENT_ID` and `IGDB_SECRET` for IGDB tests

## Notes

- API exploration tests may fail due to rate limiting (HTTP 429)
- Steam tests include built-in rate limiting (1.5s between requests)
- GOG tests use public API (no authentication required)
- All tests are safe and read-only (no data modification)
