import unittest
from unittest.mock import patch, Mock
from steam_integration import SteamIntegration

class TestSteamIntegration(unittest.TestCase):
    def setUp(self):
        self.api_key = "test_api_key"
        self.steamid = "test_steamid"
        self.steam_integration = SteamIntegration(self.api_key, self.steamid)

    def test_init(self):
        self.assertEqual(self.steam_integration.api_key, self.api_key)
        self.assertEqual(self.steam_integration.steamid, self.steamid)

    @patch('steam_integration.requests.get')
    def test_get_owned_games_success(self, mock_get):
        mock_response = Mock()
        mock_response.json.return_value = {
            'response': {
                'games': [
                    {'appid': 123, 'name': 'Test Game'},
                    {'appid': 456, 'name': 'Another Game'}
                ]
            }
        }
        mock_get.return_value = mock_response

        result = self.steam_integration.get_owned_games()

        expected_url = f'https://api.steampowered.com/IPlayerService/GetOwnedGames/v1/?key={self.api_key}&steamid={self.steamid}&include_appinfo=true'
        mock_get.assert_called_once_with(expected_url)
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]['appid'], 123)

    @patch('steam_integration.requests.get')
    def test_get_game_info_success(self, mock_get):
        appid = 123
        mock_response = Mock()
        mock_response.json.return_value = {
            '123': {
                'data': {
                    'name': 'Test Game',
                    'type': 'game'
                }
            }
        }
        mock_get.return_value = mock_response

        result = self.steam_integration.get_game_info(appid)

        expected_url = f'https://store.steampowered.com/api/appdetails?appids={appid}'
        mock_get.assert_called_once_with(expected_url)
        self.assertEqual(result['name'], 'Test Game')

    @patch('steam_integration.requests.get')
    def test_get_game_info_no_data_key(self, mock_get):
        appid = 123
        mock_response = Mock()
        mock_response.json.return_value = {
            '123': {}
        }
        mock_get.return_value = mock_response

        with patch('builtins.print') as mock_print:
            result = self.steam_integration.get_game_info(appid)
            mock_print.assert_called_once_with(f"Error: 'data' key not found in response for appid {appid}")

        self.assertIsNone(result)

    @patch('steam_integration.requests.get')
    def test_get_game_info_empty_response(self, mock_get):
        appid = 123
        mock_response = Mock()
        mock_response.json.return_value = None
        mock_get.return_value = mock_response

        with patch('builtins.print') as mock_print:
            result = self.steam_integration.get_game_info(appid)
            mock_print.assert_called_once_with(f"Error: 'data' key not found in response for appid {appid}")

        self.assertIsNone(result)

    @patch('steam_integration.requests.get')
    def test_get_game_info_json_error(self, mock_get):
        appid = 123
        mock_response = Mock()
        mock_response.json.side_effect = ValueError("Invalid JSON")
        mock_get.return_value = mock_response

        with patch('builtins.print') as mock_print:
            result = self.steam_integration.get_game_info(appid)
            mock_print.assert_called_once_with(f"Error: Unable to parse JSON response for appid {appid}")

        self.assertIsNone(result)

    @patch('steam_integration.requests.get')
    def test_get_game_info_type_error(self, mock_get):
        appid = 123
        mock_response = Mock()
        mock_response.json.side_effect = TypeError("Not JSON")
        mock_get.return_value = mock_response

        with patch('builtins.print') as mock_print:
            result = self.steam_integration.get_game_info(appid)
            mock_print.assert_called_once_with(f"Error: Response for appid {appid} is not JSON")

        self.assertIsNone(result)

if __name__ == '__main__':
    unittest.main()