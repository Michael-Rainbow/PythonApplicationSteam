import unittest
from unittest.mock import patch, MagicMock, ANY
import os
import sys
import tkinter as tk
import PIL
from PIL import Image, ImageTk
from io import BytesIO
import threading
import requests
import json
import tempfile
import shutil

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import the module to test
import PythonApplicationSteam

class TestSteamApp(unittest.TestCase):
    """Test cases for the SteamApp class in PythonApplicationSteam.py"""
    
    def setUp(self):
        """Set up test environment"""
        # Setup test environment variables
        if not os.getenv('STEAM_API_KEY'):
            os.environ['STEAM_API_KEY'] = 'test_api_key'
        
        # Create a temporary cache directory for testing
        self.temp_cache_dir = tempfile.mkdtemp()
        self.original_cache_dir = PythonApplicationSteam.CACHE_DIR
        PythonApplicationSteam.CACHE_DIR = self.temp_cache_dir
        
        # Initialize root and app for testing
        self.root = tk.Tk()
        self.app = PythonApplicationSteam.SteamApp(self.root)
        
        # Test data
        self.test_steam_id = "76561198000000000"
        self.test_appid = 440
        self.test_game_name = "Team Fortress 2"
        
    def tearDown(self):
        """Clean up after tests"""
        # Close tkinter root
        self.root.destroy()
        
        # Restore original cache directory
        PythonApplicationSteam.CACHE_DIR = self.original_cache_dir
        
        # Remove temporary cache directory
        shutil.rmtree(self.temp_cache_dir, ignore_errors=True)

    def test_init(self):
        """Test SteamApp initialization"""
        self.assertEqual(self.app.root.title(), "Steam User Game and Achievement Viewer")
        self.assertIsNotNone(self.app.queue)
        self.assertIsNotNone(self.app.image_queue)
        self.assertIsNotNone(self.app.placeholder_img)
        self.assertEqual(len(self.app.game_buttons), 0)
        
    @patch('PythonApplicationSteam.threading.Thread')
    def test_start_search(self, mock_thread):
        """Test start_search method with valid SteamID"""
        # Set up test
        self.app.steam_id_entry.delete(0, tk.END)
        self.app.steam_id_entry.insert(0, self.test_steam_id)
        
        # Call method
        self.app.start_search()
        
        # Verify behavior
        mock_thread.assert_called_once()
        self.assertEqual(self.app.loading_label.cget("text"), "Loading games...")
        self.assertEqual(self.app.search_button.cget("state"), "disabled")
        
    def test_start_search_invalid_id(self):
        """Test start_search method with invalid SteamID"""
        # Set up test with invalid ID (not 17 digits)
        self.app.steam_id_entry.delete(0, tk.END)
        self.app.steam_id_entry.insert(0, "123")
        
        # Need to patch the messagebox to avoid actual dialog
        with patch('tkinter.messagebox.showerror') as mock_error:
            self.app.start_search()
            mock_error.assert_called_once()
            
        # Verify state
        self.assertNotEqual(self.app.loading_label.cget("text"), "Loading games...")
        self.assertNotEqual(self.app.search_button.cget("state"), "disabled")
        
    @patch('Funcs.get_owned_games')
    def test_search_user_success(self, mock_get_games):
        """Test search_user method with successful response"""
        # Prepare mock response
        mock_games = [
            {'appid': 440, 'name': 'Team Fortress 2', 'playtime_forever': 1000},
            {'appid': 570, 'name': 'Dota 2', 'playtime_forever': 2000}
        ]
        mock_get_games.return_value = mock_games
        
        # Call method
        self.app.search_user(self.test_steam_id)
        
        # Check queue message
        msg = self.app.queue.get()
        self.assertEqual(msg['type'], 'search_result')
        self.assertEqual(msg['steam_id'], self.test_steam_id)
        self.assertEqual(len(msg['games']), 2)
        
    @patch('Funcs.get_owned_games')
    def test_search_user_failure(self, mock_get_games):
        """Test search_user method when games cannot be fetched"""
        # Prepare mock response
        mock_get_games.return_value = None
        
        # Call method
        self.app.search_user(self.test_steam_id)
        
        # Check queue message
        msg = self.app.queue.get()
        self.assertEqual(msg['type'], 'error')
        self.assertIn("profile is public", msg['message'])
        
    @patch('PythonApplicationSteam.download_image')
    @patch('threading.Thread')
    def test_handle_search_result(self, mock_thread, mock_download):
        """Test handle_search_result method"""
        # Prepare test data
        test_games = [
            {'appid': 440, 'name': 'Team Fortress 2'},
            {'appid': 570, 'name': 'Dota 2'}
        ]
        
        # Call method
        self.app.handle_search_result(self.test_steam_id, test_games)
        
        # Verify behavior
        self.assertEqual(self.app.loading_label.cget("text"), "")
        self.assertEqual(self.app.search_button.cget("state"), "normal")
        self.assertEqual(len(self.app.game_buttons), 2)
        self.assertEqual(len(self.app.games), 2)
        self.assertEqual(mock_thread.call_count, 2)  # One thread per game for image loading
        
    @patch('Funcs.get_player_achievements')
    @patch('Funcs.get_global_achievements')
    def test_show_achievements(self, mock_global, mock_player):
        """Test show_achievements method"""
        # Prepare mock responses
        mock_player.return_value = [
            {
                'apiname': 'ACH1',
                'achieved': 1,
                'name': 'Achievement 1',
                'description': 'Description 1'
            },
            {
                'apiname': 'ACH2',
                'achieved': 0,
                'name': 'Achievement 2',
                'description': 'Description 2'
            }
        ]
        
        mock_global.return_value = [
            {'name': 'ACH1', 'percent': 55.5},
            {'name': 'ACH2', 'percent': 22.2}
        ]
        
        # Call method
        self.app.show_achievements(self.test_steam_id, self.test_appid, self.test_game_name)
        
        # Check queue message
        msg = self.app.queue.get()
        self.assertEqual(msg['type'], 'achievements_result')
        self.assertEqual(msg['steam_id'], self.test_steam_id)
        self.assertEqual(msg['appid'], self.test_appid)
        self.assertEqual(msg['game_name'], self.test_game_name)
        self.assertEqual(len(msg['achievements']), 2)
        self.assertEqual(len(msg['global_achievements']), 2)
        
    def test_clear_games(self):
        """Test clear_games method"""
        # Create some dummy buttons 
        button1 = tk.Button(self.app.scrollable_frame)
        button2 = tk.Button(self.app.scrollable_frame)
        self.app.game_buttons = [button1, button2]
        
        # Call method
        self.app.clear_games()
        
        # Verify behavior
        self.assertEqual(len(self.app.game_buttons), 0)
        
    def test_clear_achievements(self):
        """Test clear_achievements method"""
        # Create some dummy labels
        label1 = tk.Label(self.app.achievement_frame)
        label2 = tk.Label(self.app.achievement_frame)
        self.app.achievement_labels = [label1, label2]
        
        # Call method
        self.app.clear_achievements()
        
        # Verify behavior
        self.assertEqual(len(self.app.achievement_labels), 0)

