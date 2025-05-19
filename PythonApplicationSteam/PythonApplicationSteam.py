import requests
import tkinter as tk
from tkinter import messagebox, Scrollbar, Canvas, Frame
from PIL import Image, ImageTk
import io
import os
import threading
import logging
import Funcs
from queue import Queue, Empty
#import PIL.UnidentifiedImageError

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
# Performance: INFO level reduces logging overhead in production while retaining useful info.

# Steam API key from environment variable
API_KEY = os.getenv('STEAM_API_KEY')
if not API_KEY:
    raise ValueError("STEAM_API_KEY environment variable not set")
# Security: Using environment variable prevents hardcoding sensitive API key.
# Design Rationale: Fail early if key is missing to avoid runtime issues.

# Cache directory for images
CACHE_DIR = 'image_cache'
if not os.path.exists(CACHE_DIR):
    try:
        os.makedirs(CACHE_DIR)
    except OSError as e:
        logging.error(f"Failed to create cache directory {CACHE_DIR}: {e}")
        raise
# Design Rationale: Early check ensures cache directory is writable.

def download_image(url, cache_path, resize_dims=(184, 69)):
    """Download and cache an image, return ImageTk.PhotoImage with specified resize dimensions."""
    try:
        if os.path.exists(cache_path):
            with open(cache_path, 'rb') as f:
                img_data = f.read()
        else:
            response = requests.get(url, timeout=5)
            response.raise_for_status()
            img_data = response.content
            try:
                with open(cache_path, 'wb') as f:
                    f.write(img_data)
            except OSError as e:
                logging.error(f"Cannot write to cache {cache_path}: {e}")
                return None
        try:
            img = Image.open(io.BytesIO(img_data))
            img = img.resize(resize_dims, Image.LANCZOS)
            return ImageTk.PhotoImage(img)
        except PIL.UnidentifiedImageError as e:
            logging.error(f"Invalid image data for {url}: {e}")
            return None
    except requests.RequestException as e:
        logging.error(f"Failed to download image {url}: {e}")
        return None
# Performance: Flexible resize_dims parameter avoids redundant image processing.
# Design Rationale: Specific exception handling improves debugging and robustness.
# Performance: Caching reduces API calls; timeout of 5s balances reliability and speed.


class SteamApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Steam User Game and Achievement Viewer")
        self.root.geometry("800x600")
        # Design Rationale: Fixed size is simple; consider resizable UI for future scalability.

        self.queue = Queue()
        self.image_queue = Queue()  # For lazy loading images
        # Performance: Separate queue for image loading enables asynchronous UI updates.

        # Placeholder image for failed downloads
        self.placeholder_img = ImageTk.PhotoImage(Image.new('RGB', (64, 64), color='gray'))
        # Design Rationale: Placeholder improves UX when images fail to load.

        # SteamID entry and search button
        self.steam_id_entry = tk.Entry(root, width=30)
        self.steam_id_entry.pack(pady=10)
        self.steam_id_entry.insert(0, "Enter SteamID64")

        self.search_button = tk.Button(root, text="Search", command=self.start_search)
        self.search_button.pack(pady=5)

        # Loading label
        self.loading_label = tk.Label(root, text="")
        self.loading_label.pack(pady=5)

        # Canvas for scrollable game list
        self.canvas = Canvas(root, height=300)
        self.scrollbar = Scrollbar(root, orient="vertical", command=self.canvas.yview)
        self.scrollable_frame = Frame(self.canvas)

        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )

        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        self.canvas.pack(side="top", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")

        # Achievement display frame
        self.achievement_frame = Frame(root)
        self.achievement_frame.pack(side="bottom", fill="both", expand=True)

        self.games = []
        self.game_buttons = []
        self.achievement_labels = []

        # Start queue checkers
        self.check_queue()
        self.check_image_queue()
        # Performance: Separate queue for images allows lazy loading without blocking main UI.

    def check_queue(self):
        """Check for messages in the main queue to update the UI."""
        assert threading.current_thread() == threading.main_thread(), "UI updates must occur in main thread"
        try:
            msg = self.queue.get_nowait()
            if msg['type'] == 'search_result':
                self.handle_search_result(msg['steam_id'], msg['games'])
            elif msg['type'] == 'achievements_result':
                self.handle_achievements_result(msg['steam_id'], msg['appid'], msg['game_name'], msg['achievements'], msg['global_achievements'])
            elif msg['type'] == 'error':
                self.loading_label.config(text="")
                messagebox.showerror("Error", msg['message'])
        except Empty:
            pass
        self.root.after(100, self.check_queue)
        # Performance: 100ms polling is efficient; thread safety assertion prevents future bugs.

    def check_image_queue(self):
        """Check for lazy-loaded images to update UI."""
        assert threading.current_thread() == threading.main_thread(), "UI updates must occur in main thread"
        try:
            msg = self.image_queue.get_nowait()
            widget = msg['widget']
            photo = msg['photo']
            if photo:
                widget.config(image=photo)
                widget.image = photo  # Preserve reference
            else:
                widget.config(image=self.placeholder_img)
                widget.image = self.placeholder_img
        except Empty:
            pass
        self.root.after(100, self.check_image_queue)
        # Performance: Lazy loading images improves initial UI rendering speed.

    def clear_games(self):
        """Clear the game list."""
        for button in self.game_buttons:
            button.destroy()
        self.game_buttons = []
        # Performance: Frees memory for large game lists.

    def clear_achievements(self):
        """Clear the achievement display."""
        for label in self.achievement_labels:
            label.destroy()
        self.achievement_labels = []

    def start_search(self):
        """Start a threaded search for a user's games."""
        steam_id = self.steam_id_entry.get().strip()
        if not steam_id.isdigit() or len(steam_id) != 17:
            messagebox.showerror("Error", "Please enter a valid 17-digit SteamID64")
            return

        self.clear_games()
        self.clear_achievements()
        self.loading_label.config(text="Loading games...")
        self.search_button.config(state='disabled')

        threading.Thread(target=self.search_user, args=(steam_id,), daemon=True).start()

    def search_user(self, steam_id):
        """Search for a user's games in a separate thread."""
        games = Funcs.get_owned_games(steam_id)
        if games is None:
            self.queue.put({
                'type': 'error',
                'message': "Could not fetch games. Ensure the SteamID is valid and the profile is public."
            })
        else:
            self.queue.put({
                'type': 'search_result',
                'steam_id': steam_id,
                'games': games
            })
        # Design Rationale: Specific error message guides user to check profile privacy.

    def handle_search_result(self, steam_id, games):
        """Handle the search result in the main thread."""
        assert threading.current_thread() == threading.main_thread(), "UI updates must occur in main thread"
        self.loading_label.config(text="")
        self.search_button.config(state='normal')

        self.games = games
        for game in self.games:
            appid = game['appid']
            name = game['name']
            img_url = f"https://steamcdn-a.akamaihd.net/steam/apps/{appid}/header.jpg"
            cache_path = os.path.join(CACHE_DIR, f"{appid}.jpg")

            # Create button with placeholder image initially
            button = tk.Button(
                self.scrollable_frame,
                image=self.placeholder_img,
                text=name,
                compound="top",
                command=lambda a=appid, n=name: self.start_show_achievements(steam_id, a, n)
            )
            button.image = self.placeholder_img  # Initial reference
            button.pack(fill="x", pady=2)
            self.game_buttons.append(button)

            # Queue image loading in background
            threading.Thread(
                target=self.load_image_async,
                args=(img_url, cache_path, (184, 69), button),
                daemon=True
            ).start()
        # Performance: Lazy loading images prevents UI lag during initial rendering.
        # Design Rationale: Placeholder image ensures buttons render immediately.

    def load_image_async(self, url, cache_path, resize_dims, widget):
        """Load an image in a background thread and queue for UI update."""
        photo = download_image(url, cache_path, resize_dims)
        self.image_queue.put({'widget': widget, 'photo': photo})
        # Performance: Async image loading improves responsiveness for large game lists.

    def start_show_achievements(self, steam_id, appid, game_name):
        """Start a threaded fetch of achievements."""
        self.clear_achievements()
        self.loading_label.config(text="Loading achievements...")
        threading.Thread(target=self.show_achievements, args=(steam_id, appid, game_name), daemon=True).start()

    def show_achievements(self, steam_id, appid, game_name):
        """Fetch achievements in a separate thread."""
        achievements = Funcs.get_player_achievements(steam_id, appid)
        global_achievements = Funcs.get_global_achievements(appid)
        self.queue.put({
            'type': 'achievements_result',
            'steam_id': steam_id,
            'appid': appid,
            'game_name': game_name,
            'achievements': achievements,
            'global_achievements': global_achievements
        })

    def handle_achievements_result(self, steam_id, appid, game_name, achievements, global_achievements):
        """Handle the achievements result in the main thread."""
        assert threading.current_thread() == threading.main_thread(), "UI updates must occur in main thread"
        self.loading_label.config(text="")

        if not achievements:
            tk.Label(self.achievement_frame, text="No achievements available for this game.").pack()
            return

        tk.Label(self.achievement_frame, text=f"Achievements for {game_name}", font=("Arial", 14, "bold")).pack(pady=5)

        ach_canvas = Canvas(self.achievement_frame)
        ach_scrollbar = Scrollbar(self.achievement_frame, orient="vertical", command=ach_canvas.yview)
        ach_frame = Frame(ach_canvas)

        ach_frame.bind(
            "<Configure>",
            lambda e: ach_canvas.configure(scrollregion=ach_canvas.bbox("all"))
        )

        ach_canvas.create_window((0, 0), window=ach_frame, anchor="nw")
        ach_canvas.configure(yscrollcommand=ach_scrollbar.set)

        ach_canvas.pack(side="left", fill="both", expand=True)
        ach_scrollbar.pack(side="right", fill="y")

        global_percentages = {ach['name']: ach['percent'] for ach in global_achievements}

        for ach in achievements:
            ach_name = ach.get('apiname', 'Unknown')
            display_name = ach.get('name', ach_name)
            description = ach.get('description', 'No description')
            unlocked = ach.get('achieved', 0) == 1
            icon_url = ach.get('icon') if unlocked else ach.get('icongray')
            percent = global_percentages.get(ach_name, 'N/A')

            frame = Frame(ach_frame)
            status = "Unlocked" if unlocked else "Locked"
            color = "green" if unlocked else "gray"
            text = f"{display_name}\n{description}\nStatus: {status}\nGlobal Unlock: {percent}%"

            # Create label with placeholder image
            label = tk.Label(
                frame,
                image=self.placeholder_img,
                text=text,
                compound="left",
                anchor="w",
                justify="left",
                fg=color,
                wraplength=400
            )
            label.image = self.placeholder_img  # Initial reference
            label.pack(fill="x", pady=5)
            frame.pack(fill="x", padx=5)
            self.achievement_labels.append(frame)

            # Queue image loading in background
            if icon_url:
                cache_path = os.path.join(CACHE_DIR, f"{appid}_{ach_name}.jpg")
                threading.Thread(
                    target=self.load_image_async,
                    args=(icon_url, cache_path, (64, 64), label),
                    daemon=True
                ).start()
            # Performance: Lazy loading achievement icons reduces initial rendering time.
            # Design Rationale: Placeholder ensures UI renders smoothly while images load.

if __name__ == "__main__":
    root = tk.Tk()
    app = SteamApp(root)
    root.mainloop()

