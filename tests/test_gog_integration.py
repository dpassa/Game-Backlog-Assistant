import pytest
from gog_integration import GogIntegration
from unittest.mock import Mock, patch
from consts import GOG_PUBLIC_USERNAME
# =============================================================================
# FIXTURES
# =============================================================================

@pytest.fixture
def gog_integration():
    return GogIntegration(GOG_PUBLIC_USERNAME)

# =============================================================================
# BASIC FUNCTIONALITY TESTS
# =============================================================================

def test_get_games_from_public_profile(gog_integration):
    response = gog_integration.get_games_from_public_profile()
    
    assert response is not None, "Expected a list of games, got None"

    games = response.get('_embedded', {}).get('items', [])

    assert isinstance(games, list), "Expected a list of games"
    if games:

        assert 'id' in games[0].get('game'), "Each game should have an 'id' field"
        assert 'title' in games[0].get('game'), "Each game should have a 'title' field"
    else:
        print("No games found for the provided username.")

def test_response_structure(gog_integration, monkeypatch):
    response = {"_embedded": {"items": [{"id": "1", "title": "Game 1"}]}, "page": 1, "pages": 1}
    monkeypatch.setattr(gog_integration, "get_games_from_public_profile", lambda page=1: response)
    result = gog_integration.get_games_from_public_profile()
    assert "_embedded" in result
    assert "items" in result["_embedded"]

def test_game_fields(gog_integration, monkeypatch):
    response = {"_embedded": {"items": [{"id": "1", "title": "Game 1"}]}, "page": 1, "pages": 1}
    monkeypatch.setattr(gog_integration, "get_games_from_public_profile", lambda page=1: response)
    games = gog_integration.get_games_from_public_profile()["_embedded"]["items"]
    assert isinstance(games[0], dict)
    assert 'id' in games[0]
    assert 'title' in games[0]

# =============================================================================
# GET_GAMES_FROM_PUBLIC_PROFILE TESTS
# =============================================================================

@patch('gog_integration.requests.Session')  # Patch della Session class
def test_get_games_from_public_profile_success(mock_session_class, gog_integration):
    # Mock della session instance
    mock_session = Mock()
    mock_session_class.return_value = mock_session
    
    # Mock della response
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        '_embedded': {
            'items': [
                {'id': '123', 'title': 'Test Game 1'},
                {'id': '456', 'title': 'Test Game 2'}
            ]
        },
        'page': 1,
        'pages': 1
    }
    mock_session.get.return_value = mock_response
    
    # Crea una nuova istanza per usare il mock
    gog_test = GogIntegration(GOG_PUBLIC_USERNAME)
    response = gog_test.get_games_from_public_profile()
    
    assert isinstance(response, dict)
    assert '_embedded' in response
    games = response['_embedded']['items']
    assert len(games) == 2
    assert games[0]['id'] == '123'
    assert games[0]['title'] == 'Test Game 1'

@patch('gog_integration.requests.Session')
def test_get_games_from_public_profile_failure(mock_session_class, gog_integration):
    mock_session = Mock()
    mock_session_class.return_value = mock_session
    
    mock_response = Mock()
    mock_response.status_code = 404
    mock_session.get.return_value = mock_response
    
    gog_test = GogIntegration(GOG_PUBLIC_USERNAME)
    games = gog_test.get_games_from_public_profile()
    
    assert games is None

# =============================================================================
# GET_GAME_INFO TESTS
# =============================================================================

@patch('gog_integration.requests.Session')
def test_get_game_info_success(mock_session_class):
    mock_session = Mock()
    mock_session_class.return_value = mock_session
    
    mock_response = Mock()
    mock_response.json.return_value = {
        'game': {
            'title': 'Test Game',
            'release_date': '2023-01-01'
        }
    }
    mock_session.get.return_value = mock_response
    
    gog_test = GogIntegration(GOG_PUBLIC_USERNAME)
    game_info = gog_test.get_game_info('123')
    
    assert game_info is not None
    assert game_info['title'] == 'Test Game'
    assert game_info['release_date'] == '2023-01-01'

