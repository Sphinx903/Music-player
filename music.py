import tkinter as tk
from tkinter import filedialog, messagebox
from tkinter import ttk
import pygame
from mutagen.mp3 import MP3
import os
import random
import numpy as np
from scipy.signal import butter, lfilter
from pydub import AudioSegment
import io
from PIL import Image, ImageTk
import spotipy
from spotipy.oauth2 import SpotifyOAuth

# Initialize Pygame mixer
pygame.mixer.init()

# Spotify credentials
SPOTIPY_CLIENT_ID = '6eea2d3db0274919a70b34c2ae9e68d1'
SPOTIPY_CLIENT_SECRET = '1929aaae9c6c47a4b542cfa22278de00'
SPOTIPY_REDIRECT_URI = 'http://localhost:8888/callback'
SCOPE = 'user-library-read'

class MusicPlayer:
    def __init__(self, root):
        self.root = root
        self.root.title("Flexidoba")
        self.root.geometry("700x500")

        # Playlist and current song
        self.playlist = []
        self.current_song_index = 0

        # Whether repeat is on or off
        self.repeat_on = False

        # Equalizer gains (initially set to 0)
        self.bass_gain = 0.0
        self.mid_gain = 0.0
        self.treble_gain = 0.0

        # UI Elements
        self.create_widgets()

        # Initialize Spotify
        self.sp = spotipy.Spotify(auth_manager=SpotifyOAuth(client_id=SPOTIPY_CLIENT_ID,
                                                            client_secret=SPOTIPY_CLIENT_SECRET,
                                                            redirect_uri=SPOTIPY_REDIRECT_URI,
                                                            scope=SCOPE))
        self.spotify_playing = False
        self.spotify_results = []

    def create_widgets(self):
        # Frame to contain buttons
        button_frame = ttk.Frame(self.root)
        button_frame.pack(pady=20)

        # Resize images to standard size (example buttons)
        icon_size = (32, 32)
        load_image = Image.open("images/load_icon.png").resize(icon_size)
        self.load_icon = ImageTk.PhotoImage(load_image)
        self.load_button = ttk.Button(button_frame, image=self.load_icon, command=self.load_music)
        self.load_button.grid(row=0, column=0, padx=5)

        play_image = Image.open("images/play_icon.png").resize(icon_size)
        self.play_icon = ImageTk.PhotoImage(play_image)
        self.play_button = ttk.Button(button_frame, image=self.play_icon, command=self.play_music)
        self.play_button.grid(row=0, column=1, padx=5)

        pause_image = Image.open("images/pause_icon.png").resize(icon_size)
        self.pause_icon = ImageTk.PhotoImage(pause_image)
        self.pause_button = ttk.Button(button_frame, image=self.pause_icon, command=self.pause_music)
        self.pause_button.grid(row=0, column=2, padx=5)

        stop_image = Image.open("images/stop_icon.png").resize(icon_size)
        self.stop_icon = ImageTk.PhotoImage(stop_image)
        self.stop_button = ttk.Button(button_frame, image=self.stop_icon, command=self.stop_music)
        self.stop_button.grid(row=0, column=3, padx=5)

        prev_image = Image.open("images/prev_icon.png").resize(icon_size)
        self.prev_icon = ImageTk.PhotoImage(prev_image)
        self.prev_button = ttk.Button(button_frame, image=self.prev_icon, command=self.prev_song)
        self.prev_button.grid(row=0, column=5, padx=5)

        next_image = Image.open("images/next_icon.png").resize(icon_size)
        self.next_icon = ImageTk.PhotoImage(next_image)
        self.next_button = ttk.Button(button_frame, image=self.next_icon, command=self.next_song)
        self.next_button.grid(row=0, column=4, padx=5)

        shuffle_image = Image.open("images/shuffle_icon.png").resize(icon_size)
        self.shuffle_icon = ImageTk.PhotoImage(shuffle_image)
        self.shuffle_button = ttk.Button(button_frame, image=self.shuffle_icon, command=self.shuffle_playlist)
        self.shuffle_button.grid(row=0, column=6, padx=5)

        repeat_image = Image.open("images/repeat_icon.png").resize(icon_size)
        self.repeat_icon = ImageTk.PhotoImage(repeat_image)
        self.repeat_button = ttk.Button(button_frame, image=self.repeat_icon, command=self.toggle_repeat)
        self.repeat_button.grid(row=0, column=7, padx=5)

        # Equalizer controls
        eq_frame = ttk.Frame(self.root)
        eq_frame.pack(pady=10)

        self.bass_label = ttk.Label(eq_frame, text="Bass:")
        self.bass_label.grid(row=0, column=0, padx=5)

        self.bass_scale = ttk.Scale(eq_frame, from_=-10, to=10, orient=tk.HORIZONTAL, command=self.set_bass)
        self.bass_scale.grid(row=0, column=1, padx=5)
        self.bass_scale.set(0)  # Default bass gain

        self.mid_label = ttk.Label(eq_frame, text="Mid:")
        self.mid_label.grid(row=1, column=0, padx=5)

        self.mid_scale = ttk.Scale(eq_frame, from_=-10, to=10, orient=tk.HORIZONTAL, command=self.set_mid)
        self.mid_scale.grid(row=1, column=1, padx=5)
        self.mid_scale.set(0)  # Default mid gain

        self.treble_label = ttk.Label(eq_frame, text="Treble:")
        self.treble_label.grid(row=2, column=0, padx=5)

        self.treble_scale = ttk.Scale(eq_frame, from_=-10, to=10, orient=tk.HORIZONTAL, command=self.set_treble)
        self.treble_scale.grid(row=2, column=1, padx=5)
        self.treble_scale.set(0)  # Default treble gain

        # Volume control
        volume_frame = ttk.Frame(self.root)
        volume_frame.pack(pady=10)

        self.volume_label = ttk.Label(volume_frame, text="Volume:")
        self.volume_label.grid(row=0, column=0, padx=5)

        self.volume_scale = ttk.Scale(volume_frame, from_=0.0, to=1.0, orient=tk.HORIZONTAL, command=self.set_volume)
        self.volume_scale.grid(row=0, column=1, padx=5)
        self.volume_scale.set(0.5)  # Default volume


        # Playlist panel
        playlist_frame = ttk.Frame(self.root)
        playlist_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)

        self.playlist_label = ttk.Label(playlist_frame, text="Playlist:")
        self.playlist_label.pack(pady=5)

        self.playlist_box = tk.Listbox(playlist_frame, selectmode=tk.SINGLE)
        self.playlist_box.pack(fill=tk.BOTH, expand=True)
        self.playlist_box.bind('<<ListboxSelect>>', self.on_select)

        # Title label
        self.title_label = ttk.Label(self.root, text="Flexidoba", foreground="blue", font=("Arial", 30, "bold"))
        self.title_label.pack(pady=10)

        # Spotify search
        spotify_frame = ttk.Frame(self.root)
        spotify_frame.pack(pady=10)

        self.search_label = ttk.Label(spotify_frame, text="Search Spotify:")
        self.search_label.grid(row=0, column=0, padx=5)

        self.search_entry = ttk.Entry(spotify_frame)
        self.search_entry.grid(row=0, column=1, padx=5)

        self.search_button = ttk.Button(spotify_frame, text="Search", command=self.search_spotify)
        self.search_button.grid(row=0, column=2, padx=5)

    def load_music(self):
        files = filedialog.askopenfilenames(filetypes=[("MP3 Files", "*.mp3")])
        for file in files:
            self.playlist.append(file)
            self.playlist_box.insert(tk.END, os.path.basename(file))

    def play_music(self):
     if self.playlist:
        try:
            song = self.playlist[self.current_song_index]
            pygame.mixer.music.load(song)
            pygame.mixer.music.set_volume(0.5)  # Adjust volume as needed
            pygame.mixer.music.play()
            self.display_metadata(song)
            # Highlight currently playing song in the playlist
            self.playlist_box.selection_clear(0, tk.END)
            self.playlist_box.selection_set(self.current_song_index)
            self.playlist_box.activate(self.current_song_index)
        except pygame.error as e:
            messagebox.showerror("Playback Error", f"An error occurred while playing the song: {str(e)}")
     else:
        messagebox.showinfo("No Songs", "Please load some songs to play.")


    def pause_music(self):
        pygame.mixer.music.pause()

    def stop_music(self):
        pygame.mixer.music.stop()

    def next_song(self):
        if self.playlist:
            self.current_song_index = (self.current_song_index + 1) % len(self.playlist)
            self.play_music()

    def prev_song(self):
        if self.playlist:
            self.current_song_index = (self.current_song_index - 1) % len(self.playlist)
            self.play_music()

    def shuffle_playlist(self):
        random.shuffle(self.playlist)
        self.current_song_index = 0
        self.play_music()

    def toggle_repeat(self):
        self.repeat_on = not self.repeat_on
        try:
            if self.repeat_on:
                repeat_image_path = os.path.join('images', 'repeat_icon.png')
            else:
                repeat_image_path = os.path.join('images', 'repeat_icon.png')

            repeat_image = Image.open(repeat_image_path).resize((32, 32))
            self.repeat_icon = ImageTk.PhotoImage(repeat_image)
            self.repeat_button.configure(image=self.repeat_icon)
        except FileNotFoundError:
            messagebox.showerror("Error", f"Image file not found: {repeat_image_path}")

    def set_volume(self, value):
        volume = float(value)
        pygame.mixer.music.set_volume(volume)

    def set_bass(self, value):
        self.bass_gain = float(value)

    def set_mid(self, value):
        self.mid_gain = float(value)

    def set_treble(self, value):
        self.treble_gain = float(value)

    def display_metadata(self, song):
        audio = MP3(song)
        length = audio.info.length
        self.root.title(f"{os.path.basename(song)} - {int(length // 60)}:{int(length % 60):02d}")

    def on_select(self, event):
        if self.playlist_box.curselection():
            self.current_song_index = self.playlist_box.curselection()[0]
            self.play_music()

    def search_spotify(self):
        query = self.search_entry.get()
        if query:
            results = self.sp.search(q=query, limit=10)
            self.spotify_results = results['tracks']['items']
            self.playlist_box.delete(0, tk.END)
            for idx, track in enumerate(self.spotify_results):
                track_name = track['name']
                track_artist = track['artists'][0]['name']
                self.playlist_box.insert(tk.END, f"{track_name} - {track_artist}")
            self.spotify_playing = True

    def apply_equalizer(self, audio):
        # Extract raw audio data and metadata
        sample_width = audio.sample_width
        sample_rate = audio.frame_rate
        channels = audio.channels
        samples = np.array(audio.get_array_of_samples())

        # Normalize to between -1 and 1
        if sample_width == 1:
            samples = samples.astype(np.float32) / 128.0 - 1.0
        elif sample_width == 2:
            samples = samples.astype(np.float32) / 32768.0

        # Apply equalizer settings
        bands = {
            (20, 300): self.bass_gain,
            (300, 4000): self.mid_gain,
            (4000, 16000): self.treble_gain
        }

        equalized_samples = self.apply_band_equalizer(samples, sample_rate, bands)

        # Convert back to original format
        if sample_width == 1:
            equalized_samples = (equalized_samples + 1.0) * 128.0
        elif sample_width == 2:
            equalized_samples = equalized_samples * 32768.0

        equalized_samples = np.clip(equalized_samples, -32768, 32767)
        equalized_samples = equalized_samples.astype(np.int16)

        # Create a new AudioSegment object
        equalized_audio = AudioSegment(
            data=equalized_samples.tobytes(),
            sample_width=sample_width,
            frame_rate=sample_rate,
            channels=channels
        )

        return equalized_audio

    def apply_band_equalizer(self, samples, sample_rate, bands):
        equalized_samples = samples.copy()

        for band, gain in bands.items():
            low, high = band
            if low == 0:
                low_cutoff = 1 / (sample_rate / 2)
            else:
                low_cutoff = low / (sample_rate / 2)
            high_cutoff = high / (sample_rate / 2)
            b, a = butter(1, [low_cutoff, high_cutoff], btype='band')
            equalized_samples = lfilter(b, a, equalized_samples) * gain

        return equalized_samples

if __name__ == "__main__":
    root = tk.Tk()
    music_player = MusicPlayer(root)
    root.mainloop()