@patch('PIL.Image.open')
@patch('requests.get')
class TestDownloadImage(unittest.TestCase):
    """Test the download_image function"""
    
    def setUp(self):
        """Set up test environment"""
        # Create a temporary cache directory
        self.temp_dir = tempfile.mkdtemp()
        
    def tearDown(self):
        """Clean up test environment"""
        # Remove temporary directory
        shutil.rmtree(self.temp_dir, ignore_errors=True)
        
    def test_download_image_success(self, mock_get, mock_image_open):
        """Test successful image download and processing"""
        # Setup test
        url = "http://example.com/image.jpg"
        cache_path = os.path.join(self.temp_dir, "test_image.jpg")
        
        # Mock response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.content = b'image_data'
        mock_get.return_value = mock_response
        
        # Mock PIL processing
        mock_img = MagicMock()
        mock_img.resize.return_value = mock_img
        mock_image_open.return_value = mock_img
        
        # Mock PhotoImage
        with patch('PIL.ImageTk.PhotoImage', return_value="photo_image") as mock_photo:
            result = PythonApplicationSteam.download_image(url, cache_path)
            
            # Verify behavior
            mock_get.assert_called_once()
            mock_image_open.assert_called_once()
            mock_img.resize.assert_called_once()
            mock_photo.assert_called_once()
            self.assertEqual(result, "photo_image")
            self.assertTrue(os.path.exists(cache_path))
            
    def test_download_image_from_cache(self, mock_get, mock_image_open):
        """Test image loading from cache"""
        # Setup test
        url = "http://example.com/image.jpg"
        cache_path = os.path.join(self.temp_dir, "test_image.jpg")
        
        # Create cached file
        with open(cache_path, 'wb') as f:
            f.write(b'cached_image_data')
            
        # Mock PIL processing
        mock_img = MagicMock()
        mock_img.resize.return_value = mock_img
        mock_image_open.return_value = mock_img
        
        # Mock PhotoImage
        with patch('PIL.ImageTk.PhotoImage', return_value="photo_image") as mock_photo:
            result = PythonApplicationSteam.download_image(url, cache_path)
            
            # Verify behavior
            mock_get.assert_not_called()  # Should not call requests.get
            mock_image_open.assert_called_once()
            self.assertEqual(result, "photo_image")
            
    def test_download_image_network_error(self, mock_get, mock_image_open):
        """Test handling of network errors"""
        # Setup test
        url = "http://example.com/image.jpg"
        cache_path = os.path.join(self.temp_dir, "test_image.jpg")
        
        # Mock network error
        mock_get.side_effect = requests.RequestException("Network error")
        
        # Call function
        result = PythonApplicationSteam.download_image(url, cache_path)
        
        # Verify behavior
        self.assertIsNone(result)
        mock_image_open.assert_not_called()
        
    def test_download_image_invalid_image(self, mock_get, mock_image_open):
        """Test handling of invalid image data"""
        # Setup test
        url = "http://example.com/image.jpg"
        cache_path = os.path.join(self.temp_dir, "test_image.jpg")
        
        # Mock response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.content = b'invalid_image_data'
        mock_get.return_value = mock_response
        
        # Mock image processing error
        mock_image_open.side_effect = PIL.UnidentifiedImageError("Invalid image")
        
        # Call function
        result = PythonApplicationSteam.download_image(url, cache_path)
        
        # Verify behavior
        self.assertIsNone(result)
        self.assertTrue(os.path.exists(cache_path))  # File should still be created

if __name__ == '__main__':
    unittest.main()