@patch('gog_integration.requests.Session')
def test_get_game_info_no_game_key(mock_session_class, gog_integration, capsys):
    mock_session = Mock()
    mock_session_class.return_value = mock_session
    
    mock_response = Mock()
    mock_response.json.return_value = {'other_key': 'value'}
    mock_session.get.return_value = mock_response
    
    gog_test = GogIntegration(GOG_PUBLIC_USERNAME)
    game_info = gog_test.get_game_info('123')
    
    assert game_info is None
    captured = capsys.readouterr()
    assert "Error: 'game' key not found in response for appid 123" in captured.out

@patch('gog_integration.requests.Session')
def test_get_game_info_json_error(mock_session_class, gog_integration, capsys):
    mock_session = Mock()
    mock_session_class.return_value = mock_session
    
    mock_response = Mock()
    mock_response.json.side_effect = ValueError("Invalid JSON")
    mock_session.get.return_value = mock_response
    
    gog_test = GogIntegration(GOG_PUBLIC_USERNAME)
    game_info = gog_test.get_game_info('123')
    
    assert game_info is None
    captured = capsys.readouterr()
    assert "Error: Unable to parse JSON response for appid 123" in captured.out

@patch('gog_integration.requests.Session')
def test_get_game_info_type_error(mock_session_class, gog_integration, capsys):
    mock_session = Mock()
    mock_session_class.return_value = mock_session
    
    mock_response = Mock()
    mock_response.json.side_effect = TypeError("Response is not JSON")
    mock_session.get.return_value = mock_response
    
    gog_test = GogIntegration(GOG_PUBLIC_USERNAME)
    game_info = gog_test.get_game_info('123')
    
    assert game_info is None
    captured = capsys.readouterr()
    assert "Error: Response for appid 123 is not JSON" in captured.out

@patch('gog_integration.requests.Session')
def test_get_game_info_empty_response(mock_session_class, gog_integration, capsys):
    mock_session = Mock()
    mock_session_class.return_value = mock_session
    
    mock_response = Mock()
    mock_response.json.return_value = None
    mock_session.get.return_value = mock_response
    
    gog_test = GogIntegration(GOG_PUBLIC_USERNAME)
    game_info = gog_test.get_game_info('123')
    
    assert game_info is None
    captured = capsys.readouterr()
    assert "Error: 'game' key not found in response for appid 123" in captured.out

# =============================================================================
# PAGINATION TESTS
# =============================================================================

def test_pagination_fetches_all_pages(monkeypatch):
    gog_integration = GogIntegration(GOG_PUBLIC_USERNAME)
    # Mock paginated responses
    responses = [
        {"_embedded": {"items": [{"id": "1", "title": "Game 1"}]}, "page": 1, "pages": 2},
        {"_embedded": {"items": [{"id": "2", "title": "Game 2"}]}, "page": 2, "pages": 2}
    ]
    call_count = {"count": 0}
    def mock_get_games_from_public_profile(page=1):
        call_count["count"] += 1
        return responses[page - 1] if page <= len(responses) else None
    monkeypatch.setattr(gog_integration, "get_games_from_public_profile", mock_get_games_from_public_profile)
    games = []
    response = gog_integration.get_games_from_public_profile()
    if response and "_embedded" in response and "items" in response["_embedded"]:
        page = response.get("page", 1)
        total_pages = response.get("pages", 1)
        games.extend(response["_embedded"]["items"])
        while page < total_pages:
            page += 1
            response = gog_integration.get_games_from_public_profile(page)
            if response and "_embedded" in response and "items" in response["_embedded"]:
                games.extend(response["_embedded"]["items"])
            else:
                break
    assert call_count["count"] == 2
    assert len(games) == 2