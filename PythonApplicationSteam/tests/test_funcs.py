import unittest
from unittest.mock import patch, MagicMock
import os
import sys
import json
import requests

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import the module to test
import Funcs

class TestFuncs(unittest.TestCase):
    """Test cases for the Steam API functions in Funcs.py"""
    
    def setUp(self):
        # Setup common test data
        self.test_steam_id = "76561198000000000"
        self.test_appid = 440  # Team Fortress 2
        
        # Ensure API_KEY is available for tests
        if not os.getenv('STEAM_API_KEY'):
            os.environ['STEAM_API_KEY'] = 'test_api_key'
        
    def tearDown(self):
        # Clean up after tests
        pass
        
    @patch('requests.get')
    def test_get_owned_games_success(self, mock_get):
        """Test get_owned_games function with a successful response"""
        # Prepare mock response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'response': {
                'game_count': 2,
                'games': [
                    {
                        'appid': 440,
                        'name': 'Team Fortress 2',
                        'playtime_forever': 1000
                    },
                    {
                        'appid': 570,
                        'name': 'Dota 2',
                        'playtime_forever': 2000
                    }
                ]
            }
        }
        mock_get.return_value = mock_response
        
        # Call function
        result = Funcs.get_owned_games(self.test_steam_id)
        
        # Verify function behavior
        mock_get.assert_called_once()
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]['appid'], 440)
        self.assertEqual(result[1]['name'], 'Dota 2')
        
    @patch('requests.get')
    def test_get_owned_games_private_profile(self, mock_get):
        """Test get_owned_games function with a private profile response"""
        # Prepare mock response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'response': {}  # No games key indicates private profile
        }
        mock_get.return_value = mock_response
        
        # Call function
        result = Funcs.get_owned_games(self.test_steam_id)
        
        # Verify function behavior
        self.assertIsNone(result)
        
    @patch('requests.get')
    def test_get_owned_games_request_exception(self, mock_get):
        """Test get_owned_games function handles request exceptions"""
        # Prepare mock to raise exception
        mock_get.side_effect = requests.RequestException("API error")
        
        # Call function
        result = Funcs.get_owned_games(self.test_steam_id)
        
        # Verify function behavior
        self.assertIsNone(result)

    @patch('requests.get')
    def test_get_player_achievements_success(self, mock_get):
        """Test get_player_achievements function with a successful response"""
        # Prepare mock response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'playerstats': {
                'success': True,
                'gameName': 'Team Fortress 2',
                'achievements': [
                    {
                        'apiname': 'TF_PLAY_GAME_EVERYCLASS',
                        'achieved': 1,
                        'name': 'Head of the Class',
                        'description': 'Play a complete round with all 9 classes.'
                    },
                    {
                        'apiname': 'TF_PLAY_GAME_FRIENDSONLY',
                        'achieved': 0,
                        'name': 'With Friends Like these...',
                        'description': 'Play in a game with 7 or more players from your friends list.'
                    }
                ]
            }
        }
        mock_get.return_value = mock_response
        
        # Call function
        result = Funcs.get_player_achievements(self.test_steam_id, self.test_appid)
        
        # Verify function behavior
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]['name'], 'Head of the Class')
        self.assertEqual(result[1]['achieved'], 0)
        
    @patch('requests.get')
    def test_get_player_achievements_not_successful(self, mock_get):
        """Test get_player_achievements function with unsuccessful response"""
        # Prepare mock response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'playerstats': {
                'success': False,
                'error': 'Requested app has no stats'
            }
        }
        mock_get.return_value = mock_response
        
        # Call function
        result = Funcs.get_player_achievements(self.test_steam_id, self.test_appid)
        
        # Verify function behavior
        self.assertEqual(result, [])
        
    @patch('requests.get')
    def test_get_player_achievements_request_exception(self, mock_get):
        """Test get_player_achievements function handles request exceptions"""
        # Prepare mock to raise exception
        mock_get.side_effect = requests.RequestException("API error")
        
        # Call function
        result = Funcs.get_player_achievements(self.test_steam_id, self.test_appid)
        
        # Verify function behavior
        self.assertEqual(result, [])

    @patch('requests.get')
    def test_get_global_achievements_success(self, mock_get):
        """Test get_global_achievements function with a successful response"""
        # Prepare mock response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'achievementpercentages': {
                'achievements': [
                    {
                        'name': 'TF_PLAY_GAME_EVERYCLASS',
                        'percent': 32.2
                    },
                    {
                        'name': 'TF_PLAY_GAME_FRIENDSONLY',
                        'percent': 14.7
                    }
                ]
            }
        }
        mock_get.return_value = mock_response
        
        # Call function
        result = Funcs.get_global_achievements(self.test_appid)
        
        # Verify function behavior
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]['name'], 'TF_PLAY_GAME_EVERYCLASS')
        self.assertEqual(result[1]['percent'], 14.7)
        
    @patch('requests.get')
    def test_get_global_achievements_request_exception(self, mock_get):
        """Test get_global_achievements function handles request exceptions"""
        # Prepare mock to raise exception
        mock_get.side_effect = requests.RequestException("API error")
        
        # Call function
        result = Funcs.get_global_achievements(self.test_appid)
        
        # Verify function behavior
        self.assertEqual(result, [])

if __name__ == '__main__':
    unittest.main()
