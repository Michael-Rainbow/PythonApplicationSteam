import unittest
from unittest.mock import patch, MagicMock, ANY
import os
import sys
import tkinter as tk
import tempfile
import shutil
import threading
import time
import queue

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import the modules to test
import PythonApplicationSteam
import Funcs

class TestSteamAppIntegration(unittest.TestCase):
    """Integration tests for the Steam Application"""
    
    def setUp(self):
        """Set up test environment"""
        # Setup API key for testing
        if not os.getenv('STEAM_API_KEY'):
            os.environ['STEAM_API_KEY'] = 'test_api_key'
        
        # Create a temporary cache directory
        self.temp_dir = tempfile.mkdtemp()
        self.original_cache_dir = PythonApplicationSteam.CACHE_DIR
        PythonApplicationSteam.CACHE_DIR = self.temp_dir
        
        # Sample data for testing
        self.test_steam_id = "76561198000000000"
        self.test_appid = 440
        self.test_game_name = "Team Fortress 2"
        
        # Create test games data
        self.test_games = [
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
        
        # Create test achievements data
        self.test_achievements = [
            {
                'apiname': 'ACH1',
                'achieved': 1,
                'name': 'Achievement 1',
                'description': 'Description 1',
                'icon': 'http://example.com/icon1.jpg'
            },
            {
                'apiname': 'ACH2',
                'achieved': 0,
                'name': 'Achievement 2',
                'description': 'Description 2',
                'icongray': 'http://example.com/icon2_gray.jpg'
            }
        ]
        
        self.test_global_achievements = [
            {'name': 'ACH1', 'percent': 55.5},
            {'name': 'ACH2', 'percent': 22.2}
        ]
        
        # Initialize root and app
        self.root = tk.Tk()
        self.app = PythonApplicationSteam.SteamApp(self.root)
        
    def tearDown(self):
        """Clean up after tests"""
        # Destroy tkinter objects
        self.root.destroy()
        
        # Restore original cache directory
        PythonApplicationSteam.CACHE_DIR = self.original_cache_dir
        
        # Clean up temp directory
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    @patch('Funcs.get_owned_games')
    def test_search_to_game_list(self, mock_get_games):
        """Test the flow from search to displaying game list"""
        # Setup mock
        mock_get_games.return_value = self.test_games
        
        # Prepare input
        self.app.steam_id_entry.delete(0, tk.END)
        self.app.steam_id_entry.insert(0, self.test_steam_id)
        
        # Execute the search in a separate thread to avoid blocking
        search_thread = threading.Thread(target=self.app.search_user, args=(self.test_steam_id,))
        search_thread.daemon = True
        search_thread.start()
        search_thread.join(timeout=1.0)  # Wait for search to complete
        
        # Process the queue to update UI
        self.app.check_queue()
        self.root.update()
        
        # Verify results
        self.assertEqual(len(self.app.games), 2)
        
        # Since UI testing in unit tests is limited, we mainly check that buttons were created
        self.assertGreater(len(self.app.game_buttons), 0)
    
    @patch('Funcs.get_player_achievements')
    @patch('Funcs.get_global_achievements')
    def test_achievements_flow(self, mock_global, mock_player):
        """Test the flow for displaying achievements"""
        # Setup mocks
        mock_player.return_value = self.test_achievements
        mock_global.return_value = self.test_global_achievements
        
        # Execute achievement retrieval
        self.app.show_achievements(self.test_steam_id, self.test_appid, self.test_game_name)
        
        # Process the queue to update UI
        self.app.check_queue()
        self.root.update()
        
        # Because UI testing is limited, we mainly ensure the message was processed
        msg = self.app.queue.get_nowait()
        self.assertEqual(msg['type'], 'achievements_result')
        self.assertEqual(msg['game_name'], self.test_game_name)
        self.assertEqual(len(msg['achievements']), 2)
    
    @patch('Funcs.get_owned_games')
    @patch('Funcs.get_player_achievements')
    @patch('Funcs.get_global_achievements') 
    def test_end_to_end_flow(self, mock_global, mock_player, mock_get_games):
        """Test the complete flow from search to achievements"""
        # Setup mocks
        mock_get_games.return_value = self.test_games
        mock_player.return_value = self.test_achievements
        mock_global.return_value = self.test_global_achievements
        
        # Prepare test
        self.app.steam_id_entry.delete(0, tk.END)
        self.app.steam_id_entry.insert(0, self.test_steam_id)
        
        # Start search
        self.app.search_user(self.test_steam_id)
        
        # Process queue for search results
        self.app.check_queue()
        
        # Normally the UI would trigger showing achievements for a specific game
        # We'll manually trigger it for testing
        game = self.test_games[0]
        self.app.show_achievements(self.test_steam_id, game['appid'], game['name'])
        
        # Process queue for achievement results
        self.app.check_queue()
        
        # Verify calls to API functions
        mock_get_games.assert_called_once_with(self.test_steam_id)
        mock_player.assert_called_once_with(self.test_steam_id, self.test_appid)
        mock_global.assert_called_once_with(self.test_appid)

class TestSteamAPIIntegration(unittest.TestCase):
    """Integration tests for Steam API functions"""
    
    @patch('requests.get')
    def test_api_functions_integration(self, mock_get):
        """Test the integration between the Steam API functions"""
        # Setup test data
        test_steam_id = "76561198000000000"
        test_appid = 440
        
        # Setup environment
        os.environ['STEAM_API_KEY'] = 'test_api_key'
        
        # Setup mock responses
        def get_mock_response(url, params=None, **kwargs):
            """Create appropriate mock responses based on URL"""
            mock_response = MagicMock()
            mock_response.status_code = 200
            
            if "GetOwnedGames" in url:
                # Mock owned games response
                mock_response.json.return_value = {
                    'response': {
                        'game_count': 2,
                        'games': [
                            {'appid': 440, 'name': 'Team Fortress 2', 'playtime_forever': 1000},
                            {'appid': 570, 'name': 'Dota 2', 'playtime_forever': 2000}
                        ]
                    }
                }
            elif "GetPlayerAchievements" in url:
                # Mock player achievements response
                mock_response.json.return_value = {
                    'playerstats': {
                        'success': True,
                        'gameName': 'Team Fortress 2',
                        'achievements': [
                            {'apiname': 'ACH1', 'achieved': 1, 'name': 'Achievement 1'},
                            {'apiname': 'ACH2', 'achieved': 0, 'name': 'Achievement 2'}
                        ]
                    }
                }
            elif "GetGlobalAchievementPercentagesForApp" in url:
                # Mock global achievements response
                mock_response.json.return_value = {
                    'achievementpercentages': {
                        'achievements': [
                            {'name': 'ACH1', 'percent': 55.5},
                            {'name': 'ACH2', 'percent': 22.2}
                        ]
                    }
                }
            
            return mock_response
        
        # Set the side effect to call our function
        mock_get.side_effect = get_mock_response
        
        # Test integration flow
        
        # 1. Get owned games
        games = Funcs.get_owned_games(test_steam_id)
        self.assertIsNotNone(games)
        self.assertEqual(len(games), 2)
        
        # 2. Pick first game
        first_game = games[0]
        self.assertEqual(first_game['appid'], 440)
        
        # 3. Get player achievements for that game
        achievements = Funcs.get_player_achievements(test_steam_id, first_game['appid'])
        self.assertIsNotNone(achievements)
        self.assertEqual(len(achievements), 2)
        
        # 4. Get global achievement stats for comparison
        global_achievements = Funcs.get_global_achievements(first_game['appid'])
        self.assertIsNotNone(global_achievements)
        self.assertEqual(len(global_achievements), 2)
        
        # Verify API functions were called with correct parameters
        self.assertEqual(mock_get.call_count, 3)

if __name__ == '__main__':
    unittest.main()
