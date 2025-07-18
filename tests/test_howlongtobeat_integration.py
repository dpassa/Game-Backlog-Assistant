import unittest
from unittest.mock import patch, Mock
from howlongtobeat_integration import get_timetocompelete

class TestGetTimeToComplete(unittest.TestCase):
    
    @patch('howlongtobeat_integration.requests.post')
    def test_successful_response(self, mock_post):
        # Mock successful API response
        mock_response = Mock()
        mock_response.json.return_value = {
            'data': [{'comp_main': 7200}]  # 2 hours in seconds
        }
        mock_post.return_value = mock_response
        
        result = get_timetocompelete("Test Game")
        
        self.assertEqual(result, 2.0)
        mock_post.assert_called_once()
    
    @patch('howlongtobeat_integration.requests.post')
    def test_debug_mode(self, mock_post):
        # Mock successful API response
        mock_response = Mock()
        mock_response.json.return_value = {
            'data': [{'comp_main': 10800}]  # 3 hours in seconds
        }
        mock_post.return_value = mock_response
        
        with patch('builtins.print') as mock_print:
            result = get_timetocompelete("Test Game", debug=True)
            
            self.assertEqual(result, 3.0)
            mock_print.assert_called_once_with("Game Compeletion Time: 3.0")
    
    @patch('howlongtobeat_integration.requests.post')
    def test_empty_data_response(self, mock_post):
        # Mock API response with empty data
        mock_response = Mock()
        mock_response.json.return_value = {'data': []}
        mock_post.return_value = mock_response
        
        result = get_timetocompelete("Nonexistent Game")
        
        self.assertEqual(result, 0)
    
    @patch('howlongtobeat_integration.requests.post')
    def test_invalid_json_response(self, mock_post):
        # Mock API response that raises an exception
        mock_response = Mock()
        mock_response.json.side_effect = ValueError("Invalid JSON")
        mock_post.return_value = mock_response
        
        result = get_timetocompelete("Test Game")
        
        self.assertEqual(result, 0)
    
    @patch('howlongtobeat_integration.requests.post')
    def test_network_error(self, mock_post):
        # Mock network error
        mock_post.side_effect = Exception("Network error")
        
        result = get_timetocompelete("Test Game")
        
        self.assertEqual(result, 0)
    
    @patch('howlongtobeat_integration.requests.post')
    def test_game_title_with_spaces(self, mock_post):
        # Test that game title is properly split
        mock_response = Mock()
        mock_response.json.return_value = {
            'data': [{'comp_main': 3600}]  # 1 hour in seconds
        }
        mock_post.return_value = mock_response
        
        result = get_timetocompelete("Grand Theft Auto")
        
        # Verify the request was made with properly split game name
        _, kwargs = mock_post.call_args
        self.assertEqual(kwargs['json']['searchTerms'], ['Grand', 'Theft', 'Auto'])
        self.assertEqual(result, 1.0)


if __name__ == '__main__':
    unittest.main()